from bot import Twitter
from db_mongo import Database
from datetime import datetime
from dateutil import relativedelta
# from art import *
import json
import os
from dotenv import load_dotenv
import tweepy
# from dict import
import yaml
import random
from datetime import datetime
import pprint
from tweepy.models import Status
import requests
from requests_oauthlib import OAuth1Session
from PIL import Image
import io
import time

load_dotenv()

db_name = "unairfess"

db = Database()
db.connect_db(db_name)
db.select_col('environment')

consumer_key = db.find_object('consumer_key')
consumer_secret = db.find_object('consumer_secret')
access_token = db.find_object('access_token')
access_token_secret = db.find_object('access_token_secret')

bot = Twitter(consumer_key, consumer_secret,
              access_token, access_token_secret, db_name)


def get_dms(latest_id):
    list_dm = []
    new_latest_id = latest_id

    print('📥 Fetching DMs ')
    for dm in tweepy.Cursor(bot.api.list_direct_messages).items():
        new_latest_id = max(dm.id, new_latest_id)
        text = dm.message_create['message_data']['text']
        sender = dm.message_create['sender_id']
        mutual = bot.is_mutual(sender)
        id = dm.id
        if mutual:
            print(id, text)
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
        if id == latest_id:
            break
        time.sleep(5)

    for dm in list_dm:
        print(dm)


db.select_col('dm')
l = db.find_last_object()
last_id = l['latest_dm_id']
get_dms(last_id)
