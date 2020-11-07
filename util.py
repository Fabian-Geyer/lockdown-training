from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext
import constants as c
import datetime
import Training


def action_selector(update: Update):
    """
    Main menu of the bot.
    :param update: Chat bot update object
    """
    reply_keyboard = c.MENU

    msg = 'Hi! Ich bin der Trainings-Bot.' \
          'Ich helfe dir dein Training zu organisieren.' \
          'Sende /{} um zum /{} zurückzukehren.\n\n' \
          'Was möchtest du tun?'.format(c.CMD_CANCEL, c.CMD_START)
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

    if not selected_date.isnumeric() or int(selected_date) > len(training.possible_dates):
        training.date_selector(update)
        return curr_state

    date_idx = int(selected_date) - 1
    training.set_date_idx(date_idx)
    training.set_date_from_idx(training.date_idx)


def get_readable_date_from_datetime(date: datetime) -> str:
    """
    Print a datetime object to a readable format
    :param date: Datetime object
    :return: Readable date string
    """
    return date.strftime(c.DATE_FORMAT)


def get_readable_date_from_int(date: int) -> str:
    """
    Print a datetime object to a readable format
    :param date: Int containing the date in epoch seconds
    :return: Readable date string
    """
    return get_readable_date_from_datetime(datetime.datetime.fromtimestamp(date))


def get_training_list(trainings: list, with_commands=False) -> [str, list]:
    """
    Get a list of trainings as formatted text.
    If needed commands to select each training can be generated
    :param trainings: List of trainings from the database
    :param with_commands: Bool to select whether to print commands, default:False
    :return: The formatted text and a list of commands
    """
    msg = ""
    commands = []
    for idx, t in enumerate(trainings):
        msg += "*{}. Training am {}*\n".format(idx + 1, get_readable_date_from_int(t["date"]))
        if with_commands:
            command = "/{}_{}".format(c.CMD_TRAINING, idx + 1)
            msg += command + ": "
            commands.append([command])
        else:
            msg += "Titel: "
        msg += "{}\n\n".format(t["title"].replace("\n", " "))
    if with_commands:
        return msg, commands
    else:
        return msg, commands
