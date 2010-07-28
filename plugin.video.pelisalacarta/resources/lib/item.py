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

	def __init__(self, channel="", title="", url="", thumbnail="", plot="", duration="", fanart="", action="", server="", folder=False):
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
