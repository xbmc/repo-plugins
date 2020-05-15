import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import urllib
import json
import re
from HTMLParser import HTMLParser
from collections import OrderedDict

__all__ = ['PY2', 'py2_encode', 'py2_decode']

h = HTMLParser()


PY2 = sys.version_info[0] == 2


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def py2_encode(s, encoding='utf-8'):
    if PY2 and isinstance(s, unicode):
        s = s.encode(encoding)
    return s


_url = sys.argv[0]
_handle = int(sys.argv[1])

VIDEOS = OrderedDict([
    ('RT Live', {'description': 'Multi-language channel airs 24/7',
                 'includes': [{'name': 'RT',
                                       'type': 'Live',
                                       'thumb': 'https://cdn.rt.com/distribution/kodi/rt_global.jpg',
                                       'video': 'https://rt-news-gd.secure2.footprint.net/1103.m3u8',
                                       'description': 'RT provides an alternative perspective on major global events, and acquaints an international audience with the Russian viewpoint.'
                               },
                              {'name': 'RT America',
                                       'type': 'Live',
                                       'thumb': 'https://cdn.rt.com/distribution/kodi/rt_usa.png',
                                       'video': 'https://rt-usa-gd.secure2.footprint.net/1105.m3u8',
                                       'description': 'RT America broadcasts from its studios in Washington, DC. Tune in to watch news reports, features and talk shows with a totally different perspective from the mainstream American television.'
                               },
                              {'name': 'RT UK',
                               'type': 'Live',
                               'thumb': 'https://cdn.rt.com/distribution/kodi/rt_uk.jpg',
                               'video': 'https://rt-uk-gd.secure2.footprint.net/1106.m3u8',
                               'description': 'RT UK broadcasts from our London Studio, focusing on the issues that matter most to Britons. We bring a totally different perspective to mainstream British television - in line with RT\'s core mission to Question More.'
                               },
                              {'name': 'RTD',
                               'type': 'Live',
                               'thumb': 'https://cdn.rt.com/distribution/kodi/rt_rtd.jpg',
                               'video': 'https://rt-doc-gd.secure2.footprint.net/1101.m3u8',
                               'description': 'RTDoc brings you stories from Russia and all over the world. Stories that inspire and educate. That break hearts and lift spirits. Stories that explore the depths of the human soul and the expanses of nature. Stories that are real - and true.'
                               },
                              {'name': 'RT Noticias',
                               'type': 'Live',
                               'thumb': 'https://cdn.rt.com/distribution/kodi/rt_spain.jpg',
                               'video': 'https://rt-esp-gd.secure2.footprint.net/1102.m3u8',
                               'description': "RT en espa" + u"\u00F1" + "ol ofrece una alternativa real en el mundo de la informaci" + u"\u00F3" + "n. Las noticias de actualidad de las que no hablan los principales canales internacionales adquieren importancia mundial en RT en espa" + u"\u00F1" + "ol.",
                               },
                              {'name': 'RT France',
                               'type': 'Live',
                               'thumb': 'https://cdn.rt.com/distribution/kodi/rt_france.jpg',
                               'video': 'https://rt-france-gd.secure2.footprint.net/1107.m3u8',
                               'description': 'RT France est une cha' + u'\u00EE' + 'ne de t' + u'\u00E9' + 'l' + u'\u00E9' + 'vision d\'information continue, qui diffuse dans le monde entier en langues anglaise, arabe, espagnole et fran' + u'\u00E7' + 'aise.',
                               },
                              {'name': 'RT Arabic',
                               'type': 'Live',
                               'thumb': 'https://cdn.rt.com/distribution/kodi/rt_arabic.jpg',
                               'video': 'https://rt-arab-gd.secure2.footprint.net/1104.m3u8',
                               'description': "RT Arabic is a 24-hour satellite television channel that broadcasts news in Arabic and is part of Autonomous Non-Profit Organization \"TV Novosti\". The network covers politics, economy, culture, and sports.",
                               }]
                 }),
    ('RT English', {'description': 'Shows in English',
                    'includes': []
                    }),
    ('RT French', {'description': 'Shows in French',
                   'includes': []
                   }),
    ('RT Spanish', {'description': 'Shows in Spanish',
                    'includes': []
                    })
])


urlEN = "https://www.rt.com/rtmobile/shows"
response = urllib.urlopen(urlEN)
shows = json.loads(response.read())
for show in shows[u'data']:
    VIDEOS['RT English']['includes'] += [{'name': show[u'title'].replace(u"\u2019", "'"),
                                          'type': 'Show',
                                          'thumb': show[u'imageUrl'],
                                          'description': show[u'text'].replace(u"\u2019", "'").replace(u"\u2018", "'"),
                                          'id': show[u'id'],
                                          'episodesUrl': urlEN + '/' + str(show[u'id']) + '/episodes',
                                          'episodes':[]
                                          }]

