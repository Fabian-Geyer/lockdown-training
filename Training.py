import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
)
import constants as c
import util


class Training:
    def __init__(self, coach=None, date=datetime.date.today(), title="", description="", possible_dates=[],
                 date_idx=-1, date_format_str="%d.%m.%y %H:%M"):
        self.coach = coach
        self.date = date
        self.title = title
        self.description = description
        self.possible_dates = possible_dates
        self.date_idx = date_idx
        self.date_format_str = date_format_str

    def set_coach(self, coach):
        self.coach = coach

    def set_date(self, date):
        self.date = date

    def set_date_from_idx(self, idx):
        self.date = self.possible_dates[idx]

    def set_title(self, title):
        self.title = title

    def set_description(self, description):
        self.description = description

    def set_possible_dates(self, possible_dates):
        self.possible_dates = possible_dates

    def get_possible_dates_readable(self):
        dates_str = []
        [dates_str.append(date.strftime(self.date_format_str)) for date in self.possible_dates]
        return dates_str

    def set_date_idx(self, date_idx):
        self.date_idx = date_idx

        return self.date_idx

    def get_date(self, format_str="%s"):
        return self.date.strftime(format_str)

    def get_date_readable(self):
        return self.get_date(self.date_format_str)

    def get_coach_full_name(self):
        return self.coach.full_name

    def get_coach_user_name(self):
        return self.coach.name

    def get_coach(self):
        return self.coach

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def reset(self):
        self.__init__()

    def date_selector(self, update: Update, context: CallbackContext):
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
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )

    def check(self, update: Update):
        msg = 'Möchtest du folgendes Training hinzufügen:\n\n' \
              'Datum: {}\n' \
              'Trainer/in: {}\n' \
              'Titel: {}\n' \
              'Beschreibung: {}\n\n' \
              '/{}    /{}' \
            .format(self.get_date_readable(), self.get_coach_full_name(), self.title, self.description, c.YES, c.CANCEL)

        reply_keyboard = [['/{}'.format(c.YES), '/{}'.format(c.CANCEL)]]
        update.message.reply_text(msg,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),)

    @staticmethod
    def get_training(context: CallbackContext):
        return context.user_data["training"]

    @staticmethod
    def bot_add(update: Update, context: CallbackContext) -> int:
        training = Training.get_training(context)
        training.reset()
        training.set_coach(update.message.from_user)
        training.date_selector(update, context)
        return c.TRAINING_DATE

    @staticmethod
    def bot_set_date(update: Update, context: CallbackContext) -> int:
        training = Training.get_training(context)
        user = update.message.from_user
        selected_date = update.message.text.strip("/{}_".format(c.EVENT))

        if not selected_date.isnumeric() or int(selected_date) > len(training.possible_dates):
            training.date_selector(update)
            return c.TRAINING_DATE

        date_idx = int(selected_date) - 1
        training.set_date_idx(date_idx)
        training.set_date_from_idx(training.date_idx)
        reply_keyboard = [['/{}'.format(c.CANCEL)]]

        msg = "Okay, wie lautet der Titel von deinem Training (mind. {} Zeichen)?".format(c.MIN_CHARS_TITLE)

        update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return c.TRAINING_TITLE

    @staticmethod
    def bot_set_title(update: Update, context: CallbackContext) -> int:
        training = Training.get_training(context)
        user = update.message.from_user
        title = update.message.text.strip()

        reply_keyboard = [['/{}'.format(c.SKIP), '/{}'.format(c.CANCEL)]]

        if len(title) < c.MIN_CHARS_TITLE:
            msg = "Der eingegebene Titel ist kürzer als {} Zeichen.\n" \
                  "Bitte gib einen aussagekräftigen Titel ein.".format(c.MIN_CHARS_TITLE)
            update.message.reply_text(
                msg,
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
            )
            return c.TRAINING_TITLE

        training.set_title(title)
        msg = 'Ich brauche noch eine Beschreibung zu deinem Training, also z.B.\n' \
              '- Benötigte Utensilien\n' \
              '- Spezielle Playlist\n' \
              '- ...\n\n' \
              'Falls du keine Beschreibung benötigst, kanns du diesen Schritt mit /{} überspringen.'.format(c.SKIP)
        update.message.reply_text(msg,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return c.TRAINING_DESCRIPTION

    @staticmethod
    def bot_set_description(update: Update, context: CallbackContext) -> int:
        training = Training.get_training(context)
        user = update.message.from_user
        training.set_description(update.message.text)
        training.check(update)
        return c.TRAINING_CHECK

    @staticmethod
    def bot_skip_description(update: Update, context: CallbackContext) -> int:
        training = Training.get_training(context)
        training.set_description("")
        training.check(update)
        return c.TRAINING_CHECK

    @staticmethod
    def bot_check(update: Update, context: CallbackContext) -> int:
        training = Training.get_training(context)
        if update.message.text == "/{}".format(c.YES):
            msg = "Trainingsdaten werden übermittelt. Herzlichen Glückwunsch zum Training!"
            update.message.reply_text(msg)
            db = context.user_data["db"]
            db.add_subtraining(training)
            util.action_selector(update)
            return c.START
        else:
            training.check(update)
            return c.TRAINING_CHECK

