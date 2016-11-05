from xbmcswift2 import Plugin, xbmcgui
from resources.lib import buzzfeedscraper

PLUGIN_URL = 'plugin://plugin.video.youtube/?action=play_video&videoid'

plugin = Plugin()


@plugin.route('/')
def main_menu():

    items = [
        {
            # Buzz Feed Video
            'label': plugin.get_string(30000),
            'path': plugin.url_for('get_content', url='https://www.youtube.com/user/BuzzFeedVideo/videos'),
            'thumbnail': 'https://yt3.ggpht.com/-iJJcDIkIjL0/AAAAAAAAAAI/AAAAAAAAAAA/Rf6VBJ2D-MA/s900-c-k-no/photo.jpg',
        },
        {
            # Buzz Feed Food
            'label': plugin.get_string(30001),
            'path': plugin.url_for('get_content', url='https://www.youtube.com/user/BuzzFeedFood/videos'),
            'thumbnail': 'https://pbs.twimg.com/profile_images/519943742258552832/wmQhQR3V.png',
        },
        {
            # Buzz Feed Yellow
            'label': plugin.get_string(30002),
            'path': plugin.url_for('get_content', url='https://www.youtube.com/user/BuzzFeedYellow/videos'),
            'thumbnail': 'https://yt3.ggpht.com/-qx3h-z3lc9w/AAAAAAAAAAI/AAAAAAAAAAA/QKFUBQtVG6A/s900-c-k-no/photo.jpg',
        },
        {
            # Buzz Feed Violet
            'label': plugin.get_string(30003),
            'path': plugin.url_for('get_content', url='https://www.youtube.com/user/buzzfeedviolet/videos'),
            'thumbnail': 'https://yt3.ggpht.com/--cdWOKrFOOE/AAAAAAAAAAI/AAAAAAAAAAA/wzHpOOWJAb4/s900-c-k-no/photo.jpg',
        },
        {
            # Buzz Feed Blue
            'label': plugin.get_string(30004),
            'path': plugin.url_for('get_content', url='https://www.youtube.com/user/buzzfeedblue/videos'),
            'thumbnail': 'https://yt3.ggpht.com/-GpCZ25vJ6CU/AAAAAAAAAAI/AAAAAAAAAAA/6qGF_ZTSSf0/s900-c-k-no/photo.jpg',
        }
    ]
    
    return items


@plugin.route('/content/<url>')
def get_content(url):
    
    content = buzzfeedscraper.get_latest(url)
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
