class Item(object):
	channel = ""
	title = ""
	url = ""
	thumbnail = ""
	plot = ""
	duration = ""
	fanart = ""
	folder = ""
	action = ""
	server = ""
	extra = ""

	def __init__(self, channel="", title="", url="", thumbnail="", plot="", duration="", fanart="", action="", server="", extra="", folder=False):
		self.channel = channel
		self.title = title
		self.url = url
		self.thumbnail = thumbnail
		self.plot = plot
		self.duration = duration
		self.fanart = fanart
		self.folder = folder
		self.server = server
		self.action = action
		self.extra = extra

	def tostring(self):
		return "title=["+self.title+"], url=["+self.url+"], thumbnail=["+self.thumbnail+"]"