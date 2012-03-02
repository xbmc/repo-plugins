'''
   YouTube plugin for XBMC
    Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

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
import re
import os.path
import datetime
import time
from xml.dom.minidom import parseString
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
        102: "720p vp8 webm stereo"
        }

    # YouTube Playback Feeds
    urls = {}
    urls['video_stream'] = "http://www.youtube.com/watch?v=%s&safeSearch=none"
    urls['embed_stream'] = "http://www.youtube.com/get_video_info?video_id=%s"
    urls['timed_text_index'] = "http://www.youtube.com/api/timedtext?type=list&v=%s"
    urls['video_info'] = "http://gdata.youtube.com/feeds/api/videos/%s"
    urls['close_caption_url'] = "http://www.youtube.com/api/timedtext?type=track&v=%s&name=%s&lang=%s"
    urls['transcription_url'] = "http://www.youtube.com/api/timedtext?sparams=asr_langs,caps,expire,v&asr_langs=en,ja&caps=asr&expire=%s&key=yttt1&signature=%s&hl=en&type=trackformat=1&lang=en&kind=asr&name=&v=%s&tlang=en"
    urls['annotation_url'] = "http://www.youtube.com/annotations/read2?video_id=%s&feat=TC"
    urls['remove_watch_later'] = "http://www.youtube.com/addto_ajax?action_delete_from_playlist=1"

    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin
        self.xbmcvfs = sys.modules["__main__"].xbmcvfs

        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.cache = sys.modules["__main__"].cache
        self.core = sys.modules["__main__"].core

        self.login = sys.modules["__main__"].login
        self.feeds = sys.modules["__main__"].feeds
        self.storage = sys.modules["__main__"].storage
        self.scraper = sys.modules["__main__"].scraper

    # ================================ Subtitle Downloader ====================================
    def downloadSubtitle(self, video={}):
        self.common.log("")
        get = video.get

        style = ""
        result = ""

        if self.settings.getSetting("annotations") == "true" and not "downloadPath" in video:
            xml = self.core._fetchPage({"link": self.urls["annotation_url"] % get('videoid')})
            if xml["status"] == 200 and xml["content"]:
                (result, style) = self.transformAnnotationToSSA(xml["content"])

        if self.settings.getSetting("lang_code") != "0":
            subtitle_url = self.getSubtitleUrl(video)

            if not subtitle_url and self.settings.getSetting("transcode") == "true":
                    subtitle_url = self.getTranscriptionUrl(video)

            if subtitle_url:
                xml = self.core._fetchPage({"link": subtitle_url})
                if xml["status"] == 200 and xml["content"]:
                    result += self.transformSubtitleXMLtoSRT(xml["content"])

        if len(result) > 0:
            result = "[Script Info]\r\n; This is a Sub Station Alpha v4 script.\r\n; For Sub Station Alpha info and downloads,\r\n; go to http://www.eswat.demon.co.uk/\r\n; or email kotus@eswat.demon.co.uk\r\nTitle: Auto Generated\r\nScriptType: v4.00\r\nCollisions: Normal\r\nPlayResY: 1280\r\nPlayResX: 800\r\n\r\n[V4 Styles]\r\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding\r\nStyle: Default,Arial,80,&H00FFFFFF&,65535,65535,&00000000&,-1,0,1,3,2,2,0,0,0,0,0\r\nStyle: speech,Arial,60,0,65535,65535,&H4BFFFFFF&,0,0,3,1,0,1,0,0,0,0,0\r\nStyle: popup,Arial,60,0,65535,65535,&H4BFFFFFF&,0,0,3,3,0,1,0,0,0,0,0\r\nStyle: highlightText,Wolf_Rain,60,15724527,15724527,15724527,&H4BFFFFFF&,0,0,1,1,2,2,5,5,0,0,0\r\n" + style + "\r\n[Events]\r\nFormat: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\r\n" + result

            result += "Dialogue: Marked=0,0:00:0.00,0:00:0.00,Default,Name,0000,0000,0000,,\r\n"  # This solves a bug.
            self.saveSubtitle(result, video)
            self.common.log("Done")
            return True

        self.common.log("Failure")
        return False

    def getSubtitleUrl(self, video={}):
        self.common.log("")
        get = video.get
        url = ""

        xml = self.core._fetchPage({"link": self.urls["timed_text_index"] % get('videoid')})

        self.common.log("subtitle index: " + repr(xml["content"]))

        if xml["status"] == 200:
            try:
                dom = parseString(xml["content"])
            except:
                return ""
            entries = dom.getElementsByTagName("track")

            subtitle = ""
            code = ""
            if len(entries) > 0:
                # Fallback to first in list.
                subtitle = entries[0].getAttribute("name").replace(" ", "%20")
                code = entries[0].getAttribute("lang_code")

            lang_code = ["off", "en", "es", "de", "fr", "it", "ja"][int(self.settings.getSetting("lang_code"))]
            for node in entries:
                if node.getAttribute("lang_code") == lang_code:
                    subtitle = node.getAttribute("name").replace(" ", "%20")
                    code = lang_code
                    self.common.log("found subtitle specified: " + subtitle + " - " + code)
                    break

                if node.getAttribute("lang_code") == "en":
                    subtitle = node.getAttribute("name").replace(" ", "%20")
                    code = "en"
                    self.common.log("found subtitle default: " + subtitle + " - " + code)

            if code:
                url = self.urls["close_caption_url"] % (get("videoid"), subtitle, code)

        self.common.log("found subtitle url: " + repr(url))
        return url

    def saveSubtitle(self, result, video={}):
        self.common.log("")
        get = video.get

        filename = ''.join(c for c in self.common.makeUTF8(video['Title']) if c not in self.utils.INVALID_CHARS) + "-[" + get('videoid') + "]" + ".ssa"
        
        filename = filename.encode("ascii", "ignore")

        path = os.path.join(self.xbmc.translatePath(self.settings.getAddonInfo("profile")).decode("utf-8"), filename)

        w = self.storage.openFile(path, "wb")
        w.write(result.encode("utf-8", "ignore"))
        w.close()

        if "downloadPath" in video:
            self.xbmcvfs.rename(path, os.path.join(video["downloadPath"], filename))

    def getTranscriptionUrl(self, video={}):
        self.common.log("")
        get = video.get
        trans_url = ""
        if "ttsurl" in video:
            if len(video["ttsurl"]) > 0:
                trans_url = urllib.unquote(video["ttsurl"]).replace("\\", "") + "&type=trackformat=1&lang=en&kind=asr&name=&v=" + get("videoid")
                if self.settings.getSetting("lang_code") > 1:  # 1 == en
                    lang_code = ["off", "en", "es", "de", "fr", "it", "ja"][int(self.settings.getSetting("lang_code"))]
                    trans_url += "&tlang=" + lang_code
        return trans_url

    def simpleReplaceHTMLCodes(self, str):
        str = str.strip()
        str = str.replace("&amp;", "&")
        str = str.replace("&quot;", '"')
        str = str.replace("&hellip;", "...")
        str = str.replace("&gt;", ">")
        str = str.replace("&lt;", "<")
        str = str.replace("&#39;", "'")
        return str

    def transformSubtitleXMLtoSRT(self, xml):
        self.common.log("")
        dom = parseString(xml)
        entries = dom.getElementsByTagName("text")

        result = ""

        for node in entries:
            if node:
                if node.firstChild:
                    if node.firstChild.nodeValue:
                        text = self.simpleReplaceHTMLCodes(node.firstChild.nodeValue).replace("\n", "\\n")
                        start = ""

                        if node.getAttribute("start"):
                            start = str(datetime.timedelta(seconds=float(node.getAttribute("start")))).replace("000", "")
                            if (start.find(".") == -1):
                                start += ".000"

                        dur = ""
                        if node.getAttribute("dur"):
                            dur = str(datetime.timedelta(seconds=float(node.getAttribute("start")) + float(node.getAttribute("dur")))).replace("000", "")
                            if (dur.find(".") == -1):
                                dur += ".000"

                        if start and dur:
                            result += "Dialogue: Marked=%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n" % ("0", start, dur, "Default", "Name", "0000", "0000", "0000", "", text)

        return result

    def transformColor(self, color):
        self.common.log("Color: %s - len: %s" % (color, len(color)), 3)
        if color:
            color = hex(int(color))
            color = str(color)
            color = color[2:]
            self.common.log("Color: %s - len: %s" % (color, len(color)), 5)
            if color == "0":
                color = "000000"
            if len(color) == 4:
                color = "00" + color
            if len(color) == 6:
                color = color[4:6] + color[2:4] + color[0:2]

        self.common.log("Returning color: %s - len: %s" % (color, len(color)), 5)
        return color

    def transformAlpha(self, alpha):
        self.common.log("Alpha: %s - len: %s" % (alpha, len(alpha)), 5)
        if not alpha or alpha == "0" or alpha == "0.0":
            alpha = "-1"  # No background.
        else:
            # YouTube and SSA have inverted alphas.
            alpha = int(float(alpha) * 256)
            alpha = hex(256 - alpha)
            alpha = alpha[2:]

        self.common.log("Alpha: %s - len: %s" % (alpha, len(alpha)), 5)
        return alpha

    def transformAnnotationToSSA(self, xml):
        self.common.log("")
        dom = parseString(xml)
        entries = dom.getElementsByTagName("annotation")
        result = ""
        ssa_fixes = []
        style_template = "Style: annot%s,Arial,%s,&H%s&,&H%s&,&H%s&,&H%s&,0,0,3,3,0,1,0,0,0,0,0\r\n"
        styles_count = 0
        append_style = ""
        for node in entries:
            if node:
                stype = node.getAttribute("type")
                style = node.getAttribute("style")
                self.common.log("stype : " + stype, 5)
                self.common.log("style : " + style, 5)

                if stype == "highlight":
                    linkt = self.core._getNodeAttribute(node, "url", "type", "")
                    linkv = self.core._getNodeAttribute(node, "url", "value", "")
                    if linkt == "video":
                        self.common.log("Reference to video : " + linkv)
                elif node.firstChild:
                    self.common.log("node.firstChild: %s - value : %s" % (repr(node.firstChild), repr(self.core._getNodeValue(node, "TEXT", ""))), 5)
                    text = self.core._getNodeValue(node, "TEXT", "")
                    if text:
                        text = self.common.replaceHTMLCodes(text)
                        start = ""

                        if style == "popup":
                            cnode = node.getElementsByTagName("rectRegion")
                        elif style == "speech":
                            cnode = node.getElementsByTagName("anchoredRegion")
                        elif style == "higlightText":
                            cnode = False
                        else:
                            cnode = False

                        snode = node.getElementsByTagName("appearance")
                        ns_fsize = 60
                        self.common.log("snode: %s" % snode, 5)
                        if snode:
                            if snode.item(0).hasAttribute("textSize"):
                                ns_fsize = int(1.2 * (1280 * float(snode.item(0).getAttribute("textSize")) / 100))
                            else:
                                ns_fsize = 60
                            ns_fcolor = snode.item(0).getAttribute("fgColor")
                            ns_fcolor = self.transformColor(ns_fcolor)

                            ns_bcolor = snode.item(0).getAttribute("bgColor")
                            ns_bcolor = self.transformColor(ns_bcolor)

                            ns_alpha = snode.item(0).getAttribute("bgAlpha")
                            ns_alpha = self.transformAlpha(ns_alpha)

                            append_style += style_template % (styles_count, ns_fsize, ns_fcolor, ns_fcolor, ns_fcolor, ns_alpha + ns_bcolor)
                            style = "annot" + str(styles_count)
                            styles_count += 1

                        start = False
                        end = False
                        if cnode:
                            if cnode.item(0):
                                start = cnode.item(0).getAttribute("t")

                            if cnode.item(1):
                                end = cnode.item(1).getAttribute("t")

                        self.common.log("start: %s - end: %s - style: %s" % (start, end, style), 5)
                        if start and end and style != "highlightText":
                            marginV = 1280 * float(cnode.item(0).getAttribute("y")) / 100
                            marginV += 1280 * float(cnode.item(0).getAttribute("h")) / 100
                            marginV = 1280 - int(marginV)
                            marginV += 5
                            marginL = int((800 * float(cnode.item(0).getAttribute("x")) / 100))
                            marginL += 5
                            marginR = 800 - marginL - int((800 * float(cnode.item(0).getAttribute("w")) / 100)) - 15
                            if marginR < 0:
                                marginR = 0
                            result += "Dialogue: Marked=%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n" % ("0", start, end, style, "Name", marginL, marginR, marginV, "", text)
                            ssa_fixes.append([start, end])
                else:
                    self.common.log("wrong type")
        # Fix errors in the SSA specs.
        if len(ssa_fixes) > 0:
            for a_start, a_end in ssa_fixes:
                for b_start, b_end in ssa_fixes:
                    if time.strptime(a_end[0:a_end.rfind(".")], "%H:%M:%S") < time.strptime(b_start[0:b_start.rfind(".")], "%H:%M:%S"):
                        result += "Dialogue: Marked=0,%s,%s,Default,Name,0000,0000,0000,,\r\n" % (a_end, b_start)

        self.common.log("Done : " + repr((result, append_style)), 5)
        return (result, append_style)

    def addSubtitles(self, video={}):
        get = video.get
        self.common.log("fetching subtitle if available")

        filename = ''.join(c for c in self.common.makeUTF8(video['Title']) if c not in self.utils.INVALID_CHARS) + "-[" + get('videoid') + "]" + ".ssa"

        filename = filename.encode("ascii", "ignore")

        download_path = os.path.join(self.settings.getSetting("downloadPath").decode("utf-8"), filename)
        path = os.path.join(self.xbmc.translatePath(self.settings.getAddonInfo("profile")).decode("utf-8"), filename)

        set_subtitle = False
        if self.xbmcvfs.exists(download_path):
            path = download_path
            set_subtitle = True
        elif self.xbmcvfs.exists(path):
            set_subtitle = True
        elif self.downloadSubtitle(video):
            set_subtitle = True

        self.common.log("Done trying to locate: " + path, 4)
        if self.xbmcvfs.exists(path) and not "downloadPath" in video and set_subtitle:
            player = self.xbmc.Player()

            i = 0
            while not player.isPlaying():
                i += 1
                self.common.log("Waiting for playback to start ")
                time.sleep(1)
                if i > 10:
                    break

            self.xbmc.Player().setSubtitles(path)
            self.common.log("added subtitle %s to playback" % path)

    # ================================ Video Playback ====================================

    def playVideo(self, params={}):
        self.common.log(repr(params), 3)
        get = params.get

        (video, status) = self.getVideoObject(params)

        if status != 200:
            self.common.log("construct video url failed contents of video item " + repr(video))
            self.utils.showErrorMessage(self.language(30603), video["apierror"], status)
            return False

        listitem = self.xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url'])

        listitem.setInfo(type='Video', infoLabels=video)

        self.common.log("Playing video: " + repr(video['Title']) + " - " + repr(get('videoid')) + " - " + repr(video['video_url']))

        self.xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

        if self.settings.getSetting("lang_code") != "0" or self.settings.getSetting("annotations") == "true":
            self.addSubtitles(video)

        if (get("watch_later") == "true" and get("playlist_entry_id")):
            self.common.log("removing video from watch later playlist")
            self.core.remove_from_watch_later(params)

        self.storage.storeValue("vidstatus-" + video['videoid'], "7")

    def getVideoUrlMap(self, pl_obj, video={}):
        self.common.log(repr(pl_obj))
        links = {}
        video["url_map"] = "true"

        html = ""
        if "fmt_stream_map" in pl_obj["args"]:
            html = pl_obj["args"]["fmt_stream_map"]

        if len(html) == 0 and "url_encoded_fmt_stream_map" in pl_obj["args"]:
            html = urllib.unquote(pl_obj["args"]["url_encoded_fmt_stream_map"])

        if len(html) == 0 and"fmt_url_map" in  pl_obj["args"]:
            html = pl_obj["args"]["fmt_url_map"]

        html = urllib.unquote_plus(html)

        if "liveplayback_module" in pl_obj["args"]:
            video["live_play"] = "true"

        fmt_url_map = [html]
        if html.find("|") > -1:
            fmt_url_map = html.split('|')
        elif html.find(",url=") > -1:
            fmt_url_map = html.split(',url=')
        elif html.find("&conn=") > -1:
            video["stream_map"] = "true"
            fmt_url_map = html.split('&conn=')

        if len(fmt_url_map) > 0:
            for index, fmt_url in enumerate(fmt_url_map):
                if fmt_url.find("&url") > -1:
                    self.common.log("Searching for fmt_url_map : " + repr(fmt_url))
                    fmt_url = fmt_url.split("&url")
                    fmt_url_map += [fmt_url[1]]
                    fmt_url = fmt_url[0]

                if (len(fmt_url) > 7 and fmt_url.find("&") > 7):
                    quality = "5"
                    final_url = fmt_url.replace(" ", "%20").replace("url=", "")

                    if (final_url.rfind(';') > 0):
                        final_url = final_url[:final_url.rfind(';')]

                    if (final_url.rfind(',') > final_url.rfind('&id=')):
                        final_url = final_url[:final_url.rfind(',')]
                    elif (final_url.rfind(',') > final_url.rfind('/id/') and final_url.rfind('/id/') > 0):
                        final_url = final_url[:final_url.rfind('/')]

                    if (final_url.rfind('itag=') > 0):
                        quality = final_url[final_url.rfind('itag=') + 5:]
                        if quality.find('&') > -1:
                            quality = quality[:quality.find('&')]
                        if quality.find(',') > -1:
                            quality = quality[:quality.find(',')]
                    elif (final_url.rfind('/itag/') > 0):
                        quality = final_url[final_url.rfind('/itag/') + 6:]

                    if final_url.find("&type") > 0:
                        final_url = final_url[:final_url.find("&type")]
                    if self.settings.getSetting("preferred") == "false":
                        pos = final_url.find("://")
                        fpos = final_url.find("fallback_host")
                        if pos > -1 and fpos > -1:
                            host = final_url[pos + 3:]
                            if host.find("/") > -1:
                                host = host[:host.find("/")]
                            fmt_fallback = final_url[fpos + 14:]
                            if fmt_fallback.find("&") > -1:
                                fmt_fallback = fmt_fallback[:fmt_fallback.find("&")]
                            self.common.log("Swapping cached host [%s] and fallback host [%s] " % (host, fmt_fallback), 5)
                            final_url = final_url.replace(host, fmt_fallback)
                            final_url = final_url.replace("fallback_host=" + fmt_fallback, "fallback_host=" + host)

                    # Extract RTMP variables
                    if final_url.find("rtmp") > -1 and index > 0:
                        if "url" in pl_obj:
                            final_url += " swfurl=" + pl_obj["url"] + " swfvfy=1"

                        playpath = False
                        if final_url.find("stream=") > -1:
                            playpath = final_url[final_url.find("stream=") + 7:]
                            if playpath.find("&") > -1:
                                playpath = playpath[:playpath.find("&")]
                        else:
                            playpath = fmt_url_map[index - 1]

                        if playpath:
                            if "ptk" in pl_obj["args"] and "ptchn" in pl_obj["args"]:
                                final_url += " playpath=" + playpath + "?ptchn=" + pl_obj["args"]["ptchn"] + "&ptk=" + pl_obj["args"]["ptk"]

                    links[int(quality)] = final_url.replace('\/', '/')

        self.common.log("done " + repr(links))
        return links

    def getInfo(self, params):
        get = params.get
        video = self.cache.get("videoidcache" + get("videoid"))
        if len(video) > 0:
            self.common.log("returning cache ")
            return (eval(video), 200)

        result = self.core._fetchPage({"link": self.urls["video_info"] % get("videoid"), "api": "true"})

        if result["status"] == 200:
            video = self.core.getVideoInfo(result["content"], params)

            if len(video) == 0:
                self.common.log("- Couldn't parse API output, YouTube doesn't seem to know this video id?")
                video = {}
                video["apierror"] = self.language(30608)
                return (video, 303)
        else:
            self.common.log("- Got API Error from YouTube!")
            video = {}
            video["apierror"] = result["content"]

            return (video, 303)

        video = video[0]
        self.cache.set("videoidcache" + get("videoid"), repr(video))
        return (video, result["status"])

    def selectVideoQuality(self, links, params):
        get = params.get
        link = links.get
        video_url = ""

        self.common.log("")

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
        if hd_quality > 2:
            if (link(37)):
                video_url = link(37)

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
                self.common.log("- Missing fmt_value: " + repr(fmt_key))

        if hd_quality == 0 and not get("quality"):
            return self.userSelectsVideoQuality(params, links)

        if not len(video_url) > 0:
            self.common.log("- construct_video_url failed, video_url not set")
            return video_url

        if get("proxy"):
            proxy = get("proxy")
            video_url = proxy + urllib.quote(video_url) + " |Referer=" + proxy[:proxy.rfind("/")]

        if get("action") != "download":
            video_url += " | " + self.common.USERAGENT

        self.common.log("Done")
        return video_url

    def userSelectsVideoQuality(self, params, links):
        get = params.get
        link = links.get
        quality_list = []
        choices = []

        if link(37):
            quality_list.append((37, "1080p"))

        if link(22):
            quality_list.append((22, "720p"))
        elif link(45):
            quality_list.append((45, "720p"))

        if link(35):
            quality_list.append((35, "480p"))
        elif link(44):
            quality_list.append((44, "480p"))

        if link(18):
            quality_list.append((18, "380p"))

        if link(34):
            quality_list.append((34, "360p"))
        elif link(43):
            quality_list.append((43, "360p"))

        if link(5):
            quality_list.append((5, "240p"))
        if link(17):
            quality_list.append((17, "144p"))

        if link(38) and False:
            quality_list.append((37, "2304p"))

        for (quality, message) in quality_list:
            choices.append(message)

        dialog = self.xbmcgui.Dialog()
        selected = dialog.select(self.language(30518), choices)

        if selected > -1:
            (quality, message) = quality_list[selected]
            return link(quality)

        return ""

    def checkLocalFileSource(self, get, status, video):
        result = ""
        if (get("action", "") != "download"):
            path = self.settings.getSetting("downloadPath")
            filename = ''.join(c for c in video['Title'].decode("utf-8") if c not in self.utils.INVALID_CHARS) + "-[" + get('videoid') + "]" + ".mp4"
            path = os.path.join(path.decode("utf-8"), filename)
            try:
                if self.xbmcvfs.exists(path):
                    result = path
            except:
                self.common.log("attempt to locate local file failed with unknown error, trying youtube instead")
        return result

    def getVideoObject(self, params):
        self.common.log(repr(params))
        get = params.get

        links = []
        (video, status) = self.getInfo(params)

        if status != 200:
            video['apierror'] = self.language(30618)
            return (video, 303)

        #Check if file has been downloaded locally and use that as a source instead
        video_url = self.checkLocalFileSource(get, status, video)
        if video_url:
            video['video_url'] = video_url
            return (video, 200)

        (links, video) = self._getVideoLinks(video, params)

        if not links and self.settings.getSetting("proxy"):
            params["proxy"] = self.settings.getSetting("proxy")
            (links, video) = self._getVideoLinks(video, params)

        if links:
            video["video_url"] = self.selectVideoQuality(links, params)
            if video["video_url"] == "":
                video['apierror'] = self.language(30618)
                status = 303
        else:
            status = 303
            vget = video.get
            if not "apierror" in video:
                if vget("live_play"):
                    video['apierror'] = self.language(30612)
                elif vget("stream_map"):
                    video['apierror'] = self.language(30620)
                else:
                    video['apierror'] = self.language(30618)

        self.common.log("Done : " + repr(status))
        return (video, status)

    def _convertFlashVars(self, html):
        self.common.log(repr(html))
        obj = {"PLAYER_CONFIG": {"args": {}}}
        temp = html.split("&")
        for item in temp:
            self.common.log(item, 9)
            it = item.split("=")
            self.common.log(it, 9)
            obj["PLAYER_CONFIG"]["args"][it[0]] = urllib.unquote_plus(it[1])
        return obj

    def _getVideoLinks(self, video, params):
        self.common.log("trying website: " + repr(params))

        get = params.get
        #vget = video.get
        player_object = {}
        links = []
        fresult = False

        if get("proxy"):
            result = self.core._fetchPage({"link": self.urls["video_stream"] % get("videoid"), "proxy": get("proxy")})
        else:
            result = self.core._fetchPage({"link": self.urls["video_stream"] % get("videoid")})

        if result["status"] == 200:
            start = result["content"].find("yt.playerConfig = ")
            if start > -1:
                self.common.log("Found player_config", 4)
                start = start + len("yt.playerConfig = ")
                end = result["content"].find("};", start) + 1
                data = result["content"][start: end]
                if len(data) > 0:
                    data = data.replace("\\/", "/")
                    player_object = json.loads('{ "PLAYER_CONFIG" : ' + data + "}" )
                    self.common.log("player_object " + repr(player_object), 4)
            else:
                self.common.log("Using flashvars")
                data = result["content"].replace("\n", "").replace("\u0026", "&").replace("&amp;", "&").replace('\\"', '"')
                data = re.findall('flashvars="(.*?)"', data)
                src = self.common.parseDOM(result["content"], "embed", attrs={"id": "movie_player"}, ret="src")
                self.common.log(repr(data) + " - " + repr(src))
                if len(data) > 0 and len(src) > 0:
                    self.common.log("Using flashvars converting", 4)
                    data = data[0].replace("\n", "")
                    player_object = self._convertFlashVars(data)
                    if "PLAYER_CONFIG" in player_object:
                        player_object["PLAYER_CONFIG"]["url"] = src[0]

        elif get("no_embed", "false") == "false":
            self.common.log("Falling back to embed")

            if get("proxy"):
                fresult = self.core._fetchPage({"link": self.urls["embed_stream"] % get("videoid"), "proxy": get("proxy")})
            else:
                fresult = self.core._fetchPage({"link": self.urls["embed_stream"] % get("videoid") })

            # Fallback error reporting
            if fresult["content"].find("status=fail") > -1:
                fresult["status"] = 303
                error = fresult["content"]
                if error.find("reason=") > -1:
                    error = error[error.find("reason=") + len("reason="):]
                    if error.find("%3Cbr") > -1:
                        error = error[:error.find("%3Cbr")]
                video["apierror"] = error.replace("+", " ")

            if fresult["status"] == 200:
                # this gives no player_object["PLAYER_CONFIG"]["url"] for rtmpe...
                player_object = self._convertFlashVars(fresult["content"])

        # Find playback URI
        if "PLAYER_CONFIG" in player_object:
            if "args" in player_object["PLAYER_CONFIG"]:
                if "ttsurl" in player_object["PLAYER_CONFIG"]["args"]:
                    video["ttsurl"] = player_object["PLAYER_CONFIG"]["args"]["ttsurl"]

                links = self.getVideoUrlMap(player_object["PLAYER_CONFIG"], video)

        if len(links) == 0:
            self.common.log("Couldn't find url map or stream map.")

            if not "apierror" in video:
                video['apierror'] = self.core._findErrors(result)
                if not video['apierror'] and fresult:
                    video['apierror'] = self.core._findErrors(fresult)

        self.common.log("Done")
        return (links, video)
