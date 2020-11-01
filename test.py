"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Data structures
new_training = {"trainer": "", "date": "", "title": "", "description": ""}


ACTION_BASE = 0
TRAINING_DATE = 1
TRAINING_TITLE = 2
TRAINING_DESCRIPTION = 3


def reset_data():
    for key in new_training:
        new_training[key] = ""


def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Training anbieten', 'Training absagen'],
                      ['Trainingsteilnahme', 'Info']]

    update.message.reply_text(
        'Hi! Ich bin der Trainings-Bot.'
        'Ich helfe dir dein Training zu organisieren.'
        'Sende /cancel um abzubrechen.\n\n'
        'Was möchtest du tun?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return ACTION_BASE


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()

    # Target day already happened this week
    if days_ahead <= 0:
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def get_next_training_dates():
    today = datetime.date.today()
    dates = []
    # Add mon, wed and fri to the dates
    [dates.append(next_weekday(today, i)) for i in range(0, 5, 2)]
    dates.sort()

    dates_str = []
    [dates_str.append(date.strftime("%d.%m.%y")) for date in dates]

    return dates_str


def add_training(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    reply_keyboard = [get_next_training_dates()]

    new_training["trainer"] = " ".join([user.first_name, user.last_name])

    logger.info("Training von %s", user.first_name)
    update.message.reply_text(
        'Wann möchtest du das Training anbieten?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return TRAINING_DATE


def add_training_title(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    new_training["date"] = update.message.text

    update.message.reply_text(
        'Okay, wie lautet der Titel von deinem Training?',
        reply_markup=ReplyKeyboardRemove(),
    )
    return TRAINING_TITLE


def add_training_description(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    new_training["title"] = update.message.text

    update.message.reply_text(
        'Ich brauche noch eine Beschreibung zu deinem Training, also z.B.\n'
        '- Benötigte Utensilien\n'
        '- Spezielle Playlist\n'
        '- ...\n\n'
        'Falls du keine Beschreibung benötigst, kanns du diesen Schritt mit /skip überspringen.',
    )
    return TRAINING_DESCRIPTION


def skip_description(update: Update, context: CallbackContext) -> int:
    return TRAINING_DESCRIPTION


def add_training_finish(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    new_training["description"] = update.message.text

    msg = 'Dein Training wird jetzt hinzugefügt. Hier nochmal die Daten zur Übersicht:\n\n' \
        'Datum: {}\n' \
        'Trainer/in: {}\n' \
        'Titel: {}\n' \
        'Beschreibung: {}\n' \
        .format(new_training["date"], new_training["trainer"], new_training["title"], new_training["description"])

    update.message.reply_text(msg)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )
    reset_data()

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    bot_token = '1214145722:AAEDgsafpOseDH-dsp8luQKtlM3AcciC1go'
    updater = Updater(token=bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ACTION_BASE: [MessageHandler(Filters.regex('^Training anbieten$'), add_training)],
            TRAINING_DATE: [MessageHandler(Filters.text(get_next_training_dates()), add_training_title)],
            TRAINING_TITLE: [MessageHandler(Filters.regex('^(?!/skip).*$'), add_training_description), CommandHandler('skip', skip_description)],
            TRAINING_DESCRIPTION: [MessageHandler(Filters.regex('^.*$'), add_training_finish)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()