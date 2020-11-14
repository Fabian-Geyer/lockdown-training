from Database import Database
from Notifier import Notifier
from Training import Training
import datetime
import constants as c

def hourly_check():
    """[summary]
    """
    db = Database(c.CONFIG_FILE)
    next_training = db.next_trainings(number_of_trainings=1)[0]
    now = datetime.datetime.now()
    timedelta = datetime.timedelta(minutes=40)
    if (next_training["date"]-now < timedelta):
        print("training in less than " + str(timedelta))
    else:
        print("next training in: " + str(next_training["date"]-now)[:-10] + "h")

hourly_check()