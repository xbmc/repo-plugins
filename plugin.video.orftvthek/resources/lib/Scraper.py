import abc

class Scraper(object):
	__metaclass__  = abc.ABCMeta

	@abc.abstractproperty
	def UrlMostViewed():
		pass

	@abc.abstractproperty
	def UrlNewest():
		pass
	
	@abc.abstractproperty
	def UrlTip():
		pass

	@abc.abstractmethod
	def getCategories():
		pass

	@abc.abstractmethod
	def getLiveStreams():
		pass

	@abc.abstractmethod
	def getThemen():
		pass

	@abc.abstractmethod
	def getTableResults(url):
		pass

	@abc.abstractmethod
	def getArchiv():
		pass
