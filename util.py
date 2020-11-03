from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext
import constants as c


def action_selector(update: Update):
    """
    Main menu of the bot.
    :param update: Chat bot update object
    """
    reply_keyboard = [[c.OFFER_TRAINING, c.CANCEL_TRAINING],
                      [c.ATTEND_TRAINING, c.INFO]]

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


def get_training(context: CallbackContext):
    """
    Get the training object from the chat context.
    :param context: Chat bot context
    :return: Training object
    """
    return context.user_data["training"]


def get_db(context: CallbackContext):
    """
    Get the database object from the chat context.
    :param context: Chat bot context
    :return: Database object
    """
    return context.user_data["db"]


def parse_bot_date(update: Update, training, curr_state: int):
    selected_date = update.message.text.strip("/{}_".format(c.EVENT))

    if not selected_date.isnumeric() or int(selected_date) > len(training.possible_dates):
        training.date_selector(update)
        return curr_state

    date_idx = int(selected_date) - 1
    training.set_date_idx(date_idx)
    training.set_date_from_idx(training.date_idx)