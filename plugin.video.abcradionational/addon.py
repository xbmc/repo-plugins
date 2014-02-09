from xbmcswift2 import Plugin, xbmcgui
from resources.lib import abcradionational

plugin = Plugin()

@plugin.route('/')
def main_menu():
    url = "plugin://plugin.video.youtube/?action=play_video&videoid="
    video_data = abcradionational.get_podcasts()

    items = [{
        'label': x['title'],
        'thumbnail': x['thumb'],
        'path': url + x['url'],
        'info': x['description'],
        'is_playable': True,
    } for x in video_data]

    return items


if __name__ == '__main__':
    plugin.run()