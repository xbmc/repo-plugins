#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import traceback
import xbmcplugin

from resources.lib.ServiceApi import *
from resources.lib.HtmlScraper import *

socket.setdefaulttimeout(30)

plugin = "ORF-TVthek-" + xbmcaddon.Addon().getAddonInfo('version')

# initial
settings = xbmcaddon.Addon()
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
translation = settings.getLocalizedString

# hardcoded
videoProtocol = "http"
videoQuality = "QXB"
videoDelivery = "HLS"

input_stream_protocol = 'mpd'
input_stream_drm_version = 'com.widevine.alpha'
input_stream_mime = 'application/dash+xml'
input_stream_lic_content_type = 'application/octet-stream'

# media resources
resource_path = os.path.join(basepath, "resources")
media_path = os.path.join(resource_path, "media")
defaultbanner = os.path.join(media_path, "default_banner_v2.jpg")
news_banner = os.path.join(media_path, "news_banner_v2.jpg")
recently_added_banner = os.path.join(media_path, "recently_added_banner_v2.jpg")
shows_banner = os.path.join(media_path, "shows_banner_v2.jpg")
topics_banner = os.path.join(media_path, "topics_banner_v2.jpg")
live_banner = os.path.join(media_path, "live_banner_v2.jpg")
tips_banner = os.path.join(media_path, "tips_banner_v2.jpg")
most_popular_banner = os.path.join(media_path, "most_popular_banner_v2.jpg")
schedule_banner = os.path.join(media_path, "schedule_banner_v2.jpg")
archive_banner = os.path.join(media_path, "archive_banner_v2.jpg")
search_banner = os.path.join(media_path, "search_banner_v2.jpg")
trailer_banner = os.path.join(media_path, "trailer_banner_v2.jpg")
blacklist_banner = os.path.join(media_path, "blacklist_banner_v2.jpg")
focus_banner = os.path.join(media_path, "focus_banner_v2.jpg")
defaultbackdrop = os.path.join(media_path, "fanart_v2.jpg")

# load settings
useServiceAPI = Settings.serviceAPI()
autoPlayPrompt = Settings.autoPlayPrompt()
usePlayAllPlaylist = Settings.playAllPlaylist()

# init scrapers
if useServiceAPI:
    debugLog("Service API activated")
    scraper = serviceAPI(xbmc, settings, pluginhandle, videoQuality, videoProtocol, videoDelivery, defaultbanner, defaultbackdrop, usePlayAllPlaylist)
else:
    debugLog("HTML Scraper activated")
    scraper = htmlScraper(xbmc, settings, pluginhandle, videoQuality, videoProtocol, videoDelivery, defaultbanner, defaultbackdrop, usePlayAllPlaylist)


def getMainMenu():
    debugLog("Building Main Menu")
    addDirectory((translation(30001)).encode("utf-8"), news_banner, defaultbackdrop, "", "", "getAktuelles", pluginhandle)
    addDirectory((translation(30000)).encode("utf-8"), recently_added_banner, defaultbackdrop, "", "", "getNewShows", pluginhandle)
    addDirectory((translation(30002)).encode("utf-8"), shows_banner, defaultbackdrop, "", "", "getSendungen", pluginhandle)
    if useServiceAPI:
        addDirectory((translation(30003)).encode("utf-8"), topics_banner, defaultbackdrop, "", "", "getThemen", pluginhandle)
    addDirectory((translation(30004)).encode("utf-8"), live_banner, defaultbackdrop, "", "", "getLive", pluginhandle)
    if not useServiceAPI:
        addDirectory((translation(30057)).encode("utf-8"), focus_banner, defaultbackdrop, "", "", "getFocus", pluginhandle)
    addDirectory((translation(30006)).encode("utf-8"), most_popular_banner, defaultbackdrop, "", "", "getMostViewed", pluginhandle)
    addDirectory((translation(30018)).encode("utf-8"), schedule_banner, defaultbackdrop, "", "", "getSchedule", pluginhandle)
    if not useServiceAPI:
        addDirectory((translation(30049)).encode("utf-8"), archive_banner, defaultbackdrop, "", "", "getArchiv", pluginhandle)
    addDirectory((translation(30027)).encode("utf-8"), trailer_banner, defaultbackdrop, "", "", "openTrailers", pluginhandle)
    if not useServiceAPI:
        addDirectory((translation(30007)).encode("utf-8"), search_banner, defaultbackdrop, "", "", "getSearchHistory", pluginhandle)
    if Settings.blacklist() and not useServiceAPI:
        addDirectory((translation(30037)).encode("utf-8"), blacklist_banner, defaultbackdrop, "", "", "openBlacklist", pluginhandle)
    listCallback(False, pluginhandle)


