#xbmc
import xbmc, xbmcgui, xbmcaddon, xbmcplugin

# python standart lib
from mythread import MyThread
import time
from random import randint
import library
import logging
import json

# application
from utilities import *
import top


TIME_UNKNOWN = 65535
CANCEL_DIALOG = (9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
# Default XBMC constant for hidden cancel button

__addon__  = get_current_addon()
__addonname__ = __addon__.getAddonInfo('name')
__cwd__	= __addon__.getAddonInfo('path')
__author__  = __addon__.getAddonInfo('author')
__version__   = __addon__.getAddonInfo('version')
__language__  = __addon__.getLocalizedString

class SynopsiPlayer(xbmc.Player):
	""" Bugfix and processing layer """
	started = False
	ended = False
	stopped = False
	paused = False
	ended_without_rating = False
	apiclient = None

	playing = False
	media_file = None
	mediainfotag = None
	last_played_file = None
	playerEvents = []


	def __init__(self):
		super(SynopsiPlayer, self).__init__()	# this will probably not call the xbmc.Player's init, but it is ok
		self.log('INIT')
		self.current_time = 0

		self.apiclient = top.apiClient

	def log(self, msg):
		log('SynopsiPlayer: ' + msg)

	def playerEvent(self, eventName, position=None):
		self.log('playerEvent:' + eventName)

		event = {
			'event': eventName,
			'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
		}

		if position:
			event['position'] = position
		elif self.playing:
			event['position'] = int(self.current_time)
		else:
			event['position'] = TIME_UNKNOWN

		self.playerEvents.append(event)

	def playerEventSeek(self, position):
		self.log('playerEvent: seek %f' % position)
		event = {
			'event': 'seek',
			'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
		}
		event['position'] = position
		self.playerEvents.append(event)


	def onPlayBackStarted(self):
		self.log('onPlayBackStarted')
		# this is just next file of a movie
		if self.playing:
			if self.media_file != xbmc.Player().getPlayingFile():
				self.media_file = xbmc.Player().getPlayingFile()
				self.last_played_file = self.media_file
				self.subtitle_file = self.getSubtitles()

		# started new video playback
		else:
			if xbmc.Player().isPlayingVideo():
				self.playing = True
				self.total_time = xbmc.Player().getTotalTime()
				self.current_time = self.get_time()
				self.started()
				self.media_file = self.getPlayingFile()
				self.mediainfotag = self.getVideoInfoTag()
				self.last_played_file = self.media_file
				self.subtitle_file = self.getSubtitles()

	def onPlayBackEnded(self):		
		# this will avoid entering the if branch in the middle of the multi-file
		percent = self.current_time / self.total_time
		if percent > 0.9 and self.playing:
			self.ended()
			self.playing = False
			self.media_file = None
					
	def onPlayBackStopped(self):
		self.log('onPlayBackStopped')
		if self.playing:
			self.stopped()
			self.playing = False
			self.media_file = None

	def onPlayBackPaused(self):
		self.log('onPlayBackPaused')
		if self.playing:
			self.paused()

	def onPlayBackResumed(self):
		if self.playing:
			self.resumed()

	def get_time(self, default=TIME_UNKNOWN):
		try:
			if self.isPlayingVideo():
				t = int(self.getTime())
			else:
				raise Exception('fix: xbmc missing exception')
		except:
			return default

		return t

	def get_media_info_tag(self):
		try:
			self.mediainfotag = self.getVideoInfoTag()
		except:
			pass


class SynopsiPlayerDecor(SynopsiPlayer):
	""" This class defines methods that are called from the bugfix and processing parent class"""
	def __init__(self):
		super(SynopsiPlayerDecor, self).__init__()

	def setStvList(self, cache):
		self.cache = cache

	def update_current_time(self):
		""" This function updates the current_time. To avoid race condition, it will not update
			the current time, if get_time returns None, but the player is still playing a file
			(acording to the self.playing variable). This indicates that the service thread update loop
			tries to update time while we are in the onPlayBackStopped method and handlers """
		
		t = self.get_time()
			
		if t or not self.playing:
			self.current_time = t
			
			
		#~ self.get_media_info_tag()

	def started(self):
		self.update_current_time()
		self.playerEvent('start')

	def ended(self):
		self.playerEvent('end', self.total_time)

		# rate file
		self.rate_file(self.last_played_file)

	def ended_without_rating(self):
		self.playerEvent('end')

	def stopped(self):
		self.playerEvent('stop')
		#~ self.log(dump(self.playerEvents))
		percent = self.current_time / self.total_time
		self.log('percent:' + str(self.current_time / self.total_time))

		# ask for rating only if more than 70% of movie passed
		if percent > 0.7:
			self.rate_file(self.last_played_file)
		else:
			self.send_checkin(self.last_played_file)

	def paused(self):
		self.update_current_time()
		self.playerEvent('pause')

	def resumed(self):
		self.update_current_time()
		self.playerEvent('resume')

	def rate_file(self, filename, rate=True):
		# work only on files in library
		if not self.cache.hasFilename(filename):
			return False

		# get stv id
		detail = self.cache.getByFilename(filename)

		self.log('detail: ' + str(detail))

		# only for identified by synopsi
		if not detail.has_key('stvId'):
			return False

		## prepare the data
		data = { 'player_events': json.dumps(self.playerEvents) }
	
		# prepare timestamp if avail
		pe = self.playerEvents
		if len(pe) > 0 and pe[0]['event'] == 'start':
			data['created_time'] = pe[0]['timestamp']

		# prepare rating if requested
		if rate:
			rating = get_rating()
			# if user rated the title
			if rating < 4:
				data['rating'] = rating

		self.apiclient.titleWatched(detail['stvId'], **data)

		# clear the player events
		self.playerEvents = []

	def send_checkin(self, filename):
		self.rate_file(filename, rate=False)
