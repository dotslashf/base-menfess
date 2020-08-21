import requests
import io
import tweepy
import os
import time
import yaml
from requests_oauthlib import OAuth1Session
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
        self.filters = args.filter
        self.menfess = args.menfess
        self.current_dm = None

    def authentication(self):
        self.auth = tweepy.OAuthHandler(
            self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        return self.auth

    def set_configuration(self):
        db = Database(self.menfess)
        db.connect_db(self.db_name)
        configuration = db.get_configuration()
        self.trigger_word = configuration['triggerWord']
        self.message_reply = configuration['messageReply']
        self.tweet_interval = configuration['tweetInterval']

    def load_dict(self, dict_name):
        dict = yaml.load("{}".format(dict_name), Loader=yaml.BaseLoader)
        return dict

    def is_mutual(self, sender):
        source_id = self.me.id
        if self.args.mutual:
            fs = self.api.show_friendship(
                source_id=source_id, target_id=int(sender))
            return fs[0].followed_by and fs[1].followed_by
        else:
            return True

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
        for fil in self.filters:
            if fil not in text:
                continue
            else:
                print("Contained filtered words, skipped")
                return True
        return False

    def get_dms(self, latest_id):
        self.set_configuration()
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
                    if self.is_mutual(sender):
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
                        print('Skipped sender is not mutual')
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
                print(f"\n📨 | #️⃣ : {index+1} | 👥 : @{sender.screen_name} | 💬 : {dm['text']}")
                self.notify_menfess_is_sent(sender.id)

                db.insert_object(
                    {'latest_dm_id': dm['id'], 'sender': sender.id_str, 'text': dm['text'], 'username': sender.screen_name})

            except tweepy.TweepError as error:
                print(f"{error.api_code}, {error.response}, {error.reason}")
                continue

            time.sleep(self.tweet_interval)
