from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext


def action_selector(update: Update):
    """
    Main menu of the bot.
    :param update: Chat bot update object
    """
    reply_keyboard = [['Training anbieten', 'Training absagen'],
                      ['Trainingsteilnahme', 'Info']]

    update.message.reply_text(
        'Hi! Ich bin der Trainings-Bot.'
        'Ich helfe dir dein Training zu organisieren.'
        'Sende /abbrechen um zum Start zurückzukehren.\n\n'
        'Was möchtest du tun?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )


def reset_data(context: CallbackContext):
    """
    Reset the data carried in the user_data of the chat context.
    :param context: Chat bot context
    """
    training = context.user_data["training"]
    training.reset()
