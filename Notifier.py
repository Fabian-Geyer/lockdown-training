from telegram import Bot, ParseMode
import json
from User import User


class Notifier:
    def __init__(self):
        self.bot = None
        self.connect_bot()
        
    def connect_bot(self):
        # read token from config
        with open("config.json") as f:
            conf = json.load(f)
        self.bot = Bot(token=conf["bot_token"])

    def notify_user(self, message: str, user: User):
        self.bot.send_message(
            chat_id=user.get_chat_id(),
            text=message,
            parse_mode=ParseMode.MARKDOWN)

    def notify_by_chat_id(self, message: str, chat_id: int):
        self.bot.send_message(
            chat_id=chat_id,
            text=message,
            disable_web_page_preview=True
            )