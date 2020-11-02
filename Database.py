import json
import pymongo
from datetime import timedelta
from datetime import date
import datetime
import os


class Database:
    def __init__(self, config_file="config.json"):
        self.connect()
        self.config_file = os.path.abspath(config_file)
        self.connect_string = ""
        self.client = None
        self.database = None
        self.trainings = None

    def connect(self):
        # get configuration
        if not os.path.isfile(self.config_file):
            return False

        with open(self.config_file) as config_file:
            db_conf = json.load(config_file)
        # use connect string
        self.connect_string = db_conf["database-connect-string"]
        # connect client
        self.client = pymongo.MongoClient(self.connect_string)
        self.database = self.client.lockdown_training
        # collection for trainings
        self.trainings = self.database["trainings"]
        return True
    
    def add_training(self, training_date, time):
        """ 
        add one training to the database with a unix timestamp
        """
        # make a correct date out of date and time
        training_date = datetime.datetime(
            training_date.year,
            training_date.month,
            training_date.day,
            int(time.split(':')[0]),
            int(time.split(':')[1])
        )
        # create a unix timestamp
        unix_timestamp = int(training_date.strftime("%s"))
        training = {
            "date": unix_timestamp,
            "time": time
        }
        self.trainings.insert_one(training)
        
    def add_subtraining(self, training_date, coach, title, description):
        pass
        # training = {
        #     "date": training_date,
        #     "coach": coach
        # }
        # self.trainings.insert_one(training)

    def get_trainings(self):
        """
        return all trainings in the database as a list
        of dicts
        """
        trainings = self.trainings.find()
        trainings_list = []
        for training in trainings:
            trainings_list.append(training)
        return trainings_list

    def create_trainings(self, number_of_days):
        """Create all trainings according to the config
        file if they don't exist yet """
        # get the weekdays from the config file
        with open('config.json') as config_file:
            db_conf = json.load(config_file)
        training_settings = db_conf["trainings"]
        # loop through training weekdays
        for training in training_settings:
            today = date.today()
            # loop through all days in the future
            for i in range(number_of_days):
                day = today + timedelta(i)
                if day.weekday() == training["weekday"]:
                    res = self.trainings.find_one({"date": str(day)})
                    if res is None:
                        self.add_training(training_date=day, time=training["time"])

    def next_trainings(self, number_of_trainings: int):
        """ return the next n trainings from the database as a
        list of dicts """
        trainings_list = self.trainings.find().sort("date")
        trainings = []
        for tr in trainings_list:
            trainings.append(tr)
        if len(trainings) >= number_of_trainings:
            trainings = trainings[0:number_of_trainings]
            return trainings

    def delete_all_trainings(self):
        """
        delete all training database entries
        """
        self.trainings.drop()
