# -*- coding: utf-8 -*-
from functools import wraps
from constants import PLUGIN, Images
from twitch.exception import TwitchException


def managedTwitchExceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TwitchException as error:
            handleTwitchException(error)

    return wrapper


def handleTwitchException(exception):
    codeTranslations = {TwitchException.NO_STREAM_URL: 30023,
                        TwitchException.STREAM_OFFLINE: 30021,
                        TwitchException.HTTP_ERROR: 30020,
                        TwitchException.JSON_ERROR: 30027,
                        TwitchException.NO_PLAYABLE: 30080}
    code = exception.code
    title = 30010
    msg = codeTranslations[code]
    PLUGIN.notify(PLUGIN.get_string(title), PLUGIN.get_string(msg), image=Images.ICON)
