import logging

from telegram import ReplyKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext

import constants as c
import util

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO
)
logger = logging.getLogger(__name__)


def cancel_own_or_attendee(update: Update, context: CallbackContext) -> int:
    """
    Selector whether to cancel a training as attendee or coach
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: CANCEL_TRAINING
    """
    attendee = "/{}".format(c.CMD_ATTENDEE)
    coach = "/{}".format(c.CMD_COACH)
    cancel = "/{}".format(c.CMD_CANCEL)
    msg = "Willst du ein Training absagen in dem du {} bist oder {}? Du kannst auch {}".format(attendee, coach, cancel)
    commands = [[attendee, coach], [cancel]]

    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(commands, one_time_keyboard=True, resize_keyboard=True),
    )

    return c.CANCEL_TRAINING


def cancel_training(update: Update, context: CallbackContext) -> int:
    """
    Cancel a training depending on the selected role of the user
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: CANCEL_TRAINING_ATTENDEE or CANCEL_TRAINING_COACH
    """
    user = update.message.from_user
    # Get database data
    db = util.get_db(context)
    commands = []

    role_command = update.message.text.strip("/")
    if role_command == c.CMD_COACH:
        role = c.COACH
    elif role_command == c.CMD_ATTENDEE:
        role = c.ATTENDEE
    else:
        return cancel_own_or_attendee(update, context)

    my_trainings = db.get_my_trainings(user.name, role)
    msg = ""
    if len(my_trainings) > 0:
        msg_trainings, commands = util.get_training_list(my_trainings, with_commands=True)
        msg += msg_trainings
    commands.append(["/{}".format(c.CMD_CANCEL)])

    if msg == "":
        msg = "Du kannst erst absagen, wenn du überhaupt erst zugesagt oder ein Training erstellt hast \U0001F605"
        update.message.reply_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
        )
        # Start again
        util.action_selector(update)
        return c.START

    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(commands, one_time_keyboard=True, resize_keyboard=True),
        parse_mode=ParseMode.MARKDOWN,
    )

    if role == c.ATTENDEE:
        return c.CANCEL_TRAINING_ATTENDEE
    else:
        return c.CANCEL_TRAINING_COACH


def cancel_training_attendee(update: Update, context: CallbackContext) -> int:
    """
    Remove the user from an attendees list of a subtraining
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    user = update.message.from_user
    # Get database data
    db = util.get_db(context)

    training_idx = int(update.message.text.strip("/{}_".format(c.CMD_TRAINING))) - 1
    my_trainings = db.get_my_trainings(user.name, c.ATTENDEE)

    if training_idx >= len(my_trainings):
        msg = "*Du kannst maximal /{}\_{} auswählen*\n\n".format(c.CMD_TRAINING, len(my_trainings))
        update.message.reply_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
        )
        msg_trainings, commands = util.get_training_list(my_trainings, with_commands=True)
        msg += msg_trainings
        commands.append(["/{}".format(c.CMD_CANCEL)])
        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(commands, one_time_keyboard=True, resize_keyboard=True),
            parse_mode=ParseMode.MARKDOWN,
        )
        return c.CANCEL_TRAINING_ATTENDEE

    cancelled_training = my_trainings[training_idx]
    db.cancel_subtrainings(cancelled_training["date"], user.name)

    msg = "Du wurdest erfolgreich aus der Teilnehmerliste entfernt"

    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
    )
    # Start again
    util.action_selector(update)
    return c.START


def cancel_training_coach(update: Update, context: CallbackContext) -> int:
    """
    Cancel a subtraining where the user is coach
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    msg = "*Das geht noch nicht*"

    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
    )
    # Start again
    util.action_selector(update)
    return c.START

