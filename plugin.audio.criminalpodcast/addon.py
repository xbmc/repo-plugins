from xbmcswift2 import Plugin, xbmcgui
from resources.lib import criminalpodcast

plugin = Plugin()

URL = "http://feeds.thisiscriminal.com/CriminalShow"

@plugin.route('/')
def main_menu():
    """
    main menu 
    """
    items = [
        {
            'label': plugin.get_string(30001), 
            'path': plugin.url_for('all_episodes1'),
            'thumbnail': "/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/icon.png"},
        {
            'label': plugin.get_string(30000), 
            'path': plugin.url_for('all_episodes'),
            'thumbnail': "/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/icon.png"},
        {
            'label': plugin.get_string(30002),
            'path': plugin.url_for('new_to_criminal'),
            'thumbnail': "/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/cropped-favicon-2-180x180-inverted.png"},
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
