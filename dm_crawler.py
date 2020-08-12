from bot import Twitter
from db_mongo import Database
import tweepy
import time
import argparse


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
parser.add_argument("-db", "--database", type=str,
                    help="Connect to preferred db")
parser.add_argument("-m", "--mutual", type=str2bool, nargs='?',
                    const=True, default=False,
                    help="Check mutual or not")
args = parser.parse_args()

db_name = args.database

db = Database()
db.connect_db(db_name)
db.select_col('environment')

consumer_key = db.find_object('consumer_key')
consumer_secret = db.find_object('consumer_secret')
access_token = db.find_object('access_token')
access_token_secret = db.find_object('access_token_secret')

bot = Twitter(consumer_key, consumer_secret,
              access_token, access_token_secret, args)


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
