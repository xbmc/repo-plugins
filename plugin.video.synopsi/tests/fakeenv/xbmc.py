
# python standart library
import logging
import sys
import SocketServer
import socket
import time
import json
import os

from mythread import MyThread

abortRequested = False

def sleep(tim):
	pass


def log(string):
	print string


def executeJSONRPC(js):
	print "XBMC received: ", js.strip()
	return "{}"


def executebuiltin(builtin):
	if "XBMC.Notification" in builtin:
		pass
		a = builtin.split(",")
		print "XBMC message:", a[0].strip("XBMC.Notification("), a[1]
	else:
		print "Executed Builtin:", builtin

def translatePath(path):
		return 'data/'

class Player(MyThread):
	def __init__(self):
		super(Player, self).__init__()
		self.start()

	def onPlayBackStarted(self):
		pass

	def onPlayBackEnded(self):
		pass

	def onPlayBackStopped(self):
		pass

	def onPlayBackPaused(self):
		pass

	def onPlayBackResumed(self):
		pass

	def isPlayingVideo(self):
		return True

	def getTime(self):
		return 71

	def getTotalTime(self):
		return 100

	def getPlayingFile(self):
		return ""

	def run(self):
		self.onPlayBackStarted()
		time.sleep(0.21)
		self.onPlayBackResumed()
		time.sleep(0.21)
		self.onPlayBackPaused()
		time.sleep(0.21)
		self.onPlayBackStopped()
