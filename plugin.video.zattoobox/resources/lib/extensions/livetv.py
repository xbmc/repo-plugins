# coding=utf-8

##################################
# ZattooBox extension
# LiveTV
# (c) 2014-2020 Pascal Nançoz
##################################

from resources.lib.core.zbextension import ZBExtension
from resources.lib.core.zbfolderitem import ZBFolderItem
from resources.lib.core.zbplayableitem import ZBPlayableItem
import os, time, json, base64

class LiveTV(ZBExtension):
	CHANNELS_CACHE_FILE = None
	IMAGES_ROOT = 'http://logos.zattic.com'

	def init(self):
		if self.ZapiSession.CACHE_ENABLED:
			self.CHANNELS_CACHE_FILE = os.path.join(self.ZapiSession.CACHE_FOLDER, 'channels.cache')

	def get_items(self):
		content = [
			ZBFolderItem(
				host=self,
				args={'mode': 'root', 'cat': 'fav'},
				title=self.ZBProxy.get_string(30100),
				image=os.path.join(self.ExtensionsPath, 'livetv/tv.png')
			),
			ZBFolderItem(
				host=self,
				args={'mode': 'root', 'cat': 'all'},
				title=self.ZBProxy.get_string(30101),
				image=os.path.join(self.ExtensionsPath, 'livetv/tv.png')
			)
		]
		return content

	def activate_item(self, args):
		if args['mode'] == 'root':
			self.build_channelsList(args)
		elif args['mode'] == 'watch':
			self.watch(args)

	#---
		
	def build_channelsList(self, args):
		channels = self.get_channels(args['cat'])
		if channels is None:
			return

		items = []
		for record in channels:
			items.append(ZBPlayableItem(
				host=self,
				args={'mode': 'watch', 'id': record['id']},
				title=record['title'],
				image=record['image_url'],
				title2=''
				)
			)
		self.ZBProxy.add_directoryItems(items)

	def watch(self, args):
		params = {'cid': args['id'], 'stream_type': 'hls'}
		resultData = self.ZapiSession.exec_zapiCall('/zapi/watch', params)
		if resultData is not None:
			url = resultData['stream']['watch_urls'][0]['url']
			self.ZBProxy.play_stream(url)

	#---

	def fetch_imageUrl(self, relPath):
		return self.IMAGES_ROOT + relPath.replace('/images/channels', '')

	def persist_channels(self, channelsData):
		channelsData['expires'] = time.time() + 86400
		with open(self.CHANNELS_CACHE_FILE, 'w') as f:
			f.write(base64.b64encode(json.dumps(channelsData)))

	def read_channelsCache(self):
		if os.path.isfile(self.CHANNELS_CACHE_FILE):
			with open(self.CHANNELS_CACHE_FILE, 'r') as f:
				channelsData = json.loads(base64.b64decode(f.readline()))
			if channelsData is not None and channelsData['expires'] > time.time():
				return channelsData
		return None

	def retrieve_channels(self):
		if self.ZapiSession.CACHE_ENABLED:
			channelsData = self.read_channelsCache()
			if channelsData is not None:
				return channelsData

		api = '/zapi/v2/cached/channels/%s?details=False' % self.ZapiSession.AccountData['session']['power_guide_hash']
		channelsData = self.ZapiSession.exec_zapiCall(api, None)
		if channelsData is not None:
			if self.ZapiSession.CACHE_ENABLED:
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
		allChannels = self.get_allChannels(True if category == 'fav' else False)
		if allChannels is not None:
			if category == 'fav':
				return [channel for channel in allChannels if channel['favorite'] == 1]
			elif category == 'rcm':
				return [channel for channel in allChannels if channel['recommend'] == 1]
			return allChannels
		return None

