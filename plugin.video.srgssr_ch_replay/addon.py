import sys
import json
import urllib.request
import urllib.parse
import socket
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
import traceback
from io import StringIO
import gzip
from urllib.parse import urlparse
from string import ascii_lowercase

# imports for new API
import requests
import base64
import datetime


#'Base settings'
#'Start of the plugin functionality is at the end of the file'
addon = xbmcaddon.Addon()
addonID = 'plugin.video.srgssr_ch_replay'
pluginhandle = int(sys.argv[1])
socket.setdefaulttimeout(30)
xbmcplugin.setPluginCategory(pluginhandle, "News")
xbmcplugin.setContent(pluginhandle, "tvshows")
addon_work_folder = xbmcvfs.translatePath("special://profile/addon_data/" + addonID)
if not os.path.isdir(addon_work_folder):
    os.mkdir(addon_work_folder)
FavoritesFile = xbmcvfs.translatePath("special://profile/addon_data/" + addonID + "/" + addonID + ".favorites")
numberOfEpisodesPerPage = int(addon.getSetting("numberOfShowsPerPage"))
consumerKey = addon.getSetting("consumerKey")
consumerSecret = addon.getSetting("consumerSecret")
tr = addon.getLocalizedString
default_channel = 'srf'


#####################################
# NEW SRG SSR API methods
#####################################

SRG_API_HOST = "api.srgssr.ch"


def choose_channel():
    nextMode = 'chooseTvShowLetter'
    _add_channel(default_channel, tr(30014), nextMode)
    _add_channel('swi', tr(30015), nextMode)
    _add_channel('rts', tr(30016), nextMode)
    _add_channel('rsi', tr(30017), nextMode)
    _add_channel('rtr', tr(30018), nextMode)
    xbmcplugin.endOfDirectory(handle=pluginhandle, succeeded=True)


def list_tv_shows_new(channel, letter):
    PATH = "/videometadata/v2/tv_shows/alphabetical"
    query = {"bu": channel, "characterFilter": letter}
    response = _srg_get(PATH, query=query)
    shows = response["showList"]
    mode = 'listEpisodes'

    for show in shows:
        showid = show.get('id')
        title = show.get('title')
        desc = show.get('description')
        picture = show.get('imageUrl')
        numberOfEpisodes = show.get('numberOfEpisodes')
        _add_show(title, showid, mode, desc, picture, channel, numberOfEpisodes)

    xbmcplugin.addSortMethod(pluginhandle, 1)
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmcplugin.endOfDirectory(handle=pluginhandle, succeeded=True)


def list_episodes_new(channel, showid, showbackground, pageNumber, numberOfEpisodes, nextParam):
    PATH = f"/videometadata/v2/latest_episodes/shows/{showid}"
    query = {"bu": channel}
    if nextParam:
        query.update({"next": nextParam})
    else:
        query.update({"pageSize": numberOfEpisodesPerPage})
    response = _srg_get(PATH, query=query)
    show = response.get('show')
    episodeList = response.get("episodeList")

    if show and episodeList:
        for episode in episodeList:
            title = show.get('title') + ' - ' + episode.get('title')
            desc = episode.get('description')
            pubdate = episode.get('publishedDate')
            media = episode.get('mediaList')[0]
            url = media.get('id')
            picture = media.get('imageUrl')
            length = int(media.get('duration', 0)) / 1000 / 60
            _addLink(title, url, 'playepisode', desc, picture, length, pubdate, showbackground, channel)

        next_page_url = response.get('next')
        if next_page_url:
            numberOfPages = int((numberOfEpisodesPerPage - 1 + numberOfEpisodes) / numberOfEpisodesPerPage)
            next_param = urllib.parse.parse_qs(urllib.parse.urlparse(next_page_url).query).get('next')[0]
            _addnextpage(tr(30005).format(pageNumber, numberOfPages or '?'), showid, 'listEpisodes', '', showbackground, pageNumber + 1, channel, numberOfEpisodes, next_param)

    xbmcplugin.endOfDirectory(pluginhandle)


def _add_channel(channelId, name, mode):
    directoryurl = sys.argv[0] + "?channel=" + str(channelId) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(name)
    return xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)


def _srg_api_get_simple(path, *, query=None, bearer, exp_code=None):
    headers = {}
    if bearer:
        headers.update({"Authorization": f"Bearer {bearer}"})
    return _http_request(SRG_API_HOST, 'GET', path, query, headers, None, exp_code)


