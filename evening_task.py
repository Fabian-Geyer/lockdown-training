from Database import Database
from Notifier import Notifier
import datetime
import constants as c


def notify_all_attendees(training: dict, notifier: Notifier):
    """notify all attendees about their traings tomorrow.

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


def get_message(training: dict, subtraining: dict) -> str:
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
    

def main():
    notifier = Notifier()
    db = Database(c.CONFIG_FILE, debug_mode=c.DEBUG_MODE)
    
    next_tr = db.next_trainings(number_of_trainings=1)[0]
    training_day = next_tr["date"].date()
    tomorrow = datetime.date.today() + datetime.timedelta(days=c.NEXT_TRAINING_NOTIFY_DAYS)
    
    if training_day == tomorrow:
        notify_all_attendees(training=next_tr, notifier=notifier)
        

if __name__ == "__main__":
    main()
