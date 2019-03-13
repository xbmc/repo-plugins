#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library

standard_library.install_aliases()
from builtins import object
import requests
import sys
import urllib.request, urllib.parse, urllib.error
import xbmc
import xbmcgui
import xbmcplugin

from roosterteeth_const import LANGUAGE, SETTINGS, HEADERS, convertToUnicodeString, log, VQ4K, VQ1080P, VQ720P, \
    VQ480P, VQ360P, VQ240P, ROOSTERTEETH_AUTHORIZATION_URL, KODI_ROOSTERTEETH_ADDON_CLIENT_ID


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

        # log("ARGV", repr(sys.argv))

        # Parse parameters...
        self.functional_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['functional_url'][0]
        self.technical_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['technical_url'][0]
        self.title = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = convertToUnicodeString(self.title)
        self.is_sponsor_only = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['is_sponsor_only'][0]

        log("self.functional_url", self.functional_url)

        log("self.technical_url", self.technical_url)

        # let's use the technical url
        self.url = self.technical_url

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
        title = xbmc.getInfoLabel("listitem.Title")
        # thumbnail_url = xbmc.getInfoImage("list_item.Thumb")
        studio = xbmc.getInfoLabel("list_item.Studio")
        mediatype = xbmc.getInfoLabel("list_item.Mediatype")
        # plot = xbmc.getInfoLabel("list_item.Plot")
        # genre = xbmc.getInfoLabel("list_item.Genre")

        session = ''
        try:
            # requests is sooooo nice, respect!
            session = requests.Session()

            if self.is_sponsor_only == "True":
                must_login_sponsored_user = True
                video_is_not_yet_available = False
            else:
                # try and get the non-sponsored video without being logged in
                # get the page that contains the video
                response = session.get(self.url, headers=HEADERS)

                html_source = response.text
                html_source = convertToUnicodeString(html_source)

                # log("html_source without authorization", html_source)

                # sometimes a non-sponsor video is not available. However this video will (!) be available for a sponsor
                # after logging in. One of the perks of being a sponsor, i reckon. This is what you get back in that
                # case: {"access":false,"message":"not yet available"}
                if html_source.find("not yet available") >= 0:
                    # let's try and get this non-sponsored video after login in the sponsored user then
                    must_login_sponsored_user = True
                    video_is_not_yet_available = True
                else:
                    must_login_sponsored_user = False
                    video_is_not_yet_available = False

            #log("must_login_sponsored_user", must_login_sponsored_user)

            # login if needed
            if must_login_sponsored_user:
                # is the sponsor switch in the settings of this addon turned on?
                if self.IS_SPONSOR == 'true':
                    # is it a sponsored video or not?
                    if self.is_sponsor_only == "True":
                        log("logging in with user for this sponsored video", self.url)
                    else:
                        log("logging in with user for this non-sponsored video", self.url)

                    # let's try and get authorization
                    try:
                        # we need a NEW (!!!) session
                        session = requests.Session()

                        # set the needed authorization-data
                        payload = {"client_id": KODI_ROOSTERTEETH_ADDON_CLIENT_ID,
                                   "grant_type": "password", "password": SETTINGS.getSetting('password'),
                                   "scope": "user public", "username": SETTINGS.getSetting('username')}

                        # post the payload to the authorization url, to actually get an access token (oauth) back
                        response = session.post(ROOSTERTEETH_AUTHORIZATION_URL, data=payload)

                        log('post login page response, status_code:', response.status_code)

                        html_source = response.text
                        html_source = convertToUnicodeString(html_source)

                        # log("html_source getting authorization", html_source)

                        # check that the login was technically ok (status_code 200).
                        # This in itself does NOT mean that the username/password were correct.
                        if response.status_code == 200:
                            pass
                            # {"access_token":"eyJ0eXAiOiJKV1QiLCJ<SOMETHINGSOMETHING>","token_type":"bearer","expires_
                            # check that we get back an access_token (oauth)
                            # for some reason html_source can't be loaded in json, so we have to do it the hard way :(
                            start_pos_access_token_url = html_source.find('"access_token":"')
                            if start_pos_access_token_url >= 0:

                                log('login was successful!', 'login was successful!')

                                start_pos_access_token_url = start_pos_access_token_url + len('"access_token":"')
                                end_pos_access_token = html_source.find('"', start_pos_access_token_url)
                                access_token = html_source[start_pos_access_token_url:end_pos_access_token]

                                # log("access_token", access_token)

                                # let's make a new header dictionary
                                headers_with_access_token = HEADERS
                                # add the access token to the dictionary
                                # see https://stackoverflow.com/questions/29931671/making-an-api-call-in-python-with-an-api-that-requires-a-bearer-token
                                # this is some specific magic for setting the authorization in the header
                                headers_with_access_token['Authorization'] = "Bearer " + access_token

                                # log("headers_with_access_token", headers_with_access_token)

                                # let's try getting the page with the received access_code
                                response = session.get(self.url, headers=headers_with_access_token)

                                html_source = response.text
                                html_source = convertToUnicodeString(html_source)

                                # log("html_source with authorization", html_source)

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
                            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30104) % (convertToUnicodeString(response.status_code)))
                            exit(1)

                    except urllib.error.HTTPError as error:

                        log("HTTPError1", error)

                        try:
                            dialog_wait.close()
                            del dialog_wait
                        except:
                            pass
                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (convertToUnicodeString(error)))
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

                    if video_is_not_yet_available:
                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30110))
                    else:
                        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30105))
                    exit(1)

        except urllib.error.HTTPError as error:

            log("HTTPError1", error)

            try:
                dialog_wait.close()
                del dialog_wait
            except:
                pass
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (convertToUnicodeString(error)))
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

        video_url = ''
        no_url_found = True
        have_valid_url = False

        # for some reason html_source can't be loaded in json, so we have to do it the hard way :(
        start_pos_m3u8_url = html_source.find('"url":"')
        if start_pos_m3u8_url == -1:
            found_m3u8_url = False
        else:
            start_pos_m3u8_url = start_pos_m3u8_url + len('"url":"')
            end_pos_m3u8_url = html_source.find('"', start_pos_m3u8_url)
            if end_pos_m3u8_url == -1:
                found_m3u8_url = False
            else:
                m3u8_url = html_source[start_pos_m3u8_url:end_pos_m3u8_url]

                log("m3u8_url", m3u8_url)

                found_m3u8_url = True

        log("found_m3u8_url", found_m3u8_url)

        if found_m3u8_url:
            # for some reason u0026 is present in the url, it should have been an ampersand
            # let's correct that
            m3u8_url = m3u8_url.replace('u0026', '&')

            log("corrected m3u8_url", m3u8_url)

            # try and get the non-sponsored video without being logged in
            # get the page that contains the video
            response = session.get(m3u8_url, headers=HEADERS)
            if response.status_code == 200:

                html_source = response.text
                html_source = convertToUnicodeString(html_source)

                # log("html_source m3u8 file", html_source)

                # determine the wanted video quality
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

                video_url = m3u8_url

                log("video_url", video_url)

                # an example of the content of a m3u8 file. Not all the resolutions will be there as most videos don't
                # have an 4k option:
                # #EXTM3U
                # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=21589000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"
                # aef4654c-hls_4k-rebuilds-4030.mp4.m3u8
                # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=21589000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"
                # aef4654c-hls_1080p-rebuilds-4030.mp4.m3u8
                # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=8281000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"
                # aef4654c-hls_720p-rebuilds-4030.mp4.m3u8
                # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=6370000,RESOLUTION=854x480,CODECS="avc1.4d001f,mp4a.40.2"
                # aef4654c-hls_480p-rebuilds-4030.mp4.m3u8
                # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4093000,RESOLUTION=640x360,CODECS="avc1.4d001f,mp4a.40.2"
                # aef4654c-hls_360p-rebuilds-4030.mp4.m3u8
                # #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2941000,RESOLUTION=426x240,CODECS="avc1.4d001f,mp4a.40.2"
                # aef4654c-hls_240p-rebuilds-4030.mp4.m3u8

                video_url_altered = ''
                # read the m3u8 file line for line and search for the quality. If found: alter the url of the m3u8 file.
                for line in response.iter_lines():
                    if line:
                        # let's convert the line to prevent python 2/3 troubles
                        line = convertToUnicodeString(line)

                        # log("line", line)
                        
                        if line.find(quality) >= 0:
                            video_url_altered = video_url.replace("index.m3u8", line)
                        elif line.find(quality.upper()) >= 0:
                            video_url_altered = video_url.replace("index.m3u8", line)

                if video_url_altered == '':
                    pass
                else:

                    log("video_url_altered", video_url_altered)

                    # Find out if the altered m3u8 url exists
                    response = session.get(video_url_altered)

                    log("response.status_code", response.status_code)

                    # if we find a m3u8 file with the altered url, let's use that.
                    # If it is not found, let's use the unaltered url.
                    if response.status_code == 200:
                        video_url = video_url_altered

                have_valid_url = True

                log("final video_url", video_url)
            else:
                have_valid_url = False

        # Play video...
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30107))