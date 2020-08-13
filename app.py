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

consumer_key = credentials['consumer_key']
consumer_secret = credentials['consumer_secret']
access_token = credentials['access_token']
access_token_secret = credentials['access_secret']


def main(ck, cs, at, ats):
    bot = Twitter(ck, cs, at, ats, args)
    db = Database(args.menfess)
    db.connect_db(args.database)
    db.select_collection(args.menfess)

    minute_wait = 5

    while True:
        l = db.find_last_object()
        last_id = l['latest_dm_id']

        latest_id = bot.get_dms(last_id)

        if last_id == latest_id:
            print('no new dm')

        for sec in range(minute_wait * 60, 0, -1):
            sys.stdout.write("\r")
            sys.stdout.write("{:2d} second to check dm.\r".format(sec))
            sys.stdout.flush()
            time.sleep(1)


if __name__ == "__main__":
    main(consumer_key, consumer_secret,
         access_token, access_token_secret)
