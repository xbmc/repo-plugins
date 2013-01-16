class SynopsiPlayer(object):
	""" Bugfix and processing layer """
	def __init__(self):
		super(SynopsiPlayer, self).__init__()

class SynopsiPlayerDecor(SynopsiPlayer):
	""" This class defines methods that are called from the bugfix and processing parent class"""
	def __init__(self, cache):
		super(SynopsiPlayerDecor, self).__init__()
		self.cache = cache

class StvList(object):
	pass

cache = StvList()
p = SynopsiPlayerDecor(cache)
 
