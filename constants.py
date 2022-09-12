import datetime

START = 0
TRAINING_DATE = 1
TRAINING_TITLE = 2
TRAINING_DESCRIPTION = 3
TRAINING_CHECK = 4
TRAINING_MODIFY = 5
TRAINING_ADD = 6
CANCEL_TRAINING = 7
CANCEL_TRAINING_ATTENDEE = 8
CANCEL_TRAINING_COACH = 9


MEETING_BASE_URL = "https://meet.jit.si/"
RANDOM_STR_LEN = 20

DEBUG_MODE = False
CHANNEL_KEY = "debug_channel_id" if DEBUG_MODE else "channel_id"
BOT_TOKEN = "debug_bot_token" if DEBUG_MODE else "bot_token"

COACH = 100
ATTENDEE = 101

CMD_START = "start"
CMD_CANCEL = "abbrechen"
CMD_SKIP = "weiter"
CMD_YES = "ja"
CMD_EVENT = "termin"
CMD_TRAINING = "training"
CMD_ATTENDEE = "teilnehmer"
CMD_COACH = "trainer"

CONFIG_FILE = "config.json"
FUTURE_TRAININGS = 3
MIN_CHARS_TITLE = 5

CMD_OFFER_TRAINING = "Training anbieten"
CMD_CANCEL_TRAINING = "Training absagen"
CMD_ATTEND_TRAINING = "Trainingsteilnahme"
CMD_INFO = "Info"

MENU = [
    [CMD_OFFER_TRAINING, CMD_CANCEL_TRAINING],
    [CMD_ATTEND_TRAINING, CMD_INFO],
]

DATE_FORMAT = "%a, %d.%m.%y um %H:%M"

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "coachbot.log"

NOTIFICATION_FREQUENCY_SECONDS = 60
NEXT_TRAINING_NOTIFY_FAR = datetime.timedelta(days=1)
NEXT_TRAINING_NOTIFY_NOW = datetime.timedelta(minutes=30)

INFO_TIMEDELTA = datetime.timedelta(hours=1)
