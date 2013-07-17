'''
   YouTube plugin for XBMC
    Copyright (C) 2010-2012 Tobias Ussing And Henrik Mosgaard Jensen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import urllib
import cgi
try: import simplejson as json
except ImportError: import json

class YouTubePlayer():
    fmt_value = {
        5: "240p h263 flv container",
        18: "360p h264 mp4 container | 270 for rtmpe?",
        22: "720p h264 mp4 container",
        26: "???",
        33: "???",
        34: "360p h264 flv container",
        35: "480p h264 flv container",
        37: "1080p h264 mp4 container",
        38: "720p vp8 webm container",
        43: "360p h264 flv container",
        44: "480p vp8 webm container",
        45: "720p vp8 webm container",
        46: "520p vp8 webm stereo",
        59: "480 for rtmpe",
        78: "seems to be around 400 for rtmpe",
        82: "360p h264 stereo",
        83: "240p h264 stereo",
        84: "720p h264 stereo",
        85: "520p h264 stereo",
        100: "360p vp8 webm stereo",
        101: "480p vp8 webm stereo",
        102: "720p vp8 webm stereo",
        120: "hd720",
        121: "hd1080"
        }

    # YouTube Playback Feeds
    urls = {}
    urls['video_stream'] = "http://www.youtube.com/watch?v=%s&safeSearch=none"
    urls['embed_stream'] = "http://www.youtube.com/get_video_info?video_id=%s"
    urls['video_info'] = "http://gdata.youtube.com/feeds/api/videos/%s"

    def __init__(self):
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin

        self.pluginsettings = sys.modules["__main__"].pluginsettings
        self.storage = sys.modules["__main__"].storage
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.dbg = sys.modules["__main__"].dbg

        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.cache = sys.modules["__main__"].cache
        self.core = sys.modules["__main__"].core
        self.login = sys.modules["__main__"].login
        self.subtitles = sys.modules["__main__"].subtitles

    def playVideo(self, params={}):
        self.common.log(repr(params), 3)
        get = params.get

        (video, status) = self.buildVideoObject(params)

        if status != 200:
            self.common.log(u"construct video url failed contents of video item " + repr(video))
            self.utils.showErrorMessage(self.language(30603), video["apierror"], status)
            return False

        listitem = self.xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url'])

        listitem.setInfo(type='Video', infoLabels=video)

        self.common.log(u"Playing video: " + repr(video['Title']) + " - " + repr(get('videoid')) + " - " + repr(video['video_url']))

        self.xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

        if self.settings.getSetting("lang_code") != "0" or self.settings.getSetting("annotations") == "true":
            self.common.log("BLAAAAAAAAAAAAAAAAAAAAAA: " + repr(self.settings.getSetting("lang_code")))
            self.subtitles.addSubtitles(video)

        if (get("watch_later") == "true" and get("playlist_entry_id")):
            self.common.log(u"removing video from watch later playlist")
            self.core.remove_from_watch_later(params)

        self.storage.storeValue("vidstatus-" + video['videoid'], "7")

    def getInfo(self, params):
        get = params.get
        video = self.cache.get("videoidcache" + get("videoid"))
        if len(video) > 0:
            self.common.log(u"returning cache ")
            return (eval(video), 200)

        result = self.core._fetchPage({"link": self.urls["video_info"] % get("videoid"), "api": "true"})

        if result["status"] == 200:
            video = self.core.getVideoInfo(result["content"], params)

            if len(video) == 0:
                self.common.log(u"- Couldn't parse API output, YouTube doesn't seem to know this video id?")
                video = {}
                video["apierror"] = self.language(30608)
                return (video, 303)
        else:
            self.common.log(u"- Got API Error from YouTube!")
            video = {}
            video["apierror"] = result["content"]

            return (video, 303)

        video = video[0]
        self.cache.set("videoidcache" + get("videoid"), repr(video))
        return (video, result["status"])

    def selectVideoQuality(self, params, links):
        get = params.get

        print "links: " + repr(type(links).__name__)
        link = links.get
        video_url = ""

        self.common.log(u"")

        if get("action") == "download":
            hd_quality = int(self.settings.getSetting("hd_videos_download"))
            if (hd_quality == 0):
                hd_quality = int(self.settings.getSetting("hd_videos"))

        else:
            if (not get("quality")):
                hd_quality = int(self.settings.getSetting("hd_videos"))
            else:
                if (get("quality") == "1080p"):
                    hd_quality = 3
                elif (get("quality") == "720p"):
                    hd_quality = 2
                else:
                    hd_quality = 1

        # SD videos are default, but we go for the highest res
        if (link(35)):
            video_url = link(35)
        elif (link(59)):
            video_url = link(59)
        elif link(44):
            video_url = link(44)
        elif (link(78)):
            video_url = link(78)
        elif (link(34)):
            video_url = link(34)
        elif (link(43)):
            video_url = link(43)
        elif (link(26)):
            video_url = link(26)
        elif (link(18)):
            video_url = link(18)
        elif (link(33)):
            video_url = link(33)
        elif (link(5)):
            video_url = link(5)

        if hd_quality > 1:  # <-- 720p
            if (link(22)):
                video_url = link(22)
            elif (link(45)):
                video_url = link(45)
            elif link(120):
                video_url = link(120)
        if hd_quality > 2:
            if (link(37)):
                video_url = link(37)
            elif link(121):
                video_url = link(121)

        if link(38) and False:
            video_url = link(38)

        for fmt_key in links.iterkeys():
            if link(int(fmt_key)):
                if self.dbg:
                    text = repr(fmt_key) + " - "
                    if fmt_key in self.fmt_value:
                        text += self.fmt_value[fmt_key]
                    else:
                        text += "Unknown"

                    if (link(int(fmt_key)) == video_url):
                        text += "*"
                    self.common.log(text)
            else:
                self.common.log(u"- Missing fmt_value: " + repr(fmt_key))

        if hd_quality == 0 and not get("quality"):
            return self.userSelectsVideoQuality(params, links)

        if not len(video_url) > 0:
            self.common.log(u"- construct_video_url failed, video_url not set")
            return video_url

        if get("action") != "download" and video_url.find("rtmp") == -1:
            video_url += '|' + urllib.urlencode({'User-Agent':self.common.USERAGENT})

        self.common.log(u"Done")
        return video_url

    def userSelectsVideoQuality(self, params, links):
        levels =    [([37,121], u"1080p"),
                     ([22,45,120], u"720p"),
                     ([35,44], u"480p"),
                     ([18], u"380p"),
                     ([34,43],u"360p"),
                     ([5],u"240p"),
                     ([17],u"144p")]

        link = links.get
        quality_list = []
        choices = []

        for qualities, name in levels:
            for quality in qualities:
                if link(quality):
                    quality_list.append((quality, name))
                    break

        for (quality, name) in quality_list:
            choices.append(name)

        dialog = self.xbmcgui.Dialog()
        selected = dialog.select(self.language(30518), choices)

        if selected > -1:
            (quality, name) = quality_list[selected]
            return link(quality)

        return u""

    def checkForErrors(self, video):
        status = 200

        if "video_url" not in video or video[u"video_url"] == u"":
            status = 303
            if u"apierror" not in video:
                vget = video.get
                if vget(u"live_play"):
                    video[u'apierror'] = self.language(30612)
                elif vget(u"stream_map"):
                    video[u'apierror'] = self.language(30620)
                else:
                    video[u'apierror'] = self.language(30618)

        return (video, status)

    def buildVideoObject(self, params):
        self.common.log(repr(params))

        (video, status) = self.getInfo(params)

        if status != 200:
            video[u'apierror'] = self.language(30618)
            return (video, 303)

        video_url = self.subtitles.getLocalFileSource(params, video)
        if video_url:
            video[u'video_url'] = video_url
            return (video, 200)

        (links, video) = self.extractVideoLinksFromYoutube(video, params)

        if len(links) != 0:
            video[u"video_url"] = self.selectVideoQuality(params, links)
        elif "hlsvp" in video:
            #hls selects the quality based on available bitrate (adaptive quality), no need to select it here
            video[u"video_url"] = video[u"hlsvp"]
            self.common.log("Using hlsvp url %s" % video[u"video_url"])

        (video, status) = self.checkForErrors(video)

        self.common.log(u"Done")

        return (video, status)

    def removeAdditionalEndingDelimiter(self, data):
        pos = data.find("};")
        if pos != -1:
            self.common.log(u"found extra delimiter, removing")
            data = data[:pos + 1]
        return data

    def extractFlashVars(self, data):
        flashvars = {}
        found = False

        for line in data.split("\n"):
            if line.strip().find(";ytplayer.config = ") > 0:
                found = True
                p1 = line.find(";ytplayer.config = ") + len(";ytplayer.config = ") - 1
                p2 = line.rfind(";")
                if p1 <= 0 or p2 <= 0:
                    continue
                data = line[p1 + 1:p2]
                break
        data = self.removeAdditionalEndingDelimiter(data)

        if found:
            data = json.loads(data)
            flashvars = data["args"]
        self.common.log("Step2: " + repr(data))

        self.common.log(u"flashvars: " + repr(flashvars), 2)
        return flashvars

    def scrapeWebPageForVideoLinks(self, result, video):
        self.common.log(u"")
        links = {}

        flashvars = self.extractFlashVars(result[u"content"])
        if not flashvars.has_key(u"url_encoded_fmt_stream_map"):
            return links

        if flashvars.has_key(u"ttsurl"):
            video[u"ttsurl"] = flashvars[u"ttsurl"]

        if flashvars.has_key(u"hlsvp"):                               
            video[u"hlsvp"] = flashvars[u"hlsvp"]    

        for url_desc in flashvars[u"url_encoded_fmt_stream_map"].split(u","):
            url_desc_map = cgi.parse_qs(url_desc)
            self.common.log(u"url_map: " + repr(url_desc_map), 2)
            if not (url_desc_map.has_key(u"url") or url_desc_map.has_key(u"stream")):
                continue

            key = int(url_desc_map[u"itag"][0])
            url = u""
            if url_desc_map.has_key(u"url"):
                url = urllib.unquote(url_desc_map[u"url"][0])
            elif url_desc_map.has_key(u"conn") and url_desc_map.has_key(u"stream"):
                url = urllib.unquote(url_desc_map[u"conn"][0])
                if url.rfind("/") < len(url) -1:
                    url = url + "/"
                url = url + urllib.unquote(url_desc_map[u"stream"][0])
            elif url_desc_map.has_key(u"stream") and not url_desc_map.has_key(u"conn"):
                url = urllib.unquote(url_desc_map[u"stream"][0])

            if url_desc_map.has_key(u"sig"):
                url = url + u"&signature=" + url_desc_map[u"sig"][0]
            elif url_desc_map.has_key(u"s"):
                sig = url_desc_map[u"s"][0]
                url = url + u"&signature=" + self.decrypt_signature(sig)

            links[key] = url

        return links

    def decrypt_signature(self, s):
        ''' use decryption solution by Youtube-DL project '''
        if len(s) == 88:
            return s[48] + s[81:67:-1] + s[82] + s[66:62:-1] + s[85] + s[61:48:-1] + s[67] + s[47:12:-1] + s[3] + s[11:3:-1] + s[2] + s[12]
        elif len(s) == 87:
            return s[62] + s[82:62:-1] + s[83] + s[61:52:-1] + s[0] + s[51:2:-1]
        elif len(s) == 86:
            return s[2:63] + s[82] + s[64:82] + s[63]
        elif len(s) == 85:
            return s[76] + s[82:76:-1] + s[83] + s[75:60:-1] + s[0] + s[59:50:-1] + s[1] + s[49:2:-1]
        elif len(s) == 84:
            return s[83:36:-1] + s[2] + s[35:26:-1] + s[3] + s[25:3:-1] + s[26]
        elif len(s) == 83:
            return s[6] + s[3:6] + s[33] + s[7:24] + s[0] + s[25:33] + s[53] + s[34:53] + s[24] + s[54:]
        elif len(s) == 82:
            return s[36] + s[79:67:-1] + s[81] + s[66:40:-1] + s[33] + s[39:36:-1] + s[40] + s[35] + s[0] + s[67] + s[32:0:-1] + s[34]
        elif len(s) == 81:
            return s[6] + s[3:6] + s[33] + s[7:24] + s[0] + s[25:33] + s[2] + s[34:53] + s[24] + s[54:81]
        elif len(s) == 92:
            return s[25] + s[3:25] + s[0] + s[26:42] + s[79] + s[43:79] + s[91] + s[80:83];
        else:
            self.common.log(u'Unable to decrypt signature, key length %d not supported; retrying might work' % (len(s)))

    def getVideoPageFromYoutube(self, get):
        login = "false"

        if self.pluginsettings.userHasProvidedValidCredentials():
            login = "true"

        page = self.core._fetchPage({u"link": self.urls[u"video_stream"] % get(u"videoid"), "login": login})
        self.common.log("Step1: " + repr(page["content"].find("ytplayer")))

        if not page:
            page = {u"status":303}

        return page

    def isVideoAgeRestricted(self, result):
        error = self.common.parseDOM(result['content'], "div", attrs={"id": "watch7-player-age-gate-content"})
        self.common.log(repr(error))
        return len(error) > 0

    def extractVideoLinksFromYoutube(self, video, params):
        self.common.log(u"trying website: " + repr(params))
        get = params.get

        result = self.getVideoPageFromYoutube(get)
        if self.isVideoAgeRestricted(result):
            self.common.log(u"Age restricted video")
            if self.pluginsettings.userHasProvidedValidCredentials():
                self.login._httpLogin({"new":"true"})
                result = self.getVideoPageFromYoutube(get)
            else:
                video[u"apierror"] = self.language(30622)

        if result[u"status"] != 200:
            self.common.log(u"Couldn't get video page from YouTube")
            return ({}, video)

        links = self.scrapeWebPageForVideoLinks(result, video)

        if len(links) == 0 and not( "hlsvp" in video ):
            self.common.log(u"Couldn't find video url- or stream-map.")

            if not u"apierror" in video:
                video[u'apierror'] = self.core._findErrors(result)

        self.common.log(u"Done")
        return (links, video)
