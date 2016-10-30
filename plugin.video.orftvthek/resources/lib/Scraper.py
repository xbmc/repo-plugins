import abc

class Scraper(object):
	__metaclass__  = abc.ABCMeta

	@abc.abstractmethod
	def getCategories():
		pass

	@abc.abstractmethod
	def getHighlights():
		pass

	@abc.abstractmethod
	def getLiveStreams():
		pass

	@abc.abstractmethod
	def getMostViewed():
		pass

	@abc.abstractmethod
	def getNewest():
		pass

	@abc.abstractmethod
	def getThemen():
		pass

	@abc.abstractmethod
	def getTips():
		pass

	@abc.abstractmethod
	def getArchiv():
		pass
