import json
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from Database import Database

STATEHANDLER = range(1)

def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [[
        'An Training teilnehmen',
        'Training anmelden',
        'Info',
        'Abbrechen']]

    update.message.reply_text(
        'Hi, ich bin dein digitaler Coach. was möchtest du machen? '
        'Tippe /cancel um unser Gespräch abzubrechen.\n\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return STATEHANDLER

def state_handler(update: Update, context: CallbackContext) -> int:
    pass

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )
    return STATEHANDLER

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
            STATEHANDLER: [
                MessageHandler(Filters.regex(
                    '^(An Training teilnehmen|Training anmelden|Info|Abbrechen)$'),
                    state_handler)]
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

if __name__ == "__main__":
    main()
