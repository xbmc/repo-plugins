# -*- coding: utf-8 -*-
from libmediathek4 import lm4
import resources.lib.jsonparser as jsonParser



class phoenix(lm4):
	def __init__(self):
		self.defaultMode = 'listMain'
		self.modes = {
			'listMain': self.listMain,
			'listVideos': self.listVideos,
		}	

		self.playbackModes = {
			'playVideo':self.playVideo,
		}

	def listMain(self):
		return jsonParser.parseMain()
		
	def listVideos(self):
		return jsonParser.parseVideos(self.params['id'])
		
	def playVideo(self):
		return jsonParser.getVideoUrl(self.params['smubl'])

p = phoenix()
p.action()
