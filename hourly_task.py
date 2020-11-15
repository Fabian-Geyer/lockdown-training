from Database import Database
from Notifier import Notifier
from Training import Training
import datetime
import constants as c
import time


def get_message(training: dict, subtraining: dict) -> str:
    """Generates a message to be sent when the training starts

    :param training: training date
    :type training: dict
    :param subtraining: subtraining data
    :type subtraining: dict
    :return: message to be sent
    :rtype: str
    """
    message = "Das Training startet jetzt!" +\
            "\n\n Starte durch mit der Erwärmung:"\
            "\n" + training["link"] +\
            "\n\nDanach gibt's dein Training bei " + subtraining["coach"]["full_name"] + \
            ": \n" + subtraining["link"] + \
            "\n Viel Spaß!"
    return message

def notify_all_attendees(training: dict, notifier: Notifier):
    """notify all attendees about their traings now.

    :param training: training data
    :type training: dict
    :param notifier: notifier instance
    :type notifier: Notifier
    """
    for sub in training["subtrainings"]:
        message = get_message(training=training, subtraining=sub)
        for att in sub["attendees"]:
            notifier.notify_by_chat_id(
                message=message,
                chat_id=att["chat_id"]
            )
    return

def wait_for_training(training: dict, timedelta: object, notifier: Notifier):
    """Wait until the training starts and then send a message to all
    attendees

    :param training: training date
    :type training: dict
    :param timedelta: timedelta object until training start
    :type timedelta: object
    :param notifier: notifier instance
    :type notifier: Notifier
    """
    time_to_sleep = timedelta
    time.sleep(time_to_sleep.total_seconds())
    notify_all_attendees(training=training, notifier=notifier)
    
def main():
    notifier = Notifier()
    db = Database(c.CONFIG_FILE, debug_mode=True)
    next_training = db.next_trainings(number_of_trainings=1)[0]
    now = datetime.datetime.now()
    time_to_training = next_training["date"] - now
    if  time_to_training < datetime.timedelta(hours=1):
        wait_for_training(
            training=next_training,
            timedelta=time_to_training,
            notifier=notifier)
    
if __name__ == "__main__":
    """ run this file every hour"""
    main()