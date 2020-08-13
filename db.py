import pymongo
import os
import datetime


class Database:
    def __init__(self, menfess):

        if os.environ.get("APP_ENV") == 'LOCAL':
            self.client = pymongo.MongoClient(
                "mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
        else:
            db_user = os.environ.get("DB_USER")
            db_password = os.environ.get("DB_PASS")
            db_cluster = os.environ.get("DB_CLUSTER")
            self.client = pymongo.MongoClient(
                f"mongodb+srv://{db_user}:{db_password}@{db_cluster}-kdbqm.mongodb.net/test?retryWrites=true&w=majority")

        self.db = None
        self.collection = None
        self.menfess = menfess

    def connect_db(self, database):
        try:
            db_list = self.client.list_database_names()
            if database in db_list:
                print('\n🗄️  connected to {} database'.format(database))
                self.db = self.client[database]
            else:
                print('no database such as {} found'.format(database))

        except Exception as e:
            print(e)

    def select_collection(self, collection):
        try:
            col_list = self.db.list_collection_names()
            if collection in col_list:
                self.collection = self.db[collection]
                print("➡️  {} collection selected\n".format(collection))
            else:
                print('no collection {} found'.format(collection))
                print("creating collection")
                self.create_collection_first_time()
        except Exception as e:
            print(e)

    def find_last_object(self):
        if self.collection:
            list_data = self.collection.find().sort('_id', -1)
            return list_data[0]

    def insert_object(self, data):
        last = self.find_last_object()
        last_id = last['_id'] + 1

        data.update({'_id': last_id, 'date': datetime.datetime.now()})

        self.collection.insert_one(data)
        print(f"💾 DM ID: {data['latest_dm_id']} saved")

    def get_credentials(self):
        data = self.collection.find_one({'menfess_name': self.menfess})
        return data

    def find_and_modify(self, key, value):
        self.collection.find_one_and_update(
            {'key': key}, {'$set': {'value': value}})
        print("Value of {0} changed to {1}".format(key, value))

    def create_collection_first_time(self):
        self.collection = self.db[f"{self.menfess}"]
        data = {'_id': 1, 'latest_dm_id': '', 'sender_id': '',
                'text': '', 'date': datetime.datetime.now(), 'is_active': True}
        self.collection.insert_one(data)
        print(f"created {self.menfess} dm list")
