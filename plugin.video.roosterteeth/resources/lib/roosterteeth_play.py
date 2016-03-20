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

LOGINURL = 'http://roosterteeth.com/login'
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
        unplayable_media_file = False

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
                        reply = session.get(LOGINURL)

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
                        reply = session.post(LOGINURL, data=payload)

                        if self.DEBUG == 'true':
                            xbmc.log('post login page response, status_code:' + str(reply.status_code))

                        # check that the login was technically ok (status_code 200).
                        # This in itself does NOT mean that the username/password were correct.
                        if reply.status_code == 200:
                            pass
                            # check that the username is in the response. If that's the case, the login was ok
                            # and the username and password in settings are ok.
                            if str(reply.text).find(SETTINGS.getSetting('username')) >= 0:
                                if self.DEBUG == 'true':
                                    xbmc.log('login was successfull!')
                                # let's try getting the page again after a login, hopefully it contains a link to
                                # the video now
                                reply = session.get(self.video_page_url)
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

        #soup = BeautifulSoup(html_source)

        video_url = ''
        no_url_found = True
        have_valid_url = False

        # Is it a youtube video ?
        # f.e. http://ah.roosterteeth.com/episode/happy-hour-season-1-happy-hour-1
        #       <script>
        #             onYouTubeIframeAPIReady = RT.youtube.onReady;
        #             RT.youtube.player({
        #                 iframeId: "iframe-9415",
        #                 videoId: '9415',
        #                 youtubeKey: 'zRc1CcRDI_k',
        #                 autoplay: 1,
        #                 markWatchedForm : 'watch-11630'
        #             });
        #       </script>
        search_for_string = "youtubeKey: '"
        begin_pos_search_for_youtube_id = str(html_source).find(search_for_string)
        if begin_pos_search_for_youtube_id >= 0:
            begin_pos_youtube_id = begin_pos_search_for_youtube_id + len(search_for_string)
            rest = str(html_source)[begin_pos_youtube_id:]
            length_youtube_id = rest.find("'")
            end_pos_youtube_id = begin_pos_youtube_id + length_youtube_id
            youtube_id = str(html_source)[begin_pos_youtube_id:end_pos_youtube_id]
            video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
            have_valid_url = True

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "youtube video_url", str(video_url)), xbmc.LOGNOTICE)

        if have_valid_url:
            pass
        else:
            # Is it a blip tv video ?
            # f.e. http://ah.roosterteeth.com/episode/happy-hour-season-1-happy-hour-5
            # manifest: 'http://wpc.1765A.taucdn.net/801765A/video/blip/9704/9704-manifest.m3u8'

            #			The content looks something like this
            #			#EXTM3U
            #			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=872448,RESOLUTION=640x360,NAME="360"
            #			http://wpc.1765A.taucdn.net/831765A/video/blip/9704/RoosterTeeth-RTLifePresentsHappyHour5932.m4v.m3u8
            #			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=615424,RESOLUTION=480x270,NAME="270"
            #			http://wpc.1765A.taucdn.net/831765A/video/blip/9704/RoosterTeeth-RTLifePresentsHappyHour5539.mp4.m3u8
            #			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3024896,RESOLUTION=1280x720,NAME="720"
            #			http://wpc.1765A.taucdn.net/831765A/video/blip/9704/RoosterTeeth-RTLifePresentsHappyHour5425.m4v.m3u8

            #           or like this for a sponsored video f.e.: "http://www.roosterteeth.com/episode/rt-sponsor-cut-season-2-kerry-comes-out-of-the-closet"
            #			#EXTM3U
            #           #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=559104,RESOLUTION=640x360,NAME="360"
            #           http://wpc.1765A.taucdn.net/831765A/video/blip/1684/RoosterTeeth-KerryComesOutOfCloset959.m4v.m3u8

            #			or like this for achievementhunter f.e.: "http://achievementhunter.com/episode/lets-play-lets-play-let-s-play-no-time-to-explain"
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=16655000,RESOLUTION=1920x1080,CODECS="avc1.4d001f,mp4a.40.2"
            # 			1080P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=7264000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"
            # 			720P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3377000,RESOLUTION=640x360,CODECS="avc1.4d001f,mp4a.40.2"
            # 			480P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1740000,RESOLUTION=426x238,CODECS="avc1.4d001f,mp4a.40.2"
            # 			240P.m3u8

            #			or like this for newer stuff f.e.: " http://roosterteeth.com/episode/the-know-game-news-season-1-fallout-4-b-r-o-k-e-n"
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=6037000,RESOLUTION=1920x1080,CODECS="avc1.4d001f,mp4a.40.2"
            # 			NewHLS-1080P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3181000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"
            # 			NewHLS-720P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1765000,RESOLUTION=854x480,CODECS="avc1.4d001f,mp4a.40.2"
            # 			NewHLS-480P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1261000,RESOLUTION=640x360,CODECS="avc1.4d001f,mp4a.40.2"
            # 			NewHLS-360P.m3u8
            # 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=742000,RESOLUTION=426x240,CODECS="avc1.4d001f,mp4a.40.2"
            # 			NewHLS-240P.m3u8

            search_for_string = "manifest: '"
            begin_pos_search_for_blip = str(html_source).find(search_for_string)
            if begin_pos_search_for_blip < 0:
                # if nothings found, let's try and search for something else
                search_for_string = "file: '"
                begin_pos_search_for_blip = str(html_source).find(search_for_string)
                if begin_pos_search_for_blip < 0:
                    # if nothings found, let's try and search for something else
                    search_for_string = "file : '"
                    begin_pos_search_for_blip = str(html_source).find(search_for_string)

            if begin_pos_search_for_blip >= 0:
                begin_pos_m3u8_url = begin_pos_search_for_blip + len(search_for_string)
                rest = str(html_source)[begin_pos_m3u8_url:]
                length_m3u8_url = rest.find("'")
                end_pos_m3u8_url = begin_pos_m3u8_url + length_m3u8_url
                m3u8_url = str(html_source)[begin_pos_m3u8_url:end_pos_m3u8_url]

                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "blip playlists m3u8_url", str(m3u8_url)), xbmc.LOGNOTICE)

                try:
                    reply = session.get(m3u8_url)
                    html_source = reply.text

                    if self.DEBUG == 'true':
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "content blip playlists m3u8_url", str(html_source)),
                                 xbmc.LOGNOTICE)

                    html_source = html_source.encode('utf-8', 'ignore')
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

                # Very High quality
                if self.PREFERRED_QUALITY == '0':
                    if str(html_source).find(NEWHLS) >= 0:
                        search_for_string = NEWHLS + VQ1080P
                    else:
                        search_for_string = VQ1080P
                    pos_name = str(html_source).find(search_for_string)
                    if pos_name >= 0:
                        begin_pos_playlist = str(html_source).find('http', pos_name)
                        if begin_pos_playlist == -1:
                            video_url = str(m3u8_url).replace('index', str(search_for_string))
                            have_valid_url = True
                        else:
                            end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                            video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                            have_valid_url = True
                    else:
                        if str(html_source).find(NEWHLS) >= 0:
                            search_for_string = NEWHLS + VQ720P
                        else:
                            search_for_string = VQ720P
                        pos_name = str(html_source).find(search_for_string)
                        if pos_name >= 0:
                            begin_pos_playlist = str(html_source).find('http', pos_name)
                            if begin_pos_playlist == -1:
                                video_url = str(m3u8_url).replace('index', str(search_for_string))
                                have_valid_url = True
                            else:
                                end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                have_valid_url = True
                        else:
                            if str(html_source).find(NEWHLS) >= 0:
                                search_for_string = NEWHLS + VQ480P
                            else:
                                search_for_string = VQ480P
                            pos_name = str(html_source).find(search_for_string)
                            if pos_name >= 0:
                                begin_pos_playlist = str(html_source).find('http', pos_name)
                                if begin_pos_playlist == -1:
                                    video_url = str(m3u8_url).replace('index', str(search_for_string))
                                    have_valid_url = True
                                else:
                                    end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                    video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                    have_valid_url = True
                            else:
                                if str(html_source).find(NEWHLS) >= 0:
                                    search_for_string = NEWHLS + VQ360P
                                else:
                                    search_for_string = VQ360P
                                pos_name = str(html_source).find(search_for_string)
                                if pos_name >= 0:
                                    begin_pos_playlist = str(html_source).find('http', pos_name)
                                    if begin_pos_playlist == -1:
                                        video_url = str(m3u8_url).replace('index', str(search_for_string))
                                        have_valid_url = True
                                    else:
                                        end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len(
                                            "m3u8")
                                        video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                        have_valid_url = True
                                else:
                                    if str(html_source).find(NEWHLS) >= 0:
                                        search_for_string = NEWHLS + VQ240P
                                    else:
                                        search_for_string = VQ240P
                                    pos_name = str(html_source).find(search_for_string)
                                    if pos_name >= 0:
                                        begin_pos_playlist = str(html_source).find('http', pos_name)
                                        if begin_pos_playlist == -1:
                                            video_url = str(m3u8_url).replace('index', str(search_for_string))
                                            have_valid_url = True
                                        else:
                                            end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len(
                                                "m3u8")
                                            video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                            have_valid_url = True

                # High quality
                elif self.PREFERRED_QUALITY == '1':
                    if str(html_source).find(NEWHLS) >= 0:
                        search_for_string = NEWHLS + VQ720P
                    else:
                        search_for_string = VQ720P
                    pos_name = str(html_source).find(search_for_string)
                    if pos_name >= 0:
                        begin_pos_playlist = str(html_source).find('http', pos_name)
                        if begin_pos_playlist == -1:
                            video_url = str(m3u8_url).replace('index', str(search_for_string))
                            have_valid_url = True
                        else:
                            end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                            video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                            have_valid_url = True
                    else:
                        if str(html_source).find(NEWHLS) >= 0:
                            search_for_string = NEWHLS + VQ480P
                        else:
                            search_for_string = VQ480P
                        pos_name = str(html_source).find(search_for_string)
                        if pos_name >= 0:
                            begin_pos_playlist = str(html_source).find('http', pos_name)
                            if begin_pos_playlist == -1:
                                video_url = str(m3u8_url).replace('index', str(search_for_string))
                                have_valid_url = True
                            else:
                                end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                have_valid_url = True
                        else:
                            if str(html_source).find(NEWHLS) >= 0:
                                search_for_string = NEWHLS + VQ360P
                            else:
                                search_for_string = VQ360P
                            pos_name = str(html_source).find(search_for_string)
                            if pos_name >= 0:
                                begin_pos_playlist = str(html_source).find('http', pos_name)
                                if begin_pos_playlist == -1:
                                    video_url = str(m3u8_url).replace('index', str(search_for_string))
                                    have_valid_url = True
                                else:
                                    end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                    video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                    have_valid_url = True
                            else:
                                if str(html_source).find(NEWHLS) >= 0:
                                    search_for_string = NEWHLS + VQ240P
                                else:
                                    search_for_string = VQ240P
                                pos_name = str(html_source).find(search_for_string)
                                if pos_name >= 0:
                                    begin_pos_playlist = str(html_source).find('http', pos_name)
                                    if begin_pos_playlist == -1:
                                        video_url = str(m3u8_url).replace('index', str(search_for_string))
                                        have_valid_url = True
                                    else:
                                        end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len(
                                            "m3u8")
                                        video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                        have_valid_url = True

                # Medium
                elif self.PREFERRED_QUALITY == '2':
                    if str(html_source).find(NEWHLS) >= 0:
                        search_for_string = NEWHLS + VQ480P
                    else:
                        search_for_string = VQ480P
                    pos_name = str(html_source).find(search_for_string)
                    if pos_name >= 0:
                        begin_pos_playlist = str(html_source).find('http', pos_name)
                        if begin_pos_playlist == -1:
                            video_url = str(m3u8_url).replace('index', str(search_for_string))
                            have_valid_url = True
                        else:
                            end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                            video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                            have_valid_url = True
                    else:
                        if str(html_source).find(NEWHLS) >= 0:
                            search_for_string = NEWHLS + VQ360P
                        else:
                            search_for_string = VQ360P
                        pos_name = str(html_source).find(search_for_string)
                        if pos_name >= 0:
                            begin_pos_playlist = str(html_source).find('http', pos_name)
                            if begin_pos_playlist == -1:
                                video_url = str(m3u8_url).replace('index', str(search_for_string))
                                have_valid_url = True
                            else:
                                end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                have_valid_url = True
                        else:
                            if str(html_source).find(NEWHLS) >= 0:
                                search_for_string = NEWHLS + VQ240P
                            else:
                                search_for_string = VQ240P
                            pos_name = str(html_source).find(search_for_string)
                            if pos_name >= 0:
                                begin_pos_playlist = str(html_source).find('http', pos_name)
                                if begin_pos_playlist == -1:
                                    video_url = str(m3u8_url).replace('index', str(search_for_string))
                                    have_valid_url = True
                                else:
                                    end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                    video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                    have_valid_url = True

                # Low
                elif self.PREFERRED_QUALITY == '3':
                    if str(html_source).find(NEWHLS) >= 0:
                        search_for_string = NEWHLS + VQ360P
                    else:
                        search_for_string = VQ360P
                    pos_name = str(html_source).find(search_for_string)
                    if pos_name >= 0:
                        begin_pos_playlist = str(html_source).find('http', pos_name)
                        if begin_pos_playlist == -1:
                            video_url = str(m3u8_url).replace('index', str(search_for_string))
                            have_valid_url = True
                        else:
                            end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                            video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                            have_valid_url = True
                    else:
                        if str(html_source).find(NEWHLS) >= 0:
                            search_for_string = NEWHLS + VQ240P
                        else:
                            search_for_string = VQ240P
                        pos_name = str(html_source).find(search_for_string)
                        if pos_name >= 0:
                            begin_pos_playlist = str(html_source).find('http', pos_name)
                            if begin_pos_playlist == -1:
                                video_url = str(m3u8_url).replace('index', str(search_for_string))
                                have_valid_url = True
                            else:
                                end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                                video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                                have_valid_url = True

                # Very Low
                elif self.PREFERRED_QUALITY == '4':
                    if str(html_source).find(NEWHLS) >= 0:
                        search_for_string = NEWHLS + VQ240P
                    else:
                        search_for_string = VQ240P
                    pos_name = str(html_source).find(search_for_string)
                    if pos_name >= 0:
                        begin_pos_playlist = str(html_source).find('http', pos_name)
                        if begin_pos_playlist == -1:
                            video_url = str(m3u8_url).replace('index', str(search_for_string))
                            have_valid_url = True
                        else:
                            end_pos_playlist = str(html_source).find("m3u8", begin_pos_playlist) + len("m3u8")
                            video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
                            have_valid_url = True

                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "blip playlist video_url", str(video_url)), xbmc.LOGNOTICE)

                # last ditch effort when m3u8 content wasn't quite what i expected
                if video_url == '':
                    video_url = m3u8_url
                    have_valid_url = True
                    if self.DEBUG == 'true':
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "corrected blip playlist video_url", str(video_url)),
                                 xbmc.LOGNOTICE)

        if have_valid_url:
            pass
        else:
            # Is it a cloudfront tv video ?
            #     <script type='text/javascript'>
            #                     jwplayer('video-9902').setup({
            #                         image: "http://s3.amazonaws.com/s3.roosterteeth.com/assets/epart/ep9902.jpg",
            #                         sources: [
            #                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-480p.mp4", label: "480p SD","default": "true"},
            #                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-720p.mp4", label: "720p HD"},
            #                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-1080p.mp4", label: "1080p HD"},
            #                         ],
            #                         title: 'RWBY Volume 2, Chapter 12',
            #                         width: '590',
            #                         height: '405',
            #                         aspectratio: '16:9',
            #                         sharing: '{}',
            #                           advertising: {
            #                             client: 'googima',
            #                             tag: 'http://googleads.g.doubleclick.net/pagead/ads?ad_type=video&client=ca-video-pub-0196071646901426&description_url=http%3A%2F%2Froosterteeth.com&videoad_start_delay=0&hl=en&max_ad_duration=30000'
            #                           }
            #                     });
            #                 </script>
            search_for_string = "sources"
            begin_pos_search_for_cloudfront = str(html_source).find(search_for_string)
            if begin_pos_search_for_cloudfront == -1:
                pass
            else:
                start_pos_480p = data.find("{", begin_pos_search_for_cloudfront)
                end_pos_480p = data.find("}", start_pos_480p + 1)
                string_480p = data[start_pos_480p:end_pos_480p + 1]
                start_pos_480p_file = string_480p.find("http")
                end_pos_480p_file = string_480p.find('"', start_pos_480p_file + 1)
                string_480p_file = string_480p[start_pos_480p_file:end_pos_480p_file]

                start_pos_720p = data.find("{", end_pos_480p + 1)
                end_pos_720p = data.find("}", start_pos_720p + 1)
                string_720p = data[start_pos_720p:end_pos_720p + 1]
                start_pos_720p_file = string_720p.find("http")
                end_pos_720p_file = string_720p.find('"', start_pos_720p_file + 1)
                string_720p_file = string_720p[start_pos_720p_file:end_pos_720p_file]

                start_pos_1080p = data.find("{", end_pos_720p + 1)
                end_pos_1080p = data.find("}", start_pos_1080p + 1)
                string_1080p = data[start_pos_1080p:end_pos_1080p + 1]
                start_pos_1080p_file = string_1080p.find("http")
                end_pos_1080p_file = string_1080p.find('"', start_pos_1080p_file + 1)
                string_1080p_file = string_1080p[start_pos_1080p_file:end_pos_1080p_file]

                # high video quality
                if self.PREFERRED_QUALITY == '0':
                    video_url = string_1080p_file
                    have_valid_url = True
                # medium video quality
                elif self.PREFERRED_QUALITY == '1':
                    video_url = string_720p_file
                    have_valid_url = True
                # low video quality
                elif self.PREFERRED_QUALITY == '2':
                    video_url = string_480p_file
                    have_valid_url = True

                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "cloudfront video_url", str(video_url)), xbmc.LOGNOTICE)

        # Play video...
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30107))
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30108))

            #
            # The End
            #
