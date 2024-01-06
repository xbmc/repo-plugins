import sys
import requests
import time
import json
from urllib.parse import quote

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

from lib.utils import get_component, human_format

addon = xbmcaddon.Addon()
profile_path: str = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

addon_url: str = f"plugin://{addon.getAddonInfo('id')}"
if __name__ == "__main__":
	addon_handle: int = int(sys.argv[1])
	
	xbmcplugin.setContent(addon_handle, 'videos')

instance: str = addon.getSettingString('instance')

def get_auth_token() -> str:
	if not addon.getSettingBool('use_login'): return ''

	if len(addon.getSettingString('auth_token')) > 0:
		return addon.getSettingString('auth_token')
	else:
		error_msg: str = ''
		try:
			result = requests.post(f'{instance}/login', json = dict(
				username = addon.getSettingString('username'),
				password = addon.getSettingString('password')
			))

			error_msg = result.text

			auth_token = result.json()['token']
			addon.setSettingString('auth_token', auth_token)

			return auth_token
		except:
			xbmcgui.Dialog().ok(addon.getLocalizedString(30016), error_msg)
			return ''


def home() -> None:
	folders: list = list()
	if addon.getSettingBool('use_login'):
		folders.append(('feed', addon.getLocalizedString(30001)))
		folders.append(('subscriptions', addon.getLocalizedString(30002)))
		folders.append(('playlists',addon.getLocalizedString(30003)))
		if addon.getSettingBool('watch_history_enable') and len(addon.getSettingString('watch_history_playlist')) > 0:
			folders.append(('watch_history', addon.getLocalizedString(30004)))
	
	folders.append(('trending', addon.getLocalizedString(30005)))
	folders.append(('search_select', addon.getLocalizedString(30006)))
	folders.append(('settings', addon.getLocalizedString(30007)))

	for folder in folders:
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/{folder[0]}", listitem=xbmcgui.ListItem(folder[1]), isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def watch(video_id: str) -> None:
	listitem = xbmcgui.ListItem(
		path=f'http://localhost:{addon.getSettingInt("http_port")}/watch?v={video_id}',
	)
	listitem.setProperty('inputstream', 'inputstream.adaptive')
	listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
	listitem.setProperty('piped_video_id', video_id)

	xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)

def list_videos(videos: list, hide_watched: bool=False, nextpage: str='') -> None:
	history: list = list()
	watch_history_enabled: bool = addon.getSettingBool('watch_history_enable') and len(addon.getSettingString('watch_history_playlist')) > 0
	if watch_history_enabled:
		try:
			with open(f'{profile_path}/watch_history.json', 'r') as f:                                                    
				history = json.load(f)
		except:
			pass

	for video in videos:
		plugin_url: str = f"{addon_url}{video['url'].replace('?v=', '/')}"
		video_id: str = get_component(video['url'])['params']['v']
		if hide_watched and video_id in history: continue
		if 'uploadedDate' in video and video['uploadedDate'] is not None: date: str = video['uploadedDate']
		elif video['uploaded'] > 0: date: str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(video['uploaded'] / 1000))
		else: date: str = ''
		info: str = f"{video['title']}\n\n{video['uploaderName']}\n\n"
		if video['views'] >=0: info += f"{addon.getLocalizedString(30008)}: {human_format(video['views'])}\n"
		if len(date) > 2: info += f"{addon.getLocalizedString(30009)}: {date}"
		listitem = xbmcgui.ListItem(label=video['title'], path=plugin_url)
		listitem.setProperty('isplayable', 'true')
		listitem.setArt(dict(
			thumb = video['thumbnail'],
			fanart = video['uploaderAvatar']
		))

		tag = listitem.getVideoInfoTag()
		tag.setTitle(video['title'])
		tag.setPlot(info)
		tag.setDuration(video['duration'])
		tag.setFilenameAndPath(plugin_url)
		tag.setPath(plugin_url)

		context_menu_items: list = [(addon.getLocalizedString(30010), f"RunAddon({addon.getAddonInfo('id')}, {video['uploaderUrl']})")]
		if watch_history_enabled:
			if video_id in history:
				context_menu_items.append((addon.getLocalizedString(30011), f"RunPlugin({addon_url}/mark_as_unwatched?id={video_id})"))
			else:
				context_menu_items.append((addon.getLocalizedString(30012), f"RunPlugin({addon_url}/mark_as_watched?id={video_id})"))
		listitem.addContextMenuItems(context_menu_items, replaceItems=True)

		xbmcplugin.addDirectoryItem(addon_handle, plugin_url, listitem, False)

	if len(nextpage) > 0:
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/{nextpage}", listitem=xbmcgui.ListItem(addon.getLocalizedString(30017)), isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def feed() -> None:
	instance: str = addon.getSettingString('instance')
	auth_token = get_auth_token()

	videos = requests.get(f'{instance}/feed?authToken={auth_token}').json()

	list_videos(videos, addon.getSettingBool('watch_history_hide_watched_feed'))

