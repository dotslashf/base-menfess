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
            text = dm.message_create['message_data']['text']
            sender = dm.message_create['sender_id']
            id = dm.id
            if (self.triggering_words in text) or (self.triggering_words.capitalize() in text):
                print(dm.id, text)
                list_dm.append({'text': text, 'id': id, 'sender': sender})
            if id == latest_id:
                return list_dm

        return list_dm

    def process_dm(self, list_dm):
        db = Database()
        db.connect_db(self.db_name)
        db.select_col('dm')

        for dm in reversed(list_dm):
            try:
                sender = self.api.get_user(id=dm['sender'])
                status = dm['text']
                self.api.update_status(status=status)
                print("tweeted: ", status, "sender: ", sender.screen_name)
            except tweepy.TweepError as e:
                print(e.api_code, e.response)
            db.insert_object({'latest_id': dm['id']})
            time.sleep(self.time_interval)

        return dm['id']
