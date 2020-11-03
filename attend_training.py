import datetime
import logging

from telegram import ReplyKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext

import constants as c
import util
from datetime import datetime

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO
)
logger = logging.getLogger(__name__)


def bot_attend(update: Update, context: CallbackContext) -> int:
    logger.info("User %s wants to attend a training", update.message.from_user.name)
    training = util.get_training(context)
    db = util.get_db(context)
    user = update.message.from_user

    commands = []
    subtrainings = []
    msg = "An welchem Training möchtest du teilnehmen?\n\n"

    next_trainings = db.next_trainings(c.FUTURE_TRAININGS)

    idx = 1
    for t in next_trainings:
        msg += "<b>{}. Training am {}</b>\n".format(idx, t["date"].strftime(c.DATE_FORMAT))
        sub_idx = 1
        sub_trainings = t["subtrainings"]
        if len(sub_trainings) == 0:
            msg += "Noch keine Trainings vorhanden\n"
        for st in t["subtrainings"]:
            msg += "/training_{}_{}: {}\n".format(idx, sub_idx, st["title"])
            description = st["description"]
            msg += "<u>Trainer:</u> {}\n".format(st["coach"])
            if len(description) > 0:
                msg += "<u>Info:</u> {}\n".format(st["description"])
            msg += "\n"
            sub_idx += 1
        idx += 1

    next_trainings_dates = []
    [next_trainings_dates.append(t["date"]) for t in next_trainings]

    commands.append(["/{}".format(c.CANCEL)])
    update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(commands, one_time_keyboard=True, resize_keyboard=True),
        parse_mode=ParseMode.HTML,
    )

    return c.TRAINING_ADD


def bot_attend_save(update: Update, context: CallbackContext) -> int:
    logger.info("User %s attend a training", update.message.from_user.name)

    user = update.message.from_user.name
    msg = update.message.text
    msg = msg.strip("/{}_".format(c.TRAINING))

    logger.info(msg)

    [t_idx, st_idx] = msg.split("_")
    t_idx = int(t_idx) - 1
    st_idx = int(st_idx) - 1
    db = util.get_db(context)
    next_trainings = db.next_trainings(c.FUTURE_TRAININGS)

    training = next_trainings[t_idx]
    sub_training = training["subtrainings"][st_idx]
    training_date = int(training["date"].strftime("%s"))
    db.subtraining_add_attendee(user, training_date, sub_training["coach_user"])

    util.action_selector(update)
    return c.START
