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
import re
import os.path
import time
try: import simplejson as json
except ImportError: import json


class YouTubeSubtitleControl():

    urls = {}
    urls['timed_text_index'] = "http://www.youtube.com/api/timedtext?type=list&v=%s"
    urls['close_caption_url'] = "http://www.youtube.com/api/timedtext?type=track&v=%s&lang=%s"
    urls['annotation_url'] = "http://www.youtube.com/annotations/read2?video_id=%s&feat=TC"

    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcvfs = sys.modules["__main__"].xbmcvfs

        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.core = sys.modules["__main__"].core

        self.dbg = sys.modules["__main__"].dbg
        self.settings = sys.modules["__main__"].settings
        self.storage = sys.modules["__main__"].storage

    # ================================ Subtitle Downloader ====================================
    def downloadSubtitle(self, video={}):
        self.common.log(u"")
        get = video.get

        style = u""
        result = u""

        if self.settings.getSetting("annotations") == "true" and not "download_path" in video:
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
            self.common.log(u"Done")
            return True

        self.common.log(u"Failure")
        return False

    def getSubtitleUrl(self, video={}):
        self.common.log(u"")
        get = video.get
        url = ""

        xml = self.core._fetchPage({"link": self.urls["timed_text_index"] % get('videoid')})

        self.common.log(u"subtitle index: " + repr(xml["content"]))
        self.common.log(u"CONTENT TYPE1: " + repr(type(xml["content"])))

        if xml["status"] == 200:
            subtitle = ""
            code = ""
            codelist = self.common.parseDOM(xml["content"], "track", ret="lang_code")
            sublist = self.common.parseDOM(xml["content"], "track", ret="name")
            lang_original = self.common.parseDOM(xml["content"], "track", ret="lang_original")
            if len(sublist) != len(codelist) and len(sublist) != len(lang_original):
                self.common.log(u"Code list and sublist length mismatch: " + repr(codelist) + " - " + repr(sublist))
                return ""

            if len(codelist) > 0:
                # Fallback to first in list.
                subtitle = sublist[0].replace(u" ", u"%20")
                code = codelist[0]

            lang_code = ["off", "en", "es", "de", "fr", "it", "ja"][int(self.settings.getSetting("lang_code"))]
            self.common.log(u"selected language: " + repr(lang_code))
            if True:
                for i in range(0, len(codelist)):
                    data = codelist[i].lower()
                    if data.find("-") > -1:
                        data = data[:data.find("-")]

                    if codelist[i].find(lang_code) > -1:
                        subtitle = sublist[i].replace(" ", "%20")
                        code = codelist[i]
                        self.common.log(u"found subtitle specified: " + subtitle + " - " + code)
                        break

                    if codelist[i].find("en") > -1:
                        subtitle = sublist[i].replace(" ", "%20")
                        code = "en"
                        self.common.log(u"found subtitle default: " + subtitle + " - " + code)

            if code:
                url = self.urls["close_caption_url"] % (get("videoid"), code)
                if len(subtitle) > 0:
                    url += "&name=" + subtitle


        self.common.log(u"found subtitle url: " + repr(url))
        return url

    def getSubtitleFileName(self, video):
        get = video.get
        lang_code = ["off", "en", "es", "de", "fr", "it", "ja"][int(self.settings.getSetting("lang_code"))]
        filename = ''.join(c for c in self.common.makeUTF8(video['Title']) if c not in self.utils.INVALID_CHARS) + "-[" + get('videoid') + "]-" + lang_code.upper() + ".ssa"
        filename = filename.encode("ascii", "ignore")
        return filename

    def saveSubtitle(self, result, video={}):
        self.common.log(repr(type(result)))
        filename = self.getSubtitleFileName(video)

        path = os.path.join(self.xbmc.translatePath(self.settings.getAddonInfo("profile")).decode("utf-8"), filename)

        w = self.storage.openFile(path, "w")
        try:
            w.write(result.encode("utf-8")) # WTF, didn't have to do this before, did i?
        except:
            w.write(result)
            self.common.log(u"NOT utf-8 WRITE!!!: " + path + " - " + repr(result))
            time.sleep(20)

        w.close()

        if "download_path" in video:
            self.xbmcvfs.rename(path, os.path.join(video["download_path"], filename))


    def getTranscriptionUrl(self, video={}):
        self.common.log(u"")
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

    def convertSecondsToTimestamp(self, seconds):
        self.common.log(u"", 3)
        hours = str(int(seconds / 3600))
        seconds = seconds % 3600

        minutes = str(int(seconds/60))
        if len(minutes) == 1:
            minutes = "0" + minutes

        seconds = str(seconds % 60)
        if len(seconds) == 1:
            seconds = "0" + seconds

        self.common.log(u"Done", 3)
        return "%s:%s:%s" % (hours, minutes, seconds)

    def transformSubtitleXMLtoSRT(self, xml):
        self.common.log(u"")

        result = u""
        for node in self.common.parseDOM(xml, "text", ret=True):
            text = self.common.parseDOM(node, "text")[0]
            text = self.simpleReplaceHTMLCodes(text).replace("\n", "\\n")
            start = float(self.common.parseDOM(node, "text", ret="start")[0])
            duration = self.common.parseDOM(node, "text", ret="dur")
            end = start + 0.1
            if len(duration) > 0:
                end = start + float(duration[0])

            start = self.convertSecondsToTimestamp(start)
            end = self.convertSecondsToTimestamp(end)

            if start and end:
                result += "Dialogue: Marked=%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n" % ("0", start, end, "Default", "Name", "0000", "0000", "0000", "", text)

        return result

    def transformColor(self, color):
        self.common.log(u"Color: %s - len: %s" % (color, len(color)), 3)
        if color:
            color = hex(int(color))
            color = str(color)
            color = color[2:]
            self.common.log(u"Color: %s - len: %s" % (color, len(color)), 5)
            if color == "0":
                color = "000000"
            if len(color) == 4:
                color = "00" + color
            if len(color) == 6:
                color = color[4:6] + color[2:4] + color[0:2]

        self.common.log(u"Returning color: %s - len: %s" % (color, len(color)), 5)
        return color

    def transformAlpha(self, alpha):
        self.common.log(u"Alpha: %s - len: %s" % (alpha, len(alpha)), 5)
        if not alpha or alpha == "0" or alpha == "0.0":
            alpha = "-1"  # No background.
        else:
            # YouTube and SSA have inverted alphas.
            alpha = int(float(alpha) * 256)
            alpha = hex(256 - alpha)
            alpha = alpha[2:]

        self.common.log(u"Alpha: %s - len: %s" % (alpha, len(alpha)), 5)
        return alpha

    def transformAnnotationToSSA(self, xml):
        self.common.log(u"")
        result = u""
        ssa_fixes = []
        style_template = u"Style: annot%s,Arial,%s,&H%s&,&H%s&,&H%s&,&H%s&,0,0,3,3,0,1,0,0,0,0,0\r\n"
        styles_count = 0
        append_style = u""
        entries = self.common.parseDOM(xml, "annotation", ret=True)
        for node in entries:
            if node:
                stype = u"".join(self.common.parseDOM(node, "annotation", ret="type"))
                style = u"".join(self.common.parseDOM(node, "annotation", ret="style"))
                self.common.log(u"stype : " + stype, 5)
                self.common.log(u"style : " + style, 5)

                if stype == "highlight":
                    linkt = "".join(self.common.parseDOM(node, "url", ret="type"))
                    linkv = "".join(self.common.parseDOM(node, "url", ret="value"))
                    if linkt == "video":
                        self.common.log(u"Reference to video : " + linkv)
                elif node.find("TEXT") > -1:
                    text = self.common.parseDOM(node, "TEXT")
                    if len(text):
                        text = self.common.replaceHTMLCodes(text[0])
                        start = ""

                        ns_fsize = 60
                        start = False
                        end = False

                        if style == "popup":
                            cnode = self.common.parseDOM(node, "rectRegion", ret="t")
                            start = cnode[0]
                            end = cnode[1]
                            tmp_y = self.common.parseDOM(node, "rectRegion", ret="y")
                            tmp_h = self.common.parseDOM(node, "rectRegion", ret="h")
                            tmp_x = self.common.parseDOM(node, "rectRegion", ret="x")
                            tmp_w = self.common.parseDOM(node, "rectRegion", ret="w")
                        elif style == "speech":
                            cnode = self.common.parseDOM(node, "anchoredRegion", ret="t")
                            start = cnode[0]
                            end = cnode[1]
                            tmp_y = self.common.parseDOM(node, "anchoredRegion", ret="y")
                            tmp_h = self.common.parseDOM(node, "anchoredRegion", ret="h")
                            tmp_x = self.common.parseDOM(node, "anchoredRegion", ret="x")
                            tmp_w = self.common.parseDOM(node, "anchoredRegion", ret="w")
                        elif style == "higlightText":
                            cnode = False
                        else:
                            cnode = False

                        for snode in self.common.parseDOM(node, "appearance", attrs={"fgColor": ".*?"}, ret=True):
                            ns_fsize = self.common.parseDOM(snode, "appearance", ret="textSize")
                            if len(ns_fsize):
                                ns_fsize = int(1.2 * (1280 * float(ns_fsize[0]) / 100))
                            else:
                                ns_fsize = 60
                            ns_fcolor = self.common.parseDOM(snode, "appearance", ret="fgColor")
                            ns_fcolor = self.transformColor(ns_fcolor[0])

                            ns_bcolor = self.common.parseDOM(snode, "appearance", ret="bgColor")
                            ns_bcolor = self.transformColor(ns_bcolor[0])

                            ns_alpha = self.common.parseDOM(snode, "appearance", ret="bgAlpha")
                            ns_alpha = self.transformAlpha(ns_alpha[0])

                            append_style += style_template % (styles_count, ns_fsize, ns_fcolor, ns_fcolor, ns_fcolor, ns_alpha + ns_bcolor)
                            style = "annot" + str(styles_count)
                            styles_count += 1

                        self.common.log(u"start: %s - end: %s - style: %s" % (start, end, style), 5)
                        if start and end and style != "highlightText":
                            marginV = 1280 * float(tmp_y[0]) / 100
                            marginV += 1280 * float(tmp_h[0]) / 100
                            marginV = 1280 - int(marginV)
                            marginV += 5
                            marginL = int((800 * float(tmp_x[0]) / 100))
                            marginL += 5
                            marginR = 800 - marginL - int((800 * float(tmp_w[0]) / 100)) - 15
                            if marginR < 0:
                                marginR = 0
                            result += "Dialogue: Marked=%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n" % ("0", start, end, style, "Name", marginL, marginR, marginV, "", text)
                            ssa_fixes.append([start, end])

        # Fix errors in the SSA specs.
        if len(ssa_fixes) > 0:
            for a_start, a_end in ssa_fixes:
                for b_start, b_end in ssa_fixes:
                    if time.strptime(a_end[0:a_end.rfind(".")], "%H:%M:%S") < time.strptime(b_start[0:b_start.rfind(".")], "%H:%M:%S"):
                        result += "Dialogue: Marked=0,%s,%s,Default,Name,0000,0000,0000,,\r\n" % (a_end, b_start)

        self.common.log(u"Done : " + repr((result, append_style)),5)
        return (result, append_style)

    def addSubtitles(self, video={}):
        get = video.get
        self.common.log(u"fetching subtitle if available")

        filename = self.getSubtitleFileName(video)

        download_path = os.path.join(self.settings.getSetting("download_path").decode("utf-8"), filename)
        path = os.path.join(self.xbmc.translatePath(self.settings.getAddonInfo("profile")).decode("utf-8"), filename)

        set_subtitle = False
        if self.xbmcvfs.exists(download_path):
            path = download_path
            set_subtitle = True
        elif self.xbmcvfs.exists(path):
            set_subtitle = True
        elif self.downloadSubtitle(video):
            set_subtitle = True

        self.common.log(u"Done trying to locate: " + path, 4)
        if self.xbmcvfs.exists(path) and not "download_path" in video and set_subtitle:
            player = self.xbmc.Player()

            i = 0
            while not player.isPlaying():
                i += 1
                self.common.log(u"Waiting for playback to start ")
                time.sleep(1)
                if i > 10:
                    break

            self.xbmc.Player().setSubtitles(path)
            self.common.log(u"added subtitle %s to playback" % path)

    def getLocalFileSource(self, params, video):
        get = params.get
        result = u""
        if (get("action", "") != "download"):
            path = self.settings.getSetting("download_path")
            filename = u"".join(c for c in self.common.makeUTF8(video['Title']) if c not in self.utils.INVALID_CHARS) + u"-[" + get('videoid') + u"]" + u".mp4"
            path = os.path.join(path.decode("utf-8"), filename)
            try:
                if self.xbmcvfs.exists(path):
                    result = path
            except:
                self.common.log(u"failed to locate local subtitle file, trying youtube instead")
        return result
