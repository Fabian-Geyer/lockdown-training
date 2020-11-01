import json
import logging
from training import Training, get_next_training_dates

from Database import Database
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
import constants as c
import util

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Data structures
training = Training()


def reset_data():
    training.reset()


def start(update: Update, context: CallbackContext) -> int:
    util.action_selector(update)
    return c.START


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )
    reset_data()
    util.action_selector(update)
    return c.START


def skip_description(update: Update, context: CallbackContext) -> int:
    return c.TRAINING_DESCRIPTION


def main() -> None:
    # initialize database
    db = Database()

    # read token from config file
    with open('config.json') as config_file:
        conf = json.load(config_file)
    bot_token = conf["bot_token"]
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states ....
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            c.START: [MessageHandler(Filters.regex('^Training anbieten$'), training.bot_add)],
            c.TRAINING_DATE: [MessageHandler(Filters.text(['02.11.20', '04.11.20', '06.11.20']), training.bot_set_date)],
            c.TRAINING_TITLE: [MessageHandler(Filters.regex('.*$'), training.bot_set_title),
                               CommandHandler('skip', skip_description)],
            c.TRAINING_DESCRIPTION: [MessageHandler(Filters.regex('^.*$'), training.bot_set_description)],
        },
        fallbacks=[CommandHandler('abbrechen', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
