import threading

from sqlalchemy import Column, UnicodeText, Boolean, Integer, BigInteger

from tg_bot.modules.sql import BASE, SESSION, engine


class AFK(BASE):
    __tablename__ = "afk_users"

    user_id = Column(BigInteger, primary_key=True)
    is_afk = Column(Boolean)
    reason = Column(UnicodeText)

    def __init__(self, user_id, reason="", is_afk: bool = True):
        self.user_id = user_id
        self.reason = reason
        self.is_afk = is_afk

    def __repr__(self):
        return "afk_status for {}".format(self.user_id)


AFK.__table__.create(bind=engine,checkfirst=True)
INSERTION_LOCK = threading.RLock()

AFK_USERS = {}


def is_afk(user_id):
    return user_id in AFK_USERS


def check_afk_status(user_id):
    if user_id in AFK_USERS:
        return True, AFK_USERS[user_id]
    return False, ""


def set_afk(user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if not curr:
            curr = AFK(user_id, reason, True)
        else:
            curr.is_afk = True
            curr.reason = reason

        AFK_USERS[user_id] = reason

        SESSION.add(curr)
        SESSION.commit()


def rm_afk(user_id):
    with INSERTION_LOCK:
        curr = SESSION.query(AFK).get(user_id)
        if curr:
            if user_id in AFK_USERS:  # sanity check
                del AFK_USERS[user_id]

            SESSION.delete(curr)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def __load_afk_users():
    global AFK_USERS
    try:
        all_afk = SESSION.query(AFK).all()
        AFK_USERS = {
            user.user_id: user.reason
            for user in all_afk if user.is_afk
        }
    finally:
        SESSION.close()


__load_afk_users()
