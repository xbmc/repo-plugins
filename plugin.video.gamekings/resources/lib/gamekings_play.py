#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import requests
import sys
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin

from gamekings_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION

LOGINURL = 'http://www.gamekings.tv/wp-login.php'
TWITCHURL =  'plugin://plugin.video.twitch/playLive/gamekings/'

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
        self.IS_PREMIUM_MEMBER = SETTINGS.getSetting('is-premium-member')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        # Parse parameters
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGDEBUG)

        #
        # Play video
        #
        self.playVideo()

    #
    # Play video
    #
    def playVideo(self):
        #
        # Init
        #
        video_url = ""

        #
        # Get current list item details
        #
        # title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail = xbmc.getInfoImage("list_item.Thumb")
        # studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
        plot = unicode(xbmc.getInfoLabel("list_item.Plot"), "utf-8")
        genre = unicode(xbmc.getInfoLabel("list_item.Genre"), "utf-8")

        #
        # Show wait dialog while parsing data
        #
        dialog_wait = xbmcgui.DialogProgress()
        dialog_wait.create(LANGUAGE(30504), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        reply = ''
        session = ''
        try:
            # requests is sooooo nice, respect!
            session = requests.Session()

            # get the page that contains the video
            reply = session.get(self.video_page_url)

            # is it a premium-only video? (f.e. http://www.gamekings.tv/premium/110853/)
            # <div class="video__premiumonly">
            #     <div class="video__premiumonlywrapper">
            #         <h3 class="video__notice">Premium <span>Content</span></h3>
            #         <a href="#" class="field__button  js-login">Log in</a>
            #         <span class="video__or-text">of</span>
            #         <a href="http://www.gamekings.tv/get-premium/" class="field__button  field__button--premium">Word Premium</a>
            #     </div>
            # </div>

            if str(reply.text).find('premiumonly') >= 0:
                if self.IS_PREMIUM_MEMBER == 'true':
                    try:
                        # we need a NEW (!!!) session
                        session = requests.Session()

                        # # get the login-page
                        # reply = session.get(LOGINURL)
                        # html_source = reply.text
                        # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        #     ADDON, VERSION, DATE, "login-page", str(html_source)), xbmc.LOGDEBUG)
                        #
                        # the login should contain something like this
                        #  <input type="text" name="log" id="user_login" ...
                        # ...
                        # <input type="password" name="pwd" id="user_pass" ...

                        payload = {'log': SETTINGS.getSetting('username'),
                                   'pwd': SETTINGS.getSetting('password')}
                        # post the LOGIN-page with the LOGIN-data, to actually login this session
                        reply = session.post(LOGINURL, data=payload)
                        html_source = reply.text

                        # check that the login was technically ok (status_code 200).
                        # This in itself does NOT mean that the username/password were correct.
                        if reply.status_code == 200:
                            # check that 'login_error' is in the response. If that's the case, the login was not ok
                            # and the username and password in settings are not ok.
                            if str(html_source).find('login_error') >= 0:
                                try:
                                    dialog_wait.close()
                                    del dialog_wait
                                except:
                                    pass
                                xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30601), LANGUAGE(30602),
                                                    LANGUAGE(30603))
                                sys.exit(1)
                            else:
                                dialog_wait.create("Login Success", "Currently looking for videos in '%s'" % self.title)
                                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                                    ADDON, VERSION, DATE, "self.video_page_url", str("Login was succesfull!!")), xbmc.LOGDEBUG)
                                # let's try getting the page again after a login, hopefully it contains a link to
                                # the video now
                                reply = session.get(self.video_page_url)
                                xbmc.log("[ADDON] %s v%s (%s) debug mode, Loaded %s" % (
                                    ADDON, VERSION, DATE, str(self.video_page_url)),
                                         xbmc.LOGDEBUG)
                        else:
                            # Something went wrong with logging in
                            try:
                                dialog_wait.close()
                                del dialog_wait
                            except:
                                pass
                            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30604) % (str(reply.status_code)))
                            sys.exit(1)

                    except urllib2.HTTPError, error:
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGDEBUG)
                        try:
                            dialog_wait.close()
                            del dialog_wait
                        except:
                            pass
                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30606) % (str(error)))
                        sys.exit(1)
                    except:
                        exception = sys.exc_info()[0]
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "Exception1:", str(exception)), xbmc.LOGDEBUG)
                        try:
                            dialog_wait.close()
                            del dialog_wait
                        except:
                            pass
                        sys.exit(1)
                # This is a premium video and the Premium-membership-switch in the settings is off
                else:
                    try:
                        dialog_wait.close()
                        del dialog_wait
                    except:
                        pass
                    xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30605))
                    sys.exit(1)

        except urllib2.HTTPError, error:
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGDEBUG)
            try:
                dialog_wait.close()
                del dialog_wait
            except:
                pass
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30606) % (str(error)))
            sys.exit(1)
        except:
            exception = sys.exc_info()[0]
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "Exception2:", str(exception)), xbmc.LOGDEBUG)
            try:
                dialog_wait.close()
                del dialog_wait
            except:
                pass
            sys.exit(1)

        html_source = reply.text
        html_source = html_source.encode('utf-8', 'ignore')

        # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
        #     ADDON, VERSION, DATE, "html_source:", str(html_source)), xbmc.LOGDEBUG)

        # Get the video url
        # <div class="content  content--page  content--bglight  content--blue">
        #             <div class="video">
        #             <div id='videoplayer'></div>
        #             <script type="text/javascript">
        #                 jwplayer('videoplayer').setup({
        #                     file: 'https://player.vimeo.com/external/166503498.hd.mp4?s=c44264eced6082c0789371cb5209af96bc44035b',
        #                     image: 'http://www.gamekings.tv/wp-content/uploads/20160513_gk1702_splash.jpg',
        #                     title: 'Gamekings S17E02: De Synergie Aflevering',
        #                     width: '100%',
        #                     aspectratio: '16:9',
        #                     skin: '',
        #                     primary: 'html5',
        #                     autostart: 'true',
        #                     startparam: 'start',
        #                     ...
        no_url_found = False
        have_valid_url = True
        start_pos_video_url = html_source.find("http://player.vimeo.com")
        if start_pos_video_url == -1:
            start_pos_video_url = html_source.find("https://player.vimeo.com")
            if start_pos_video_url == -1:
                start_pos_video_url = html_source.find("http://www.youtube.com/")
                if start_pos_video_url == -1:
                    start_pos_video_url = html_source.find("https://www.youtube.com/")
                    if start_pos_video_url == -1:
                        no_url_found = True
                        have_valid_url = False

        # Try to make a valid video url
        if have_valid_url:
            end_pos_video_url = html_source.find("'", start_pos_video_url)
            video_url = html_source[start_pos_video_url:end_pos_video_url]
            if video_url.find("target=") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""
            elif video_url.find("http://www.youtube.com/channel/") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""
            elif video_url.find("https://www.youtube.com/channel/") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "video_url", str(video_url)),
                    xbmc.LOGDEBUG)

        # Play video
        if have_valid_url:
            if video_url.find("youtube") > 0:
                youtube_id = str(video_url)
                youtube_id = youtube_id.replace("http://www.youtube.com/embed/", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/embed/", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/watch?v=", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/watch?v=", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/", "")
                video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
            # premium video's on vimeo look like this: http://player.vimeo.com/video/190106340?title=0&autoplay=1&portrait=0&badge=0&color=C7152F
            elif video_url.find("player.vimeo.com/video/") > 0:
                vimeo_id = str(video_url)
                vimeo_id = vimeo_id.replace("http://player.vimeo.com/video/", "")
                vimeo_id = vimeo_id.replace("https://player.vimeo.com/video/", "")
                vimeo_id = vimeo_id[0:vimeo_id.find("?")]
                video_url = 'plugin://plugin.video.vimeo/play/?video_id=%s' % vimeo_id

            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Check if it's a twitch live stream
        #
        elif str(html_source).find("twitch") > 0:
            video_url = TWITCHURL

            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))