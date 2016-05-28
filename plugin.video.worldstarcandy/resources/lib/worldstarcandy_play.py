#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from worldstarcandy_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from worldstarcandy_utils import HTTPCommunicator
import sys
import urlparse
import xbmc
import xbmcgui
import xbmcplugin


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
        self.VIDEO = SETTINGS.getSetting('video')

        if (self.DEBUG) == 'true':
            print 'Python Version: ' + sys.version
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters...
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        if (self.DEBUG) == 'true':
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
        is_folder = False
        # Create a list for our items.
        listing = []
        unplayable_media_file = False
        have_valid_url = False

        #
        # Get current list item details...
        #
        # title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8")
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

        # find the video_url (f.e. http://www.worldstarhiphop.com/embed/76200)
        html_source = HTTPCommunicator().get(self.video_page_url)
        begin_pos_video_file = str(html_source).find("http://www.worldstarhiphop.com/embed/")
        end_pos_video_file = str(html_source).find('&quot;', begin_pos_video_file)
        video_url = html_source[begin_pos_video_file:end_pos_video_file]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGNOTICE)

        try:
            # Get HTML page...
            html_source = HTTPCommunicator().get(video_url)

            # It should contain something like this:
            # <script type="text/javascript">
            # var file = "http://hw-videos.worldstarhiphop.com/u/vid/2015/11/18/wioletta_NW_FNl_1.mp4";
            # var mfile = "http://hw-videos.worldstarhiphop.com/u/vid/2015/11/18/wioletta_NW_FNl_1.mp4";
            # var thumb = "http://hw-static.worldstarhiphop.com/u/pic/2015/11/18/WiolettaPawlukGoldVer-Thumbewewdewdedwedw2.jpg";

            if str(html_source).find("file") >= 0:
                #
                # Make the video url
                begin_pos_video_file = str(html_source).find("http", str(html_source).find("file"))
                end_pos_video_file = str(html_source).find('"', begin_pos_video_file)
                video_url = html_source[begin_pos_video_file:end_pos_video_file]
                have_valid_url = True
            else:
                unplayable_media_file = True
        except:
            unplayable_media_file = True

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "have_valid_url", str(have_valid_url)), xbmc.LOGNOTICE)
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGNOTICE)

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
