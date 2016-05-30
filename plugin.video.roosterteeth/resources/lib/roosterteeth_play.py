#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import re
import requests
import sys
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from roosterteeth_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION

LOGINURL_RT = 'http://roosterteeth.com/login'
LOGINURL_AH = 'http://achievementhunter.com/login'
LOGINURL_FH = 'http://fun.haus/login'
LOGINURL_TK = 'http://theknow.tv/login'
LOGINURL_SA = 'http://screwattack.roosterteeth.com/login'
NEWHLS = 'NewHLS-'
VQ1080P = '1080P'
VQ720P = '720P'
VQ480P = '480P'
VQ360P = '360P'
VQ240P = '240P'


#
# Main class
#
class Main:
    #
    # Init
    #
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        # Get plugin settings
        self.DEBUG = SETTINGS.getSetting('debug')
        self.PREFERRED_QUALITY = SETTINGS.getSetting('quality')
        self.IS_SPONSOR = SETTINGS.getSetting('is_sponsor')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters...
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGNOTICE)
        #
        # Play video...
        #
        self.playVideo()

    #
    # Play video...
    #
    def playVideo(self):
        #
        # Init
        #

        #
        # Get current list item details...
        #
        #title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail_url = xbmc.getInfoImage("list_item.Thumb")
        #studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
        plot = unicode(xbmc.getInfoLabel("list_item.Plot"), "utf-8")
        genre = unicode(xbmc.getInfoLabel("list_item.Genre"), "utf-8")

        #
        # Show wait dialog while parsing data...
        #
        dialog_wait = xbmcgui.DialogProgress()
        dialog_wait.create(LANGUAGE(30100), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        reply = ''
        session = ''
        try:
            # requests is sooooo nice, respect!
            session = requests.Session()

            # get the page that contains the video
            reply = session.get(self.video_page_url)

            # is it a sponsored video?
            if str(reply.text).find('sponsor-only') >= 0 or str(reply.text).find('non-sponsor') >= 0:
                if self.IS_SPONSOR == 'true':
                    try:
                        # we need a NEW (!!!) session
                        session = requests.Session()

                        # get the LOGIN-page
                        if 'achievementhunter.com' in reply.url:
                            reply = session.get(LOGINURL_AH)
                        elif 'fun.haus' in reply.url:
                            reply = session.get(LOGINURL_FH)
                        elif 'theknow.tv' in reply.url:
                            reply = session.get(LOGINURL_TK)
                        elif 'screwattack' in reply.url:
                            reply = session.get(LOGINURL_SA)
                        else:
                            reply = session.get(LOGINURL_RT)

                        if self.DEBUG == 'true':
                            xbmc.log('get login page request, status_code:' + str(reply.status_code))

                        # This is part of the LOGIN page, it contains a token!:
                        #
                        # 	<input name="_token" type="hidden" value="Zu8TRC43VYiTxfn3JnNgiDnTpbQvPv5xWgzFpEYJ">
                        #     <fieldset>
                        #       <h3 class="content-title">Log In</h3>
                        # 	  <label for="username">Username</label>
                        # 	  <input name="username" type="text" value="" id="username">
                        # 	  <label for="password">Password</label>
                        # 	  <input name="password" type="password" value="" id="password">
                        # 	<input type="submit" value="Log in">
                        # 	</fieldset>

                        # get the token
                        soup = BeautifulSoup(reply.text)
                        video_urls = soup.findAll('input', attrs={'name': re.compile("_token")}, limit=1)
                        token = str(video_urls[0]['value'])

                        # set the needed LOGIN-data
                        payload = {'_token': token, 'username': SETTINGS.getSetting('username'),
                                   'password': SETTINGS.getSetting('password')}
                        # post the LOGIN-page with the LOGIN-data, to actually login this session
                        if 'achievementhunter.com' in reply.url: # AH Login
                            reply = session.post(LOGINURL_AH, data=payload)
                        elif 'fun.haus' in reply.url: # FH Login
                            reply = session.post(LOGINURL_FH, data=payload)
                        elif 'theknow.tv' in reply.url: # TK Login
                            reply = session.post(LOGINURL_TK, data=payload)
                        else: # RT Login
                            reply = session.post(LOGINURL_RT, data=payload)

                        if self.DEBUG == 'true':
                            xbmc.log('post login page response, status_code:' + str(reply.status_code))

                        # check that the login was technically ok (status_code 200).
                        # This in itself does NOT mean that the username/password were correct.
                        if reply.status_code == 200:
                            pass
                            # check that the username is in the response. If that's the case, the login was ok
                            # and the username and password in settings are ok.
                            if str(reply.text).find(SETTINGS.getSetting('username')) >= 0:
                                dialog_wait.create("Login Success","Currently looking for videos in '%s'" % self.title)
                                if self.DEBUG == 'true':
                                    xbmc.log('login was successful!')
                                # let's try getting the page again after a login, hopefully it contains a link to
                                # the video now
                                reply = session.get(self.video_page_url)
                                if self.DEBUG == 'true':
                                    xbmc.log("[ADDON] %s v%s (%s) debug mode, Loaded %s" % (ADDON, VERSION, DATE, self.video_page_url))
                            else:
                                try:
                                    dialog_wait.close()
                                    del dialog_wait
                                except:
                                    pass
                                xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30101), LANGUAGE(30102),
                                                    LANGUAGE(30103))
                                exit(1)
                        else:
                            try:
                                dialog_wait.close()
                                del dialog_wait
                            except:
                                pass
                            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30104) % (str(reply.status_code)))
                            exit(1)

                    except urllib2.HTTPError, error:
                        if self.DEBUG == 'true':
                            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                                ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGNOTICE)
                        try:
                            dialog_wait.close()
                            del dialog_wait
                        except:
                            pass
                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (str(error)))
                        exit(1)
                    except:
                        exception = sys.exc_info()[0]
                        if self.DEBUG == 'true':
                            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                                ADDON, VERSION, DATE, "Exception1:", str(exception)), xbmc.LOGNOTICE)
                        try:
                            dialog_wait.close()
                            del dialog_wait
                        except:
                            pass
                        exit(1)

                else:
                    try:
                        dialog_wait.close()
                        del dialog_wait
                    except:
                        pass
                    xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30105))
                    exit(1)

        except urllib2.HTTPError, error:
            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGNOTICE)
                try:
                    dialog_wait.close()
                    del dialog_wait
                except:
                    pass
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (str(error)))
            exit(1)
        except:
            exception = sys.exc_info()[0]
            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "Exception2:", str(exception)), xbmc.LOGNOTICE)
            try:
                dialog_wait.close()
                del dialog_wait
            except:
                pass
            exit(1)

        html_source = reply.text
        html_source = html_source.encode('utf-8', 'ignore')

        video_url = ''
        no_url_found = True
        have_valid_url = False

        match = re.search(b'\'(.*?m3u8)', html_source, re.I | re.U)
        if match:
            if self.PREFERRED_QUALITY == '0': # Very High Quality
                quality = VQ1080P
            elif self.PREFERRED_QUALITY == '1': # High Quality
                quality = VQ720P
            elif self.PREFERRED_QUALITY == '2': # Medium
                quality = VQ480P
            elif self.PREFERRED_QUALITY == '3': # Low
                quality = VQ360P
            elif self.PREFERRED_QUALITY == '4': # Very Low
                quality = VQ240P
            else: # Default in case quality is not found?
                quality = VQ720P
            video_url = str(match.group(1))
            video_url_altered = video_url.replace("index","NewHLS-%s" % quality)
            # Find out if the m3u8 file exists
            reply = session.get(video_url_altered)
            # m3u8 file is found, let's use that. If it is not found, let's use the unaltered video url.
            if reply.status_code == 200:
                video_url = video_url_altered
            have_valid_url = True
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "final video_url", str(video_url)), xbmc.LOGNOTICE)

        # Play video...
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30107))
        #
        # The End
        #
