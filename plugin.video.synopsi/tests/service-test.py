import unittest
import SocketServer
import time
import threading
from mythread import MyThread
import sys

sys.path.append('..')
service = __import__('service')
scrobbler = __import__('scrobbler')
import xbmc, xbmcgui, xbmcaddon



def PrepareTests():
	pass

def NotificationTests(request):
	time.sleep(0.85) # wait for scrobbler tests
	def send(data):
		request.send(data)
		time.sleep(0.05)
	# {"jsonrpc":"2.0","method":"VideoLibrary.OnUpdate","params":{"data":{"item":{"id":48,"type":"episode"}},"sender":"xbmc"}}
	send('{"jsonrpc":"2.0","method":"VideoLibrary.OnUpdate","params":{"data":{"item":{"id":48,"type":"episode"}},"sender":"xbmc"}}')
	send('{"jsonrpc":"2.0","method":"VideoLibrary.OnRemove","params":{"data":{"id":2,"type":"episode"},"sender":"xbmc"}}')
	send('{"jsonrpc":"2.0","method":"System.OnQuit","params":{"data":null,"sender":"xbmc"}}')

def MethodTests():
	pass

class EchoRequestHandler(SocketServer.BaseRequestHandler):
	def setup(self):
		print "Client", self.client_address[0], "PID:",self.client_address[1], 'connected'
		NotificationTests(self.request)

	# def handle(self):
	#	 data = 'dummy'
	#	 while data:
	#		 data = self.request.recv(1024)
	#		 self.request.send(data)
	#		 if data.strip() == 'bye':
	#			 return

	def finish(self):
		print "Client", self.client_address[0], "PID:",self.client_address[1], 'disconnected'

HOST, PORT = "localhost", 9090
SERVER = SocketServer.TCPServer((HOST, PORT), EchoRequestHandler)
class TCPServer(MyThread):
	def __init__(self):
		super(TCPServer, self).__init__()

	def run(self):
		SERVER.serve_forever()

def main():
	service.main()


if __name__ == '__main__':
	PrepareTests()
	print "Starting XBMC emulator at", HOST, PORT
	t = TCPServer().start()
	try:
		main()
	except Exception,e:
		SERVER.shutdown()
		raise e
	else: 
		SERVER.shutdown()
