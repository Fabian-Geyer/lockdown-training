import json
import pymongo
import datetime

class Database():
    def __init__(self):
        # establish connection
        self.connect()

    def connect(self):
        # get configuration
        with open('config.json') as config_file:
            dbconf = json.load(config_file)
        # use connect string
        self.connect_string = dbconf["database-connect-string"]
        # connect client
        self.client = pymongo.MongoClient(self.connect_string)
        self.database = self.client.lockdown_training
        # collection for trainings
        self.trainings = self.database["trainings"]

    def add_training(self, date, coach):
        training = {
            "date": date,
            "coach": coach
        }
        self.trainings.insert_one(training)

    def get_trainings(self):
        trainings = self.trainings.find()
        trainings_list = []
        for training in trainings:
            trainings_list.append(training)
        return trainings_list

    def create_trainings(self, numberOfWeeks, weekdays):
        pass

    def delete_all_trainings(self):
        self.trainings.drop()

db = Database()
# db.add_training("2019-12-11-15:00:00", "Fabi")
db.delete_all_trainings()
ts = db.get_trainings()
print(ts)