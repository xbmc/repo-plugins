#import xbmc
#from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
#from xbmc import Plugin, xbmcgui
#from kodi_six import Plugin
from xbmcswift2 import Plugin, xbmcgui
from resources.lib import criminalpodcast
#from xmbc import xmbcplugin

URL = "http://feeds.thisiscriminal.com/CriminalShow"

plugin = Plugin()

@plugin.route('/')
def main_menu():
    """
    main menu 
    """
    items = [
        {
            'label': plugin.get_string(30001), 
            'path': plugin.url_for('all_episodes1'),
            'thumbnail': "https://f.prxu.org/criminal/images/aaff5251-e6ab-44da-8886-092289630040/CRIMINAL_LOGOS_FINAL_wt_sq.png"},
        {
            'label': plugin.get_string(30000), 
            'path': plugin.url_for('all_episodes'),
            'thumbnail': "https://f.prxu.org/criminal/images/aaff5251-e6ab-44da-8886-092289630040/CRIMINAL_LOGOS_FINAL_wt_sq.png"},
        {
            'label': plugin.get_string(30002),
            'path': plugin.url_for('new_to_criminal'),
            'thumbnail': "https://f.prxu.org/criminal/images/aaff5251-e6ab-44da-8886-092289630040/CRIMINAL_LOGOS_FINAL_wt_sq.png"},
    ]
    return items

@plugin.route('/all_episodes/')
def all_episodes():
    """
    contains playable podcasts listed as just-in
    """
    soup = criminalpodcast.get_soup(URL)
    playable_podcast = criminalpodcast.get_playable_podcast(soup)
    items = criminalpodcast.compile_playable_podcast(playable_podcast)
    return items

@plugin.route('/all_episodes1/')
def all_episodes1():
    """
    contains playable podcasts listed as just-in
    """
    soup = criminalpodcast.get_soup(URL)
    playable_podcast1 = criminalpodcast.get_playable_podcast1(soup)
    items = criminalpodcast.compile_playable_podcast1(playable_podcast1)
    return items

@plugin.route('/new_to_criminal/')
def new_to_criminal():
    """
    contains playable podcasts listed as just-in
    """
    #soup = criminalpodcast.compile_new_to_criminal(URL)    
    compile_ntc = criminalpodcast.get_new_to_criminal
    items = criminalpodcast.compile_new_to_criminal(compile_ntc)
    return items

if __name__ == '__main__':
    plugin.run()
