from xbmcswift2 import Plugin, xbmcgui
from resources.lib import thisweekscraper

PLUGIN_URL = 'plugin://plugin.video.youtube/?action=play_video&videoid'
SITE_URL = 'https://www.youtube.com/user/ThisWeekIn'

plugin = Plugin()


@plugin.route('/')
def main_menu():

    items = [
        {
            'label': plugin.get_string(30000),
            'path': plugin.url_for('get_latest'),
            'thumbnail': 'http://ec-cdn-assets.stitcher.com/feedimagesplain328/9728.jpg',
        },
        {
            'label': plugin.get_string(30001),
            'path': plugin.url_for('get_highlight'),
            'thumbnail': 'http://ec-cdn-assets.stitcher.com/feedimagesplain328/9728.jpg',
        },
        {
            'label': plugin.get_string(30002),
            'path': plugin.url_for('get_topten'),
            'thumbnail': 'http://ec-cdn-assets.stitcher.com/feedimagesplain328/9728.jpg',
        }
    ]
    
    return items


@plugin.route('/latest/')
def get_latest():
    
    keyword = 'Uploads' 
    content = thisweekscraper.get_latest(SITE_URL, keyword)
    items = []

    for i in content:
        items.append({
            'label': i['label'],
            'path': PLUGIN_URL + i['path'],
            'thumbnail': i['thumbnail'],
            'is_playable': True,
        })

    return items


@plugin.route('/highlight/')
def get_highlight():
    
    keyword = 'Highlight Clips' 
    content = thisweekscraper.get_latest(SITE_URL, keyword)
    items = []

    for i in content:
        items.append({
            'label': i['label'],
            'path': PLUGIN_URL + i['path'],
            'thumbnail': i['thumbnail'],
            'is_playable': True,
        })

    return items


@plugin.route('/topten/')
def get_topten():
    
    keyword = 'Top 10 TWiST videos' 
    content = thisweekscraper.get_latest(SITE_URL, keyword)
    items = []

    for i in content:
        items.append({
            'label': i['label'],
            'path': PLUGIN_URL + i['path'],
            'thumbnail': i['thumbnail'],
            'is_playable': True,
        })

    return items


if __name__ == '__main__':
    plugin.run()
