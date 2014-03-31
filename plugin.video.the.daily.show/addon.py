import json
import os
from datetime import datetime
import re
import sys
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup as BS3
from requests import get
from xbmc import translatePath as tp
from xbmc import log
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon('plugin.video.the.daily.show')
pluginhandle = int(sys.argv[1])
image_fanart = tp(os.path.join(addon.getAddonInfo('path'), 'fanart.jpg'))
image_fanart_search = tp(
    os.path.join(addon.getAddonInfo('path'),
                 'fanart-search.jpg'))
xbmcplugin.setPluginFanart(pluginhandle, image_fanart, color2='0xFFFF3300')
TVShowTitle = 'The Daily Show'

if xbmcplugin.getSetting(pluginhandle, "sort") == '0':
    SORTORDER = 'date'
elif xbmcplugin.getSetting(pluginhandle, "sort") == '1':
    SORTORDER = 'views'
elif xbmcplugin.getSetting(pluginhandle, "sort") == '2':
    SORTORDER = 'rating'


class Guest(object):

    def __init__(self, data):
        self.soup = data

    def day(self):
        raw_text = self.soup('a', {'class': 'full-episode-url'})[0].getText()

        raw_text = raw_text.replace('Full Episode Available', '')
        m = re.search(r'(.*) - .*', raw_text)

        return m.group(1)

    def name(self):
        return self.soup('span', {'class': 'title'})[0].getText().replace('Exclusive - ', '')

    def url(self):
        return self.soup('a', {'class': 'imageHolder'})[0]['href']


class Episode:

    def __init__(self, rtmp, bitrate, width, height):
        self.rtmp = rtmp
        self.bitrate = bitrate
        self.width = width
        self.height = height

    @staticmethod
    def fromUrlData(data):
        # get attributes
        m = re.search(
            """width="([0-9]+).*height="([0-9]+).*bitrate="([0-9]+).*<src>(rtmpe[^<]+)</src>""",
            data,
            re.S)
        if m:
            (width, height, bitrate, rtmp) = m.groups()
            return Episode(rtmp, int(bitrate), int(width), int(height))

        # this should not happen
        raise Exception

    def __repr__(self):
        return "rtmp: %s, bitrate: %i, width: %i, height: %i" % (self.rtmp,
                                                                 self.bitrate, self.width, self.height)


def get_episodes(data):
    # split urldata into renditions
    renditions = re.findall("(<rendition.*?</rendition>)", data, re.S)
    # return a list of episodes
    return [Episode.fromUrlData(r) for r in renditions]


def get_settings_bitrate():
    # map plugin settings to actual bitrates
    setting2bitrate = {'1': 400, '2': 750, '3': 1200, '4': 1700, '5': 2200,
                       '6': 3500}
    setting = xbmcplugin.getSetting(pluginhandle, "bitrate")
    lbitrate = setting2bitrate.get(setting, 0)
    return lbitrate


# Common
def get_url(url):
    try:
        log('The Daily Show --> get_url :: url = ' + url)
        txdata = None
        txheaders = {
            'Referer': 'http://thedailyshow.cc.com/',
            'X-Forwarded-For': '12.13.14.15',
            'User-Agent':
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',
        }
        req = urllib2.Request(url, txdata, txheaders)
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()
    except urllib2.URLError as e:
        log('Error code: ', e.code)
        return False
    else:
        return link


def make_in_app_url(**kwargs):
    data = json.dumps(kwargs)
    url = "{sysarg}?{data}".format(sysarg=sys.argv[0], data=data)
    return url


def add_directory_entry(name, identifier):
    """Adds a directory entry to the xbmc ListItem"""
    url = make_in_app_url(mode=identifier)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('fanart_image', image_fanart)
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url,
                                listitem=liz, isFolder=True)

# Root listing


def root(**ignored):
    msg = addon.getLocalizedString(30030)
    add_directory_entry(msg, 'full')
    #msg = addon.getLocalizedString(30032)
    #add_directory_entry(msg, 'search')
    #msg = addon.getLocalizedString(30033)
    #add_directory_entry(msg, 'browse')
    xbmcplugin.endOfDirectory(pluginhandle)



def full_episodes(**ignored):
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)
    url = 'http://thedailyshow.cc.com/full-episodes/'
    # Due to unstructured daily show site, there is no canonical JSON url
    # so we find the full episode json url presented on the latest full episode
    jsonurl = re.compile(r'http[^"]+/f1010\\/[^"]+').findall(get(url).content)[0].replace("\\", "")

    jsonresponse = json.loads(get(jsonurl).content)
    episodes = jsonresponse.get('result').get('episodes')
    for episode in episodes:
        thumbnail = None
        if len(episode.get('images', ())) >= 1:
            thumbnail = episode.get('images')[0].get('url')
        airdate = episode.get('airDate', '0')
        airdate = datetime.fromtimestamp(int(airdate)).strftime('%Y-%m-%d')
        liz = xbmcgui.ListItem(
            episode.get('title'),
            iconImage="DefaultFolder.png",
            thumbnailImage=thumbnail)
        liz.setInfo(
            type="Video", infoLabels={"Title": episode.get('title'),
                                      "Plot":
                                      episode.get('description'),
                                      "Season": episode.get('season', {}).get('seasonNumber'),
                                      "Episode": episode.get('season', {}).get('episodeNumber'),
                                      "premiered": airdate,
                                      "TVShowTitle": TVShowTitle})
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty('fanart_image', image_fanart)
        url = make_in_app_url(
            mode="play_full_episode",
            episode_id=episode.get('id'),
            additional_data=episode,
        )
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=liz)

    xbmcplugin.endOfDirectory(pluginhandle)




