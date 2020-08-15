import sys
import time
import os
import argparse
from bot import Twitter
from db import Database
from args import create_parser


args = create_parser()

if args.filter:
    with open(args.filter) as f:
        filters = f.read().split(', ')
    args.filter = filters
else:
    args.filter = ['^']

db = Database(args.menfess)
db.connect_db(args.database)
db.select_collection('menfess_credentials')

credentials = db.get_credentials()

consumer_key = credentials['consumerKey']
consumer_secret = credentials['consumerSecret']
access_token = credentials['accessToken']
access_token_secret = credentials['accessSecret']
is_active = credentials['isActive']
refresh_interval = args.refresh


def run(is_active):
    bot = Twitter(consumer_key, consumer_secret,
                  access_token, access_token_secret, args)
    db = Database(args.menfess)
    db.connect_db(args.database)
    db.select_collection(args.menfess)

    if is_active:
        print(f"Menfess is_active: {is_active}")
        l = db.find_last_object()
        last_id = l['latest_dm_id']

        latest_id = bot.get_dms(last_id)

        if last_id == latest_id:
            print('no new dm')

        for sec in range(refresh_interval * 60, 0, -1):
            sys.stdout.write("\r")
            sys.stdout.write("{:2d} second to check dm.\r".format(sec))
            sys.stdout.flush()
            time.sleep(1)

        db.select_collection('menfess_credentials')
        is_active = credentials['isActive']
    else:
        print(f"Menfess is_active: {is_active}")
        db.select_collection('menfess_credentials')
        is_active = credentials['isActive']
        time.sleep(60)


if __name__ == "__main__":
    while True:
        run(is_active)
