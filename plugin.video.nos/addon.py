#from resources.lib import routing
import routing
import xbmcplugin
from xbmcgui import ListItem
from resources.lib import nos

plugin = routing.Plugin()

@plugin.route('/')
def index():
	data = nos.index()
	for entry in data:
		endpoint = entry['path']['endpoint']
		pluginURL = plugin.url_for(globals()[endpoint], entry['path']['category_url'])
		xbmcplugin.addDirectoryItem(plugin.handle, pluginURL, ListItem(entry['label']), True)
		
	xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/show_category/<path:category_url>')
def show_category(category_url):
	data = nos.show_category(category_url)
	for entry in data:
		endpoint = entry['path']['endpoint']
		pluginURL = plugin.url_for(globals()[endpoint], entry['path']['video_url'])
		
		item = ListItem(entry['label'])
		item.setLabel(entry['label'])
		item.setInfo('video', {'title': entry['label'], 'genre': entry['label'], 'mediatype': 'video'})
		item.setProperty('IsPlayable', str(entry['is_playable']))
		xbmcplugin.addDirectoryItem(plugin.handle, pluginURL, item, False)
	
	xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/show_video/<path:video_url>')
def show_video(video_url):
	xbmcplugin.setContent(plugin.handle, 'videos')
	print('NOS - Showing: %s' % video_url)
	item = ListItem(path = video_url)
	xbmcplugin.setResolvedUrl(plugin.handle, True, item)
 
if __name__ == '__main__':
	plugin.run()
