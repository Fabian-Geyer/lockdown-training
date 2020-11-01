import json
import pymongo
from datetime import timedelta
from datetime import date
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
    
    def add_training(self, date, time):
        # make a correct date out of date and time
        date = datetime.datetime(
            date.year,
            date.month,
            date.day,
            int(time.split(':')[0]),
            int(time.split(':')[1])
            )
        # create a unix timestamp
        unix_timestamp = date.strftime("%s")
        training = {
            "date": unix_timestamp,
            "time": time
        }
        self.trainings.insert_one(training)
        
    def add_subtraining(self, date, coach, title, description):
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

    def create_trainings(self, numberOfDays):
        # get the weekdays from the config file
        with open('config.json') as config_file:
            dbconf = json.load(config_file)
        training_settings = dbconf["trainings"]
        # loop through training weekdays
        for training in training_settings:
            today = date.today()
            # loop through all days in the future
            for i in range(numberOfDays):
                day = today + timedelta(i)
                if day.weekday() == training["weekday"]:
                    res = self.trainings.find_one({"date": str(day)})
                    if res == None:
                        self.add_training(date=day, time=training["time"])



    def delete_all_trainings(self):
        self.trainings.drop()

