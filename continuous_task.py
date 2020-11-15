from Database import Database
from Notifier import Notifier
import datetime
import constants as c


def get_message_next_day(training: dict, subtraining: dict) -> str:
    """create the message for the given training and subtraining

    :param training: training date
    :type training: dict
    :param subtraining: subtraining data
    :type subtraining: dict
    :return: message to user
    :rtype: str
    """
    message = "Morgen hast du Training um " +\
              training["time"] + " Uhr!"\
              "\n\nErwärmung:" + \
              "\n" + training["link"] +\
              "\n\nTraining bei " + subtraining["coach"]["full_name"] + \
              ": \n" + subtraining["link"] + \
              "\n Viel Spaß!"
    return message


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


def notify_all_attendees(training: dict, notifier: Notifier, time_to_training: datetime.timedelta):
    """notify all attendees about their trainings now.

    :param training: training data
    :type training: dict
    :param notifier: notifier instance
    :type notifier: Notifier
    :param time_to_training: Timedelta till next training
    :type time_to_training: datetime.timedelta
    """

    for sub in training["subtrainings"]:
        if time_to_training <= c.NEXT_TRAINING_NOTIFY_NOW:
            message = get_message(training=training, subtraining=sub)
        elif time_to_training < c.NEXT_TRAINING_NOTIFY_FAR:
            message = get_message_next_day(training=training, subtraining=sub)
        else:
            return
        for att in sub["attendees"]:
            if (time_to_training <= c.NEXT_TRAINING_NOTIFY_NOW and sub["notified_now"] == 1) \
               or (time_to_training < c.NEXT_TRAINING_NOTIFY_FAR and sub["notified_far"] == 1):
                continue
            notifier.notify_by_chat_id(
                message=message,
                chat_id=att["chat_id"]
            )
    return


def main():
    notifier = Notifier()
    db = Database(c.CONFIG_FILE, debug_mode=c.DEBUG_MODE)
    next_training = db.next_trainings(number_of_trainings=1)[0]
    now = datetime.datetime.now()
    training_start_time = datetime.datetime.fromtimestamp(next_training["date"])
    if now > training_start_time:
        return
    time_to_training = training_start_time - now
    notify_all_attendees(training=next_training, notifier=notifier, time_to_training=time_to_training)
    

if __name__ == "__main__":
    """ run this file every hour"""
    main()
