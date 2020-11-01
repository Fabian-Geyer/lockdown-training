from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
)


def action_selector(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Training anbieten', 'Training absagen'],
                      ['Trainingsteilnahme', 'Info']]

    update.message.reply_text(
        'Hi! Ich bin der Trainings-Bot.'
        'Ich helfe dir dein Training zu organisieren.'
        'Sende /cancel um zum Start zurückzukehren.\n\n'
        'Was möchtest du tun?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )