import requests
import io
import tweepy
import os
import time
import yaml
from requests_oauthlib import OAuth1Session
from dateutil import relativedelta
from datetime import datetime
from db import Database
from PIL import Image
from splicer import Splicer


class Twitter:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, args):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.auth = self.authentication()
        self.api = tweepy.API(self.auth)
        self.me = self.api.me()
        self.trigger_word = None
        self.message_reply = None
        self.tweet_interval = None
        self.path_media = "img/current_img.png"
        self.args = args
        self.db_name = args.database
        self.menfess = args.menfess
        self.current_dm = None
        self.filter_words = []
        self.mutual_only = None
        self.min_tweets = 0
        self.min_followers = 0
        self.min_join_month = 0
        self.soft_block_lists = []

    def authentication(self):
        self.auth = tweepy.OAuthHandler(
            self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        return self.auth

    def get_configuration(self):
        db = Database(self.menfess)
        db.connect_db(self.db_name)
        configuration = db.get_configuration()
        self.trigger_word = configuration['triggerWord']
        self.message_reply = configuration['messageReply']
        self.tweet_interval = configuration['tweetInterval']
        self.min_tweets = configuration['minTweets']
        self.min_followers = configuration['minFollowers']
        self.min_join_month = configuration['minJoinMonths']
        self.mutual_only = configuration['mutualOnly']
        self.soft_block_lists = configuration['softBlockLists']
        self.filter_words = configuration['filterWords']

    def is_mutual(self, sender):
        source_id = self.me.id
        if self.mutual_only:
            fs = self.api.show_friendship(
                source_id=source_id, target_id=sender.id)
            return fs[0].followed_by and fs[1].followed_by
        else:
            return True

    def get_account_old(self, user_old):
        today = datetime.now()
        diff = relativedelta.relativedelta(today, user_old)
        return diff.months+(diff.years*12)

    def get_criteria_sender(self, sender):
        sender = self.api.get_user(int(sender))
        account_old = self.get_account_old(sender.created_at.date())
        followers = sender.followers_count
        total_tweets = sender.statuses_count

        for i in range(len(self.soft_block_lists)):
            if sender == self.soft_block_lists[i]['id']:
                return False, "soft blocked"

        if self.is_mutual(sender):
            is_elligible = (account_old >= self.min_join_month) and (
                followers >= self.min_followers) and (total_tweets >= self.min_tweets)

            if (account_old < self.min_join_month):
                reason = 'account not old enough'
            elif (followers < self.min_followers):
                reason = 'followers not enough'
            elif (total_tweets < self.min_tweets):
                reason = 'total tweets not enough'
            else:
                reason = 'in criteria'

            return is_elligible, reason

        else:
            return False, "not mutual"

    def tweet_status(self, dm):
        if self.is_dm_longer(dm):
            self.tweet_in_thread(dm, None)
        else:
            status = dm['text']
            self.api.update_status(status=status)

    def tweet_status_with_media(self, dm, filename):
        if self.is_dm_longer(dm):
            self.tweet_in_thread(dm, filename)
        else:
            status = dm['text']

            final_text = ''
            words = [i for j in status.split() for i in (j, ' ')][:-1]
            for word in words:
                if 'http' in word:
                    word = word.replace(word, '')
                    final_text += word
                else:
                    final_text += word

            self.api.update_with_media(filename=filename, status=final_text)

    def is_dm_longer(self, dm):
        return len(dm['text']) > 280

    def tweet_in_thread(self, dm, filename):
        tweets = Splicer(dm['text'])
        tweets = tweets.split_tweets()

        if dm['media_url']:
            for i in range(len(tweets)):
                if i == 0:
                    final_text = ''
                    words = [i for j in tweets[i].split()
                             for i in (j, ' ')][:-1]
                    for word in words:
                        if 'http' in word:
                            word = word.replace(word, '')
                            final_text += word
                        else:
                            final_text += word

                    self.api.update_with_media(
                        filename=filename, status=final_text)
                else:
                    user_tl = self.api.user_timeline(count=5)
                    latest_tweet_id = user_tl[0].id
                    self.api.update_status(
                        status=tweets[i], in_reply_to_status_id=latest_tweet_id)
                time.sleep(5)
        else:
            for i in range(len(tweets)):
                if i == 0:
                    self.api.update_status(status=tweets[i])
                else:
                    user_tl = self.api.user_timeline(count=5)
                    latest_tweet_id = user_tl[0].id
                    self.api.update_status(
                        status=tweets[i], in_reply_to_status_id=latest_tweet_id)

    def get_dm_media(self, url):
        client = OAuth1Session(self.consumer_key,
                               client_secret=self.consumer_secret,
                               resource_owner_key=self.access_token,
                               resource_owner_secret=self.access_token_secret)
        r = client.get(url)
        media = Image.open(io.BytesIO(r.content))
        media.save(self.path_media)
        time.sleep(1)
        media = Image.open(self.path_media)
        return media.filename

    def find_menfess(self):
        if len(self.current_dm) < 15:
            return None

        latest_tweet = self.api.user_timeline(count=10)
        for tweet in latest_tweet:
            if self.current_dm[0:15] in tweet.text:
                return tweet.id
            else:
                return None

    def notify_menfess_is_sent(self, sender_id):
        latest_tweet_id = self.find_menfess()
        if latest_tweet_id != None:
            base_menfess = self.me
            text = f"{self.message_reply} https://twitter.com/{base_menfess.screen_name}/status/{latest_tweet_id}"
            try:
                self.api.send_direct_message(sender_id, text)
                print("User notified!")
            except tweepy.TweepError as error:
                print(error)
        else:
            print("Menfess not found / Menfess to short to be identified")

    def is_contained_filtered_words(self, text):
        for words in self.filter_words:
            if words not in text:
                continue
            else:
                print("Contained filtered words, skipped")
                return True
        return False

    def is_blank_menfess(self, dm):
        pass
        text = dm.message_create['message_data']['text']
        attachment = dm.message_create['message_data']
        if (len(text.split()) == 1) and "attachment" not in attachment:
            return True
        else:
            return False

    def get_dms(self, latest_id):
        self.get_configuration()
        list_dm = []
        new_latest_id = latest_id

        print('📥 Fetching DMs ')
        for dm in tweepy.Cursor(self.api.list_direct_messages).items(limit=50):
            new_latest_id = max(dm.id, new_latest_id)
            text = dm.message_create['message_data']['text']
            sender = dm.message_create['sender_id']
            id = dm.id

            if id != latest_id:
                if ((self.trigger_word in text) or (self.trigger_word.capitalize() in text)) and (not self.is_contained_filtered_words(text)):
                    is_in_criteria, reason = self.get_criteria_sender(sender)
                    if is_in_criteria and not self.is_blank_menfess(dm):
                        if "attachment" in dm.message_create['message_data']:
                            dm_media_url = dm.message_create['message_data']["attachment"]["media"]["media_url_https"]
                            list_dm.append(
                                {'text': text, 'id': id, 'sender': sender, 'media_url': dm_media_url})
                            print('Added 1 DM')
                        else:
                            dm_media_url = None
                            list_dm.append(
                                {'text': text, 'id': id, 'sender': sender, 'media_url': dm_media_url})
                            print('Added 1 DM')
                    else:
                        print(f'Reason skipped: {reason}')
            elif id == latest_id:
                break

        self.process_dm(list_dm)
        return new_latest_id

    def process_dm(self, list_dm):
        db = Database(self.menfess)
        db.connect_db(self.db_name)
        db.select_collection(self.menfess)

        if len(list_dm) != 0:
            print(f'Processing {len(list_dm)} DMs:')

        for index, dm in enumerate(reversed(list_dm)):
            sender = self.api.get_user(id=dm['sender'])

            try:
                if dm['media_url']:
                    file = self.get_dm_media(dm['media_url'])
                    self.tweet_status_with_media(dm, file)
                else:
                    self.tweet_status(dm)

                self.current_dm = dm['text']
                print(
                    f"\n📨 | #️⃣ : {index+1} | 👥 : @{sender.screen_name} | 💬 : {dm['text']}")
                self.notify_menfess_is_sent(sender.id)

                db.insert_object(
                    {'latest_dm_id': dm['id'], 'sender': sender.id_str, 'text': dm['text'], 'username': sender.screen_name})

            except tweepy.TweepError as error:
                print(f"{error.api_code}, {error.response}, {error.reason}")
                continue

            time.sleep(self.tweet_interval)
