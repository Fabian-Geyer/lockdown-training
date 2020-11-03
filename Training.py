import datetime
import logging

from telegram import ReplyKeyboardMarkup, Update, User
from telegram.ext import CallbackContext

import constants as c
import util

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO
)
logger = logging.getLogger(__name__)


class Training:
    def __init__(self, coach=None, date=None, title="", description="", possible_dates=None,
                 date_idx=-1, date_format_str="%d.%m.%y %H:%M"):
        """
        Initialization of the training object.
        :param coach: Telegram User object
        :param date: Training date as datetime
        :param title: Training title as string
        :param description: Training description as string
        :param possible_dates: List of possible dates for this training as list of datetime objects
        :param date_idx: Index which date of possible_dates the user chose
        :param date_format_str: Format specifier for human readable dates
        """
        self.coach = coach
        self.date = date
        self.title = title
        self.description = description
        self.possible_dates = possible_dates
        self.date_idx = date_idx
        self.date_format_str = date_format_str

    def set_coach(self, coach: User):
        """
        Set the coach of a training.
        :param coach: User object of the telegram chat
        """
        self.coach = coach

    def set_date(self, date: datetime):
        """
        Set the date of this training session.
        :param date:
        """
        self.date = date

    def set_date_from_idx(self, idx: int):
        """
        Choose the date of the training by the index of the list of possible trainings.
        :param idx: List index for the list of possible trainings
        """
        self.set_date(self.possible_dates[idx])

    def set_title(self, title: str):
        """
        Set the title of the training.
        :param title: Title string
        """
        self.title = title

    def set_description(self, description: str):
        """
        Set the description of the training.
        :param description: Description string
        """
        self.description = description

    def set_possible_dates(self, possible_dates: list):
        """
        Set the list of all possible dates for this training.
        The user can later choose the date.
        :param possible_dates: List of datetime dates
        """
        self.possible_dates = possible_dates

    def set_date_idx(self, date_idx: int):
        """
        Set the index which of the possible dates the user chose.
        :param date_idx: List index
        """
        self.date_idx = date_idx

    def get_possible_dates_readable(self) -> list:
        """
        Get a list of human readable dates of the possible list of dates.
        :return: List of strings with human readable dates
        """
        dates_str = []
        [dates_str.append(date.strftime(self.date_format_str)) for date in self.possible_dates]
        return dates_str

    def get_date(self, format_str="%s") -> str:
        """
        Return the training date as string.
        :param format_str: Specifies the format of the output
        :return: String representing the training date
        """
        return self.date.strftime(format_str)

    def get_date_readable(self) -> str:
        """
        Get the training date in a human readable way.
        The format is specified by self.date_format_str.
        :return: String representing the training date
        """
        return self.get_date(self.date_format_str)

    def get_coach_full_name(self) -> str:
        """
        Get the full name of the coach as specified in the telegram settings.
        :return: Full name of the coach
        """
        return self.coach.full_name

    def get_coach_user_name(self) -> str:
        """
        Get the telegram username of the coach.
        :return: Username of the coach
        """
        return self.coach.name

    def get_coach(self) -> User:
        """
        Get the coach as telegram user object.
        :return: coach object
        """
        return self.coach

    def get_title(self) -> str:
        """
        Get the title of the training.
        :return: Title string
        """
        return self.title

    def get_description(self) -> str:
        """
        Get the description of the training.
        :return: Description string
        """
        return self.description

    def reset(self):
        """
        Initialize the training object with its default values.
        """
        self.__init__()

    def date_selector(self, update: Update, context: CallbackContext):
        """
        Display the menu to select a date for the training.
        The dates are loaded from the mongoDB database.
        The number of future trainings determines the number of buttons.
        :param update: Chat bot update object
        :param context: Chat bot context
        """
        db = context.user_data["db"]
        next_trainings = db.next_trainings(c.FUTURE_TRAININGS)

        next_trainings_dates = []
        [next_trainings_dates.append(t["date"]) for t in next_trainings]

        self.set_possible_dates(next_trainings_dates)
        readable_dates = self.get_possible_dates_readable()

        events = []
        for idx, date in enumerate(readable_dates):
            events.append("/{}_{}".format(c.EVENT, idx + 1))

        reply_keyboard = [events, ['/{}'.format(c.CANCEL)]]
        msg = "Folgende Termine stehen zur Auswahl:\n"
        for idx, event in enumerate(events):
            msg += "{}: {}\n".format(event, readable_dates[idx])

        msg += "\nWelchen Termin möchtest du auswählen?"
        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )

    def check(self, update: Update):
        """
        Displays a menu to choose whether the data should be submitted to the database.
        :param update: Chat bot update object
        """
        msg = 'Möchtest du folgendes Training hinzufügen:\n\n' \
              'Datum: {}\n' \
              'Trainer/in: {}\n' \
              'Titel: {}\n' \
              'Beschreibung: {}\n\n' \
              '/{}    /{}' \
            .format(self.get_date_readable(), self.get_coach_full_name(), self.title, self.description, c.YES, c.CANCEL)

        reply_keyboard = [['/{}'.format(c.YES), '/{}'.format(c.CANCEL)]]
        update.message.reply_text(msg,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                   resize_keyboard=True)
                                  )

    @staticmethod
    def bot_add(update: Update, context: CallbackContext) -> int:
        """
        Initial method when adding a new training. Saves the coach and displays the date selector.
        :param update: Chat bot update object
        :param context: Chat bot context
        :return: Next state: TRAINING_DATE
        """
        logger.info("User %s wants to offer a training", update.message.from_user.full_name)
        training = util.get_training(context)
        training.set_coach(update.message.from_user)
        training.date_selector(update, context)
        return c.TRAINING_DATE

    @staticmethod
    def bot_set_date(update: Update, context: CallbackContext) -> int:
        """
        Set the date of the training based on the available dates.
        :param update: Chat bot update object
        :param context: Chat bot context
        :return: TRAINING_TITLE on success, TRAINING_DATE else
        """
        training = util.get_training(context)
        if util.parse_bot_date(update, training, c.TRAINING_DATE) == c.TRAINING_DATE:
            return c.TRAINING_DATE
        reply_keyboard = [['/{}'.format(c.CANCEL)]]

        msg = "Okay, wie lautet der Titel von deinem Training (mind. {} Zeichen)?".format(c.MIN_CHARS_TITLE)

        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        logger.info("Date for the training: %s", training.get_date_readable())
        return c.TRAINING_TITLE

    @staticmethod
    def bot_set_title(update: Update, context: CallbackContext) -> int:
        """
        Set the title of the training. The input must be at least MIN_CHARS_TITLE long.
        :param update: Chat bot update object
        :param context: Chat bot context
        :return: TRAINING_DESCRIPTION on success, TRAINING_TITLE else
        """
        training = util.get_training(context)
        title = update.message.text.strip()

        reply_keyboard = [['/{}'.format(c.SKIP), '/{}'.format(c.CANCEL)]]

        if len(title) < c.MIN_CHARS_TITLE:
            msg = "Der eingegebene Titel ist kürzer als {} Zeichen.\n" \
                  "Bitte gib einen aussagekräftigen Titel ein.".format(c.MIN_CHARS_TITLE)
            update.message.reply_text(
                msg,
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
            )
            return c.TRAINING_TITLE

        training.set_title(title)
        msg = 'Ich brauche noch eine Beschreibung zu deinem Training, also z.B.\n' \
              '- Benötigte Utensilien\n' \
              '- Spezielle Playlist\n' \
              '- ...\n\n' \
              'Falls du keine Beschreibung benötigst, kannst du diesen Schritt mit /{} überspringen.'.format(c.SKIP)
        update.message.reply_text(msg,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                   resize_keyboard=True),
                                  )

        logger.info("Title for the training: %s", training.get_title())
        return c.TRAINING_DESCRIPTION

    @staticmethod
    def bot_set_description(update: Update, context: CallbackContext) -> int:
        """
        Set the description of the training.
        :param update: Chat bot update object
        :param context: Chat bot context
        :return: TRAINING_CHECK
        """
        training = util.get_training(context)
        training.set_description(update.message.text)
        training.check(update)
        logger.info("Description for the training: %s", training.get_description())
        return c.TRAINING_CHECK

    @staticmethod
    def bot_skip_description(update: Update, context: CallbackContext) -> int:
        """
        Skip the description part (leave the description empty)
        :param update: Chat bot update object
        :param context: Chat bot context
        :return: TRAINING_CHECK
        """
        training = util.get_training(context)
        training.set_description("")
        training.check(update)
        logger.info("No description provided")
        return c.TRAINING_CHECK

    @staticmethod
    def bot_check(update: Update, context: CallbackContext) -> int:
        """
        Write the training to the database, if the user agrees.
        :param update: Chat bot update object
        :param context: Chat bot context
        :return: START when agreed, TRAINING_CHECK else
        """
        training = util.get_training(context)
        if update.message.text == "/{}".format(c.YES):
            msg = "Trainingsdaten werden übermittelt. Herzlichen Glückwunsch zum Training!"
            update.message.reply_text(msg)
            db = context.user_data["db"]
            db.add_subtraining(training)
            util.action_selector(update)
            logger.info("Training data submitted to the database")
            return c.START
        else:
            training.check(update)
            return c.TRAINING_CHECK
