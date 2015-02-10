import xbmc
		
class Dialog(object):
	"""
	docstring for Dialog
	"""
	def __init__(self):
		super(Dialog, self).__init__()
		print "Dialog opened."

	def ok(self, title, message):
		print "Showing OKDialog: Title: {0}, Message{1}".format(title, message)
	
	def close(self):
		pass

class WindowXMLDialog(Dialog):
	"""
	docstring for WindowXMLDialog
	"""
	def __init__(self):
		super(WindowXMLDialog, self).__init__()

	def doModal(self):
		pass
