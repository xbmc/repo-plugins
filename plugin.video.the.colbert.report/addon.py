import os
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

addon = xbmcaddon.Addon('plugin.video.the.colbert.report')
pluginhandle = int(sys.argv[1])
image_fanart = tp(os.path.join(addon.getAddonInfo('path'), 'fanart.jpg'))
image_fanart_search = tp(
    os.path.join(addon.getAddonInfo('path'),
                 'fanart-search.jpg'))
xbmcplugin.setPluginFanart(pluginhandle, image_fanart, color2='0xFFFF3300')
TVShowTitle = 'The Colbert Report'

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
        log('The Colbert Report --> get_url :: url = ' + url)
        txdata = None
        txheaders = {
            'Referer': 'http://www.colbertnation.com/video/',
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


def add_directory_entry(name, identifier):
    """Adds a directory entry to the xbmc ListItem"""
    url = "{sysarg}?mode={mode}".format(sysarg=sys.argv[0], mode=identifier)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('fanart_image', image_fanart)
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url,
                                listitem=liz, isFolder=True)

# Root listing


def root():
    msg = addon.getLocalizedString(30030)
    add_directory_entry(msg, 'full')
#    msg = addon.getLocalizedString(30031)
#    add_directory_entry(msg, 'guests')
    msg = addon.getLocalizedString(30032)
    add_directory_entry(msg, 'search')
#    msg = addon.getLocalizedString(30033)
#    add_directory_entry(msg, 'browse')
    xbmcplugin.endOfDirectory(pluginhandle)


def full_episodes():
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)
    full = 'http://www.colbertnation.com/full-episodes/'
    allData = get_url(full)

    episodeURLs = re.compile(
        '"(http://www.colbertnation.com/full-episodes/....+?)"').findall(
        allData)
    episodeURLSet = set(episodeURLs)

    listings = []
    for episodeURL in episodeURLs:
        if episodeURL in episodeURLSet:
            episodeURLSet.remove(episodeURL)
            episodeData = get_url(episodeURL)

            title = re.compile(
                '<meta property="og:title" content="(.+?)"').search(
                episodeData)
            thumbnail = re.compile(
                '<meta property="og:image" content="(.+?)"').search(
                episodeData)
            description = re.compile(
                '<meta property="og:description" content="(.+?)"').search(
                episodeData)
            airDate = re.compile(
                '<meta itemprop="datePublished" content="(.+?)"').search(
                episodeData)
            epNumber = re.compile('/season_\d+/(\d+)').search(episodeData)
            link = re.compile(
                '<meta property="og:url" content="(.+?)"').search(
                episodeData)

            listing = []
            listing.append(title.group(1))
            listing.append(link.group(1))
            listing.append(thumbnail.group(1))
            listing.append(description.group(1))
            listing.append(airDate.group(1))
            listing.append(epNumber.group(1))
            listings.append(listing)

    #for name, link, thumbnail, plot, date, seasonepisode in listings:
    for name, link, thumbnail, plot, date, seasonepisode in listings:
        mode = "play"
        season = int(seasonepisode[:-3])
        episode = int(seasonepisode[-3:])
        u = sys.argv[
            0] + "?url=" + urllib.quote_plus(
            link) + "&mode=" + str(
            mode) + "&name=" + urllib.quote_plus(
            name)
        u += "&season=" + urllib.quote_plus(str(season))
        u += "&episode=" + urllib.quote_plus(str(episode))
        u += "&premiered=" + urllib.quote_plus(date)
        u += "&plot=" + urllib.quote_plus(plot)
        u += "&thumbnail=" + urllib.quote_plus(thumbnail)
        liz = xbmcgui.ListItem(
            name,
            iconImage="DefaultFolder.png",
            thumbnailImage=thumbnail)
        liz.setInfo(
            type="Video", infoLabels={"Title": BS3(name, convertEntities=BS3.HTML_ENTITIES),
                                      "Plot":
                                      BS3(plot,
                                          convertEntities=BS3.HTML_ENTITIES),
                                      "Season": season,
                                      "Episode": episode,
                                      "premiered": date,
                                      "TVShowTitle": TVShowTitle})
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty('fanart_image', image_fanart)
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

    xbmcplugin.endOfDirectory(pluginhandle)


def guests():
    gurl = "http://www.colbertnation.com/feeds/search?keywords=&tags=interviews&sortOrder=desc&sortBy=date&page=1"
    data = get_url(gurl).replace('</pre>', '</div>')
    soup = BS3(data)

    guest_items = soup('div', {'class': 'entry'})
    mode = "play"
    for item in guest_items:
        g = Guest(item)

        liz = xbmcgui.ListItem(g.name(), iconImage='', thumbnailImage='')
        liz.setInfo(type="Video", infoLabels={"Title": g.name(),
                                              "TVShowTitle": 'The Colbert Report'})
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty('fanart_image', image_fanart)
        u = sys.argv[
            0] + "?url=" + g.url(
        ) + "&mode=" + str(
            mode) + "&name=" + g.name(
        )
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

    xbmcplugin.endOfDirectory(pluginhandle)


