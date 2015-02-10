
class Fake(object):

	def __init__(self, what):
		self.what = what
		print what, 'x'

	def noop(self):
		pass

	def __getattr__(self, methodName):
		try:
			method = getattr(m, methodName)
			print method
		except:
			print 'Undefined method:' + methodName
			return self.noop

		return method

class Methods(object):
	def __init__(self):
		pass

	def Gama(self, someValue):
		print someValue

  

m = Methods()

f = Fake('a')
f.ble()
f.Gama('huh')

