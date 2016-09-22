#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from worldstarhiphop_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from worldstarhiphop_utils import HTTPCommunicator
import sys
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import YDStreamExtractor
import re
from BeautifulSoup import BeautifulSoup


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
        self.VIDEO = SETTINGS.getSetting('video')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
            ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        # Parse parameters...
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGDEBUG)

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
        is_folder = False
        # Create a list for our items.
        listing = []
        unplayable_media_file = False
        have_valid_url = False

        #
        # Get current list item details...
        #
        #title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8")
        thumbnail_url = xbmc.getInfoImage("ListItem.Thumb")
        studio = unicode(xbmc.getInfoLabel("ListItem.Studio"), "utf-8")
        plot = unicode(xbmc.getInfoLabel("ListItem.Plot"), "utf-8")
        genre = unicode(xbmc.getInfoLabel("ListItem.Genre"), "utf-8")

        #
        # Show wait dialog while parsing data...
        #
        dialogWait = xbmcgui.DialogProgress()
        dialogWait.create(LANGUAGE(30504), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        video_url = self.video_page_url

        try:
            vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
            video_url = vid.streamURL()
            have_valid_url = True
        except:
            # Maybe it's an 18+ video ?!
            #
            # Get HTML page...
            #
            html_source = HTTPCommunicator().get(video_url)
            # A bit of a dirty hack, but let's try it anyway...
            # so.addVariable("file","http://hw-videos.worldstarhiphop.com/u/vid/2015/09/SAWGSqGpaohk.mp4");
            if str(html_source).find("file") >= 0:
                # Seems like it's an 18+ video
                begin_pos_video_file = str(html_source).find("http", str(html_source).find("file"))
                end_pos_video_file = str(html_source).find('"', begin_pos_video_file)
                video_url = html_source[begin_pos_video_file:end_pos_video_file]
                have_valid_url = True
            else:
                # Maybe it's a youtube video then ?!
                if str(html_source).find("www.youtube.com/embed") >= 0:
                    # Seems like it's an youtube video
                    # <iframe src="http://www.youtube.com/embed/1xcxn7pOYCg?autoplay=1" width="640" height="390" frameborder="0"></iframe>
                    soup = BeautifulSoup(html_source)
                    # look for http youtube
                    video_urls = soup.findAll('iframe', attrs={'src': re.compile("^http://www.youtube.com/embed")}, limit=1)
                    if len(video_urls) == 0:
                        # look for https youtube
                        video_urls = soup.findAll('iframe', attrs={'src': re.compile("^https://www.youtube.com/embed")}, limit=1)
                        if len(video_urls) == 0:
                            unplayable_media_file = True
                        else:
                            video_url = video_urls[0]['src']
                            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)
                            # make youtube plugin url
                            pos_of_last_question_mark = video_url.rfind("?")
                            video_url = video_url[0: pos_of_last_question_mark]
                            video_url_len = len(video_url)
                            youtubeID = video_url[len("https://www.youtube.com/embed/"):video_url_len]
                            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
                            have_valid_url = True
                            video_url = youtube_url
                    else:
                        video_url = video_urls[0]['src']
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)
                        # make youtube plugin url
                        pos_of_last_question_mark = video_url.rfind("?")
                        video_url = video_url[0: pos_of_last_question_mark]
                        video_url_len = len(video_url)
                        youtubeID = video_url[len("http://www.youtube.com/embed/"):video_url_len]
                        youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
                        have_valid_url = True
                        video_url = youtube_url
                else:
                    unplayable_media_file = True

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "have_valid_url", str(have_valid_url)), xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)

        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)

        #
        # Alert user
        #
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))
        #
        # The End
        #