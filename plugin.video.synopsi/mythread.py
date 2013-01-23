# xbmc
import xbmc

# python standart lib
import threading
import logging
import os

# application
import loggable
		
class MyThread(threading.Thread, loggable.Loggable):
	def __init__(self):
		#~ super(MyThread, self).__init__()
		# workaround: super doesn't call the Loggable's init
		threading.Thread.__init__(self)
		loggable.Loggable.__init__(self)
		
		self.name = self.__class__.__name__
