import sys
import time
import os
import argparse
from bot import Twitter
from db_mongo import Database


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mutual", type=str2bool, nargs='?',
                    const=True, default=False,
                    help="Check mutual or not")
parser.add_argument("-db", "--database", type=str,
                    help="Connect to preferred db")
args = parser.parse_args()

db_name = os.environ.get(args.database)

db = Database()
db.connect_db(db_name)
db.select_col('environment')

consumer_key = db.find_object('consumer_key')
consumer_secret = db.find_object('consumer_secret')
access_token = db.find_object('access_token')
access_token_secret = db.find_object('access_token_secret')

def main(ck, cs, at, ats):
    bot = Twitter(ck, cs, at, ats, args)
    db = Database()
    db.connect_db(db_name) 
    db.select_col('dm')

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
