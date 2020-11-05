import logging

from telegram import Update, ParseMode
from telegram.ext import CallbackContext

import constants as c
import util

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO
)
logger = logging.getLogger(__name__)


def print_info(update: Update, context: CallbackContext) -> int:
    """
    Print the information about all trainings as coach or attendee for the user
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    user = update.message.from_user
    # Get database data
    db = util.get_db(context)

    as_coach = db.get_my_trainings(user.name, c.COACH)
    as_attendee = db.get_my_trainings(user.name, c.ATTENDEE)

    msg = ""
    if len(as_coach) > 0:
        msg += "*In diesen Trainings bist du Trainer:*\n"
        trainings, _ = util.get_training_list(as_coach)
        msg += trainings

    if len(as_attendee) > 0:
        if msg != "":
            msg += "\n"
        msg += "*An diesen Trainings nimmst du teil:*\n"
        trainings, _ = util.get_training_list(as_attendee)
        msg += trainings

    if msg == "":
        msg += "Du gibst kein Training als Coach und bist auch zu keinem Trianing angemeldet?\n" \
               "Zeit das ganz schnell zu ändern!"

    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
    )

    # Start again
    util.action_selector(update)
    return c.START
