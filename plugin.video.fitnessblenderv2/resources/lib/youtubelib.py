# -*- coding: utf-8 -*-
import requests
import kodiutils
import addonutils
import xbmc
import math
import re
import xbmcaddon
from xbmcgui import ListItem

CHANNEL_ID = kodiutils.get_setting("channel_id")
YOUTUBE_API_KEY = kodiutils.get_setting("api_key")
TVSHOWTITLE = "Fitness Blender"
CAST = [TVSHOWTITLE]
STATUS = 'in production'


def get_playlists():
    api_endpoint = 'https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&channelId=%s&maxResults=50&key=%s' % (CHANNEL_ID,YOUTUBE_API_KEY)
    try:
        resp = requests.get(api_endpoint).json()
    except ValueError:
        kodiutils.log(kodiutils.get_string(32003), xbmc.LOGERROR)
    if "items" in resp.keys():
        for playlist in resp["items"]:
            liz = ListItem(playlist["snippet"]["title"])
            infolabels = {"plot": playlist["snippet"]["localized"]["description"]}
            liz.setInfo(type="video", infoLabels=infolabels)
            liz.setArt({"thumb": playlist["snippet"]["thumbnails"]["high"]["url"], "fanart": xbmcaddon.Addon().getAddonInfo("fanart")})
            liz.setProperty("type","playlist")
            liz.setProperty("playlist_id", playlist["id"])
            yield liz


def get_upload_playlist():
    api_endpoint = 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id=%s&key=%s' % (CHANNEL_ID,YOUTUBE_API_KEY)
    try:
        resp = requests.get(api_endpoint).json()
    except ValueError:
        kodiutils.log(kodiutils.get_string(32004), xbmc.LOGERROR)
        return None
    if "items" in resp.keys():
        uploads_playlist = resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return uploads_playlist

def get_videos(name,playlist_id,token="",page_num=1):
    items_per_page = kodiutils.get_setting_as_int("items_per_page")
    url_api = 'https://www.googleapis.com/youtube/v3/playlistItems?part=id,snippet,contentDetails&maxResults=%s&playlistId=%s&key=%s' \
              % (str(items_per_page), playlist_id, YOUTUBE_API_KEY)
    if page_num != 1:
        url_api += "&pageToken=%s" % (token)

    try:
        resp = requests.get(url_api).json()
    except ValueError:
        kodiutils.log(kodiutils.get_string(32004), xbmc.LOGERROR)
        resp = None

    if resp:
        nextpagetoken = resp["nextPageToken"] if "nextPageToken" in resp.keys() else ""
        availablevideos = resp["pageInfo"]["totalResults"] if "pageInfo" in resp.keys() and "totalResults" in resp["pageInfo"].keys() else 1

        returnedVideos = resp["items"]
        totalpages = int(math.ceil((float(availablevideos) / items_per_page)))
        video_ids = []
        if returnedVideos:
            for video in returnedVideos:
                videoid = video["contentDetails"]["videoId"]
                video_ids.append(videoid)
            video_ids = ','.join(video_ids)
            url_api = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=%s&key=%s' % (video_ids,YOUTUBE_API_KEY)
            try:
                resp = requests.get(url_api).json()
            except ValueError:
                kodiutils.log(kodiutils.get_string(32005), xbmc.LOGERROR)
                resp = None

            if resp:
                returnedVideos = resp["items"]

                for video in returnedVideos:
                    title = video["snippet"]["title"]
                    plot = video["snippet"]["description"]
                    aired = video["snippet"]["publishedAt"]
                    thumb = video["snippet"]["thumbnails"]["high"]["url"]
                    videoid = video["id"]
                    # process duration
                    duration_string = video["contentDetails"]["duration"]
                    duration = addonutils.return_duration_as_seconds(duration_string)
                    try:
                        aired = re.compile('(.+?)-(.+?)-(.+?)T').findall(aired)[0]
                        date = aired[2] + '.' + aired[1] + '.' + aired[0]
                        aired = aired[0] + '-' + aired[1] + '-' + aired[2]
                    except IndexError:
                        aired = ''
                        date = ''

                    infolabels = {'plot': plot.encode('utf-8'), 'aired': aired, 'date': date, 'tvshowtitle': TVSHOWTITLE,
                                  'title': title.encode('utf-8'), 'originaltitle': title.encode('utf-8'), 'status': STATUS,
                                  'cast': CAST, 'duration': duration}

                    # Video and audio info
                    video_info = {'codec': 'avc1', 'aspect': 1.78}
                    audio_info = {'codec': 'aac', 'language': 'en'}
                    if video["contentDetails"]["definition"].lower() == 'hd':
                        video_info['width'] = 1280
                        video_info['height'] = 720
                        audio_info['channels'] = 2
                    else:
                        video_info['width'] = 854
                        video_info['height'] = 480
                        audio_info['channels'] = 1
                    if xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality.ask') == 'false' and xbmcaddon.Addon(
                                    id='plugin.video.youtube').getSetting('kodion.video.quality') != '3' and xbmcaddon.Addon(
                                    id='plugin.video.youtube').getSetting('kodion.video.quality') != '4':
                        video_info['width'] = 854
                        video_info['height'] = 480
                        audio_info['channels'] = 1

                    yield build_video_item(title.encode('utf-8'), thumb, videoid, infolabels, video_info, audio_info)

    if totalpages > 1 and (page_num + 1) <= totalpages:
        nextpage = ListItem("[B]%s[/B] (%s/%s)" % (kodiutils.get_string(32008), str(page_num), str(totalpages)))
        nextpage.setProperty("type", "next")
        nextpage.setProperty("page", str(page_num+1))
        nextpage.setProperty("token", str(nextpagetoken))
        nextpage.setInfo(type="video",infoLabels={"plot": kodiutils.get_string(32002)})
        yield nextpage

def build_video_item(name,thumb,videoid,info,video_info,audio_info):
    liz=ListItem(name)
    cm = []
    cm.append(("Info", 'XBMC.Action(Info)'))
    thumb = thumb if thumb else xbmcaddon.Addon().getAddonInfo("icon")
    liz.setProperty("type", "youtube_video")
    liz.setProperty("videoid",videoid)
    liz.setArt({'thumb': thumb, 'fanart': xbmcaddon.Addon().getAddonInfo("fanart"), "poster": thumb})
    liz.setInfo(type="Video", infoLabels=info)
    liz.addStreamInfo('video', video_info)
    liz.addStreamInfo('audio', audio_info)
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems(cm, replaceItems=False)
    return liz
