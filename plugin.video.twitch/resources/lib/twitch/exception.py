# -*- coding: utf-8 -*-
class TwitchException(Exception):
    NO_STREAM_URL = 0
    STREAM_OFFLINE = 1
    HTTP_ERROR = 2
    JSON_ERROR = 3
    NO_PLAYABLE = 4

    def __init__(self, code):
        Exception.__init__(self)
        self.code = code

    def __str__(self):
        return repr(self.code)
