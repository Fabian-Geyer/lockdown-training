import json
import logging
from Training import Training

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
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def reset_data(context: CallbackContext):
    training = context.user_data["training"]
    training.reset()


def start(update: Update, context: CallbackContext) -> int:

    # Init data
    db = Database(c.CONFIG_FILE)
    training = Training()

    # Store data in user context
    context.user_data["db"] = db
    context.user_data["training"] = training

    util.action_selector(update)
    return c.START


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )
    reset_data(context)
    util.action_selector(update)
    return c.START


def skip_description(update: Update, context: CallbackContext) -> int:
    return c.TRAINING_DESCRIPTION


def main(config_file=c.CONFIG_FILE) -> None:
    # initialize database

    if not os.path.isfile(config_file):
        logger.error("Config file {} not found".format(config_file))
        return

    db = Database(config_file)

    # read token from config file
    with open(config_file) as f:
        conf = json.load(f)

    bot_token = conf["bot_token"]
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states ....
    # TODO: Newlines in description and title are currently not possible
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            c.START: [MessageHandler(Filters.regex('^Training anbieten$'), Training.bot_add)],
            c.TRAINING_DATE: [MessageHandler(Filters.regex('^/{}_[0-9]+$'.format(c.EVENT)), Training.bot_set_date)],
            c.TRAINING_TITLE: [MessageHandler(Filters.regex('^(?!/{}).*$'.format(c.CANCEL)), Training.bot_set_title)],
            c.TRAINING_DESCRIPTION: [MessageHandler(Filters.regex('^(?!(/{}|/{})).*$'.format(c.CANCEL, c.SKIP)),
                                                    Training.bot_set_description),
                                     CommandHandler(c.SKIP, Training.bot_skip_description)],
            c.TRAINING_CHECK: [MessageHandler(Filters.regex('^(?!(/{})).*$'.format(c.CANCEL)), Training.bot_check)],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
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
