from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters


bot_token = '1214145722:AAEDgsafpOseDH-dsp8luQKtlM3AcciC1go'
# channel id: -1001492255135

def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi, ich bin dein virtueller Coach!" +
        " Wenn du ein Training anbieten willst bist du hier genau richtig")

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


if __name__ == "__main__":
    # init some stuff
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # handlers
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    caps_handler = CommandHandler('caps', caps)

    # add stuff to dispatcher
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(caps_handler)

    # start that shit
    updater.start_polling()
    