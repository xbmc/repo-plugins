import os
import sys
import urllib
import urllib2
import cookielib

import xbmc
import xbmcgui
import xbmcplugin

from elementtree import ElementTree
import danishaddons
import danishaddons.web

URL = 'http://yousee.tv/feeds/player/livetv/%s/'
LOGIN1_URL = 'https://login.yousee.dk'
LOGIN2_URL = 'http://yousee.tv/sso/login'

class YouseeTv:
    def __init__(self):
        self.cookieJar = cookielib.LWPCookieJar()
        self.cookieFile = os.path.join(danishaddons.ADDON_DATA_PATH, 'cookies.lwp')
        if os.path.isfile(self.cookieFile):
            self.cookieJar.load(self.cookieFile, ignore_discard = True, ignore_expires = True)

        opener = urllib2.build_opener(LoginHTTPRedirectHandler, urllib2.HTTPCookieProcessor(self.cookieJar))
        urllib2.install_opener(opener)

        if danishaddons.ADDON.getSetting('username') == '' or danishaddons.ADDON.getSetting('password') == '':
            # username and password is required
            xbmcgui.Dialog().ok(danishaddons.msg(30001), danishaddons.msg(30002), danishaddons.msg(30003))
            danishaddons.ADDON.openSettings()

    def showChannels(self):
        doc = self.loadDocForChannel()
        if doc is not None:
            fanArt = os.path.join(danishaddons.ADDON.getAddonInfo('path'), '/fanart.jpg')

            for channel in doc.findall('channels/channel'):
                name = channel.findtext('name')
                logoLarge = channel.findtext('logo_large')

                item = xbmcgui.ListItem(name, iconImage = logoLarge)
                item.setProperty('Fanart_Image', fanArt)
                url = danishaddons.ADDON_PATH + '?id=' + channel.findtext('id').replace(' ', '%20')
                xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

        xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE, succeeded = doc is not None)

    def playChannel(self, channelId):
        doc = self.loadDocForChannel(channelId)

        if danishaddons.ADDON.getSetting('quality') == '1200':
            streamIdx = 1
        else:
            streamIdx = 0

        streams = doc.findall('server/streams/stream/name')
        if len(streams) == 1:
            stream = streams[0].text
        else:
            stream = streams[streamIdx].text            

        swfUrl = "http://yousee.tv/design/swf/YouSeeVideoPlayer_beta.swf"
        pageUrl = "http://yousee.tv/livetv/"
        tcUrl = doc.findtext('server/url')
        conn = 'S:serverurl:%s' % tcUrl

        rtmpUrl = '%s/%s swfUrl=%s swfVfy=1 pageUrl=%s tcUrl=%s conn=%s' % (tcUrl, stream, swfUrl, pageUrl, tcUrl, conn)
        xbmc.log("Attempting to play url: %s" % rtmpUrl)

        item = xbmcgui.ListItem(doc.findtext('channelname'), thumbnailImage = doc.findtext('channellogo'))
        item.setProperty("IsLive", "true")
        xbmc.Player().play(rtmpUrl, item)

    def login(self):
        username = danishaddons.ADDON.getSetting('username')
        password = danishaddons.ADDON.getSetting('password')

        postData = urllib.urlencode({'Username' : username, 'Password' : password, 'SucessURl' : LOGIN2_URL})
        req = urllib2.Request(LOGIN1_URL, postData)
        res = urllib2.urlopen(req)
        res.close()

        self.cookieJar.save(self.cookieFile, ignore_discard = True, ignore_expires = True)

    def loadDocForChannel(self, slug = 'dr1', retry = False):
        if not self.isLoggedIn():
            self.login()

            # if still not logged in - bail out
            if not self.isLoggedIn():
                xbmcgui.Dialog().ok(danishaddons.msg(30010), danishaddons.msg(30011))
                return None

        try:
            xml = danishaddons.web.downloadUrl(URL % slug)
        except urllib2.URLError:
            # Session expired; retry with a forced login
            if not retry:
                self.cookieJar.clear_session_cookies()
                self.loadDocForChannel(slug, retry = True)
            else:
                xbmcgui.Dialog().ok(danishaddons.msg(30010), danishaddons.msg(30011))
                return None

        doc = ElementTree.fromstring(xml)
        return doc

    def isLoggedIn(self):
        loggedIn = False
        for cookie in self.cookieJar:
            if cookie.name == 'yspro':
                loggedIn = True
                break
        return loggedIn


class LoginHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        # patch url to inject / before parameters to avoid [...].dk?param
        url = headers.getheaders('location')[0].replace('?', '/?')
        new = self.redirect_request(req, fp, code, msg, headers, url)
        return self.parent.open(new)


if __name__ == '__main__':
    danishaddons.init(sys.argv)

    ytv = YouseeTv()
    if danishaddons.ADDON_PARAMS.has_key('id'):
        ytv.playChannel(danishaddons.ADDON_PARAMS['id'])
    else:
        ytv.showChannels()

