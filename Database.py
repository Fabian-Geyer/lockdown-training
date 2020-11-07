import datetime
import json
import os

import pymongo

import constants as c
import util
from Training import Training


class Database:
    def __init__(self, config_file):
        self.config_file = config_file
        self.connect_string = ""
        self.client = None
        self.database = None
        self.trainings = None
        self.connect()

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
        """add one training to the database with a unix timestamp

        :param training_date: day of the new training
        :type training_date: datetime.date object
        :param time: time of the training in 24h format
        :type time: str
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
            "time": time,
            "attendees": [],
            "subtrainings": []
        }
        self.trainings.insert_one(training)

    def subtraining_add_attendee(self, user: str, date: int, coach_user: str):
        """add an attendee to a subtraining"""
        # find the correct training by date
        training = self.trainings.find_one({"date": date})
        # delete user from all subtrainings
        for subtraining in training["subtrainings"]:
            if user in subtraining["attendees"]:
                subtraining["attendees"].remove(user)
        for subtraining in training["subtrainings"]:
            if coach_user == subtraining["coach_user"]:
                subtraining["attendees"].append(user)
                break
        # overwrite the old object
        self.trainings.replace_one({"date": date}, training)
        return "user removed from all other trainings and added to desired subtraining"

    def training_add_attendee(self, user: str, date: int):
        """add an attendee to a training"""
        # check if user already is an attendee
        training = self.trainings.find_one({"date": date})
        if user in training["attendees"]:
            return "user already is attendee"
        # add the user to the training
        self.trainings.update({"date": date}, {"$push": {"attendees": user}})
        return "user was added"

    def add_subtraining(self, training: Training):
        """Add a subtraining to the database, only if the given
        user has not signed in a training yet that day

        :param training: Training object with user chosen data
        :type training: Training
        :return: Returns False if training already set by user
        :rtype: bool
        """
        training_data = {
            "date": int(training.get_date("%s")),
            "time": training.get_date("%H:%M"),
            "coach": training.get_coach_full_name(),
            "coach_user": training.get_coach_user_name(),
            "title": training.get_title(),
            "description": training.get_description(),
            "attendees": []
        }
        # check if user already has a training on that day
        main_training = self.trainings.find_one({"date": training_data["date"]})
        for subtraining in main_training["subtrainings"]:
            if training_data["coach_user"] == subtraining["coach_user"]:
                return False

        # add the subtraining to the main training
        self.trainings.update(
            {"date": training_data["date"]},
            {"$push": {"subtrainings": training_data}}
        )
        return True

    def get_trainings(self):
        """return all trainings in the database as a list
        of dicts

        :return: list of dicts with all trainings and their data
        :rtype: list of dicts
        """
        trainings = self.trainings.find()
        trainings_list = []
        for training in trainings:
            if util.is_in_future(training["date"]):
                training["date"] = datetime.datetime.fromtimestamp(training["date"])
                trainings_list.append(training)
        return trainings_list

    def get_my_trainings(self, user: str, role: int) -> list:
        """return all the subtrainings the user is
        in as specified in the role

        :param role: Specify the role of the user (can be COACH or ATTENDEE)
        :type role: int
        :param user: string with username
        :type user: str
        :return: returns the subtrainings as a list of dicts
        :rtype: list
        """
        trainings = self.trainings.find({})
        my_trainings = []
        for training in trainings:
            for subtraining in training["subtrainings"]:
                if (user == subtraining["coach_user"] and role == c.COACH) \
                        or user in subtraining["attendees"] and role == c.ATTENDEE:
                    if util.is_in_future(subtraining["date"]):
                        my_trainings.append(subtraining)
        return my_trainings

    def get_subtrainings(self, user: str) -> list:
        """get all subtrainings for a user

        :param user: string with telegram username
        :type user: str
        :return: list of dicts with all subtrainings
        :rtype: list
        """
        trainings = self.trainings.find({})
        user_subtrainings = []
        for training in trainings:
            for sub in training["subtrainings"]:
                if user in sub["attendees"]:
                    user_subtrainings.append(sub)
        return user_subtrainings

    def cancel_subtrainings(self, date: int, user: str):
        """remove the user from his/her subtraining by date

        :param date: date as integer in unix timestamp
        :type date: int
        :param user: string with telegram username
        :type user: str
        :return: return success message
        :rtype: str
        """
        training = self.trainings.find_one({"date": date})
        for subtraining in training["subtrainings"]:
            if user in subtraining["attendees"]:
                subtraining["attendees"].remove(user)
        # replace the old database entry
        self.trainings.replace_one({"date": date}, training)
        return "user was removed"

    def remove_training_of_coach(self, coach_user: str, date: int) -> dict:
        """remove training by coach username and date. Return data of 
        the deleted training

        :param coach_user: username coach
        :type coach_user: str
        :param date: date as int unix timestamp
        :type date: int
        :return: dict with data of the deleted training 
        :rtype: dict
        """
        training = self.trainings.find_one({"date": date})
        for subtraining in training["subtrainings"]:
            if coach_user == subtraining["coach_user"]:
                removed_subtraining = subtraining
                # remove subtraining
                training["subtrainings"].remove(subtraining)
                # write to database
                self.trainings.replace_one({"date": date}, training)
                return removed_subtraining

    def create_trainings(self, number_of_days: int):
        """Read training weekdays and time from the config file and 
        Create all trainings accordingly for the time period of the 
        next n days

        :param number_of_days: How many days ahead trainings get created
        :type number_of_days: int
        """
        # get the weekdays from the config file
        with open('config.json') as config_file:
            db_conf = json.load(config_file)
        training_settings = db_conf["trainings"]
        # loop through training weekdays
        for training in training_settings:
            today = datetime.date.today()
            # loop through all days in the future
            for i in range(number_of_days):
                day = today + datetime.timedelta(i)
                if day.weekday() == training["weekday"]:
                    res = self.trainings.find_one({"date": str(day)})
                    if res is None:
                        self.add_training(training_date=day, time=training["time"])

    def next_trainings(self, number_of_trainings: int):
        """return the next n trainings from the database as a
        list of dicts

        :param number_of_trainings: How many trainings will be returned
        :type number_of_trainings: int
        :return: the trainings as a List of dicts
        :rtype: list of dicts
        """
        trainings_list = self.trainings.find().sort("date")
        trainings = []
        for tr in trainings_list:
            if util.is_in_future(tr["date"]):
                tr["date"] = datetime.datetime.fromtimestamp(tr["date"])
                trainings.append(tr)
        if len(trainings) >= number_of_trainings:
            trainings = trainings[0:number_of_trainings]
            return trainings

    def delete_all_trainings(self):
        """delete all training database entries
        """
        self.trainings.drop()
