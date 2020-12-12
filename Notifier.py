from telegram import Bot, ParseMode
import json
import constants as c


class Notifier:
    def __init__(self):
        self.bot = None
        self.connect_bot()
        
    def connect_bot(self):
        # read token from config
        with open("config.json") as f:
            conf = json.load(f)
        self.bot = Bot(token=conf[c.BOT_TOKEN])

    def notify(self, message: str, chat_id):
        self.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
