import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
)
import constants as c
import util


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()

    # Target day already happened this week
    if days_ahead <= 0:
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def get_next_training_dates():
    today = datetime.date.today()
    dates = []
    # Add mon, wed and fri to the dates
    [dates.append(next_weekday(today, i)) for i in range(0, 5, 2)]
    dates.sort()
    return dates


class Training:
    def __init__(self, coach=None, date=datetime.date.today(), title="", description="", possible_dates=[], date_idx=-1):
        self.coach = coach
        self.date = date
        self.title = title
        self.description = description
        self.possible_dates = possible_dates
        self.date_idx = date_idx

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
        [dates_str.append(date.strftime("%d.%m.%y")) for date in self.possible_dates]
        return dates_str

    def set_date_idx(self, readable_date):
        dates_readable = self.get_possible_dates_readable()
        self.date_idx = dates_readable.index(readable_date)

        return self.date_idx

    def get_date_readable(self):
        return self.date.strftime("%d.%m.%y")

    def get_coach_readable(self):
        return self.coach.full_name

    def print(self):
        msg = "Trainer: {}\n" \
              "Titel: {}\n" \
              "Beschreibung: {}".format(
               self.coach, self.title, self.description
                )
        print(msg)

    def reset(self):
        self.__init__()

    def bot_add(self, update: Update, context: CallbackContext) -> int:
        self.reset()

        user = update.message.from_user
        #TODO: Korrekte Funktion hinterlegen
        next_trainings = get_next_training_dates()
        self.set_possible_dates(next_trainings)

        reply_keyboard = [self.get_possible_dates_readable(), ['/abbrechen']]

        self.set_coach(user)

        update.message.reply_text(
            'Wann möchtest du das Training anbieten?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return c.TRAINING_DATE

    def bot_set_date(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user
        selected_date = update.message.text
        self.set_date_idx(selected_date)
        self.set_date_from_idx(self.date_idx)

        update.message.reply_text(
            'Okay, wie lautet der Titel von deinem Training?',
            reply_markup=ReplyKeyboardRemove(),
        )
        return c.TRAINING_TITLE

    def bot_set_title(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user
        self.set_title(update.message.text)

        update.message.reply_text(
            'Ich brauche noch eine Beschreibung zu deinem Training, also z.B.\n'
            '- Benötigte Utensilien\n'
            '- Spezielle Playlist\n'
            '- ...\n\n'
            'Falls du keine Beschreibung benötigst, kanns du diesen Schritt mit /skip überspringen.',
        )
        return c.TRAINING_DESCRIPTION

    def bot_set_description(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user
        self.set_description(update.message.text)
        self.finish(update)
        return c.START

    def bot_skip_description(self, update: Update, context: CallbackContext) -> int:
        self.set_description("")
        self.finish(update)
        return c.START

    def finish(self, update: Update):
        msg = 'Dein Training wird jetzt hinzugefügt. Hier nochmal die Daten zur Übersicht:\n\n' \
              'Datum: {}\n' \
              'Trainer/in: {}\n' \
              'Titel: {}\n' \
              'Beschreibung: {}\n' \
            .format(self.get_date_readable(), self.get_coach_readable(), self.title, self.description)
        update.message.reply_text(msg)
        util.action_selector(update)
