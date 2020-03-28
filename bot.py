import tweepy
import os
import time
import yaml
import random
from db_mongo import Database
from dict import error_code, trigger_words


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
        self.db_name = os.environ.get("DB_NAME_DM_TEST")

    def authentication(self):
        self.auth = tweepy.OAuthHandler(
            self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        return self.auth

    def load_dict(self, dict_name):
        dict = yaml.load("{}".format(dict_name), Loader=yaml.BaseLoader)
        return dict

    def get_dms(self, latest_id):
        list_dm = []

        for dm in tweepy.Cursor(self.api.list_direct_messages).items():
            dm_text = dm.message_create['message_data']['text']
            print(dm.id, dm_text)
            list_dm.append(dm_text)
            if dm.id == latest_id:
                latest_id = int(dm.id)
                return list_dm, latest_id

        latest_id = int(dm.id)
        return list_dm, latest_id

    def process_dm(self, list_dm):
        db = Database()
        db.connect_db(self.db_name)
        db.select_col('dm')

        for dm in reversed(list_dm):
            if self.triggering_words in dm:
                print("tweeted: ", dm)
                self.api.update_status(status=dm)
                time.sleep(self.time_interval)
