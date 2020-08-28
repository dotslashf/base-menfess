from bot import Twitter
from db import Database
from args import create_parser
import tweepy
import time
import argparse


args = create_parser()

db_name = args.database

db = Database(args.menfess)
db.connect_db(db_name)
db.select_collection('menfess_credentials')

credentials = db.get_credentials()

consumer_key = credentials['consumerKey']
consumer_secret = credentials['consumerSecret']
access_token = credentials['accessToken']
access_token_secret = credentials['accessSecret']

bot = Twitter(consumer_key, consumer_secret,
              access_token, access_token_secret, args)


def get_dms(latest_id):
    new_latest_id = latest_id

    print('📥 Fetching DMs ')
    for dm in tweepy.Cursor(bot.api.list_direct_messages).items():
        new_latest_id = max(dm.id, new_latest_id)
        text = dm.message_create['message_data']['text']
        sender_id = dm.message_create['sender_id']
        id = dm.id

        sender = bot.api.get_user(sender_id)
        if bot.get_criteria_sender(sender.id):
            print(f"{id}\n{sender.screen_name}\n{text}\n")
            print('Added 1 DM')

        if id == latest_id:
            break
        time.sleep(5)


db.select_collection(args.menfess)
l = db.find_last_object()
last_id = l['latest_dm_id']
get_dms(last_id)
