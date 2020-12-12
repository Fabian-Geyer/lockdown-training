import datetime
import json
import os

import pymongo

from User import User
import constants as c
from Training import Training
import util


class Database:
    def __init__(self, config_file, debug_mode: bool):
        self.config_file = config_file
        self.connect_string = ""
        self.client = None
        self.database = None
        self.trainings = None
        self.connect(debug_mode)

    def connect(self, debug_mode: bool):
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
        if debug_mode:
            self.trainings = self.database["debug_trainings"]
        else:
            self.trainings = self.database["trainings"]
        return True

    def add_training(self, training_date, time):
        """add one training to the database with a unix timestamp
        and a random meeting link

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
            "subtrainings": [],
            "link": c.MEETING_BASE_URL + util.get_random_string(num_of_chars=c.RANDOM_STR_LEN)
        }
        self.trainings.insert_one(training)

    def subtraining_add_attendee(self, attendee: User, date: int, coach: User):
        """add an attendee to a subtraining"""
        # find the correct training by date
        training = self.trainings.find_one({"date": date})
        # delete user from all subtrainings
        for subtraining in training["subtrainings"]:
            for usr in subtraining["attendees"]:
                if attendee.chat_id == usr["chat_id"]:
                    subtraining["attendees"].remove(usr)
        # add the user to the wanted training
        for subtraining in training["subtrainings"]:
            if coach.get_chat_id() == subtraining["coach"]["chat_id"]:
                subtraining["attendees"].append(attendee.get_dict())
                break
        # overwrite the old object
        self.trainings.replace_one({"date": date}, training)
        return "user removed from all other trainings and added to desired subtraining"

    def training_add_attendee(self, attendee: User, date: int):
        """add an attendee to a training"""
        # check if user already is an attendee
        training = self.trainings.find_one({"date": date})
        for att in training["attendees"]:
            if att["chat_id"] == attendee.get_chat_id():
                return "user already is attendee"
        # add the user to the training
        self.trainings.update({"date": date}, {"$push": {"attendees": attendee.get_dict()}})
        return "user was added"

    def add_subtraining(self, training: Training):
        """Add a subtraining to the database, only if the given
        user has not signed in a training yet that day.
        Also give the subtraining a random meeting link

        :param training: Training object with user chosen data
        :type training: Training
        :return: Returns False if training already set by user
        :rtype: bool
        """
        training_data = training.get_dict()
        # add random link to database
        training_data["link"] = c.MEETING_BASE_URL + util.get_random_string(num_of_chars=c.RANDOM_STR_LEN)

        # check if user already has a training on that day
        main_training = self.trainings.find_one({"date": training_data["date"]})
        for subtraining in main_training["subtrainings"]:
            if training_data["coach"]["chat_id"] == subtraining["coach"]["chat_id"]:
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

    def get_my_trainings(self, user: User, role: int) -> list:
        """return all the subtrainings the user is
        in as specified in the role

        :param role: Specify the role of the user (can be COACH or ATTENDEE)
        :type role: int
        :param user: string with username
        :type user: str
        :param offset: Timedelta, how long a training can be in the past to be still shown
        :type offset: datetime.timedelta
        :return: returns the subtrainings as a list of dicts
        :rtype: list
        """
        trainings = self.trainings.find({})
        my_trainings = []
        for training in trainings:
            for subtraining in training["subtrainings"]:
                tr = Training(from_dict=subtraining)
                if (user.get_chat_id() == tr.get_coach().get_chat_id() and role == c.COACH)\
                        or (user in tr.get_attendees() and role == c.ATTENDEE):
                    if util.is_in_future(subtraining["date"], offset=offset):
                        my_trainings.append(tr)
        if len(my_trainings) > 0:
            my_trainings.sort(key=lambda x: x.date, reverse=False)
        return my_trainings

    def get_subtrainings(self, user: User) -> list:
        """get all subtrainings for a user

        :param user: user object
        :type user: obj
        :return: list of dicts with all subtrainings
        :rtype: list
        """
        trainings = self.trainings.find({})
        user_subtrainings = []
        for training in trainings:
            for sub in training["subtrainings"]:
                tr = Training(from_dict=sub)
                for attendee in tr.get_attendees():
                    if user.get_chat_id() == attendee.get_chat_id():
                        user_subtrainings.append(tr)
        return user_subtrainings

    def cancel_subtrainings(self, date: int, user: User):
        """remove user from the subtraining

        :param date: date as unix-timestamp
        :type date: int
        :param user: user object
        :type user: user
        :return: return success message
        :rtype: str
        """
        training = self.trainings.find_one({"date": date})
        for subtraining in training["subtrainings"]:
            for attendee in subtraining["attendees"]:
                if attendee["chat_id"] == user.get_chat_id():
                    subtraining["attendees"].remove(attendee)
        # replace the old database entry
        self.trainings.replace_one({"date": date}, training)
        return "user was removed"

    def remove_training_of_coach(self, coach: User, date: int) -> Training:
        """remove training by coach username and date. Return data of 
        the deleted training

        :param coach: object of type Coach
        :type coach: object
        :param date: date as int unix timestamp
        :type date: int
        :return: dict with data of the deleted training 
        :rtype: dict
        """
        training = self.trainings.find_one({"date": date})
        for subtraining in training["subtrainings"]:
            if coach.get_chat_id() == subtraining["coach"]["chat_id"]:
                removed_subtraining = subtraining
                # remove subtraining
                training["subtrainings"].remove(subtraining)
                # write to database
                self.trainings.replace_one({"date": date}, training)
                return Training(from_dict=removed_subtraining)

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

        added_trainings = 0
        for tr in trainings_list:
            if added_trainings >= number_of_trainings:
                break
            if util.is_in_future(tr["date"]):
                tr["date"] = datetime.datetime.fromtimestamp(tr["date"])
                trainings.append(tr)
                added_trainings += 1
        return trainings

    def delete_all_trainings(self):
        """delete all training database entries
        """
        self.trainings.drop()

    def set_notify_now_flag(self, flag: bool, subtraining: Training, user: User):
        training = self.trainings.find_one({"date": int(subtraining.get_date())})
        for sub in training["subtrainings"]:
            if user.is_coach():
                if user.get_chat_id() == sub["coach"]["chat_id"]:
                    sub["coach"]["notified_now"] = flag
            if user.is_attendee():
                for att in sub["attendees"]:
                    if user.get_chat_id() == att["chat_id"]:
                        att["notified_now"] = flag
        self.trainings.replace_one({"date": int(subtraining.get_date())}, training)

    def set_notify_far_flag(self, flag: bool, subtraining: Training, user: User):
        training = self.trainings.find_one({"date": int(subtraining.get_date())})
        for sub in training["subtrainings"]:
            if user.is_coach():
                if user.get_chat_id() == sub["coach"]["chat_id"]:
                    sub["coach"]["notified_far"] = flag
            if user.is_attendee():
                for att in sub["attendees"]:
                    if user.get_chat_id() == att["chat_id"]:
                        att["notified_far"] = flag
        self.trainings.replace_one({"date": int(subtraining.get_date())}, training)