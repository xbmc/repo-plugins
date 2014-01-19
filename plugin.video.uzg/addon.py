'''
    Uitzendinggemist(NPO)
    ~~~~~

    An XBMC addon for watching uzg

    :copyright: (c) 2012 by Jonathan Beluch (Documentary.net xbmc addon)    
    :license: GPLv3, see LICENSE.txt for more details.
    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

    uzg = Made/(changed Jonathans code) by Bas Magre (Opvolger)
    
'''
from xbmcswift2 import Plugin, SortMethod
from resources.lib.uzg import  get_overzicht, get_items_uitzending

PLUGIN_NAME = 'uzg'
PLUGIN_ID = 'plugin.video.uzg'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)

@plugin.route('/')
def index():
    ##main, alle shows
    items = [{
        'path': plugin.url_for('show_afleveringen', nebo_id=item['nebo_id']),
        'label': item['title'],
        'thumbnail': item['thumbnail'],
    } for item in get_overzicht()]    
    return items

@plugin.route('/afleveringen/<nebo_id>/')
def show_afleveringen(nebo_id):
    ##alleen afleveringen weergeven
    return show_items(get_items_uitzending(nebo_id))

def show_items(opgehaaldeitemsclass):
    '''Lists playable videos for a given category url.'''
    items = [{
        'path': item['video_url'],
        'label': item['title'],
        'thumbnail': item['thumbnail'],
        'is_playable': True,
        'info': {
                'date': item['date']
        },
    } for item in opgehaaldeitemsclass]
    return plugin.finish(items,sort_methods=[SortMethod.DATE,SortMethod.LABEL])

if __name__ == '__main__':
    plugin.run()
