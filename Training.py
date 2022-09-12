import datetime
import logging

from telegram import ReplyKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext

import constants as c
import util
from User import User
from Notifier import Notifier

logging.basicConfig(
    format=c.LOG_FORMAT, level=logging.INFO, filename="coachbot.log"
)
logger = logging.getLogger(__name__)


class Training:
    def __init__(self, coach=None, date=None, title="", description="", attendees=None, from_dict=None):
        """
        Initialization of the training object.
        :param coach: Telegram User object
        :param date: Training date as datetime
        :param title: Training title as string
        :param description: Training description as string
        """
        self.attendees = attendees if attendees else []
        if from_dict is None:
            self.coach = coach
            self.date = date
            self.title = title
            self.description = description
            self.attendees = attendees if attendees else []
        else:
            self.coach = User(from_dict=from_dict["coach"])
            self.date = datetime.datetime.fromtimestamp(from_dict["date"])
            self.title = from_dict["title"]
            self.description = from_dict["description"]
            for a in from_dict["attendees"]:
                self.attendees.append(User(from_dict=a))
        self.possible_dates = []

    def get_dict(self):
        att = []
        return {"date": int(self.get_date("%s")),
                "coach": self.coach.get_dict(),
                "title": self.title,
                "description": self.description,
                "attendees": [att.append(a.get_dict()) for a in self.get_attendees()],
                "time": self.get_date("%H:%M")}

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

    def get_attendees(self) -> list:
        """
        Get a list of all attendees
        :return: List of attendees as list of User objects
        """
        return self.attendees

    def get_possible_dates(self) -> list:
        """
        Get a list of dates of the possible list of training dates.
        :return: List of strings with dates
        """
        return self.possible_dates

    def get_date(self, format_str="%s") -> str:
        """
        Return the training date as string.
        :param format_str: Specifies the format of the output
        :return: String representing the training date
        """
        return self.date.strftime(format_str)

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
        user = User(update.message.chat_id, update.message.from_user)
        next_trainings_all = db.next_trainings(number_of_trainings=c.FUTURE_TRAININGS)
        next_trainings = []
        for t in next_trainings_all:
            coaches = []
            [coaches.append(User(from_dict=s["coach"])) for s in t["subtrainings"]]
            if user not in coaches:
                next_trainings.append(t)

        next_trainings_dates = []
        [next_trainings_dates.append(t["date"]) for t in next_trainings]
        self.possible_dates = next_trainings_dates

        readable_dates = []
        [readable_dates.append(date.strftime(c.DATE_FORMAT)) for date in next_trainings_dates]

        events = []
        for idx, date in enumerate(readable_dates):
            events.append("/{}\_{}".format(c.CMD_EVENT, idx + 1))

        reply_keyboard = [[e.replace("\\", "") for e in events], ['/{}'.format(c.CMD_CANCEL)]]
        msg = "Folgende Termine stehen zur Auswahl (pro Termin kannst du nur *ein* Training anbieten):\n"
        for idx, event in enumerate(events):
            msg += "{}: {}\n".format(event, readable_dates[idx])

        msg += "\nWelchen Termin möchtest du auswählen?"
        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
            parse_mode=ParseMode.MARKDOWN,
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
            .format(util.get_readable_date_from_datetime(self.date), self.get_coach().get_full_name(), self.title,
                    self.description, c.CMD_YES, c.CMD_CANCEL)

        reply_keyboard = [['/{}'.format(c.CMD_YES), '/{}'.format(c.CMD_CANCEL)]]
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
        training.set_coach(User(update.message.chat_id, update.message.from_user, c.COACH))
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
        reply_keyboard = [['/{}'.format(c.CMD_CANCEL)]]

        msg = "Okay, wie lautet der Titel von deinem Training (mind. {} Zeichen)?".format(c.MIN_CHARS_TITLE)

        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        logger.info("Date for the training: %s", util.get_readable_date_from_datetime(training.date))
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

        reply_keyboard = [['/{}'.format(c.CMD_SKIP), '/{}'.format(c.CMD_CANCEL)]]

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
              'Falls du keine Beschreibung benötigst, kannst du diesen Schritt mit /{} überspringen.'.format(c.CMD_SKIP)
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
        if update.message.text == "/{}".format(c.CMD_YES):
            msg = "Trainingsdaten werden übermittelt. Herzlichen Glückwunsch zum Training!"
            update.message.reply_text(msg)
            db = context.user_data["db"]
            db.add_subtraining(training)
            if len(training.get_description().strip()) > 0:
                description = "*Beschreibung: *" + training.get_description().strip() + "\n\n"
            else:
                description = "\n"
            broadcast_message = "*Neues Training!*\n\n" + \
                                training.get_coach().get_full_name() + \
                                " bietet am " + util.get_readable_date_from_datetime(training.date) + \
                                " ein Training an. \n\n*Titel:* " + \
                                training.get_title() + "\n" + \
                                description + \
                                "Schreibe @gymnastics\_coach\_bot um dich anzumelden."
            notifier = Notifier()
            notifier.notify(message=broadcast_message, chat_id=context.user_data["channel_id"])
            util.action_selector(update, context)
            logger.info("Training data submitted to the database")
            return c.START
        else:
            training.check(update)
            return c.TRAINING_CHECK
