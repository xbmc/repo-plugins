from xbmcswift2 import Plugin
from resources.lib import abcradionational

plugin = Plugin()


@plugin.route('/')
def main_menu():
    url = "plugin://plugin.video.youtube/?action=play_video&videoid="
    video_data = abcradionational.get_videos()
    items = []

    for x in video_data:
        items.append({
            'label': x['title'],
            'thumbnail': x['thumbnail'],
            'path': url + x['youtube_id'],
            'info': x['description'],
            'is_playable': True,
        })

    return items


if __name__ == '__main__':
    plugin.run()
