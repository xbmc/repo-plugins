import abc


class Scraper(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getCategories(self):
        pass

    @abc.abstractmethod
    def getHighlights(self):
        pass

    @abc.abstractmethod
    def getLiveStreams(self):
        pass

    @abc.abstractmethod
    def getMostViewed(self):
        pass

    @abc.abstractmethod
    def getNewest(self):
        pass

    @abc.abstractmethod
    def getThemen(self):
        pass

    @abc.abstractmethod
    def getTips(self):
        pass

    @abc.abstractmethod
    def getSchedule(self):
        pass

    @abc.abstractmethod
    def getArchiv(self):
        pass
