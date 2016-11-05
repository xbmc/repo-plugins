from xbmcswift2 import Plugin, xbmcgui
from resources.lib import c31scraper

PLUGIN_URL = 'plugin://plugin.video.youtube/play/?video_id'
MAIN_URL = 'https://www.youtube.com/user/channel31melbourne/featured'
LATEST_URL = 'https://www.youtube.com/user/channel31melbourne/videos'

plugin = Plugin()


@plugin.route('/')
def main_menu():

    item = [
        {
            # live stream
            'label': plugin.get_string(30000),
            'path': plugin.url_for('live_stream'),
        },
        {
            # all shows
            'label': plugin.get_string(30001),
            'path': plugin.url_for('get_shows'),
        },
        {
            # latest 
            'label': plugin.get_string(30002),
            'path': plugin.url_for('play_alt_show', url=LATEST_URL),
        },
        {
            # popular 
            'label': plugin.get_string(30003),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword='Popular uploads'),
        },
        {
            # c31 production vlog
            'label': plugin.get_string(30004),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword='C31 Production Team Video Diary'),
        },
        { 
            # Melbourne best in five
            'label': plugin.get_string(30005),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword="""Melbourne's Best Five....In Five Minutes"""),
        },
        {
            # c31 how to
            'label': plugin.get_string(30006),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword='C31 How To... Series'),
        },
        {
            # about tonight
            'label': plugin.get_string(30007),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword='About Tonight (2015)'),
        },
        {
            # move it or loose it
            'label': plugin.get_string(30008),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword='Move it or Lose it Complete Season 1'),
        },
        {
            # how to be a rockstar
            'label': plugin.get_string(30009),
            'path': plugin.url_for('play_show', url=MAIN_URL, keyword='How To Be A Rockstar With Tessa Waters'),
        }
    ]

    return item


@plugin.route('/live_stream/')
def live_stream():

    item = []
    
    item.append(
        plugin.play_video({
            'label': 'C31 Live',
            'path': 'http://c31.mediafoundry.com.au/sites/default/files/manifest/manifest_live_27.m3u8',
        })
    )

    return item


@plugin.route('/get_shows/')
def get_shows():
    KEYWORD= 'Uploads'
    item = [
        {
            'label': '4WD TV',
            'path': plugin.url_for('play_show', url='https://www.youtube.com/user/4wdTVtube', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg//4wd-440x326.jpg',
        },
        {
            'label': """Vasili's Garden to Kitchen""",
            'path': plugin.url_for('play_show', url='https://www.youtube.com/channel/UCUNfGu0l8O6FvCsuvJFgHOA/featured', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg//vasili_hag_main_2.jpg',
        },
        {
            'label': 'On the List... Melbourne',
            'path': plugin.url_for('play_show', url='https://www.youtube.com/channel/UCbcvUNnJEsQLzciJr9RFvRg', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg/onthelist_largenew.jpg',
        },
        {
            'label': 'New Game Plus',
            'path': plugin.url_for('play_show', url='https://www.youtube.com/user/NewGamePlusTV', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg//newgameplus_main.jpg',
        },
        {
            'label': 'Mr Sink Show',
            'path': plugin.url_for('play_show', url='https://www.youtube.com/channel/UCpCZWhMIPrMpAL9x1oG264w', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg//mrsink_largenew.jpg',
        },
        {
            'label': 'Talking Fishing',
            'path': plugin.url_for('play_alt_show', url='https://www.youtube.com/channel/UCKA0WVP5cIu0z5nLwH7d4BA'),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg/talkingfishing_largenew.jpg',
        },
        {
            'label': 'Your 4x4',
            'path': plugin.url_for('play_show', url='https://www.youtube.com/user/Your4x4', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg//your-4x4.jpg',
        },
        {
            'label': 'The Top of Down Under',
            'path': plugin.url_for('play_alt_show', url='https://www.youtube.com/user/DiscoverOzProduction'),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg//tothetopofdownunder-main.jpg',
        },
        {
            'label': 'In Pit Lane',
            'path': plugin.url_for('play_show', url='https://www.youtube.com/user/inpitlane', keyword=KEYWORD),
            'thumbnail': 'http://www.c31.org.au/library/program/preview_lg/in-pit-lane.jpg',
        }
    ]

    return item


@plugin.route('/get_shows/<url>/<keyword>')
def play_show(url, keyword):

    content = c31scraper.get_content(url, keyword)
    
    item = []
    for i in content:
        item.append({
            'label': i['label'],
            'path': PLUGIN_URL + i['path'],
            'thumbnail': i['thumbnail'],
            'is_playable': True,
        })

    return item


@plugin.route('/play_alt_shows/<url>')
def play_alt_show(url):
    
    content = c31scraper.get_alt_content(url)
    
    item = []
    for i in content:
        item.append({
            'label': i['label'],
            'path': PLUGIN_URL + i['path'],
            'thumbnail': i['thumbnail'],
            'is_playable': True,
        })

    return item


if __name__ == '__main__':
    plugin.run()
