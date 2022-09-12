import logging

from telegram import ReplyKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext

import constants as c
import util
from User import User
from Notifier import Notifier

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO, filename="coachbot.log"
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


def cancel_training_selector(update: Update, context: CallbackContext) -> int:
    """
    Cancel a training depending on the selected role of the user
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: CANCEL_TRAINING_ATTENDEE or CANCEL_TRAINING_COACH
    """
    tg_user = update.message.from_user
    user = User(update.message.chat_id, tg_user)
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

    my_trainings = db.get_my_trainings(user, role)
    msg = ""
    if len(my_trainings) > 0:
        msg_trainings, commands = util.get_training_list(my_trainings, with_commands=True)
        msg_trainings = msg_trainings.replace("_", "\_")
        msg += msg_trainings
    commands.append(["/{}".format(c.CMD_CANCEL)])

    if msg == "":
        msg = "Du kannst erst absagen, wenn du überhaupt erst zugesagt, oder ein Training erstellt hast \U0001F605"
        update.message.reply_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
        )
        # Start again
        util.action_selector(update, context)
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


def cancel_training(update: Update, context: CallbackContext, role: int):
    """
    Get the training to cancel
    :param update: Chat bot update object
    :param context: Chat bot context
    :param role: Role of the user (COACH or ATTENDEE)
    :return: Tuple of training and true or false
    """
    tg_user = update.message.from_user
    user = User(update.message.chat_id, tg_user, role)
    # Get database data
    db = util.get_db(context)

    training_idx = int(update.message.text.strip("/{}_".format(c.CMD_TRAINING))) - 1
    my_trainings = db.get_my_trainings(user, role)

    if training_idx >= len(my_trainings):
        msg = "*Du kannst maximal /{}_{} auswählen*\n\n".format(c.CMD_TRAINING, len(my_trainings))

        msg_trainings, commands = util.get_training_list(my_trainings, with_commands=True)
        msg_trainings = msg_trainings.replace("_", "\_")
        msg += msg_trainings
        commands.append(["/{}".format(c.CMD_CANCEL)])
        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(commands, one_time_keyboard=True, resize_keyboard=True),
            parse_mode=ParseMode.MARKDOWN,
        )
        return None, False

    cancelled_training = my_trainings[training_idx]
    return cancelled_training, True


def cancel_training_attendee(update: Update, context: CallbackContext) -> int:
    """
    Remove the user from an attendees list of a subtraining
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    tg_user = update.message.from_user
    user = User(update.message.chat_id, tg_user, c.ATTENDEE)
    # Get database data
    db = util.get_db(context)

    cancelled_training, ret = cancel_training(update, context, c.ATTENDEE)
    if not ret:
        return c.CANCEL_TRAINING_ATTENDEE

    db.cancel_subtrainings(int(cancelled_training.get_date("%s")), user)
    msg = "Du wurdest erfolgreich aus der Teilnehmerliste entfernt"

    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
    )
    # Start again
    util.action_selector(update, context)
    return c.START


def cancel_training_coach(update: Update, context: CallbackContext) -> int:
    """
    Cancel a subtraining where the user is coach
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    tg_user = update.message.from_user
    user = User(update.message.chat_id, tg_user, c.COACH)
    # Get database data
    db = util.get_db(context)

    cancelled_training, ret = cancel_training(update, context, c.COACH)
    if not ret:
        return c.CANCEL_TRAINING_COACH

    db.remove_training_of_coach(user, int(cancelled_training.get_date("%s")))
    date = cancelled_training.get_date(c.DATE_FORMAT)
    msg = "Du hast das Training am {} abgesagt".format(date)
    notifier = Notifier()
    for attendee in cancelled_training.get_attendees():
        notifier.notify("Das Training am *{}* wurde leider *abgesagt* \U0001F625".format(date),
                        attendee.get_chat_id())

    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
    )
    # Start again
    util.action_selector(update, context)
    return c.START
