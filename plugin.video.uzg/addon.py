'''
    Uitzendinggemist(NPO)
    ~~~~~~~

    An XBMC addon for watching uzg 
    :license: GPLv3, see LICENSE.txt for more details.
    
    based on: https://github.com/jbeluch/plugin.video.documentary.net
    Uitzendinggemist(NPO) / uzg = Made by Bas Magre (Opvolger)
    
'''
from xbmcswift2 import Plugin, SortMethod
import resources.lib.uzg
import time
import xbmcplugin

PLUGIN_NAME = 'uzg'
PLUGIN_ID = 'plugin.video.uzg'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)

uzg = resources.lib.uzg.Uzg()
subtitle = plugin.get_setting( "subtitle", bool )

@plugin.route('/')
def index():
    ##main, alle shows
    items = [{
        'path': plugin.url_for('show_afleveringen', nebo_id=item['nebo_id']),
        'label': item['label'],
        'thumbnail': item['thumbnail'],
    } for item in uzg.get_overzicht()]    
    return items

@plugin.route('/afleveringen/<nebo_id>/')
def show_afleveringen(nebo_id):
    return show_items(uzg.get_items(nebo_id))

@plugin.route('/lectures/<whatson_id>/')
def play_lecture(whatson_id):
	plugin.set_resolved_url(uzg.get_play_url(whatson_id))	
	if (subtitle):
		add_subtitlesstream(uzg.get_ondertitel(whatson_id))

def add_subtitlesstream(subtitles):
	player = xbmc.Player()
	for _ in xrange(30):
		if player.isPlaying():
			break
		time.sleep(1)
	else:
		raise Exception('No video playing. Aborted after 30 seconds.')
	player.setSubtitles(subtitles)
	player.setSubtitleStream(1)

	
def show_items(opgehaaldeitemsclass):
    '''Lists playable videos for a given category url.'''
    items = [{
        'path': plugin.url_for('play_lecture', whatson_id=item['whatson_id']),
        ##'whatson_id': item['whatson_id'],
        'label': item['label'],
        'thumbnail': item['thumbnail'],
        'is_playable': True,
        'info': {
                'date': item['date']
        },
    } for item in opgehaaldeitemsclass]
    return plugin.finish(items,sort_methods=[SortMethod.DATE,SortMethod.LABEL])

if __name__ == '__main__':
    plugin.run()