def _srg_api_auth_token():
    token_ts = addon.getSetting('srgssrTokenTS')
    if token_ts:
        delta_ts = datetime.datetime.utcnow() - datetime.datetime.fromisoformat(token_ts)
        token = addon.getSetting('srgssrToken')
        if delta_ts < datetime.timedelta(days=25) and token:
            return token

    query = {"grant_type": "client_credentials"}
    headers = {"Authorization": "Basic " + str(base64.b64encode(f"{consumerKey}:{consumerSecret}".encode("utf-8")), "utf-8")}
    try:
        r = _http_request(SRG_API_HOST, 'POST', "/oauth/v1/accesstoken", query=query, headers=headers, exp_code=200)
    except UnexpectedStatusCodeException as e:
        if e.status_code in [401, 403]:
            xbmc.log(f"Authentication failed -> No API token")
        raise e
    access_token = r.json()["access_token"]
    addon.setSetting('srgssrToken', access_token)
    addon.setSetting('srgssrTokenTS', datetime.datetime.utcnow().isoformat())
    return access_token


def _srg_get(path, query):
    def _get_with_token(path, query):
        token = _srg_api_auth_token()
        if token:
            r = _srg_api_get_simple(path, bearer=token, query=query, exp_code=[200, 203])
            return r.json()
        return None

    try:
        data = _get_with_token(path, query)
    except UnexpectedStatusCodeException as e:
        if e.status_code in [401, 403]:
            # clear cached api token
            addon.setSetting('srgssrToken', '')
            addon.setSetting('srgssrTokenTS', '')
            data = _get_with_token(path, query)
        else:
            raise e
    return data


class UnexpectedStatusCodeException(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)


def _http_request(host, method, path, query=None, headers={}, body_dict=None, exp_code=None):
    uri = f'https://{host}{path}'
    xbmc.log(f"request: {method} {uri}")
    res = requests.request(method, uri, params=query, headers=headers, json=body_dict)
    if exp_code:
        if type(exp_code) is not list:
            exp_code = [exp_code]
        if (res.status_code not in exp_code):
            raise UnexpectedStatusCodeException(res.status_code, str(res.status_code) + ':' + res.text)
    return res


#####################################
# Common methods
#####################################

def play_episode(channel, episodeid):
    """
    this method plays the selected episode
    """

    besturl = ''

    if channel == 'rsi':
        besturl = _parse_integrationplayer_2(channel, episodeid)
    else: 
        besturl = _parse_integrationplayer_1(channel, episodeid)

    # add authentication token for akamaihd
    if "akamaihd" in urlparse(besturl).netloc:
        url = "http://tp.srgssr.ch/akahd/token?acl=" + urlparse(besturl).path
        response = json.load(_open_url(url))
        token = response["token"]["authparams"]
        besturl = besturl + '?' + token

    listitem = xbmcgui.ListItem(path=besturl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


# TODO (milestone 3) not stable yet
def _parse_integrationplayer_2(channel, episodeid):
    """
    RSI channel only at the moment
    """
    
    url = f'https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/urn:{channel}:video:{episodeid}.json'
    response = json.load(_open_url(url))
    
    # Future improvements: search for the best akaidhd stream in response['chapterList'][0]['resourceList'] e.g https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/urn:rsi:video:14670486.json
    # 1) search for HLS if found search for HD take it
    # 2) only take HD
    # 3) otherwise take the first one
    tempUrl = response['chapterList'][0]['resourceList'][0]['url']
    
    # remove all URL parameter
    besturl = urlparse(tempUrl)
    return f'{besturl.scheme}://{besturl.netloc}{besturl.path}'
    

def _parse_integrationplayer_1(channel, episodeid):
    besturl = ''

    try:
        url = 'http://il.srgssr.ch/integrationlayer/1.0/ue/' + channel + '/video/play/' + episodeid + '.json'
        response = json.load(_open_url(url))
        playlistVector = response['Video']['Playlists']['Playlist']

        # filter objects with list comprehensions
        playlist = [obj for obj in playlistVector if obj['@protocol'] == 'HTTP-HLS']

        playlistVector = playlist[0]
        urls = playlistVector['url']

        besturl = urls[0]['text']
        for tempurl in urls:
            if tempurl['@quality'] == 'HD':
                besturl = tempurl['text']
                break

    except:
        xbmc.log(traceback.format_exc())

    if besturl == '':
        try:
            url = 'http://il.srgssr.ch/integrationlayer/1.0/ue/' + channel + '/video/play/' + episodeid + '.json'
            response = json.load(_open_url(url))
            urls = response['Video']['Playlists']['Playlist'][0]['url']

            besturl = urls[0]['text']
            for tempurl in urls:
                if tempurl['@quality'] == 'HD':
                    besturl = tempurl['text']
                    break

        except:
            xbmc.log(traceback.format_exc())
    
    return besturl


def _open_url(urlstring):
    request = urllib.request.Request(urlstring)
    request.add_header('Accept-encoding', 'gzip')
    response = ''
    try:
        response = urllib.request.urlopen(urlstring)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
            response = StringIO(f.read())
    except Exception as e:
        xbmc.log(traceback.format_exc())
        xbmcgui.Dialog().ok(tr(30006), str(e.__class__.__name__), str(e))
    return response


def choose_tv_show_letter(channel):
    nextMode = 'listTvShows'
    _add_letter(channel, '#', tr(30019), nextMode)
    for c in ascii_lowercase:
        _add_letter(channel, c, c, nextMode)
    xbmcplugin.endOfDirectory(handle=pluginhandle, succeeded=True)


def _add_letter(channel, letter, letterDescription, mode):
    directoryurl = sys.argv[0] + "?mode=" + str(mode) + "&channel=" + str(channel) + "&letter=" + letter
    liz = xbmcgui.ListItem(letterDescription)
    return xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)


