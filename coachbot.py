import json
import locale
import logging
import os

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

import attend_training
import cancel_training
import constants as c
import info
import util
from Database import Database
from Training import Training

locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> int:
    """
    Entrypoint for the telegram chat bot.
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    # Init data
    # Enable logging
    db = Database(c.CONFIG_FILE)
    training = Training()

    # Store data in user context
    context.user_data["db"] = db
    context.user_data["training"] = training

    util.action_selector(update)
    return c.START


def cancel(update: Update, context: CallbackContext) -> int:
    """
    Function to cancel the current progress. Restarts the conversation and resets the data.
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: START
    """
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )
    util.reset_data(context)
    util.action_selector(update)
    return c.START


def select_action(update: Update, context: CallbackContext) -> int:
    """
    Selector for the main menu
    :param update: Chat bot update object
    :param context: Chat bot context
    :return: The specific values for the next state of each menu operation
    """
    util.reset_data(context)
    usr_input = update.message.text

    if usr_input == c.CMD_OFFER_TRAINING:
        return Training.bot_add(update, context)
    elif usr_input == c.CMD_ATTEND_TRAINING:
        return attend_training.bot_attend(update, context)
    elif usr_input == c.CMD_INFO:
        return info.print_info(update, context)
    elif usr_input == c.CMD_CANCEL_TRAINING:
        return cancel_training.cancel_own_or_attendee(update, context)
    else:
        return c.START


def main(config_file: str) -> bool:
    """
    Main function of the training telegram bot
    :param config_file: Path to the config file as string
    :return: False in case of an error before the bot starts
    """

    if not os.path.isfile(config_file):
        logger.error("Config file {} not found".format(config_file))
        return False

    # read token from config file
    with open(config_file) as f:
        conf = json.load(f)

    bot_token = conf["bot_token"]
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Regex for the main menu
    menu_regex = '^({})$'.format('|'.join([m for menu in c.MENU for m in menu]))

    # Add conversation handler with the states ....
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(c.CMD_START, start)],
        states={
            c.START: [MessageHandler(Filters.regex(menu_regex),
                                     select_action)],
            c.TRAINING_DATE: [MessageHandler(Filters.regex('^/{}_[0-9]+$'.format(c.CMD_EVENT)), Training.bot_set_date)],
            c.TRAINING_TITLE: [MessageHandler(Filters.regex('^(?!/{})[\\S\\s]*$'.format(c.CMD_CANCEL)),
                                              Training.bot_set_title)],
            c.TRAINING_DESCRIPTION: [MessageHandler(Filters.regex('^(?!(/{}|/{}))[\\S\\s]*$'.format(c.CMD_CANCEL,
                                                                                                    c.CMD_SKIP)),
                                                    Training.bot_set_description),
                                     CommandHandler(c.CMD_SKIP, Training.bot_skip_description)],
            c.TRAINING_CHECK: [MessageHandler(Filters.regex('^(?!(/{})).*$'.format(c.CMD_CANCEL)), Training.bot_check)],
            c.TRAINING_ADD: [MessageHandler(Filters.regex('^/{}_[0-9]+_[0-9]+$'.format(c.CMD_TRAINING)),
                                            attend_training.bot_attend_save)],
            c.CANCEL_TRAINING: [MessageHandler(Filters.regex('^/({}|{})$'.format(c.CMD_COACH, c.CMD_ATTENDEE)),
                                               cancel_training.cancel_training_selector)],
            c.CANCEL_TRAINING_ATTENDEE: [MessageHandler(Filters.regex('^/{}_[0-9]+$'.format(c.CMD_TRAINING)),
                                                        cancel_training.cancel_training_attendee)],
            c.CANCEL_TRAINING_COACH: [MessageHandler(Filters.regex('^/{}_[0-9]+$'.format(c.CMD_TRAINING)),
                                                     cancel_training.cancel_training_coach)],
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
    main(c.CONFIG_FILE)