def list_channels(channels: list, nextpage: str='') -> None:
	for channel in channels:
		info: str = ''
		if 'shortDescription' in channel and channel['shortDescription'] is not None: info += channel['shortDescription'] + "\n\n"
		elif 'description' in channel and channel['description'] is not None: info += channel['description'] + "\n\n"

		listitem = xbmcgui.ListItem(channel['name'])

		if 'avatar' in channel:
			listitem.setArt(dict(
				thumb = channel['avatar']
			))
		elif 'thumbnail' in channel:
			listitem.setArt(dict(
				thumb = channel['thumbnail']
			))

		tag = listitem.getVideoInfoTag()
		tag.setTitle(channel['name'])
		tag.setPlot(info)

		xbmcplugin.addDirectoryItem(addon_handle, f"{addon_url}{channel['url']}", listitem, True)

	if len(nextpage) > 0:
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/{nextpage}", listitem=xbmcgui.ListItem(addon.getLocalizedString(30017)), isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def subscriptions() -> None:
	instance: str = addon.getSettingString('instance')
	auth_token = get_auth_token()

	list_channels(requests.get(f'{instance}/subscriptions', headers={'Authorization': auth_token}).json())

def list_playlists(playlists: list, nextpage: str='') -> None:
	for playlist in playlists:
		info: str = ''
		if 'shortDescription' in playlist and playlist['shortDescription'] is not None: info += playlist['shortDescription'] + "\n\n"
		elif 'description' in playlist and playlist['description'] is not None: info += playlist['description'] + "\n\n"
		info += f"{addon.getLocalizedString(30018)}: {playlist['videos']}"

		if 'id' not in playlist:
			playlist['id'] = get_component(playlist['url'])['params']['list']
		
		listitem = xbmcgui.ListItem(playlist['name'])
		listitem.setArt(dict(
			thumb = playlist['thumbnail']
		))

		tag = listitem.getVideoInfoTag()
		tag.setTitle(playlist['name'])
		tag.setPlot(info)

		listitem.addContextMenuItems([(addon.getLocalizedString(30013), f"RunPlugin({addon_url}/set_watch_history?id={playlist['id']})")])
		xbmcplugin.addDirectoryItem(addon_handle, f"{addon_url}/playlist?id={playlist['id']}", listitem, True)

	if len(nextpage) > 0:
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/{nextpage}", listitem=xbmcgui.ListItem(addon.getLocalizedString(30017)), isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def playlists() -> None:
	instance: str = addon.getSettingString('instance')
	auth_token = get_auth_token()

	list_playlists(requests.get(f'{instance}/user/playlists', headers={'Authorization': auth_token}).json())

def playlist(playlist_id: str, hide_watched=None) -> None:
	instance: str = addon.getSettingString('instance')

	playlist_info = requests.get(f'{instance}/playlists/{playlist_id}').json()
	hide_watched: bool = hide_watched if hide_watched is not None else addon.getSettingBool('watch_history_hide_watched_playlists')

	if playlist_info['videos'] > 0: list_videos(playlist_info['relatedStreams'], hide_watched)
	else: xbmcgui.Dialog().ok(addon.getLocalizedString(30014), addon.getLocalizedString(30015))

def watch_history() -> None:
	playlist(addon.getSettingString('watch_history_playlist'), False)

def set_watch_history(playlist_id: str) -> None:
	addon.setSettingBool('watch_history_enable', True)
	addon.setSettingString('watch_history_playlist', playlist_id)

