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

from gamekings_const import SETTINGS, LANGUAGE, LOGIN_URL, convertToUnicodeString, log, TWITCH_URL_GAMEKINGS_TV, \
    VQ4K, VQ1080P, VQ720P, VQ480P, VQ360P, decodeString, MASTER_DOT_M3U8, HTTPSCOLONSLASHSLASH_ENCODED, END_TAG, STREAM

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
        self.IS_PREMIUM_MEMBER = SETTINGS.getSettingBool('is-premium-member')
        self.PREFERRED_QUALITY = SETTINGS.getSetting('quality')

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
                if self.IS_PREMIUM_MEMBER:
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

                                # log("retrieved page", self.video_page_url)
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

        have_valid_url = False
        no_url_found = True
        youtube_id = ''

        # encoded container with the m3u8 url:
        # "c34696670236c6163737d32256d6265646d236f6e6471696e6562722e3c396662716d656027796464786d3226343032202865696768647d3223363032202372736d322
        # 8647470737a3f2f27616d656b696e67637e2763646e6e236f6f267964656f637f243435373f58507235454f4d6463335074405262335
        # 2202662716d65626f627465627d32203220216c6c6f6776657c6c63736275656e6e3c3f296662716d656e3c3f2469667e3"
        # Let's get the encoded video url, in the example above that's the second line
        start_pos_encoded_m3u8_url = html_source.find(HTTPSCOLONSLASHSLASH_ENCODED)
        if start_pos_encoded_m3u8_url >= 0:

            # log("start_pos_encoded_m3u8_url", start_pos_encoded_m3u8_url)

            end_pos_encoded_m3u8_url = html_source[start_pos_encoded_m3u8_url:].find(END_TAG)
            if end_pos_encoded_m3u8_url >= 0:

                # log("end_pos_encoded_m3u8_url", end_pos_encoded_m3u8_url)

                encoded_m3u8_url = html_source[start_pos_encoded_m3u8_url:start_pos_encoded_m3u8_url + end_pos_encoded_m3u8_url]

                # log("encoded_m3u8_url", encoded_m3u8_url)

                decoded_m3u8_url = decodeString(encoded_m3u8_url)

                log("decoded_m3u8_url", decoded_m3u8_url)

                # The decoded m3u8 url should look something like this: https://gamekings.gcdn.co/videos/4457_Xp2EEOmd3SpDPb2S
                # We have to lowercase the part before the last '/' to fix any uppercase digits (i guess my magic decoding isn't perfect ;))
                pos_last_slash = decoded_m3u8_url.rfind("/")
                if pos_last_slash >= 0:
                    first_part = decoded_m3u8_url[0:pos_last_slash]

                    # log("first_part", first_part)

                    second_part = decoded_m3u8_url[pos_last_slash:]

                    # log("second_part", second_part)

                    # Lowercase the first part and add the filename of the m3u8-file
                    decoded_m3u8_url = first_part.lower() + second_part + "/" + MASTER_DOT_M3U8

                    log("decoded_m3u8_url completed", decoded_m3u8_url)

                    response = session.get(decoded_m3u8_url)

                    # determine the wanted video quality
                    if self.PREFERRED_QUALITY == '0':  # Low
                        quality = VQ360P
                    elif self.PREFERRED_QUALITY == '1':  # Medium
                        quality = VQ480P
                    elif self.PREFERRED_QUALITY == '2':  # High Quality
                        quality = VQ720P
                    elif self.PREFERRED_QUALITY == '3':  # Very High Quality
                        quality = VQ1080P
                    elif self.PREFERRED_QUALITY == '4':  # Ultra High Quality
                        quality = VQ4K
                    else:  # Default in case quality is not found
                        quality = VQ720P

                    # log("wanted quality", quality)

                    # an example of the content of a m3u8 file:
                    # #EXTM3U
                    # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=464000,RESOLUTION=640x360,FRAME-RATE=60.000,CODECS="avc1.4d401f,mp4a.40.2"
                    # index-s360p-v1-a1.m3u8
                    # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=928000,RESOLUTION=854x480,FRAME-RATE=60.000,CODECS="avc1.4d401f,mp4a.40.2"
                    # index-s480p-v1-a1.m3u8
                    # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2128000,RESOLUTION=1280x720,FRAME-RATE=60.000,CODECS="avc1.4d4020,mp4a.40.2"
                    # index-s720p-v1-a1.m3u8
                    # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=6128000,RESOLUTION=1920x1080,FRAME-RATE=60.000,CODECS="avc1.4d402a,mp4a.40.2"
                    # index-s1080p-v1-a1.m3u8
                    #EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=18304,RESOLUTION=640x360,CODECS="avc1.4d401f",URI="iframes-s360p-v1-a1.m3u8"
                    #EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=36479,RESOLUTION=854x480,CODECS="avc1.4d401f",URI="iframes-s480p-v1-a1.m3u8"
                    #EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=92824,RESOLUTION=1280x720,CODECS="avc1.4d4020",URI="iframes-s720p-v1-a1.m3u8"
                    #EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=240783,RESOLUTION=1920x1080,CODECS="avc1.4d402a",URI="iframes-s1080p-v1-a1.m3u8"

                    # Let's try and find a video of the desired video quality.
                    # If that can't be found, try to find a video with less than the desired video quality
                    # 4K doesn't seem to be available as of now (september 2019) but it may be in the future
                    video_quality_url = ''
                    if video_quality_url == '':
                        if quality in [VQ4K]:
                            video_quality_url = self.find_video_quality_url(VQ4K, response, decoded_m3u8_url)

                    if video_quality_url == '':
                        if quality in [VQ4K, VQ1080P]:
                            video_quality_url = self.find_video_quality_url(VQ1080P, response, decoded_m3u8_url)

                    if video_quality_url == '':
                        if quality in [VQ4K, VQ1080P, VQ720P]:
                            video_quality_url = self.find_video_quality_url(VQ720P, response, decoded_m3u8_url)

                    if video_quality_url == '':
                        if quality in [VQ4K, VQ1080P, VQ720P, VQ480P]:
                            video_quality_url = self.find_video_quality_url(VQ480P, response, decoded_m3u8_url)

                    if video_quality_url == '':
                        if quality in [VQ4K, VQ1080P, VQ720P, VQ480P, VQ360P]:
                            video_quality_url = self.find_video_quality_url(VQ360P, response, decoded_m3u8_url)

                    # If we didn't find a video url with the desired video quality or lower, use the m3u8 file url
                    if video_quality_url == '':
                        video_url = decoded_m3u8_url
                    else:

                        log("video_quality_url", video_quality_url)

                        # Find out if the altered m3u8 url exists
                        response = session.get(video_quality_url)

                        # log("response.status_code", response.status_code)

                        # if we find a m3u8 file with the altered url, let's use that.
                        # If it is not found, let's use the unaltered url.
                        if response.status_code in [200]:
                            video_url = video_quality_url
                        else:
                            video_url = decoded_m3u8_url

                    log("decoded video_url", video_url)

                    have_valid_url = True
                    no_url_found = False

        # Maybe it's something like this. Let's try and find the youtube id
        # <div id="videoplayer" data-autoplay="false" data-type="youtube" data-color="0567D8" data-url='https://youtu.be/hmGe65Wf9Hw' data-thumb='https://www.gamekings.tv/wp-content/uploads/robocop-terminator-mortal-kombat-11-1280x720.jpg' style='background-image: url(https://www.gamekings.tv/wp-content/uploads/robocop-terminator-mortal-kombat-11-1280x720.jpg);'>
        if have_valid_url:
            pass
        else:
            start_pos_video_url = html_source.find("https://youtu.be/")
            if start_pos_video_url >= 0:
                end_pos_video_url = html_source.find("'", start_pos_video_url)
                if end_pos_video_url >= 0:
                    youtube_id = html_source[start_pos_video_url:end_pos_video_url]
                    youtube_id = youtube_id.replace("https://youtu.be/","")

                    log("youtube_id", youtube_id)

                    have_valid_url = True
                    no_url_found = False

        if have_valid_url:
            pass
        # I guess we try another way
        else:
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
            start_pos_video_url = html_source.find("https://player.vimeo.com/external")
            if start_pos_video_url == -1:
                start_pos_video_url = html_source.find("https://player.vimeo.com/video")
                if start_pos_video_url == -1:
                    start_pos_video_url = html_source.find("https://www.youtube.com/")
                    if start_pos_video_url >= 0:
                        # Ignore a found "https://www.youtube.com/gamekingsextra"
                        start_pos_youtube_gamekingsextra = html_source.find("https://www.youtube.com/gamekingsextra")
                        if start_pos_video_url == start_pos_youtube_gamekingsextra:
                            start_pos_video_url = html_source.find("https://www.youtube.com/", start_pos_youtube_gamekingsextra + 1)
                            if start_pos_video_url == -1:
                                no_url_found = True
                                have_valid_url = False

            # Try to make a valid video url
            if have_valid_url:

                #log("html_source[start_pos_video_url:]", html_source[start_pos_video_url:])

                # Let's only use the video_url part
                html_source_split = str(html_source[start_pos_video_url:]).split()
                video_url = html_source_split[0]

                # Remove the quote on the last position
                if video_url.endswith('"') or video_url.endswith("'"):
                    video_url = video_url[0:len(video_url) - 1]

                log("video_url after split and removing trailing quote", video_url)

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
                # no need to do anything with the vimeo addon, we can use the video_url directly
                pass
            # premium video's on vimeo look like this: https://player.vimeo.com/video/190106340?title=0&autoplay=1&portrait=0&badge=0&color=C7152F
            if video_url.find("player.vimeo.com/video/") > 0:
                # no need to do anything with the vimeo addon, we can use the video_url directly
                pass
            if youtube_id == '':
                if video_url.find("youtube") > 0:
                    youtube_id = str(video_url)
                    youtube_id = youtube_id.replace("https://www.youtube.com/embed/", "")
                    youtube_id = youtube_id.replace("https://www.youtube.com/watch?v=", "")
                    youtube_id = youtube_id.replace("https://www.youtube.com/watch", "")
                    youtube_id = youtube_id.replace("https://www.youtube.com/", "")
                    youtube_id = youtube_id[0:youtube_id.find("?")]

                    log("youtube_id2", youtube_id)

                    video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
            else:
                video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

            log("final video_url", video_url)

            # It was a loooong and twisted walk, but at last we can try and play an actual video file
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Check if it's a twitch live stream
        #
        # example of a live stream: video_url = 'plugin://plugin.video.twitch/?channel_id=57330659&amp;mode=play;'
        elif str(html_source).find(TWITCH_URL_GAMEKINGS_TV) > 0:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30611))
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))


    def find_video_quality_url(self, quality, response, video_quality_url):

        # log("starting find_video_quality_url, this is the input", quality + "/" + str(response)+ "/" + video_url)

        # the video url will be something like this:
        # https://gamekings.gcdn.co/videos//4457_Xp2EEOmd3SpDPb2S/master.m3u8
        # However, the direct link should be something like this:
        # https://gamekings.gcdn.co/videos//4457_Xp2EEOmd3SpDPb2S/index-s1080p-v1-a1.m3u8
        # its composed of 2 parts:
        # part 1:
        # https://gamekings.gcdn.co/videos//4457_Xp2EEOmd3SpDPb2S/
        # part 2:
        # the line found in the m3u8 of the corresponding quality (f.e. index-s1080p-v1-a1.m3u8)

        # lets determine part 1 and 2
        pos_last_slash = video_quality_url.rfind("/")
        if pos_last_slash >= 0:
            first_part = video_quality_url[0:pos_last_slash + 1]
            second_part = video_quality_url[pos_last_slash:]

            # read the m3u8 file line for line and search for the quality. If found: replace the second part with the
            # value of the line in m3u8 file
            for line in response.iter_lines():
                if line:
                    # let's convert the line to prevent python 2/3 troubles
                    line = convertToUnicodeString(line)

                    # log("line", line)

                    # Let's exclude lines with the word "STREAM" in them
                    if line.find(STREAM) >= 0:
                        pass
                    elif line.find(quality) >= 0:
                        second_part = line
                        video_quality_url = first_part + second_part
                    elif line.find(quality.upper()) >= 0:
                        second_part = line
                        video_quality_url = first_part + second_part

            log("adjusted video_quality_url", video_quality_url)

        # log("returning video_quality_url", video_quality_url)

        return video_quality_url