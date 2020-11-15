import constants as c


class User:
    def __init__(self, chat_id=-1, user=None, role=c.ATTENDEE, from_dict=None):
        if from_dict is None:
            self.chat_id = chat_id
            self.user_name = user.username
            self.full_name = user.full_name
            self.notified_now = False
            self.notified_far = False
            self.role = role
        else:
            self.chat_id = from_dict["chat_id"]
            self.user_name = from_dict["user_name"]
            self.full_name = from_dict["full_name"]
            self.notified_now = from_dict["notified_now"]
            self.notified_far = from_dict["notified_far"]
            self.role = from_dict["role"]

    def __eq__(self, other):
        return (self.chat_id == other.chat_id and
                self.user_name == other.user_name and
                self.full_name == other.full_name)

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id

    def set_user_name(self, user_name):
        self.user_name = user_name

    def set_full_name(self, full_name):
        self.full_name = full_name

    def get_chat_id(self):
        return self.chat_id

    def get_user_name(self):
        return self.user_name

    def get_full_name(self):
        return self.full_name

    def is_notified_now(self):
        return self.notified_now

    def is_notified_far(self):
        return self.notified_far

    def is_attendee(self):
        return self.role == c.COACH

    def is_coach(self):
        return self.role == c.ATTENDEE

    def get_dict(self) -> dict:
        return {"chat_id": self.chat_id,
                "user_name": self.user_name,
                "full_name": self.full_name,
                "notified_far": self.notified_far,
                "notified_now": self.notified_now,
                "role": self.role}
