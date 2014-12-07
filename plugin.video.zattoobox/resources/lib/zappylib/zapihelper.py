# coding=utf-8

##################################
# Zappylib V0.5.0
# ZapiHelper
# (c) 2014 Pascal Nançoz
##################################
import os, time, json, base64

class ZapiHelper:
	IMAGES_ROOT = 'http://logos.zattic.com'
	CHANNELS_CACHE_FILE = None
	ZapiSession = None

	def __init__(self, zapiSession):
		self.CHANNELS_CACHE_FILE = os.path.join(zapiSession.DATA_FOLDER, 'channels.cache')
		self.ZapiSession = zapiSession

# -- Channels -- 
	def fetch_imageUrl(self, relPath):
		return self.IMAGES_ROOT + relPath.replace('/images/channels', '')

	def persist_channels(self, channelsData):
		channelsData['expires'] = time.time() + 86400
		with open(self.CHANNELS_CACHE_FILE, 'w') as f:
			f.write(base64.b64encode(json.dumps(channelsData)))

	def retrieve_channels(self):
		if os.path.isfile(self.CHANNELS_CACHE_FILE):
			with open(self.CHANNELS_CACHE_FILE, 'r') as f:
				channelsData = json.loads(base64.b64decode(f.readline()))
			if channelsData is not None and channelsData['expires'] > time.time():
				return channelsData
		api = '/zapi/v2/cached/channels/' + self.ZapiSession.AccountData['account']['power_guide_hash'] + '?details=False'
		channelsData = self.ZapiSession.exec_zapiCall(api, None)
		if channelsData is not None:
			self.persist_channels(channelsData)
			return channelsData
		return None

	def get_allChannels(self, flag_favorites=False):
		channelsData = self.retrieve_channels()
		if channelsData is None: 
			return None

		if flag_favorites:
			api = '/zapi/channels/favorites'
			favoritesData = self.ZapiSession.exec_zapiCall(api, None)
			if favoritesData is None:
				return None

		allChannels = []
		for group in channelsData['channel_groups']:
			for channel in group['channels']:
				allChannels.append({
					'id': channel['id'],
					'title': channel['title'],
					'image_url': self.fetch_imageUrl(channel['qualities'][0]['logo_black_84']),
					'recommend': 1 if channel['recommendations'] == True else 0,
					'favorite': 1 if flag_favorites and channel['id'] in favoritesData['favorites'] else 0})
		return allChannels

	def get_channels(self, category):
		allChannels = self.get_allChannels(True if category == 'favorites' else False)
		if allChannels is not None:
			if category == 'favorites':
				return [channel for channel in allChannels if channel['favorite'] == 1]
			elif category == 'recommended':
				return [channel for channel in allChannels if channel['recommend'] == 1]
			return allChannels
		return None

