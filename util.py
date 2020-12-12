import datetime
import random
import string

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext

import Training
import constants as c


def action_selector(update: Update):
    """
    Main menu of the bot.
    :param update: Chat bot update object
    """
    reply_keyboard = c.MENU

    msg = 'Hi! Ich bin der Trainings-Bot. ' \
          'Ich helfe dir dein Training zu organisieren. ' \
          'Sende /{} um zum /{} zurückzukehren.\n\n' \
          'Folge {} um über die Trainings imformiert zu werden.\n\n' \
          'Was möchtest du tun?'.format(c.CMD_CANCEL, c.CMD_START, c.CHANNEL_ID)
    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )


def reset_data(context: CallbackContext):
    """
    Reset the data carried in the user_data of the chat context.
    :param context: Chat bot context
    """
    training = context.user_data["training"]
    training.reset()


def get_training(context: CallbackContext):
    """
    Get the training object from the chat context.
    :param context: Chat bot context
    :return: Training object
    """
    return context.user_data["training"]


def get_db(context: CallbackContext):
    """
    Get the database object from the chat context.
    :param context: Chat bot context
    :return: Database object
    """
    return context.user_data["db"]


def parse_bot_date(update: Update, training: Training, curr_state: int) -> int:
    """
    Parse the date command of an event
    :param update: Chat bot update object
    :param training: Training object
    :param curr_state: Current state of the conversation
    :return: The current state in case of a wrong command
    """
    selected_date = update.message.text.strip("/{}_".format(c.CMD_EVENT))

    if not selected_date.isnumeric() or int(selected_date) > len(training.get_possible_dates()):
        training.date_selector(update)
        return curr_state

    date_idx = int(selected_date) - 1
    training.set_date(training.get_possible_dates()[date_idx])


def get_readable_date_from_datetime(date: datetime) -> str:
    """
    Print a datetime object to a readable format
    :param date: Datetime object
    :return: Readable date string
    """
    return date.strftime(c.DATE_FORMAT)


def get_training_list(trainings: list, with_commands=False, with_attendees=False) -> [str, list]:
    """
    Get a list of trainings as formatted text.
    If needed commands to select each training can be generated
    :param trainings: List of trainings from the database
    :param with_commands: Bool to select whether to print commands, default:False
    :param with_attendees: If true, also get a list of attendees of the training
    :return: The formatted text and a list of commands
    """
    msg = ""
    commands = []
    for idx, t in enumerate(trainings):
        msg += "*{}. Training am {}*\n".format(idx + 1, t.get_date(c.DATE_FORMAT))
        if with_commands:
            command = "/{}_{}".format(c.CMD_TRAINING, idx + 1)
            msg += command + ": "
            commands.append([command])
        else:
            msg += "Titel: "
        msg += "{}".format(t.get_title().replace("\n", " "))
        msg += "\nAnzahl Teilnehmer: {}".format(len(t.get_attendees()))
        if with_attendees and len(t.get_attendees()) > 0:
            msg += "\nTeilnehmer: {}".format(", ".join([i.get_full_name() for i in t.get_attendees()]))
        msg += "\n\n"
    if with_commands:
        return msg, commands
    else:
        return msg, commands


def is_in_future(unix_timestamp: int, offset=datetime.timedelta(seconds=0)) -> bool:
    """Check if given date is in the future or not

    :param unix_timestamp: unix timestamp
    :type unix_timestamp: int
    :param offset: Timedelta, how long a training can be in the past to be still shown
    :type offset: datetime.timedelta
    :return: whether the date is in the futere
    :rtype: bool
    """
    now = datetime.datetime.now()
    date = datetime.datetime.fromtimestamp(unix_timestamp)
    return (now - offset) < date


def get_random_string(num_of_chars: int) -> str:
    """Return a random string of length n 
    with ASCII letters and digits 

    :param num_of_chars: length of the desired string
    :type num_of_chars: int
    :return: random string of desired length
    :rtype: str
    """
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(num_of_chars)])
