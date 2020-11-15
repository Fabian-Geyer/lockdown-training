from Database import Database
from Notifier import Notifier
import datetime
import constants as c
from User import User
from Training import Training


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


def notify_user(db: Database, sub_tr: Training, notifier: Notifier, user: User, time_to_training: datetime.timedelta, message: str):
    """
    Notify a user with the given message

    :param db: Database object
    :param sub_tr: Subtraining object
    :param notifier: Notifier object
    :param user: User object
    :param time_to_training: Time till the next training starts
    :param message: Notification message
    :return:
    """
    is_now = time_to_training <= c.NEXT_TRAINING_NOTIFY_NOW
    is_far = time_to_training < c.NEXT_TRAINING_NOTIFY_FAR
    if is_now and user.is_notified_now() is True:
        db.set_notify_now_flag(True, sub_tr, user)
        return
    elif is_far and user.is_notified_far() is True:
        db.set_notify_far_flag(True, sub_tr, user)
        return
    notifier.notify_by_chat_id(
        message=message,
        chat_id=user.get_chat_id()
    )


def notify_all_attendees(db: Database, training: dict, notifier: Notifier, time_to_training: datetime.timedelta):
    """notify all attendees about their trainings now.

    :param db: Database object
    :type db: Database
    :param training: training data
    :type training: dict
    :param notifier: notifier instance
    :type notifier: Notifier
    :param time_to_training: Timedelta till next training
    :type time_to_training: datetime.timedelta
    """

    is_now = time_to_training <= c.NEXT_TRAINING_NOTIFY_NOW
    is_far = time_to_training < c.NEXT_TRAINING_NOTIFY_FAR

    for sub in training["subtrainings"]:
        sub_tr = Training(from_dict=sub)
        if is_now:
            message = get_message(training=training, subtraining=sub)
        elif is_far:
            message = get_message_next_day(training=training, subtraining=sub)
        else:
            return
        for att in sub["attendees"]:
            attendee = User(from_dict=att)
            notify_user(db, sub_tr, notifier, attendee, time_to_training, message)
        coach = sub_tr.get_coach()
        notify_user(db, sub_tr, notifier, coach, time_to_training, message)
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
    notify_all_attendees(db=db, training=next_training, notifier=notifier, time_to_training=time_to_training)
    

if __name__ == "__main__":
    """ run this file every hour"""
    main()