def extract_search_results_from_response(response):
    """Creates an xbmc DirectoryItem with ListItems of videos extracted from
    the http results.

    Returns False if there are no video urls found in the request.
    Otherwise, returns True."""

    soup = BS3(response.text)
    results = soup.find('div', {'class': 'search-results'})

    if results is None:
        return False

    for entry in results.findAll('div', {'class': 'entry'}):
        video_page_url = entry.find('meta', dict(itemprop="url"))['content']
        name = entry.find('meta', dict(itemprop="name"))['content']
        description = entry.find(
            'meta',
            dict(itemprop="description"))['content']
        thumbnail = entry.find(
            'meta',
            dict(itemprop="thumbnailUrl"))['content']
        if thumbnail:
            # strip unnecessary ?width= parameters that make the image too
            # small
            thumbnail = re.search(r"(.*)\?.*", thumbnail).groups()[0]
        duration = None
        duration_match = re.search(
            'T(\d+)M',
            entry.find('meta',
                       dict(itemprop="duration"))['content'])
        if duration_match:
            duration = duration_match.groups()[0]
        upload_date = entry.find(
            'meta',
            dict(itemprop="uploadDate"))['content']

        url = "{sysarg}?mode={mode}&name={name}&url={video_page_url}".format(
            sysarg=sys.argv[0],
            name=urllib.quote_plus(name),
            video_page_url=urllib.quote_plus(video_page_url),
            mode="play")
        date_and_name = "%s - %s" % (upload_date.replace('-','/'), name)
        liz = xbmcgui.ListItem(date_and_name, thumbnailImage=thumbnail)
        liz.setInfo(type="Video", infoLabels={"Title": name,
                                              "plot": description,
                                              "premiered": upload_date,
                                              "aired": upload_date,
                                              "duration": duration,
                                              "TVShowTitle": TVShowTitle
                                              })
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty('fanart_image', image_fanart_search)
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=liz)

    return True


def get_user_input(title, default="", hidden=False):
    """Display a virtual keyboard to the user"""

    keyboard = xbmc.Keyboard(default, title)
    keyboard.setHiddenInput(hidden)
    keyboard.doModal()

    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return None


def search(**ignored):
    msg = addon.getLocalizedString(30032)
    query = get_user_input(msg)
    if not query:
        return

    response = get(
        "http://www.thedailyshow.com/videos",
        params=dict(term=query))

    if extract_search_results_from_response(response) is True:
        xbmcplugin.endOfDirectory(pluginhandle)
    else:
        mydialogue = xbmcgui.Dialog()
        msg = addon.getLocalizedString(30022)
        mydialogue.ok(heading=TVShowTitle,
                      line1=msg)


def browse(**ignored):
    """Browse videos by Date"""
    mydialogue = xbmcgui.Dialog()
    msg = addon.getLocalizedString(30020)
    datestring = mydialogue.numeric(type=1, heading=msg)

    if not datestring:
        return

    day, month, year = datestring.split("/")

    urlstring = "http://www.thedailyshow.com/feeds/search" + \
        "?startDate={year}-{month}-{day}&tags=&keywords=&sortOrder=desc&sortBy=date&page=1".format(
            day=day,
            month=month,
            year=year)

    response = get(urlstring)

    if extract_search_results_from_response(response) is True:
        xbmcplugin.endOfDirectory(pluginhandle)
    else:
        mydialogue = xbmcgui.Dialog()
        msg = addon.getLocalizedString(30021)
        mydialogue.ok(heading=TVShowTitle,
                      line1=msg)


def play_full_episode(episode_id, additional_data, **ignored):
    content_id = 'mgid:arc:episode:thedailyshow.com:%s' % episode_id
    url = 'http://thedailyshow.cc.com/feeds/mrss?uri=' + content_id
    data = get_url(url)
    uris = re.compile('<guid isPermaLink="false">(.+?)</guid>').findall(data)
    stacked_url = 'stack://'
    for uri in uris:
        rtmp = grab_rtmp(uri)
        stacked_url += rtmp.replace(',', ',,') + ' , '
    stacked_url = stacked_url[:-3]

    log('stacked_url --> %s' % stacked_url)

    item = xbmcgui.ListItem("ignored", path=stacked_url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, item)

# Grab rtmp


def grab_rtmp(uri):
    url = 'http://thedailyshow.cc.com/feeds/mediagen/?uri=' + uri
    mp4_url = "http://mtvnmobile.vo.llnwd.net/kip0/_pxn=0+_pxK=18639+_pxE=/44620/mtvnorigin"

    data = get_url(url)
    episodes = get_episodes(data)

    # sort episodes by bitrate ascending
    episodes.sort(key=lambda x: x.bitrate)

    # chose maximum bitrate by default
    ep = episodes[-1]

    # check user settings
    lbitrate = get_settings_bitrate()
    if lbitrate:
        # use the largest bitrate smaller-or-equal to the user-chosen value
        ep = filter(lambda x: x.bitrate <= lbitrate, episodes)[-1]

    furl = mp4_url + ep.rtmp.split('viacomccstrm')[2]
    log('furl --> %s' % furl)
    return furl


mode_handlers = {
    "browse": browse,
    "full": full_episodes,
    "play_full_episode": play_full_episode,
    "search": search,
    "root": root,
}
def main(data):
    decoded = urllib2.unquote(data or "{}")
    if len(decoded) >= 1 and decoded[0] == '?':
        decoded = decoded[1:]
    parsed_data = json.loads(decoded)
    mode = parsed_data.get('mode') or 'root'
    mode_handlers[mode](**parsed_data)

main(sys.argv[2])
