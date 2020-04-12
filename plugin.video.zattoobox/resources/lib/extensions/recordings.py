# coding=utf-8

##################################
# ZattooBox extension
# Recordings
# (c) 2014-2020 Pascal Nançoz
##################################

from resources.lib.core.zbextension import ZBExtension
from resources.lib.core.zbfolderitem import ZBFolderItem
from resources.lib.core.zbplayableitem import ZBPlayableItem
import os

class Recordings(ZBExtension):

	def init(self):
		return

	def get_items(self):
		content = [
			ZBFolderItem(
				host=self,
				args={'mode': 'root'},
				title=self.ZBProxy.get_string(30102),
				image=os.path.join(self.ExtensionsPath, 'recordings/video.png')
			)
		]
		return content

	def activate_item(self, args):
		if args['mode'] == 'root':
			self.build_recordingsList()
		elif args['mode'] == 'watch':
			self.watch(args)

	#---

	def build_recordingsList(self):
		resultData = self.ZapiSession.exec_zapiCall('/zapi/playlist', None)
		if resultData is None:
			return

		recordings = []
		for record in resultData['recordings']:
			recordings.append(ZBPlayableItem(
				host=self,
				args={'mode': 'watch', 'id': record['id']},
				title=record['title'],
				image=record['image_url'],
				title2=record['episode_title']
				)
			)
		self.ZBProxy.add_directoryItems(recordings)

	def watch(self, args):
		params = {'recording_id': args['id'], 'stream_type': 'hls'}
		resultData = self.ZapiSession.exec_zapiCall('/zapi/watch', params)
		if resultData is not None:
			url = resultData['stream']['url']
			self.ZBProxy.play_stream(url)

