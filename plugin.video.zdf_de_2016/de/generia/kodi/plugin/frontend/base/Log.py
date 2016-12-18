import datetime

class Log(object):
    def __init__(self):
        pass
    
    def debug(self, message, *args):
        pass
    
    def info(self, message, *args):
        pass

    def warn(self, message, *args):
        pass
    
    def error(self, message, *args):
        pass
    
    def start(self):
        return datetime.datetime.now()

    def stop(self, start):
        return self._total_milliseconds(datetime.datetime.now() - start)

    def _total_milliseconds(self, td):
        return int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**3)