def _add_show(name, url, mode, desc, iconimage, channel, numberOfEpisodes):
    """
    helper method to create a folder with subitems
    """
    directoryurl = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&showbackground=" + urllib.parse.quote_plus(iconimage) + \
        "&channel=" + str(channel) + "&numberOfEpisodes=" + str(numberOfEpisodes or "")
    liz = xbmcgui.ListItem(name)
    liz.setLabel2(desc)
    liz.setArt({'poster': iconimage, 'banner': iconimage, 'fanart': iconimage, 'thumb': iconimage})
    liz.setInfo(type="Video", infoLabels={"title": name, "plot": desc, "plotoutline": desc})
    xbmcplugin.setContent(pluginhandle, 'tvshows')
    ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)
    return ok


def _addLink(name, url, mode, desc, iconurl, length, pubdate, showbackground, channel):
    """
    helper method to create an item in the list
    """
    linkurl = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&channel=" + str(channel)
    liz = xbmcgui.ListItem(name)
    liz.setLabel2(desc)
    liz.setArt({'poster': iconurl, 'banner': iconurl, 'fanart': showbackground, 'thumb': iconurl})
    liz.setInfo(type='Video', infoLabels={"Title": name, "Duration": length, "Plot": desc, "Aired": pubdate})
    liz.setProperty('IsPlayable', 'true')
    xbmcplugin.setContent(pluginhandle, 'episodes')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=linkurl, listitem=liz)
    return ok


def _addnextpage(name, url, mode, desc, showbackground, pageNumber, channel, numberOfEpisodes, nextParam):
    """
    helper method to create a folder with subitems
    """
    directoryurl = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&showbackground=" + urllib.parse.quote_plus(showbackground) + \
        "&page=" + str(pageNumber or "") + "&channel=" + str(channel) + "&numberOfEpisodes=" + str(numberOfEpisodes or "") + "&next=" + str(nextParam)
    liz = xbmcgui.ListItem(name)
    liz.setLabel2(desc)
    #liz.setArt({'poster' : '' , 'banner' : '', 'fanart' : showbackground, 'thumb' : ''})
    liz.setInfo(type="Video", infoLabels={"title": name, "plot": desc, "plotoutline": desc})
    xbmcplugin.setContent(pluginhandle, 'episodes')
    ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)
    return ok


def _parameters_string_to_dict(parameters):
    """
    helper method to retrieve parameters in a dict from the arguments given to this plugin by xbmc
    """
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


#####################################
# Start
#####################################
params = _parameters_string_to_dict(sys.argv[2])
mode = params.get('mode', '')
url = params.get('url', '')
showbackground = urllib.parse.unquote_plus(params.get('showbackground', ''))
page = int(params.get('page', 1))
channel = params.get('channel', default_channel)
letter = params.get('letter', '')
numberOfEpisodes = int(params.get('numberOfEpisodes', 0))
nextParam = params.get('next', '')

if consumerKey == '' or consumerSecret == '':
    xbmcgui.Dialog().ok(tr(30012) + ' / ' + tr(30013), tr(30020))
    addon.openSettings()
elif mode == 'playepisode':
    play_episode(channel, url)
elif mode == 'listEpisodes':
    list_episodes_new(channel, url, showbackground, page, numberOfEpisodes, nextParam)
elif mode == 'listTvShows':
    list_tv_shows_new(channel, letter)
elif mode == 'chooseTvShowLetter':
    choose_tv_show_letter(channel)
else:
    choose_channel()