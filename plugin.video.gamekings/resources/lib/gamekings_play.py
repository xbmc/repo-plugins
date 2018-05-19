#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import requests
import sys
import urllib.request, urllib.error, urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

from gamekings_const import SETTINGS, LANGUAGE, LOGIN_URL, convertToUnicodeString, log

#
# Main class
#
class Main(object):
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

        log("ARGV", repr(sys.argv))

        # Parse parameters
        self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]

        log("self.video_page_url", self.video_page_url)

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
        dialog_wait = xbmcgui.DialogProgress()

        #
        # Get current list item details...
        #
        # title = convertToUnicodeString(xbmc.getInfoLabel("list_item.Title"))
        thumbnail_url = convertToUnicodeString(xbmc.getInfoImage("list_item.Thumb"))
        # studio = convertToUnicodeString(xbmc.getInfoLabel("list_item.Studio"))
        # plot = convertToUnicodeString(xbmc.getInfoLabel("list_item.Plot"))
        # genre = convertToUnicodeString(xbmc.getInfoLabel("list_item.Genre"))

        try:
            # requests is sooooo nice, respect!
            session = requests.Session()

            # get the page that contains the video
            response = session.get(self.video_page_url)

            html_source = response.text
            html_source = convertToUnicodeString(html_source)

            # is it a premium-only video? (f.e. https://www.gamekings.tv/premium/110853/)
            # <div class="video__premiumonly">
            #     <div class="video__premiumonlywrapper">
            #         <h3 class="video__notice">Premium <span>Content</span></h3>
            #         <a href="#" class="field__button  js-login">Log in</a>
            #         <span class="video__or-text">of</span>
            #         <a href="https://www.gamekings.tv/get-premium/" class="field__button  field__button--premium">Word Premium</a>
            #     </div>
            # </div>

            if str(html_source).find('premiumonly') >= 0:
                if self.IS_PREMIUM_MEMBER == 'true':
                    try:
                        # we need a NEW (!!!) session
                        session = requests.Session()

                        # # get the login-page
                        # response = session.get(LOGINURL)
                        # html_source = reply.text
                        # html_source = convertToUnicodeString(html_source)
                        #
                        # log("login-page", html_source)
                        #
                        # the login page should contain something like this
                        #  <input type="text" name="log" id="user_login" ...
                        # ...
                        # <input type="password" name="pwd" id="user_pass" ...

                        payload = {'log': SETTINGS.getSetting('username'),
                                   'pwd': SETTINGS.getSetting('password')}

                        # post the LOGIN-page with the LOGIN-data, to actually login this session
                        response = session.post(LOGIN_URL, data=payload)

                        html_source = response.text
                        html_source = convertToUnicodeString(html_source)

                        # check that the login was technically ok (status_code 200).
                        # This in itself does NOT mean that the username/password were correct.
                        if response.status_code == 200:
                            # check that 'login_error' is in the response. If that's the case, the login was not ok
                            # and the username and password in settings are not ok.
                            if str(html_source).find('login_error') >= 0:
                                xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30601), LANGUAGE(30602),
                                                    LANGUAGE(30603))
                                sys.exit(1)
                            else:
                                # dialog_wait.create("Login Successfull", "Currently looking for video")

                                log("self.video_page_url", "login was succesfull!!")

                                # let's try getting the page again after a login, hopefully it contains a link to
                                # the video now
                                response = session.get(self.video_page_url)

                                log("retrieved page", self.video_page_url)
                        else:
                            # Something went wrong with logging in
                            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30604) % (str(response.status_code)))
                            sys.exit(1)

                    except urllib.error.HTTPError as error:

                        log("HTTPerror1", error)

                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30606) % (str(error)))
                        sys.exit(1)
                    except:
                        exception = sys.exc_info()[0]

                        log("Exception1", exception)

                        sys.exit(1)
                # This is a premium video and the Premium-membership-switch in the settings is off
                else:
                    xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30605))
                    sys.exit(1)

        except urllib.error.HTTPError as error:

            log("HTTPerror2", error)

            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30606) % (str(error)))
            sys.exit(1)
        except:
            exception = sys.exc_info()[0]

            log("Exception2", exception)

            sys.exit(1)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # log("html_source", html_source)

        # Get the video url
        # <div class="content  content--page  content--bglight  content--blue">
        #             <div class="video">
        #             <div id='videoplayer'></div>
        #             <script type="text/javascript">
        #                 jwplayer('videoplayer').setup({
        #                     file: 'https://player.vimeo.com/external/166503498.hd.mp4?s=c44264eced6082c0789371cb5209af96bc44035b',
        #                     image: 'https://www.gamekings.tv/wp-content/uploads/20160513_gk1702_splash.jpg',
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
        start_pos_video_url = html_source.find("http://player.vimeo.com/external")
        if start_pos_video_url == -1:
            start_pos_video_url = html_source.find("https://player.vimeo.com/external")
            if start_pos_video_url == -1:
                start_pos_video_url = html_source.find("http://player.vimeo.com/video")
                if start_pos_video_url == -1:
                    start_pos_video_url = html_source.find("https://player.vimeo.com/video")
                    if start_pos_video_url == -1:
                        start_pos_video_url = html_source.find("http://www.youtube.com/")
                        if start_pos_video_url == -1:
                            start_pos_video_url = html_source.find("https://www.youtube.com/")
                            if start_pos_video_url == -1:
                                no_url_found = True
                                have_valid_url = False

        log("start_pos_video_url", start_pos_video_url)

        #log("html_source[start_pos_video_url:]", html_source[start_pos_video_url:])

        # Try to make a valid video url
        if have_valid_url:
            # Let's only use the video_url part
            html_source_split = str(html_source[start_pos_video_url:]).split()
            video_url = html_source_split[0]

            log("video_url after split", video_url)

            if video_url.find("target=") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""
            elif video_url.find("www.youtube.com/channel/") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""
            elif video_url.find("player.vimeo.com/api/player.js") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""
            elif video_url.find("www.youtube.com/user/Gamekingsextra") >= 0:
                no_url_found = True
                have_valid_url = False
                video_url = ""

        log("video_url", video_url)

        # Play video
        if have_valid_url:
            # regular gamekings video's on vimeo look like this: https://player.vimeo.com/external/166503498.hd.mp4?s=c44264eced6082c0789371cb5209af96bc44035b
            if video_url.find("player.vimeo.com/external/") > 0:
                vimeo_id = str(video_url)
                vimeo_id = vimeo_id.replace("http://player.vimeo.com/external/", "")
                vimeo_id = vimeo_id.replace("https://player.vimeo.com/external/", "")
                vimeo_id = vimeo_id[0:vimeo_id.find(".")]

                log("vimeo_id1", vimeo_id)

                video_url = 'plugin://plugin.video.vimeo/play/?video_id=%s' % vimeo_id
            # premium video's on vimeo look like this: https://player.vimeo.com/video/190106340?title=0&autoplay=1&portrait=0&badge=0&color=C7152F
            if video_url.find("player.vimeo.com/video/") > 0:
                vimeo_id = str(video_url)
                vimeo_id = vimeo_id.replace("http://player.vimeo.com/video/", "")
                vimeo_id = vimeo_id.replace("https://player.vimeo.com/video/", "")
                vimeo_id = vimeo_id[0:vimeo_id.find("?")]

                log("vimeo_id2", vimeo_id)

                video_url = 'plugin://plugin.video.vimeo/play/?video_id=%s' % vimeo_id
            elif video_url.find("youtube") > 0:
                youtube_id = str(video_url)
                youtube_id = youtube_id.replace("http://www.youtube.com/embed/", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/embed/", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/watch?v=", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/watch?v=", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/watch", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/watch", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/", "")
                youtube_id = youtube_id[0:youtube_id.find("?")]

                log("youtube_id", youtube_id)

                video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Check if it's a twitch live stream
        #
        elif str(html_source).find("twitch") > 0:
            #example of a live stream: video_url = 'plugin://plugin.video.twitch/?channel_id=57330659&amp;mode=play;'
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30611))
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))