def extract_search_results_from_response(response):
    """Creates an xbmc DirectoryItem with ListItems of videos extracted from
    the http results.

    Returns False if there are no video urls found in the request.
    Otherwise, returns True."""

    soup = BS3(response.text)

    if soup is None:
        return False

    for entry in soup.findAll('div', {'class': 'video_result'}):
        video_page_url = entry.find('a', {'class':"clipTitle"}).get('href')
        name = entry.find('a', {'class':"clipTitle"}).string
        description = entry.find('p', {'class':"description"}).string
        thumbnail = entry.find('img').get('src')
        # strip unnecessary ?width= parameters that make the image too small
        if thumbnail:
            thumbnail = re.search(r"(.*)\?.*", thumbnail).groups()[0]
        duration = None
        #duration_match = re.search('T(\d+)M',entry.find('meta', dict(itemprop="duration"))['content'])
        duration_match = None
        if duration_match:
            duration = duration_match.groups()[0]

        try:
            upload_date = re.search('videos/[0-9]+/(.+20[01][0-9])/',
                    entry.find('a',
                        {'class':"clipTitle"}).get('href')).group(1)
        except:
            upload_date = ""

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


def search():
    msg = addon.getLocalizedString(30032)
    query = get_user_input(msg)
    if not query:
        return

    url = "http://www.colbertnation.com/video/" + "+".join(query.split(" "))
    log("Searching %s" % url)
    response = get(url)
        #params=dict(term=query))

    if extract_search_results_from_response(response) is True:
        xbmcplugin.endOfDirectory(pluginhandle)
    else:
        mydialogue = xbmcgui.Dialog()
        msg = addon.getLocalizedString(30022)
        mydialogue.ok(heading=TVShowTitle,
                      line1=msg)


def browse():
    """Browse videos by Date"""
    mydialogue = xbmcgui.Dialog()
    msg = addon.getLocalizedString(30020)
    datestring = mydialogue.numeric(type=1, heading=msg)

    if not datestring:
        return

    day, month, year = datestring.split("/")

    urlstring = "http://www.colbertnation.com/feeds/search" + \
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


def play_random():
    """Play a random videos"""
    raise NotImplementedError
    # Do something intelligent to select from all available videos while
    # minimizng the wait time prior to play. We suggest selecting a random,
    # valid date.


# Play Video
def play_video(name, url):
    data = get_url(url)
    uri = re.compile('"http://media.mtvnservices.com/(.+?)"/>').findall(
        data)[0].replace('fb/', '').replace('.swf', '')

    rtmp = grab_rtmp(uri)
    item = xbmcgui.ListItem(
        name,
        iconImage="DefaultVideo.png",
        thumbnailImage=thumbnail,
        path=rtmp)
    item.setInfo(type="Video", infoLabels={"Title": name,
                                           "Plot": plot,
                                           "premiered": premiered,
                                           "Season": int(season),
                 "Episode": int(episode),
        "TVShowTitle": TVShowTitle})
    item.setProperty('fanart_image', image_fanart)
    xbmcplugin.setResolvedUrl(pluginhandle, True, item)

# Play Full Episode


def play_full_episode(name, url):
    data = get_url(url)
    uri = re.compile(
        '(mgid:cms:episode:colbertnation.com:\d{6}|mgid:cms:video:colbertnation.com:\d{6})').findall(data)[0]
    url = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?uri=' + uri
    data = get_url(url)
    uris = re.compile('<guid isPermaLink="false">(.+?)</guid>').findall(data)
    stacked_url = 'stack://'
    for uri in uris:
        rtmp = grab_rtmp(uri)
        stacked_url += rtmp.replace(',', ',,') + ' , '
    stacked_url = stacked_url[:-3]

    log('stacked_url --> %s' % stacked_url)

    item = xbmcgui.ListItem(
        name,
        iconImage="DefaultVideo.png",
        thumbnailImage=thumbnail,
        path=stacked_url)

    log('item --> %s' % item)

    item.setInfo(type="Video", infoLabels={"Title": name,
                                           "Plot": plot,
                                           "premiered": premiered,
                                           "Season": int(season),
                 "Episode": int(episode),
        "TVShowTitle": TVShowTitle})
    item.setProperty('fanart_image', image_fanart)
    xbmcplugin.setResolvedUrl(pluginhandle, True, item)

# Grab rtmp


def grab_rtmp(uri):
    url = 'http://www.comedycentral.com/global/feeds/entertainment/media/mediaGenEntertainment.jhtml?uri=' + \
        uri + '&showTicker=true'
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


# Since params are defined by us in this module, we could use JSON
# representation here instead of parsing this by hand
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

params = get_params()
url = None
name = None
mode = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = params["mode"]
except:
    pass
try:
    thumbnail = urllib.unquote_plus(params["thumbnail"])
except:
    thumbnail = ''
try:
    season = int(params["season"])
except:
    season = 0
try:
    episode = int(params["episode"])
except:
    episode = 0
try:
    premiered = urllib.unquote_plus(params["premiered"])
except:
    premiered = ''
try:
    plot = urllib.unquote_plus(params["plot"])
except:
    plot = ''

#log("Mode: " + str(mode))
#log("URL: " + str(url))
#log("Name: " + str(name))

mode_handlers = {"browse": browse,
                 "full": full_episodes,
                 "guests": guests,
                 "play": lambda: play_full_episode(name, url),
                 "search": search,
                 }

mode_handlers.get(mode, root)()
