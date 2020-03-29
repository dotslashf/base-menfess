import requests
import io
import tweepy
import os
import time
import yaml
from requests_oauthlib import OAuth1Session
from db_mongo import Database
from dict import error_code, trigger_words
from PIL import Image


class Twitter:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.auth = self.authentication()
        self.api = tweepy.API(self.auth)
        self.me = self.api.me()
        self.triggering_words = trigger_words
        self.error_code = self.load_dict(error_code)
        self.time_interval = 15
        self.path_media = "img/current_img.png"
        self.db_name = os.environ.get("DB_NAME_DM_TEST")

    def authentication(self):
        self.auth = tweepy.OAuthHandler(
            self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        return self.auth

    def load_dict(self, dict_name):
        dict = yaml.load("{}".format(dict_name), Loader=yaml.BaseLoader)
        return dict

    def tweet_status(self, dm):
        status = dm['text']
        # self.api.update_status(status=status)
        print("tweeted: ", status)

    def tweet_status_with_media(self, dm, filename):
        status = dm['text']
        # self.api.update_with_media(filename=filename, status=status)
        print("tweeted: ", status)

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

    def get_dms(self, latest_id):
        list_dm = []
        new_latest_id = latest_id
        for dm in tweepy.Cursor(self.api.list_direct_messages).items():
            new_latest_id = max(dm.id, new_latest_id)
            text = dm.message_create['message_data']['text']
            sender = dm.message_create['sender_id']
            id = dm.id
            time.sleep(1)

            if id != latest_id:
                if (self.triggering_words in text) or (self.triggering_words.capitalize() in text):
                    if "attachment" in dm.message_create['message_data']:
                        dm_media_url = dm.message_create['message_data']["attachment"]["media"]["media_url_https"]
                        list_dm.append(
                            {'text': text, 'id': id, 'sender': sender, 'media_url': dm_media_url})
                    else:
                        dm_media_url = None
                        list_dm.append(
                            {'text': text, 'id': id, 'sender': sender, 'media_url': dm_media_url})
            elif id == latest_id:
                break

        self.process_dm(list_dm)
        return new_latest_id

    def process_dm(self, list_dm):
        db = Database()
        db.connect_db(self.db_name)
        db.select_col('dm')

        for index, dm in enumerate(reversed(list_dm)):
            print(index + 1)
            try:
                if dm['media_url'] is not None:
                    file = self.get_dm_media(dm['media_url'])
                    self.tweet_status_with_media(dm, file)
                else:
                    self.tweet_status(dm)

            except tweepy.TweepError as e:
                print(e.api_code, e.response)
            db.insert_object({'latest_dm_id': dm['id']})
            time.sleep(self.time_interval)
