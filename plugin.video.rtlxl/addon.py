'''
    RTLxl
    ~~~~~

    An XBMC addon for watching RTLxl

    :copyright: (c) 2012 by Jonathan Beluch (Documentary.net xbmc addon)    
    :license: GPLv3, see LICENSE.txt for more details.
    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

    RTLxl = Made/(changed Jonathans code) by Bas Magre (Opvolger)
    
'''
from xbmcswift2 import Plugin, SortMethod
from resources.lib.rtlxl import  get_categories, get_overzicht, get_items_uitzending, get_items_alles

PLUGIN_NAME = 'RTLxl'
PLUGIN_ID = 'plugin.video.rtlxl'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)

@plugin.route('/')
def index():
    ##main, alle shows
    items = [{
        'path': plugin.url_for('show_keuze', url=item['url']),
        'label': item['title'],
        'thumbnail': item['thumbnail'],
    } for item in get_overzicht()]    
    return items

@plugin.route('/keuze/<url>/')
def show_keuze(url):
    ##keuze tussel alles of alleen afleveringen (wel fijn bij RTL Nieuws)
    items = [{
        'path': plugin.url_for('show_'+item['keuze'], url=item['url']),
        'label': item['title'],
        'selected': item['selected'],
    } for item in get_categories(url)]    
    return items

@plugin.route('/keuze/afleveringen/<url>/')
def show_afleveringen(url):
    ##alleen afleveringen weergeven
    return show_items(get_items_uitzending(url))

@plugin.route('/keuze/alles/<url>/')
def show_alles(url):
    ##alles weergeven
    return show_items(get_items_alles(url))

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
