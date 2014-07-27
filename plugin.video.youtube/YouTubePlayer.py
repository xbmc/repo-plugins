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

import re
import sys
import cgi
import urllib
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

        self.algoCache = {}

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

    def normalizeUrl(self, url):
        if url[0:2] == "//":
            url = "http:" + url
        return url

    def extractFlashVars(self, data, assets=0):
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
            if assets:
                flashvars = data["assets"]
            else:
                flashvars = data["args"]

        for k in ["html", "css", "js"]:
            if k in flashvars:
                flashvars[k] = self.normalizeUrl(flashvars[k])

        self.common.log("Step2: " + repr(data), 4)

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
                flashvars = self.extractFlashVars(result[u"content"], 1)
                url = url + u"&signature=" + self.decrypt_signature(sig, flashvars[u"js"])

            links[key] = url

        return links

    def _extractVarLocalFuns(self, match):
        varName, objBody = match.groups()
        output = ''
        for func in objBody.split( '},' ):
            output += re.sub(
                r'^([^:]+):function\(([^)]*)\)',
                r'function %s__\1(\2,*args)' % varName,
                func
            ) + '\n'
        return output

    def _jsToPy(self, jsFunBody):
        self.common.log(jsFunBody)
        pythonFunBody = re.sub(r'var ([^=]+)={(.*?)}};', self._extractVarLocalFuns, jsFunBody)
        pythonFunBody = re.sub(r'function (\w*)\$(\w*)', r'function \1_S_\2', pythonFunBody)
        pythonFunBody = pythonFunBody.replace('function', 'def').replace('{', ':\n\t').replace('}', '').replace(';', '\n\t').replace('var ', '')
        pythonFunBody = pythonFunBody.replace('.reverse()', '[::-1]')

        lines = pythonFunBody.split('\n')
        for i in range(len(lines)):
            # a.split("") -> list(a)
            match = re.search('(\w+?)\.split\(""\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'list(' + match.group(1)  + ')')
            # a.length -> len(a)
            match = re.search('(\w+?)\.length', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'len(' + match.group(1)  + ')')
            # a.slice(3) -> a[3:]
            match = re.search('(\w+?)\.slice\((\w+?)\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), match.group(1) + ('[%s:]' % match.group(2)) )

            # a.join("") -> "".join(a)
            match = re.search('(\w+?)\.join\(("[^"]*?")\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), match.group(2) + '.join(' + match.group(1) + ')' )

            # a.splice(b,c) -> del a[b:c]
            match = re.search('(\w+?)\.splice\(([^,]+),([^)]+)\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'del ' + match.group(1) + '[' + match.group(2) + ':' + match.group(3) + ']' )

        pythonFunBody = "\n".join(lines)
        pythonFunBody = re.sub(r'(\w+)\.(\w+)\(', r'\1__\2(', pythonFunBody)
        pythonFunBody = re.sub(r'([^=])(\w+)\[::-1\]', r'\1\2.reverse()', pythonFunBody)
        return pythonFunBody

    def _getLocalFunBody(self, funName, playerData):
        # get function body
        funName=funName.replace('$', '\\$')
        match = re.search('(function %s\([^)]+?\){[^}]+?})' % funName, playerData)
        if match:
            # return jsFunBody
            return match.group(1)
        return ''

    def _getAllLocalSubFunNames(self, mainFunBody):
        match = re.compile('[ =(,]([\w\$_]+)\([^)]*\)').findall( mainFunBody )
        if len(match):
            # first item is name of main function, so omit it
            funNameTab = set( match[1:] )
            return funNameTab
        return set()

    def decrypt_signature(self, s, playerUrl):
        self.common.log("decrypt_signature sign_len[%d] playerUrl[%s]" % (len(s), playerUrl) )

        # use algoCache
        if playerUrl not in self.algoCache:
            # get player HTML 5 sript
            res = self.core._fetchPage({u"link": playerUrl})
            playerData = res["content"]
            try:
                playerData = playerData.decode('utf-8', 'ignore')
            except Exception as ex:
                self.common.log("Error: " + str(sys.exc_info()[0]) + " - " + str(ex))
                self.common.log('Unable to download playerUrl webpage')
                return ''

            # get main function name
            match = re.search("signature=([$a-zA-Z]+)\([^)]\)", playerData)

            if match:
                mainFunName = match.group(1)
                self.common.log('Main signature function name = "%s"' % mainFunName)
            else:
                self.common.log('Can not get main signature function name')
                return ''

            fullAlgoCode = self._getfullAlgoCode( mainFunName, playerData )

            # wrap all local algo function into one function extractedSignatureAlgo()
            algoLines = fullAlgoCode.split('\n')
            for i in range(len(algoLines)):
                algoLines[i] = '\t' + algoLines[i]
            fullAlgoCode  = 'def extractedSignatureAlgo(param):'
            fullAlgoCode += '\n'.join(algoLines)
            fullAlgoCode += '\n\treturn %s(param)' % mainFunName
            fullAlgoCode += '\noutSignature = extractedSignatureAlgo( inSignature )\n'

            # after this function we should have all needed code in fullAlgoCode

            self.common.log( "---------------------------------------" )
            self.common.log( "|    ALGO FOR SIGNATURE DECRYPTION    |" )
            self.common.log( "---------------------------------------" )
            self.common.log( fullAlgoCode                         )
            self.common.log( "---------------------------------------" )

            try:
                algoCodeObj = compile(fullAlgoCode, '', 'exec')
            except:
                self.common.log('decryptSignature compile algo code EXCEPTION')
                return ''
        else:
            # get algoCodeObj from algoCache
            self.common.log('Algo taken from cache')
            algoCodeObj = self.algoCache[playerUrl]

        # for security alow only flew python global function in algo code
        vGlobals = {"__builtins__": None, 'len': len, 'list': list}

        # local variable to pass encrypted sign and get decrypted sign
        vLocals = { 'inSignature': s, 'outSignature': '' }

        # execute prepared code
        try:
            exec( algoCodeObj, vGlobals, vLocals )
        except:
            self.common.log('decryptSignature exec code EXCEPTION')
            exec( algoCodeObj, vGlobals, vLocals )
            return ''

        self.common.log('Decrypted signature = [%s]' % vLocals['outSignature'])
        # if algo seems ok and not in cache, add it to cache
        if playerUrl not in self.algoCache and '' != vLocals['outSignature']:
            self.common.log('Algo from player [%s] added to cache' % playerUrl)
            self.algoCache[playerUrl] = algoCodeObj

        return vLocals['outSignature']

    def _extractLocalVarNames(self, mainFunBody ):
        valid_funcs = ( 'reverse', 'split', 'splice', 'slice', 'join' )
        match = re.compile( r'[; =(,](\w+)\.(\w+)\(' ).findall( mainFunBody )
        local_vars = []
        for name in match:
            if name[1] not in valid_funcs:
                local_vars.append( name[0] )
        self.common.log('Found variable names: ' + str(local_vars))
        return set( local_vars )

    def _getLocalVarObjBody(self, varName, playerData):
        match = re.search( r'var %s={.*?}};' % varName, playerData )
        if match:
            self.common.log('Found variable object: ' + match.group(0))
            return match.group(0)
        return ''

    # Note, this method is using a recursion
    def _getfullAlgoCode( self, mainFunName, playerData, recDepth = 0, allLocalFunNamesTab=[], allLocalVarNamesTab=[] ):
        # Max recursion of 5
        if 5 <= recDepth:
            self.common.log('_getfullAlgoCode: Maximum recursion depth exceeded')
            return

        funBody = self._getLocalFunBody( mainFunName, playerData)
        if '' != funBody:
            funNames = self._getAllLocalSubFunNames(funBody)
            if len(funNames):
                for funName in funNames:
                    funName_=funName.replace('$','_S_')
                    if funName not in allLocalFunNamesTab:
                        funBody=funBody.replace(funName,funName_)
                        allLocalFunNamesTab.append(funName)
                        self.common.log("Add local function %s to known functions" % mainFunName)
                        funBody = self._getfullAlgoCode( funName, playerData, recDepth + 1, allLocalFunNamesTab ) + "\n" + funBody

            varNames = self._extractLocalVarNames(funBody)
            if len(varNames):
                for varName in varNames:
                    self.common.log("Found local var object: " + str(varName))
                    self.common.log("Known vars: " + str(allLocalVarNamesTab))
                    if varName not in allLocalVarNamesTab:
                        self.common.log("Adding local var object %s to known objects" % varName)
                        allLocalVarNamesTab.append(varName)
                        funBody = self._getLocalVarObjBody( varName, playerData ) + "\n" + funBody

            # conver code from javascript to python
            funBody = self._jsToPy(funBody)
            return '\n' + funBody + '\n'
        return funBody

    def getVideoPageFromYoutube(self, get, has_verified = False):
        login = "false"
        verify = ""

        if self.pluginsettings.userHasProvidedValidCredentials():
            login = "true"
            if has_verified:
                verify = u"&has_verified=1"

        page = self.core._fetchPage({u"link": (self.urls[u"video_stream"] % get(u"videoid")) + verify, "login": login})
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
                result = self.getVideoPageFromYoutube(get, True)
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
