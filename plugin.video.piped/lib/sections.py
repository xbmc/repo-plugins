import time
import json
from re import sub
from urllib.parse import quote
from requests import get
from xbmcaddon import Addon
from xbmcvfs import translatePath
import xbmcgui
import xbmcplugin

from lib.authentication import get_auth_token
from lib.history import set_watch_history, mark_as_watched, mark_as_unwatched
from lib.utils import get_component, human_format

addon = Addon()
addon_handle: int = -1 # Will be properly set by router
addon_url: str = f"plugin://{addon.getAddonInfo('id')}"

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
			with open(f'{translatePath(addon.getAddonInfo("profile"))}/watch_history.json', 'r') as f:                                                    
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

	videos = get(f'{instance}/feed?authToken={auth_token}').json()

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

	list_channels(get(f'{instance}/subscriptions', headers={'Authorization': auth_token}).json())

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

	list_playlists(get(f'{instance}/user/playlists', headers={'Authorization': auth_token}).json())

def playlist(playlist_id: str, hide_watched=None) -> None:
	instance: str = addon.getSettingString('instance')

	playlist_info = get(f'{instance}/playlists/{playlist_id}').json()
	hide_watched: bool = hide_watched if hide_watched is not None else addon.getSettingBool('watch_history_hide_watched_playlists')

	if playlist_info['videos'] > 0: list_videos(playlist_info['relatedStreams'], hide_watched)
	else: xbmcgui.Dialog().ok(addon.getLocalizedString(30014), addon.getLocalizedString(30015))

def watch_history() -> None:
	playlist(addon.getSettingString('watch_history_playlist'), False)

def channel(channel_id: str, nextpage: str="") -> None:
	instance: str = addon.getSettingString('instance')

	url: str = f'{instance}/nextpage/channel/{channel_id}?nextpage={quote(nextpage)}' if len(nextpage) > 0 else f'{instance}/channel/{channel_id}'

	response: dict = get(url).json()

	component_nextpage: str = ''
	if 'nextpage' in response and isinstance(response["nextpage"], str): component_nextpage = f'/channel/{channel_id}?nextpage={quote(response["nextpage"])}'

	list_videos(response['relatedStreams'], addon.getSettingBool('watch_history_hide_watched_channels'), component_nextpage)

def trending() -> None:
	instance: str = addon.getSettingString('instance')

	videos = get(f'{instance}/trending?region=US').json()

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

	response: dict = get(url).json()

	component_nextpage: str = ''
	if 'nextpage' in response and isinstance(response["nextpage"], str): component_nextpage = f'/search?nextpage={quote(response["nextpage"])}&q={quote(query)}&search_filter={search_filter}'

	if search_filter == 'videos':
		list_videos(response['items'], addon.getSettingBool('watch_history_hide_watched_search'), component_nextpage)
	elif search_filter == 'channels':
		list_channels(response['items'], component_nextpage)
	elif search_filter == 'playlists':
		list_playlists(response['items'], component_nextpage)

def search_select() -> None:
	window = xbmcgui.Window(10000)
	window.setProperty('PipedLastSearch', '')

	xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/search?search_filter=videos", listitem=xbmcgui.ListItem(addon.getLocalizedString(30018)), isFolder=True)
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/search?search_filter=channels", listitem=xbmcgui.ListItem(addon.getLocalizedString(30019)), isFolder=True)
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/search?search_filter=playlists", listitem=xbmcgui.ListItem(addon.getLocalizedString(30003)), isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)

def settings() -> None:
	addon.openSettings()

def router(argv: list) -> None:
	component: dict = get_component(argv[0] + argv[2])

	global addon_handle
	addon_handle = int(argv[1])

	routes: dict = {
		'home': {},
		'feed': {},
		'settings': {},
		'subscriptions': {},
		'playlists': {},
		'search_select': {},
		'search': {
			'search_filter': component['params']['search_filter'] if 'search_filter' in component['params'] else '',
			'query': component['params']['q'] if 'q' in component['params'] else '',
			'nextpage': component['params']['nextpage'] if 'nextpage' in component['params'] else ''
		},
		'trending': {},
		'playlist': {
			'playlist_id': component['params']['id'] if 'id' in component['params'] else ''
		},
		'watch_history': {},
		'set_watch_history': {
			'playlist_id': component['params']['id'] if 'id' in component['params'] else ''
		},
		'mark_as_watched': {
			'video_id': component['params']['id'] if 'id' in component['params'] else ''
		},
		'mark_as_unwatched': {
			'video_id': component['params']['id'] if 'id' in component['params'] else ''
		},
		'watch': {
			'video_id': sub(r'.*\/', '', component['path'])
		},
		'channel': {
			'channel_id': sub(r'.*\/', '', component['path']),
			'nextpage': component['params']['nextpage'] if 'nextpage' in component['params'] else ''
		},
	}

	route: str = sub(r'\/.*', '', component['path'][1:])
	if route == '': route = 'home'

	if route in routes:
		globals()[route](**routes[route])