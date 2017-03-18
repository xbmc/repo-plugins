# Imports
#
import os
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from gamegurumania_const import SETTINGS, LANGUAGE, IMAGES_PATH, ADDON, DATE, VERSION
from gamegurumania_utils import HTTPCommunicator


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
        
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
            ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        # Parse parameters...
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.video_list_page_url = str(self.video_list_page_url)
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGDEBUG)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            # http://www.ggmania.com/more.php3?next=000&kategory=movie
            pos_of_next = self.video_list_page_url.rfind('next=')
            item_number_str = str(
                self.video_list_page_url[pos_of_next + len('next='):pos_of_next + len('next=') + len('000')])
            item_number = int(item_number_str)
            # the site only skips 10 items per page, seems like a bug. Skip 20 to go onto next new itempage
            item_number_next = item_number + 20
            if item_number_next >= 100:
                item_number_next_str = str(item_number_next)
            else:
                item_number_next_str = '0' + str(item_number_next)
            self.next_url = self.video_list_page_url.replace(item_number_str, item_number_next_str)

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.next_url", str(urllib.unquote_plus(self.next_url))),
                         xbmc.LOGDEBUG)

        #
        # Get the videos...
        #
        self.getVideos()

    #
    # Get videos...
    #
    def getVideos(self):
        #
        # Init
        #
        video_page_url_napdis = ''
        video_page_url_iframe = ''
        video_page_url_youtube = ''
        nadpis_found = False
        iframe_found = False
        youtube_found = False
        thumbnail_url = ''
        list_item = ''
        is_folder = False
        # Create a list for our items.
        listing = []

        # 
        # Get HTML page...
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response...
        soup = BeautifulSoup(html_source)

        # find a title and directly after it a video-link. Some title don't have a video-link and must be skipped. 
        # Find Title
        # <a class="nadpis" name="shadowrun-returns-alpha-gameplay-video-34776" href="http://www.ggmania.com/?smsid=shadowrun-returns-alpha-gameplay-video-34776">Shadowrun Returns - Alpha Gameplay Video</a>
        # Find youtubeID
        # <iframe width="560" height="315" src="http://www.youtube.com/embed/9MiMjQwd2VE" frameborder="0" allowfullscreen="allowfullscreen"></iframe>		
        # <div class="youtube" id="fDZF-jIhhbk" style="width: 640px; height: 360px;">

        video_page_urls = soup.findAll(["a", "iframe", "div"])

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "len(video_page_urls)", str(len(video_page_urls))), xbmc.LOGDEBUG)

        for video_page_url in video_page_urls:

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGDEBUG)

            video_page_url_str = str(video_page_url)
            if video_page_url_str.startswith('<a class="nadpis"'):
                nadpis_found = True
                youtube_found = False
                video_page_url_napdis = video_page_url
            if video_page_url_str.startswith('<iframe'):
                iframe_found = True
                video_page_url_iframe = video_page_url
            if video_page_url_str.startswith('<div class="youtube"'):
                youtube_found = True
                video_page_url_youtube = video_page_url
            if (nadpis_found == True and iframe_found == True) or (nadpis_found == True and youtube_found == True):
                # Find Title
                # <a class="nadpis" name="shadowrun-returns-alpha-gameplay-video-34776" href="http://www.ggmania.com/?smsid=shadowrun-returns-alpha-gameplay-video-34776">Shadowrun Returns - Alpha Gameplay Video</a>

                video_page_url_napdis_str = str(video_page_url_napdis)
                start_pos_title = video_page_url_napdis_str.find(">") + 1
                title = video_page_url_napdis_str[start_pos_title:]
                title = title.replace("</a>", "")

                title = title.capitalize()
                title = title.replace('/', ' ')
                title = title.replace('&amp;', '&')
                title = title.replace(' i ', ' I ')
                title = title.replace(' amp ', ' & ')
                title = title.replace(' ii ', ' II ')
                title = title.replace(' iii ', ' III ')
                title = title.replace(' iv ', ' IV ')
                title = title.replace(' v ', ' V ')
                title = title.replace(' vi ', ' VI ')
                title = title.replace(' vii ', ' VII ')
                title = title.replace(' viii ', ' VIII ')
                title = title.replace(' ix ', ' IX ')
                title = title.replace(' x ', ' X ')
                title = title.replace(' xi ', ' XI ')
                title = title.replace(' xii ', ' XII ')
                title = title.replace(' xiii ', ' XIII ')
                title = title.replace(' xiv ', ' XIV ')
                title = title.replace(' xv ', ' XV ')
                title = title.replace(' xvi ', ' XVI ')
                title = title.replace(' xvii ', ' XVII ')
                title = title.replace(' xviii ', ' XVIII ')
                title = title.replace(' xix ', ' XIX ')
                title = title.replace(' xx ', ' XXX ')
                title = title.replace(' xxi ', ' XXI ')
                title = title.replace(' xxii ', ' XXII ')
                title = title.replace(' xxiii ', ' XXIII ')
                title = title.replace(' xxiv ', ' XXIV ')
                title = title.replace(' xxv ', ' XXV ')
                title = title.replace(' xxvi ', ' XXVI ')
                title = title.replace(' xxvii ', ' XXVII ')
                title = title.replace(' xxviii ', ' XXVIII ')
                title = title.replace(' xxix ', ' XXIX ')
                title = title.replace(' xxx ', ' XXX ')

                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "title", str(title)), xbmc.LOGDEBUG)

                # Find youtubeID
                # <iframe width="560" height="315" src="http://www.youtube.com/embed/9MiMjQwd2VE" frameborder="0" allowfullscreen="allowfullscreen"></iframe>				
                # <div class="youtube" id="fDZF-jIhhbk" style="width: 640px; height: 360px;">
                if iframe_found == True:
                    youtubeID = str(video_page_url_iframe['src'])
                    youtubeID = youtubeID.replace("//www.youtube.com/embed/", '')
                if youtube_found == True:
                    youtubeID = str(video_page_url_youtube['id'])

                youtube_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % youtubeID

                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "youtube_url", str(youtube_url)), xbmc.LOGDEBUG)

                # Add to list...
                list_item = xbmcgui.ListItem(title, thumbnailImage=thumbnail_url)
                list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
                list_item.setProperty('IsPlayable', 'true')
                is_folder = False
                url = youtube_url
                # Add refresh option to context menu
                list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
                # Add our item to the listing as a 3-element tuple.
                listing.append((url, list_item, is_folder))

                nadpis_found = False
                iframe_found = False
                youtube_found = False

        # Next page entry...
        if self.next_page_possible == 'True':
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-play", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
