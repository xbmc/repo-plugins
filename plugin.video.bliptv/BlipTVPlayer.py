'''
   BlipTV plugin for XBMC
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
import xml.dom.minidom as minidom


class BlipTVPlayer:
    def __init__(self):
        # BlipTV Playback Feeds
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.storage = sys.modules["__main__"].storage
        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.xbmcvfs = sys.modules["__main__"].xbmcvfs
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin

        self.urls = {"video_info": "http://blip.tv/post/episode-%s?skin=rss"}

    # ================================ Video Playback ====================================
    def playVideo(self, params={}):
        self.common.log("")
        get = params.get

        video = self.getVideoObject(params)

        print repr(video)
        if len(video) == 0:
            self.common.log("construct video url failed contents of video item " + repr(video))
            self.utils.showErrorMessage(self.language(30603), params["apierror"], 303)
            return False

        listitem = self.xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url'])
        listitem.setInfo(type='Video', infoLabels=video)

        self.common.log("Playing video: " + self.common.makeAscii(video['Title']) + " - " + get('videoid') + " - " + video['video_url'])

        self.xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

        self.settings.setSetting("vidstatus-" + get('videoid'), "7")

    def getInfo(self, result={}, params={}):
        self.common.log("")
        video = {}

        if result["status"] == 200:
            video = self.getVideoInfo(result["content"], params)
            if len(video) == 0:
                self.common.log("Couldn't parse API output, BlipTV doesn't seem to know this video id?")
                params["apierror"] = self.language(30608)
        else:
            self.common.log("Got API Error from BlipTV!")
            params["apierror"] = result["content"]

        return video

    def getVideoInfo(self, xml, params={}):
        self.common.log("")
        get = params.get
        dom = minidom.parseString(xml)
        entries = dom.getElementsByTagName("item")

        # find out if there are more pages
        video = {"videoid": get("videoid")}
        for node in entries:
            video['Title'] = self._getNodeValue(node, "title", "Unknown Title").encode('utf-8')  # Convert from utf-16 to combat breakage
            video['Date'] = self._getNodeValue(node, "blip:datestamp", "Unknown Date").encode("utf-8")
            video['user'] = self._getNodeValue(node, "blip:user", "Unknown Name").encode("utf-8")
            video['Studio'] = self._getNodeValue(node, "blip:user", "").encode("utf-8")
            video['Genre'] = self._getNodeValue(node, "blip:category").encode("utf-8")
            video['thumbnail'] = self._getNodeValue(node, "itunes:image", "false")

            overlay = self.storage.retrieveValue("vidstatus-" + get('videoid') )
            if overlay:
                video['Overlay'] = int(overlay)
            break

        return video

    def selectVideoQuality(self, links, params):
        self.common.log("")
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
        if (link("SD")):
            video_url = link("SD")

        if hd_quality > 1:  # <-- 720p
            if (link("720p")):
                video_url = link("720p")
        if hd_quality > 2:  # <-- 1080p
            if (link("1080p")):
                video_url = link("1080p")

        if hd_quality == 0 and not get("quality") and False:  # This is not implemented yet TODO!!!!!!!!!!!!!!!!!!!!!!!!
            return self.userSelectsVideoQuality(params, links)

        if not len(video_url) > 0:
            self.common.log("construct_video_url failed, video_url not set")
            return video_url

        if get("action") != "download":
            video_url += " | " + self.utils.USERAGENT

        self.common.log("Done" )
        return video_url

    def getVideoObject(self, params):
        self.common.log("")
        get = params.get
        video = {}
        links = []
        result = self.common.fetchPage({"link": self.urls["video_info"] % get("videoid")})

        video = self.getInfo(result, params)

        # Check if file has been downloaded locally and use that as a source instead
        if (len(video) > 0 and get("action", "") != "download"):
            self.common.log("QQQ2 : " + repr(video))
            path = self.settings.getSetting("downloadPath")
            path = "%s%s-[%s].mp4" % (path, ''.join(c for c in video['Title'] if c in self.utils.VALID_CHARS), get("videoid"))
            try:
                if self.xbmcvfs.exists(path):
                    video['video_url'] = path
                    return video
            except:
                self.common.log("attempt to locate local file failed with unknown error, trying bliptv instead")

        links = self._getVideoLinks(result, params)
        if links:
            video["video_url"] = self.selectVideoQuality(links, params)
            if video["video_url"] == "":
                params['apierror'] = self.language(30618)
        else:
            params['apierror'] = self.language(30618)

        self.common.log("Done")
        return video

    def _getVideoLinks(self, result, params):
        self.common.log("")
        links = {}

        if result["status"] == 200:
            dom = minidom.parseString(result["content"])
            entries = dom.getElementsByTagName("media:content")
            for node in entries:
                type = node.getAttribute("type")
                if type.find("video") < 0:
                    continue
                quality = "SD"
                url = node.getAttribute("url")
                height = int(node.getAttribute("height"))

                if height > 720:
                    quality = "1080p"
                elif height == 720:
                    quality = "720p"

                links[quality] = url

        self.common.log(repr(links))

        return links

    def _getNodeAttribute(self, node, tag, attribute, default=""):
        if node.getElementsByTagName(tag).item(0):
            if node.getElementsByTagName(tag).item(0).hasAttribute(attribute):
                return node.getElementsByTagName(tag).item(0).getAttribute(attribute)

        return default

    def _getNodeValue(self, node, tag, default=""):
        if node.getElementsByTagName(tag).item(0):
            if node.getElementsByTagName(tag).item(0).firstChild:
                return node.getElementsByTagName(tag).item(0).firstChild.nodeValue

        return default
