import time
import json
import re
from urllib.parse import quote, unquote
from requests import get
from xbmcaddon import Addon
from xbmcvfs import translatePath
import xbmcgui
import xbmcplugin

from lib.authentication import authenticated_request
from lib.history import set_watch_history, mark_as_watched, mark_as_unwatched
from lib.blacklist import blacklist_load, blacklist_add, blacklist_remove
from lib.utils import get_component, human_format

addon = Addon()
addon_handle: int = -1 # Will be properly set by router
addon_url: str = f"plugin://{addon.getAddonInfo('id')}"

def home() -> None:
	folders: list = list()
	if addon.getSettingBool('use_login'):
		if addon.getSettingBool('menu_show_feed'):
			folders.append(('feed', addon.getLocalizedString(30001)))
		if addon.getSettingBool('menu_show_feed_update'):
			folders.append(('updatefeed', addon.getLocalizedString(30020)))
		if addon.getSettingBool('menu_show_subscriptions'):
			folders.append(('subscriptions', addon.getLocalizedString(30002)))
		if addon.getSettingBool('menu_show_playlists'):
			folders.append(('playlists',addon.getLocalizedString(30003)))
		if addon.getSettingBool('menu_show_watch_history') and addon.getSettingBool('watch_history_enable') and len(addon.getSettingString('watch_history_playlist')) > 0:
			folders.append(('watch_history', addon.getLocalizedString(30004)))

	if addon.getSettingBool('menu_show_watch_trending'):
		folders.append(('trending', addon.getLocalizedString(30005)))
	if addon.getSettingBool('menu_show_watch_blacklist') and addon.getSettingBool('blacklist_channels_enable'):
			folders.append(('blacklist_section', addon.getLocalizedString(30600)))
	if addon.getSettingBool('menu_show_watch_search'):
		folders.append(('search_select', addon.getLocalizedString(30006)))
	if addon.getSettingBool('menu_show_watch_settings'):
		folders.append(('settings', addon.getLocalizedString(30007)))

	for folder in folders:
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/{folder[0]}", listitem=xbmcgui.ListItem(folder[1]), isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def watch(video_id: str) -> None:
	listitem = xbmcgui.ListItem(
		path=f'http://localhost:{addon.getSettingInt("http_port")}/watch?v={video_id}',
	)
	listitem.setProperty('inputstream', 'inputstream.adaptive')
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

	blacklist_channels_enabled: bool = addon.getSettingBool('blacklist_channels_enable')
	if blacklist_channels_enabled:
		blacklist_channels_list = blacklist_load()

	blacklist_titles_enabled: bool = addon.getSettingBool('blacklist_titles_enable')
	if blacklist_titles_enabled:
		blacklist_titles_regex_str: str = addon.getSettingString('blacklist_titles_regex')
		if len(blacklist_titles_regex_str) > 0:
			blacklist_titles_regex = re.compile(rf"{blacklist_titles_regex_str}", re.IGNORECASE if addon.getSettingBool('blacklist_titles_case_insensitive') else re.NOFLAG)
		else:
			blacklist_titles_enabled = False

	for video in videos:
		if blacklist_titles_enabled and 'title' in video and re.match(blacklist_titles_regex, video['title']):
			continue

		plugin_url: str = f"{addon_url}{video['url'].replace('?v=', '/')}"
		video_id: str = get_component(video['url'])['params']['v']
		channel_id: str = video['uploaderUrl'][9:] if ('uploaderUrl' in video and len(str(video['uploaderUrl'])) > 8) else ''

		if (hide_watched and video_id in history) or (blacklist_channels_enabled and channel_id in blacklist_channels_list):
			continue

		if 'uploadedDate' in video and video['uploadedDate'] is not None: date: str = video['uploadedDate']
		elif video['uploaded'] > 0: date: str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(video['uploaded'] / 1000))
		else: date: str = ''
		info: str = f"{video['title']}\n\n{video['uploaderName']}\n\n"
		if addon.getSettingBool('show_description') and 'shortDescription' in video and video['shortDescription'] is not None: info += video['shortDescription'] + "\n\n"
		if video['views'] >=0: info += f"{addon.getLocalizedString(30008)}: {human_format(video['views'])}\n"
		if len(date) > 2: info += f"{addon.getLocalizedString(30009)}: {date}"
		listitem = xbmcgui.ListItem(label=video['title'], path=plugin_url)
		listitem.setProperty('isplayable', 'true')
		listitem.setArt(dict(
			thumb = video['thumbnail'],
			fanart = video['thumbnail'].replace('hqdefault.jpg', 'maxresdefault.jpg')
		))

		tag = listitem.getVideoInfoTag()
		tag.setTitle(video['title'])
		tag.setPlot(info)
		tag.setDuration(video['duration'])
		if 'uploaded' in video and video['uploaded'] > 0: tag.setFirstAired(time.strftime('%Y-%m-%d', time.localtime(video['uploaded'] / 1000)))
		tag.setFilenameAndPath(plugin_url)
		tag.setPath(plugin_url)

		context_menu_items: list = [(addon.getLocalizedString(30010), f"RunAddon({addon.getAddonInfo('id')}, {video['uploaderUrl']})")]
		if watch_history_enabled:
			if video_id in history:
				context_menu_items.append((addon.getLocalizedString(30011), f"RunPlugin({addon_url}/mark_as_unwatched?id={video_id})"))
			else:
				context_menu_items.append((addon.getLocalizedString(30012), f"RunPlugin({addon_url}/mark_as_watched?id={video_id})"))

		if blacklist_channels_enabled:
			if channel_id in blacklist_channels_list:
				context_menu_items.append((addon.getLocalizedString(30023), f"RunPlugin({addon_url}/blacklist_remove?id={channel_id})"))
			else:
				context_menu_items.append((addon.getLocalizedString(30022), f"RunPlugin({addon_url}/blacklist_add?id={channel_id}&name={quote(video['uploaderName'])})"))

		listitem.addContextMenuItems(context_menu_items, replaceItems=True)

		xbmcplugin.addDirectoryItem(addon_handle, plugin_url, listitem, False)

	if len(nextpage) > 0:
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=f"{addon_url}/{nextpage}", listitem=xbmcgui.ListItem(addon.getLocalizedString(30017)), isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def feed() -> None:
	list_videos(authenticated_request('/feed?authToken=', True), addon.getSettingBool('watch_history_hide_watched_feed'))

