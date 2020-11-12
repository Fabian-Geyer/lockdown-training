import logging

from telegram import ReplyKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext

import constants as c
import util
from User import User

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO, filename="coachbot.log"
)
logger = logging.getLogger(__name__)


def bot_attend(update: Update, context: CallbackContext) -> int:
    """
    Display an overview of all available trainings and subtrainings
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: c.TRAINING_ADD
    """
    logger.info("User %s wants to attend a training", update.message.from_user.name)

    # Get database data
    db = util.get_db(context)
    next_trainings = db.next_trainings(c.FUTURE_TRAININGS)

    commands = []
    msg = "An welchem Training möchtest du teilnehmen?\n\n"

    # Build string to display all trainings and subtrainings
    idx = 1
    for t in next_trainings:
        msg += "<b>{}. Training am {}</b>\n".format(idx, t["date"].strftime(c.DATE_FORMAT))
        sub_idx = 1
        sub_trainings = t["subtrainings"]
        if len(sub_trainings) == 0:
            msg += "Noch keine Trainings vorhanden\n"
        for st in t["subtrainings"]:
            command = "/training_{}_{}".format(idx, sub_idx)
            commands.append([command])
            msg += "{}: {}\n".format(command, st["title"])
            description = st["description"]
            msg += "<u>Trainer:</u> {}\n".format(st["coach"]["full_name"])
            if len(description) > 0:
                msg += "<u>Info:</u> {}\n".format(st["description"])
            msg += "\n"
            sub_idx += 1
        idx += 1

    commands.append(["/{}".format(c.CMD_CANCEL)])
    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(commands, one_time_keyboard=True, resize_keyboard=True),
        parse_mode=ParseMode.HTML,
    )

    return c.TRAINING_ADD


def bot_attend_save(update: Update, context: CallbackContext) -> int:
    """
    Parse the user selection and add the user as attendee to the selected subtraining
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: c.START
    """
    logger.info("User %s attend a training", update.message.from_user.name)

    user = update.message.from_user
    tg_user = User(update.message.chat_id, user)

    msg = update.message.text
    msg = msg.strip("/{}_".format(c.CMD_TRAINING))

    # Identify which training and subtraining the user chose, based on the indices of the command
    [t_idx, st_idx] = msg.split("_")
    t_idx = int(t_idx) - 1
    st_idx = int(st_idx) - 1

    # Extract the necessary data from the database
    db = util.get_db(context)
    next_trainings = db.next_trainings(c.FUTURE_TRAININGS)
    training = next_trainings[t_idx]
    sub_training = training["subtrainings"][st_idx]
    date = training["date"]
    training_date = int(date.strftime("%s"))

    coach = User(from_dict=sub_training["coach"])
    # Add the user as attendee to the selected subtraining
    db.subtraining_add_attendee(tg_user, training_date, coach)

    msg = "Glückwunsch, du nimmst am *{}* an *{}* mit *{}* teil \U0001F4AA\U0001F4AA\U0001F4AA \n\n" \
          "Wir freuen uns auf dich!".format(date.strftime(c.DATE_FORMAT), sub_training["title"].replace("\n", " "),
                                            coach.get_full_name())
    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
    )

    # Start again
    util.action_selector(update)
    return c.START
