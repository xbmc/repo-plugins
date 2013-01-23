import xbmc

class Addon(object):
	"""
	docstring for Addon
	"""
	def __init__(self):
		super(Addon, self).__init__()
		self.data = {}
	
	def getAddonInfo(self, type):
		return ""

	def setSetting(self, id="id", value="value"):
		self.data[id] = value

	def getSetting(self, id):
		if self.data.has_key(id):
			return self.data[id]
		else:
			return ""

	def openSettings(self):
		pass

	def getLocalizedString(self, *args, **kwargs):
		return "String"