def listCallback(sort, pluginhandle):
    xbmcplugin.setContent(pluginhandle, 'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)


def startPlaylist(player, playlist):
    if playlist is not None:
        player.play(playlist)
    else:
        d = xbmcgui.Dialog()
        d.ok((translation(30051)).encode("utf-8"), (translation(30050)).encode("utf-8"))


def run():
    # video playback
    tvthekplayer = xbmc.Player()
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

    # parameters
    params = parameters_string_to_dict(sys.argv[2])
    mode = params.get('mode')
    link = params.get('link')
    if mode == 'openSeries':
        playlist.clear()
        playlist = scraper.getLinks(link, params.get('banner'), playlist)
        if autoPlayPrompt and playlist is not None:
            listCallback(False, pluginhandle)
            ok = xbmcgui.Dialog().yesno((translation(30047)).encode("utf-8"), (translation(30048)).encode("utf-8"))
            listCallback(False, pluginhandle)
            if ok:
                debugLog("Starting Playlist for %s" % unqoute_url(link))
                tvthekplayer.play(playlist)
        else:
            debugLog("Running Listcallback from no autoplay openseries")
            listCallback(False, pluginhandle)
    elif mode == 'unblacklistShow':
        heading = translation(30040).encode('UTF-8') % unqoute_url(link).replace('+', ' ').strip()
        if isBlacklisted(link) and xbmcgui.Dialog().yesno(heading, heading):
            unblacklistItem(link)
            xbmc.executebuiltin('Container.Refresh')
    elif mode == 'blacklistShow':
        blacklistItem(link)
        xbmc.executebuiltin('Container.Refresh')
    if mode == 'openBlacklist':
        printBlacklist(defaultbanner, defaultbackdrop, translation, pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'getSendungen':
        scraper.getCategories()
        listCallback(True, pluginhandle)
    elif mode == 'getAktuelles':
        scraper.getHighlights()
        listCallback(False, pluginhandle)
    elif mode == 'getLive':
        scraper.getLiveStreams()
        listCallback(False, pluginhandle)
    elif mode == 'getTipps':
        scraper.getTips()
        listCallback(False, pluginhandle)
    elif mode == 'getFocus':
        scraper.getFocus()
        listCallback(False, pluginhandle)
    elif mode == 'getNewShows':
        scraper.getNewest()
        listCallback(False, pluginhandle)
    elif mode == 'getMostViewed':
        scraper.getMostViewed()
        listCallback(False, pluginhandle)
    elif mode == 'getThemen':
        scraper.getThemen()
        listCallback(True, pluginhandle)
    elif mode == 'getSendungenDetail':
        scraper.getCategoriesDetail(link, params.get('banner'))
        listCallback(False, pluginhandle)
    elif mode == 'getThemenDetail':
        scraper.getArchiveDetail(link)
        listCallback(False, pluginhandle)
    elif mode == 'getArchiveDetail':
        scraper.getArchiveDetail(link)
        listCallback(False, pluginhandle)
    elif mode == 'getSchedule':
        scraper.getSchedule()
        listCallback(False, pluginhandle)
    elif mode == 'getArchiv':
        scraper.getArchiv()
        listCallback(False, pluginhandle)
    elif mode == 'getScheduleDetail':
        scraper.openArchiv(link)
        listCallback(True, pluginhandle)
    elif mode == 'openTrailers':
        scraper.getTrailers()
        listCallback(False, pluginhandle)
    elif mode == 'getSearchHistory':
        scraper.getSearchHistory()
        listCallback(False, pluginhandle)
    elif mode == 'getSearchResults':
        if link is not None:
            scraper.getSearchResults(unqoute_url(link))
        else:
            scraper.getSearchResults("")
        listCallback(False, pluginhandle)
    elif mode == 'openDate':
        scraper.getDate(link, params.get('from'))
        listCallback(False, pluginhandle)
    elif mode == 'openProgram':
        scraper.getProgram(link, playlist)
        listCallback(False, pluginhandle)
    elif mode == 'openTopic':
        scraper.getTopic(link)
        listCallback(False, pluginhandle)
    elif mode == 'openEpisode':
        scraper.getEpisode(link, playlist)
        listCallback(False, pluginhandle)
    elif mode == 'liveStreamRestart':
        try:
            import inputstreamhelper
            is_helper = inputstreamhelper.Helper(input_stream_protocol, drm=input_stream_drm_version)
            if is_helper.check_inputstream():
                link = unqoute_url(link)
                debugLog("Restart Source Link: %s" % link)
                headers = "User-Agent=%s&Content-Type=%s" % (Settings.userAgent(), input_stream_lic_content_type)
                if params.get('lic_url'):
                    lic_url = unqoute_url(params.get('lic_url'))
                    debugLog("Playing DRM protected Restart Stream")
                    debugLog("Restart License URL: %s" % lic_url)
                    streaming_url, play_item = scraper.liveStreamRestart(link, 'dash')
                    play_item = xbmcgui.ListItem(path=streaming_url, offscreen=True)
                    play_item.setContentLookup(False)
                    play_item.setMimeType(input_stream_mime)
                    play_item.setProperty('inputstream.adaptive.stream_headers', headers)
                    play_item.setProperty('inputstream', is_helper.inputstream_addon)
                    play_item.setProperty('inputstream.adaptive.manifest_type', input_stream_protocol)
                    play_item.setProperty('inputstream.adaptive.license_type', input_stream_drm_version)
                    play_item.setProperty('inputstream.adaptive.license_key', lic_url + '|' + headers + '|R{SSM}|')
                else:
                    streaming_url, play_item = scraper.liveStreamRestart(link, 'hls')
                    debugLog("Playing Non-DRM protected Restart Stream")
                    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                    play_item.setProperty('inputstream.adaptive.stream_headers', headers)
                    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                debugLog("Restart Stream Url: %s; play_item: %s" % (streaming_url, play_item))
                #This works on matrix. On Kodi <19 the stream wont play
                #xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)
                #listCallback(False, pluginhandle)
                xbmc.Player().play(streaming_url, play_item)
        except Exception as e:
            debugLog("Exception: %s" % ( e, ), xbmc.LOGDEBUG)
            debugLog("TB: %s" % ( traceback.format_exc(), ), xbmc.LOGDEBUG)
            userNotification((translation(30067)).encode("utf-8"))
    elif mode == 'playlist':
        startPlaylist(tvthekplayer, playlist)
    elif mode == 'play':
        link = "%s|User-Agent=%s" % (link, Settings.userAgent())
        play_item = xbmcgui.ListItem(path=link, offscreen=True)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)
        listCallback(False, pluginhandle)
    elif mode == 'playDRM':
        try:
            import inputstreamhelper
            stream_url = unqoute_url(params.get('link'))
            lic_url = unqoute_url(params.get('lic_url'))
            headers = "User-Agent=%s&Content-Type=%s" % (Settings.userAgent(), input_stream_lic_content_type)
            is_helper = inputstreamhelper.Helper(input_stream_protocol, drm=input_stream_drm_version)
            if is_helper.check_inputstream():
                debugLog("Video Url: %s" % stream_url)
                debugLog("DRM License Url: %s" % lic_url)
                play_item = xbmcgui.ListItem(path=stream_url, offscreen=True)
                play_item.setContentLookup(False)
                play_item.setMimeType(input_stream_mime)
                play_item.setProperty('inputstream.adaptive.stream_headers', headers)
                play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                play_item.setProperty('inputstream.adaptive.manifest_type', input_stream_protocol)
                play_item.setProperty('inputstream.adaptive.license_type', input_stream_drm_version)
                play_item.setProperty('inputstream.adaptive.license_key', lic_url + '|' + headers + '|R{SSM}|')
                xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)
                listCallback(False, pluginhandle)
            else:
                userNotification((translation(30066)).encode("utf-8"))
        except:
            userNotification((translation(30067)).encode("utf-8"))
    elif sys.argv[2] == '':
        getMainMenu()
    else:
        listCallback(False, pluginhandle)
