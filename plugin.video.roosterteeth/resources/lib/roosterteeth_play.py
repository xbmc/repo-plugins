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
import re
import urllib.request, urllib.parse, urllib.error
import xbmc
import xbmcgui
import xbmcplugin

from roosterteeth_const import LANGUAGE, SETTINGS, HEADERS, convertToUnicodeString, log, getSoup, LOGINURL_RT, LOGINURL_AH, \
    LOGINURL_FH, LOGINURL_SA, LOGINURL_GA, LOGINURL_TK, LOGINURL_CC, LOGINURL_SP7, VQ4K, VQ1080P, VQ720P, VQ480P, \
    VQ360P, VQ240P


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
        self.PREFERRED_QUALITY = SETTINGS.getSetting('quality')
        self.IS_SPONSOR = SETTINGS.getSetting('is_sponsor')

        log("ARGV", repr(sys.argv))

        # Parse parameters...
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        log("self.video_page_url", self.video_page_url)

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
        dialog_wait = xbmcgui.DialogProgress()

        #
        # Get current list item details...
        #
        # title = xbmc.getInfoLabel("listitem.Title")
        thumbnail_url = xbmc.getInfoImage("list_item.Thumb")
        # studio = xbmc.getInfoLabel("list_item.Studio")
        plot = xbmc.getInfoLabel("list_item.Plot")
        genre = xbmc.getInfoLabel("list_item.Genre")

        session = ''
        try:
            # requests is sooooo nice, respect!
            session = requests.Session()

            # get the page that contains the video
            response = session.get(self.video_page_url, headers=HEADERS)

            html_source = response.text
            html_source = convertToUnicodeString(html_source)

            # is it a sponsored video?
            if str(response.text).find('sponsor-only') >= 0 or str(response.text).find('non-sponsor') >= 0:
                if self.IS_SPONSOR == 'true':
                    try:
                        # we need a NEW (!!!) session
                        session = requests.Session()

                        # get the LOGIN-page
                        if 'achievementhunter' in response.url:
                            response = session.get(LOGINURL_AH)
                        elif 'funhaus' in response.url:
                            response = session.get(LOGINURL_FH)
                        elif 'screwattack' in response.url:
                            response = session.get(LOGINURL_SA)
                        elif 'gameattack' in response.url:
                            response = session.get(LOGINURL_GA)
                        elif 'theknow' in response.url:
                            response = session.get(LOGINURL_TK)
                        elif 'cowchop' in response.url:
                            response = session.get(LOGINURL_CC)
                        elif 'sugarpine7' in response.url:
                            response = session.get(LOGINURL_SP7)
                        else:
                            response = session.get(LOGINURL_RT)

                        log('get login page request, status_code:',  response.status_code)

                        html_source = response.text
                        html_source = convertToUnicodeString(html_source)

                        # log("html_source1", html_source)

                        soup = getSoup(html_source)

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

                        video_urls = soup.findAll('input', attrs={'name': re.compile("_token")}, limit=1)
                        token = str(video_urls[0]['value'])

                        # log("token", token)

                        # set the needed LOGIN-data
                        payload = {'_token': token, 'username': SETTINGS.getSetting('username'),
                                   'password': SETTINGS.getSetting('password')}
                        # post the LOGIN-page with the LOGIN-data, to actually login this session
                        if 'achievementhunter' in response.url:
                            response = session.post(LOGINURL_AH, data=payload)
                        elif 'funhaus' in response.url:
                            response = session.post(LOGINURL_FH, data=payload)
                        elif 'screwattack' in response.url:
                            response = session.post(LOGINURL_SA, data=payload)
                        elif 'gameattack' in response.url:
                            response = session.post(LOGINURL_GA, data=payload)
                        elif 'theknow' in response.url:
                            response = session.post(LOGINURL_TK, data=payload)
                        elif 'cowchop' in response.url:
                            response = session.post(LOGINURL_CC, data=payload)
                        elif 'sugarpine7' in response.url:
                            response = session.get(LOGINURL_SP7)
                        else:
                            response = session.post(LOGINURL_RT, data=payload)

                        log('post login page response, status_code:', response.status_code)

                        html_source = response.text
                        html_source = convertToUnicodeString(html_source)

                        # check that the login was technically ok (status_code 200).
                        # This in itself does NOT mean that the username/password were correct.
                        if response.status_code == 200:
                            pass
                            # check that the username is in the response. If that's the case, the login was ok
                            # and the username and password in settings are ok.
                            if str(response.text).find(SETTINGS.getSetting('username')) >= 0:

                                log('login was successful!', 'login was successful!')

                                # let's try getting the page again after a login, hopefully it contains a link to
                                # the video now
                                response = session.get(self.video_page_url)

                                log("self.video_page_url", self.video_page_url)

                            else:

                                log('login was NOT successful!', 'login was NOT successful!')

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
                            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30104) % (str(response.status_code)))
                            exit(1)

                    except urllib.error.HTTPError as error:

                        log("HTTPError1", error)

                        try:
                            dialog_wait.close()
                            del dialog_wait
                        except:
                            pass
                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (str(error)))
                        exit(1)
                    except:
                        exception = sys.exc_info()[0]

                        log("ExceptionError1", exception)

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

        except urllib.error.HTTPError as error:

            log("HTTPError1", error)

            try:
                dialog_wait.close()
                del dialog_wait
            except:
                pass
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (str(error)))
            exit(1)
        except:
            exception = sys.exc_info()[0]

            log("ExceptionError2", exception)

            try:
                dialog_wait.close()
                del dialog_wait
            except:
                pass
            exit(1)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        video_url = ''
        no_url_found = True
        have_valid_url = False

        match = re.search('\'(.*?m3u8)', html_source, re.I | re.U)

        #index.m3u8:
        #f.e. https://rtv3-video.roosterteeth.com/store/66b4a662c6aba71015e1ecd267a01590-6b7aafe6/ts/index.m3u8:
        #EXTM3U
        #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=11844000,RESOLUTION=1920x1080,CODECS="avc1.4d001f,mp4a.40.2"6b7aafe6-hls_4k-store-66b4a662c6aba71015e1ecd267a01590.m3u8
        #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=11844000,RESOLUTION=1920x1080,CODECS="avc1.4d001f,mp4a.40.2"6b7aafe6-hls_1080p-store-66b4a662c6aba71015e1ecd267a01590.m3u8
        #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=6661000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"6b7aafe6-hls_720p-store-66b4a662c6aba71015e1ecd267a01590.m3u8
        #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3712000,RESOLUTION=854x480,CODECS="avc1.4d001f,mp4a.40.2"6b7aafe6-hls_480p-store-66b4a662c6aba71015e1ecd267a01590.m3u8
        #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2598000,RESOLUTION=640x360,CODECS="avc1.4d001f,mp4a.40.2"6b7aafe6-hls_360p-store-66b4a662c6aba71015e1ecd267a01590.m3u8
        #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1478000,RESOLUTION=426x240,CODECS="avc1.4d001f,mp4a.40.2"6b7aafe6-hls_240p-store-66b4a662c6aba71015e1ecd267a01590.m3u8


        if match:
            if self.PREFERRED_QUALITY == '0':  # Very Low
                quality = VQ240P
            elif self.PREFERRED_QUALITY == '1':  # Low
                quality = VQ360P
            elif self.PREFERRED_QUALITY == '2':  # Medium
                quality = VQ480P
            elif self.PREFERRED_QUALITY == '3':  # High Quality
                quality = VQ720P
            elif self.PREFERRED_QUALITY == '4':  # Very High Quality
                quality = VQ1080P
            elif self.PREFERRED_QUALITY == '5':  # Ultra High Quality
                quality = VQ4K
            else:  # Default in case quality is not found?
                quality = VQ720P

            video_url = str(match.group(1))

            log("video_url", video_url)

            #Change this
            #https://rtv3-video.roosterteeth.com/store/66b4a662c6aba71015e1ecd267a01590-6b7aafe6/ts/index.m3u8
            #to this
            #https://rtv3-video.roosterteeth.com/store/66b4a662c6aba71015e1ecd267a01590-6b7aafe6/ts/6b7aafe6-hls_<quality>-store-66b4a662c6aba71015e1ecd267a01590.m3u8
            #f.e.
            #https://rtv3-video.roosterteeth.com/store/66b4a662c6aba71015e1ecd267a01590-6b7aafe6/ts/6b7aafe6-hls_240p-store-66b4a662c6aba71015e1ecd267a01590.m3u8

            new_index_part_2 = 'hls_' + quality
            video_url_temp = video_url
            video_url_temp = video_url_temp.replace("//", "/")
            video_url_parts = str(video_url_temp).split("/")
            new_index_part_3 = video_url_parts[2]
            part4 = video_url_parts[3]
            new_index_part_4, new_index_part_1 = part4.split("-")
            new_index = new_index_part_1 + '-' + new_index_part_2 + '-' + new_index_part_3 + '-' + new_index_part_4
            video_url_altered = video_url.replace("index", new_index)

            log("video_url_altered", video_url_altered)

            # Find out if the m3u8 file exists
            response = session.get(video_url_altered)

            # log("response.status_code", response.status_code)

            # m3u8 file is found, let's use that. If it is not found, let's use the unaltered video url.
            if response.status_code == 200:
                video_url = video_url_altered

            have_valid_url = True

            log("final video_url", video_url)

        # Play video...
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30107))