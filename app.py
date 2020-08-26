import sys
import time
import os
import argparse
from tweepy import TweepError
from bot import Twitter
from db import Database
from args import create_parser


args = create_parser()

db = Database(args.menfess)
db.connect_db(args.database)

credentials = db.get_credentials()

consumer_key = credentials['consumerKey']
consumer_secret = credentials['consumerSecret']
access_token = credentials['accessToken']
access_token_secret = credentials['accessSecret']


def run(db):
    bot = Twitter(consumer_key, consumer_secret,
                  access_token, access_token_secret, args)

    configuration = db.get_configuration()
    is_active = configuration['isActive']
    refresh_interval = configuration['refreshInterval']

    if is_active and db.is_subscribe():
        print(f'Menfess status: {"on" if is_active else "off"}')
        db.select_collection(args.menfess)

        l = db.find_last_object()
        last_id = l['latest_dm_id']

        try:
            latest_id = bot.get_dms(last_id)
        except TweepError as error:
            print(f"{error.api_code}, {error.response}, {error.reason}")
            if error.api_code == 326 or error.api_code == "326":
                print("Account locked, sleeping 30 minutes")
                time.sleep(30 * 60)

        if last_id == latest_id:
            print('no new dm')

        print(f"Will check DMs in {refresh_interval} mins")
        time.sleep(refresh_interval * 60)

    else:
        if not db.is_subscribe():
            print("Continue subscription please")
            sys.exit()
        else:
            print(f'Menfess status: {"on" if is_active else "off"}')
            print("Check menfess status in 5 min")
            time.sleep(5 * 60)


if __name__ == "__main__":
    while True:
        run(db)
