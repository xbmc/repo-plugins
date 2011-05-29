import sys

import ClientCookie

try:
    import warnings
except ImportError:
    def warn(text):
        ClientCookie.WARNINGS_STREAM.write("WARNING: "+text)
else:
    def warn(text):
        warnings.warn(text, stacklevel=2)

try:
    import logging
except:
    NOTSET = None
    INFO = 20
    DEBUG = 10
    class NullHandler:
        def write(self, data): pass
    class Logger:
        def __init__(self):
            self.level = NOTSET
            self.handler = NullHandler()
        def log(self, level, text, *args):
            if args:
                text = text % args
            if self.level is not None and level <= self.level:
                self.handler.write(text+"\n")
        def debug(self, text, *args):
            apply(self.log, (DEBUG, text)+args)
        def info(self, text, *args):
            apply(self.log, (INFO, text)+args)
        def setLevel(self, lvl):
            self.level = lvl
        def addHandler(self, handler):
            self.handler = handler
    LOGGER = Logger()
    def getLogger(name): return LOGGER
    class StreamHandler:
        def __init__(self, strm=None):
            if not strm:
                strm = sys.stderr
            self.stream = strm
        def write(self, data):
            self.stream.write(data)
else:
    from logging import getLogger, StreamHandler, INFO, DEBUG, NOTSET