def mark_as_watched(video_id: str) -> None:
	instance: str = addon.getSettingString('instance')
	auth_token: str = get_auth_token()
	playlist_id: str = addon.getSettingString('watch_history_playlist')

	videos = requests.get(f'{instance}/playlists/{playlist_id}').json()['relatedStreams']
	index: int = -1

	for i in range(len(videos)):
		if videos[i]['url'] == f"/watch?v={video_id}":
			index = i
			break

	if index == -1:
		requests.post(f'{instance}/user/playlists/add', json = dict(
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
	instance: str = addon.getSettingString('instance')
	auth_token: str = get_auth_token()
	playlist_id: str = addon.getSettingString('watch_history_playlist')

	videos: list = requests.get(f'{instance}/playlists/{playlist_id}').json()['relatedStreams']

	for i in range(len(videos)):
		if videos[i]['url'] == f"/watch?v={video_id}":
			requests.post(f'{instance}/user/playlists/remove', json = dict(
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

def channel(channel_id: str, nextpage: str="") -> None:
	instance: str = addon.getSettingString('instance')

	url: str = f'{instance}/nextpage/channel/{channel_id}?nextpage={quote(nextpage)}' if len(nextpage) > 0 else f'{instance}/channel/{channel_id}'

	response: dict = requests.get(url).json()

	component_nextpage: str = ''
	if 'nextpage' in response and isinstance(response["nextpage"], str): component_nextpage = f'/channel/{channel_id}?nextpage={quote(response["nextpage"])}'

	list_videos(response['relatedStreams'], addon.getSettingBool('watch_history_hide_watched_channels'), component_nextpage)

def trending() -> None:
	instance: str = addon.getSettingString('instance')

	videos = requests.get(f'{instance}/trending?region=US').json()

	list_videos(videos, addon.getSettingBool('watch_history_hide_watched_trending'))

def search(search_filter: str, query: str='', nextpage: str='') -> None:
	instance: str = addon.getSettingString('instance')

	window = xbmcgui.Window(10000)

	if not len(query) > 0:
		query = window.getProperty('PipedLastSearch') if len(window.getProperty('PipedLastSearch')) > 0 else xbmcgui.Dialog().input(addon.getLocalizedString(30006))
		window.setProperty('PipedLastSearch', query)

		if not len(query) > 0: return

	url: str = f'{instance}/nextpage/search?nextpage={quote(nextpage)}&' if len(nextpage) > 0 else f'{instance}/search?'
	url += f'q={quote(query)}&filter={search_filter}'

	response: dict = requests.get(url).json()

	component_nextpage: str = ''
	if 'nextpage' in response and isinstance(response["nextpage"], str): component_nextpage = f'/search?nextpage={quote(response["nextpage"])}&q={quote(query)}&search_filter={search_filter}'

	if search_filter == 'videos':
		list_videos(response['items'], addon.getSettingBool('watch_history_hide_watched_search'), component_nextpage)
	elif search_filter == 'channels':
		list_channels(response['items'], component_nextpage)
	elif search_filter == 'playlists':
		list_playlists(response['items'], component_nextpage)

def search_select():
	window = xbmcgui.Window(10000)
	window.setProperty('PipedLastSearch', '')

	xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/search?search_filter=videos", listitem=xbmcgui.ListItem(addon.getLocalizedString(30018)), isFolder=True)
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/search?search_filter=channels", listitem=xbmcgui.ListItem(addon.getLocalizedString(30019)), isFolder=True)
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/search?search_filter=playlists", listitem=xbmcgui.ListItem(addon.getLocalizedString(30003)), isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)

if __name__ == "__main__":
	component: dict = get_component(sys.argv[0] + sys.argv[2])

	if component['path'] == '/': home()
	elif component['path'] == '/feed': feed()
	elif component['path'] == '/settings': addon.openSettings()
	elif component['path'] == '/subscriptions': subscriptions()
	elif component['path'] == '/playlists': playlists()
	elif component['path'] == '/search_select': search_select()
	elif component['path'] == '/search': search(component['params']['search_filter'], component['params']['q'] if 'q' in component['params'] else '', component['params']['nextpage'] if 'nextpage' in component['params'] else '')
	elif component['path'] == '/trending': trending()
	elif component['path'] == '/playlist': playlist(component['params']['id'])
	elif component['path'] == '/watch_history': watch_history()
	elif component['path'] == '/set_watch_history': set_watch_history(component['params']['id'])
	elif component['path'] == '/mark_as_watched': mark_as_watched(component['params']['id'])
	elif component['path'] == '/mark_as_unwatched': mark_as_unwatched(component['params']['id'])
	elif component['path'][:6] == '/watch': watch(component['path'][7:])
	elif component['path'][:8] == '/channel': channel(component['path'][9:], component['params']['nextpage'] if 'nextpage' in component['params'] else '')
