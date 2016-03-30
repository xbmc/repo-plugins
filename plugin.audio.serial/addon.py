from xbmcswift2 import Plugin, xbmcgui
from resources.lib import serial

plugin = Plugin()


@plugin.route('/')
def main_menu():
    
    items = [
        {
            # Season 1
            'label': plugin.get_string(30000),
            'path': plugin.url_for('play_season_one'),
            'thumbnail': 'http://si.wsj.net/public/resources/images/AR-AH827_SERIAL_P_20141113163544.jpg',
        },
        {
            # Season 2
            'label': plugin.get_string(30001),
            'path': plugin.url_for('play_season_two'),
            'thumbnail': 'http://pixel.nymag.com/imgs/daily/intelligencer/2016/01/07/07-bowe-bergdahl.w529.h352.jpg',
        }
    ]

    return items


@plugin.route('/play_season_one/')
def play_season_one():
    
    url = 'https://serialpodcast.org/season-one'
    content = serial.get_podcast_s1(url)

    item = []
    for i in content:
        item.append({
            'label': i['label'],
            'path': i['path'],
            'is_playable': True,
        })

    return item


@plugin.route('/play_season_two/')
def play_season_two():
    
    url = 'http://serialpodcast.org/season-two'
    content = serial.get_podcast_s2(url)
    
    item = []
    for i in content:
        item.append({
            'label': i['label'],
            'path': i['path'],
            'is_playable': True,
        })

    return item


if __name__ == '__main__':
    plugin.run()