urlFR = "https://francais.rt.com/rtmobile/v3/shows"
response = urllib.urlopen(urlFR)
shows = json.loads(response.read())
for show in shows[u'data']:
    description = show[u'text'].replace(u"\u2019", "'")
    VIDEOS['RT French']['includes'] += [{'name': show[u'title'].replace(u"\u2019", "'").encode(encoding='UTF-8', errors='strict'),
                                         'type': 'Show',
                                         'thumb': show[u'imageUrl'],
                                         'description': h.unescape(description),
                                         'id': show[u'id'],
                                         'episodesUrl': urlFR + '/' + str(show[u'id']) + '/episodes',
                                         'episodes':[]
                                         }]

urlES = "https://actualidad.rt.com/mobiledata/v3/shows"
response = urllib.urlopen(urlES)
shows = json.loads(response.read())
for show in shows[u'data']:
    description = show[u'text'].replace(u"\u2019", "'")
    VIDEOS['RT Spanish']['includes'] += [{'name': show[u'title'].replace(u"\u2019", "'").encode(encoding='UTF-8', errors='strict'),
                                          'type': 'Show',
                                          'thumb': show[u'imageUrl'],
                                          'description': h.unescape(description),
                                          'id': show[u'id'],
                                          'episodesUrl': urlES + '/' + str(show[u'id']) + '/episodes',
                                          'episodes':[]
                                          }]


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_categories():
    return VIDEOS.keys()


def get_videos(category):
    return VIDEOS[category]['includes']


def list_categories():
    xbmcplugin.setPluginCategory(_handle, 'Main')
    xbmcplugin.setContent(_handle, 'videos')
    categories = get_categories()

    for category in categories:
        list_item = xbmcgui.ListItem(label=category)
        include = get_videos(category)
        list_item.setArt({'thumb': include[0]['thumb'],
                          'icon': include[0]['thumb'],
                          'fanart': include[0]['thumb']})

        list_item.setInfo('video', {'title': category,
                                    'plot': VIDEOS[category]['description'],
                                    'mediatype': 'video'})

        url = get_url(action='listing', category=category)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_TRACKNUM)

    xbmcplugin.endOfDirectory(_handle)


def list_videos(category):

    xbmcplugin.setPluginCategory(_handle, category)
    xbmcplugin.setContent(_handle, 'videos')

    if category in VIDEOS:
        videos = get_videos(category)
        for video in videos:

            if video['type'] == 'Live':
                list_item = xbmcgui.ListItem(label=video['name'])
                list_item.setInfo('video', {'title': video['name'],
                                            'plot': video['description'],
                                            'mediatype': 'video'})
                list_item.setArt({'thumb': video['thumb'],
                                  'icon': video['thumb'],
                                  'fanart': video['thumb']})
                list_item.setProperty('IsPlayable', 'true')
                url = get_url(action='play', video=video['video'])
                is_folder = False
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

            elif video['type'] == 'Show':
                list_item = xbmcgui.ListItem(label=video['name'])
                list_item.setArt({'thumb': video['thumb'],
                                  'icon': video['thumb'],
                                  'fanart': video['thumb']})
                list_item.setInfo('video', {'title': video['name'],
                                            'plot': video['description'][0: 250] + '...' if len(video['description']) > 250 else video['description'],
                                            'mediatype': 'video'})
                url = get_url(action='listing', category=video['name'])
                is_folder = True
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    else:
        for sub in VIDEOS:
            for show in VIDEOS[sub]['includes']:
                if show['name'] == category:
                    url = show['episodesUrl']
        response = urllib.urlopen(url)
        episodes = json.loads(response.read())
        for episode in episodes[u'data']:
            plot = h.unescape(cleanhtml(episode[u'summary'].replace(u"\u2019", "'"))[0: 250] + '...' if len(cleanhtml(
                episode[u'summary'].replace(u"\u2019", "'"))) > 250 else cleanhtml(episode[u'summary'].replace(u"\u2019", "'")))
            test_list = xbmcgui.ListItem(
                label=episode[u'title'].replace(u"\u2019", "'"))
            test_list.setInfo('video', {'title': h.unescape(episode[u'title'].replace(u"\u2019", "'").encode(encoding='UTF-8', errors='strict')),
                                        'plot': plot,
                                        'mediatype': 'video'})
            pic = episode[u'image']
            test_list.setArt({'thumb': pic,
                              'icon': pic,
                              'fanart': pic
                              })
            test_list.setProperty('IsPlayable', 'true')
            if u'youtube_id' in episode[u'video']:
                video_link = 'plugin://plugin.video.youtube/play/?video_id=' + \
                    episode[u'video'][u'youtube_id']
            else:
                video_link = episode[u'video'][u'url']
            xbmcplugin.addDirectoryItem(_handle, video_link, test_list, False)

    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'listing':
            list_videos(params['category'])
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