def updatefeed() -> None:
	instance: str = addon.getSettingString('instance')

	channels: list = authenticated_request('/subscriptions')
	channelcount: int = len(channels)

	progressbar = xbmcgui.DialogProgress()
	progressbar.create(addon.getLocalizedString(30021))

	for i in range(channelcount):
		channel = channels[i]
		progressbar.update(int((i + 1) / channelcount * 100), f"{i + 1}/{channelcount} | {channel['name']}")
		authenticated_request(channel['url'])

	feed()

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
	list_channels(authenticated_request('/subscriptions'))

def list_playlists(playlists: list, nextpage: str='') -> None:
	for playlist in playlists:
		info: str = ''
		if 'shortDescription' in playlist and playlist['shortDescription'] is not None: info += playlist['shortDescription'] + "\n\n"
		elif 'description' in playlist and playlist['description'] is not None: info += playlist['description'] + "\n\n"
		if 'videos' in playlist and playlist['videos'] is not None: info += f"{addon.getLocalizedString(30018)}: {playlist['videos']}"

		if 'id' not in playlist:
			playlist['id'] = get_component(playlist['url'])['params']['list']

		listitem = xbmcgui.ListItem(playlist['name'])
		listitem.setArt(dict(
			thumb = playlist['thumbnail'],
			fanart = playlist['thumbnail'].replace('hqdefault.jpg', 'maxresdefault.jpg')
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
	list_playlists(authenticated_request('/user/playlists'))

def playlist(playlist_id: str, hide_watched=None) -> None:
	instance: str = addon.getSettingString('instance')

	playlist_info = get(f'{instance}/playlists/{playlist_id}').json()
	hide_watched: bool = hide_watched if hide_watched is not None else addon.getSettingBool('watch_history_hide_watched_playlists')

	if playlist_info['videos'] > 0: list_videos(playlist_info['relatedStreams'], hide_watched)
	else: xbmcgui.Dialog().ok(addon.getLocalizedString(30014), addon.getLocalizedString(30015))

def watch_history() -> None:
	playlist(addon.getSettingString('watch_history_playlist'), False)

def blacklist_section() -> None:
	blacklist: dict = dict(sorted(blacklist_load().items(), key=lambda x: x[1]['name'].lower()))

	for channel_id in blacklist.keys():
		listitem = xbmcgui.ListItem(blacklist[channel_id]['name'])

		tag = listitem.getVideoInfoTag()
		tag.setTitle(blacklist[channel_id]['name'])

		xbmcplugin.addDirectoryItem(addon_handle, f"{addon_url}/blacklist_remove?id={channel_id}&prompt=true", listitem, False)

	xbmcplugin.endOfDirectory(addon_handle)

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
		'updatefeed': {},
		'settings': {},
		'subscriptions': {},
		'playlists': {},
		'blacklist_section': {},
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
		'blacklist_add': {
			'channel_id': component['params']['id'] if 'id' in component['params'] else '',
			'channel_name': unquote(component['params']['name']) if 'name' in component['params'] else ''
		},
		'blacklist_remove': {
			'channel_id': component['params']['id'] if 'id' in component['params'] else '',
			'prompt': True if 'prompt' in component['params'] and component['params']['prompt'] == 'true' else False
		},
		'watch': {
			'video_id': re.sub(r'.*\/', '', component['path'])
		},
		'channel': {
			'channel_id': re.sub(r'.*\/', '', component['path']),
			'nextpage': component['params']['nextpage'] if 'nextpage' in component['params'] else ''
		},
	}

	route: str = re.sub(r'\/.*', '', component['path'][1:])
	if route == '': route = 'home'

	if route in routes:
		globals()[route](**routes[route])
