import json
from requests import get, post
from xbmcaddon import Addon
from xbmcvfs import translatePath

from lib.authentication import get_auth_token

def set_watch_history(playlist_id: str) -> None:
	addon = Addon()
	addon.setSettingBool('watch_history_enable', True)
	addon.setSettingString('watch_history_playlist', playlist_id)

def mark_as_watched(video_id: str) -> None:
	addon = Addon()
	profile_path: str = translatePath(addon.getAddonInfo("profile"))
	instance: str = addon.getSettingString('instance')
	auth_token: str = get_auth_token()
	playlist_id: str = addon.getSettingString('watch_history_playlist')

	videos = get(f'{instance}/playlists/{playlist_id}').json()['relatedStreams']
	index: int = -1

	for i in range(len(videos)):
		if videos[i]['url'] == f"/watch?v={video_id}":
			index = i
			break

	if index == -1:
		post(f'{instance}/user/playlists/add', json = dict(
			playlistId = playlist_id,
			videoId = video_id
		), headers={'Authorization': auth_token})

	try:
		with open(f'{profile_path}/watch_history.json', 'r') as f:                                                    
			history = json.load(f)
		history.insert(0, video_id)

		with open(f'{profile_path}/watch_history.json', 'w+') as f:                                                    
			json.dump(history, f)
	except:
		pass

def mark_as_unwatched(video_id: str) -> None:
	addon = Addon()
	profile_path: str = translatePath(addon.getAddonInfo("profile"))
	instance: str = addon.getSettingString('instance')
	auth_token: str = get_auth_token()
	playlist_id: str = addon.getSettingString('watch_history_playlist')

	videos: list = get(f'{instance}/playlists/{playlist_id}').json()['relatedStreams']

	for i in range(len(videos)):
		if videos[i]['url'] == f"/watch?v={video_id}":
			post(f'{instance}/user/playlists/remove', json = dict(
				playlistId = playlist_id,
				index = i
			), headers={'Authorization': auth_token})
			break

	try:
		with open(f'{profile_path}/watch_history.json', 'r') as f:                                                    
			history = json.load(f)
		history.remove(video_id)

		with open(f'{profile_path}/watch_history.json', 'w+') as f:                                                    
			json.dump(history, f)
	except:
		pass
