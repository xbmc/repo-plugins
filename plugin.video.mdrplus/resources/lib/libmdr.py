# -*- coding: utf-8 -*-	
import resources.lib.libmdrmetaparser as libmdrmetaparser
from libmediathek4 import lm4

#https://www.mdr.de/video/mdrplus-videos100-meta.xml
#https://www.mdr.de/livestream%2Dmdr%2Dplus100-meta.xml
#https://www.mdr.de/alle-videos-mdrplus-100-meta.xml

parser = libmdrmetaparser.parser()
class libmdr(lm4):
	def __init__(self):
		self.defaultMode = 'libMdrListMain'
		self.modes = {
			'libMdrListMain': self.libMdrListMain,
			'libMdrBroadcast': self.libMdrBroadcast,
			
			'libMdrListShows': self.libMdrListShows,
			'libMdrListPlus': self.libMdrListPlus,
			'libMdrListVideos': self.libMdrListVideos,
			#'libMdrListDateChannels': self.libMdrListDateChannels,
		}

		self.playbackModes = {
			'libMdrPlay':self.libMdrPlay,
		}

	def libMdrListMain(self):
		l = []
		l.append({'metadata':{'name':self.translation(32143)}, 'params':{'mode':'libMdrListPlus', 'url':'https://www.mdr.de/video/livestreams/livestreams-socialtv-event-100-meta.xml'}, 'type':'dir'})
		l.append({'metadata':{'name':self.translation(32146)}, 'params':{'mode':'libMdrListPlus', 'url':'https://www.mdr.de/video/mdrplus-videos100-meta.xml'}, 'type':'dir'})
		return {'items':l,'name':'root'}

	def libMdrBroadcast():
		return libMdrMetaParser.parseBroadcast(params['url'])
				
	def libMdrListShows():
		libMediathek.sortAZ()
		return libMdrMetaParser.parseShows()

	def libMdrListPlus(self):
		return parser.parsePlus(self.params['url'])
		return parser.parseMdrPlus(self.params['url'])
		
	def libMdrListVideos():
		return libMdrMetaParser.parseVideos(params['url'])
		
	def libMdrPlay(self):
		return parser.parseVideo(self.params['url'])
		
		