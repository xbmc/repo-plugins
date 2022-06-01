from __future__ import absolute_import
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import sys
import urllib.request, urllib.parse, urllib.error
import requests
import xbmc
import xbmcgui
import xbmcplugin
from .gamegurumania_const import LANGUAGE, IMAGES_PATH, ADDON, DATE, VERSION, HEADERS, convertToUnicodeString, log, getSoup

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

        log("ARGV", repr(sys.argv))

        # Parse parameters
        try:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
            self.video_list_page_url = str(self.video_list_page_url)
            self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except KeyError:
            self.plugin_category = LANGUAGE(30000)
            self.video_list_page_url = "https://www.ggmania.com/more.php3?next=000"
            self.next_page_possible = "True"

        log("self.video_list_page_url", self.video_list_page_url)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            # https://www.ggmania.com/more.php3?next=000&kategory=movie
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
                ADDON, VERSION, DATE, "self.next_url", str(urllib.parse.unquote_plus(self.next_url))),
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
        thumbnail_url = ''
        nadpis_found = False
        iframe_found = False
        youtube_found = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(self.video_list_page_url, headers=HEADERS, verify=False)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # <b><a class="nadpis" name="middle-earth-shadow-of-war-gameplay-43762" href="https://www.ggmania.com/?smsid=middle-earth-shadow-of-war-gameplay-43762">Middle-earth: Shadow of War Gameplay</a></b></font><b><font color="black" size="-1" face="arial,helvetica"> - movie</font></b><br />
        # <font style="color:#000080;text-decoration:none" face="arial,helvetica"><small>(hx) 09:46 AM EDT - Jul,17 2017
        #
        # </small></font><a class="koment" href="https://www.ggmania.com/cf.php3?show=43762">Post a comment</a><br /><font class="textik"> Warner Bros and Monolith have shared a video, showing 40 minutes of new gameplay footage from Middle-earth: Shadow of War. This video showcases some of the new skills, abilities and upgrades, as well as the games enhanced combat mechanics and its improved environments. Middle Earth: Shadow of War is currently planned for an October 10th.
        # <br /> <br />
        # <center>
        # <iframe src="https://player.twitch.tv/?video=v159159060&amp;autoplay=false" frameborder="0" allowfullscreen="true" scrolling="no" height="378" width="620"></iframe><a href="https://www.twitch.tv/monolithlive?tt_medium=live_embed&amp;tt_content=text_link" style="padding:2px 0px 4px; display:block; width:345px; font-weight:normal; font-size:10px; text-decoration:underline;">Watch live video from monolithlive on www.twitch.tv</a>
        # </center> </font></td></tr>

        items = soup.findAll("tr")

        log("len(items", len(items))

        for item in items:

            # Skip these items
            if str(item).find('youtube') < 0:

                log("skipped item without youtube", item)

                continue

            log("item", item)

            try:
                youtubeID = item.div['id']
            except KeyError as error:

                log("skipped item without youtube id1", item)

                continue

            except TypeError as error:

                log("skipped item without youtube id2", item)

                continue

            log("youtubeID", youtubeID)

            title = item.a.string

            title = title.capitalize()
            title = title.replace('/', ' ')
            title = title.replace(' i ', ' I ')
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

            log("title", title)

            youtube_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % youtubeID

            log("youtube_url", youtube_url)

            item_string = str(item)
            start_pos_of_plot = item_string.find('"textik"> ', 0) + len('"textik"> ')
            end_pos_of_plot = item_string.find('<', start_pos_of_plot)
            plot = item_string[start_pos_of_plot:end_pos_of_plot]

            log("plot", plot)

            meta = {'plot': plot,
                    'duration': '',
                    'year': '',
                    'dateadded': ''}

            add_sort_methods()

            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
            # Add episode  info to context menu
            context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

            # Add to list...
            list_item = xbmcgui.ListItem(title, thumbnailImage=thumbnail_url)
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            is_folder = False
            url = youtube_url

            log("url", url)

            list_item.setInfo("mediatype", "video")
            list_item.setInfo("video", meta)
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry...
        if self.next_page_possible == 'True':
            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))

            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-play", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = True
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
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


def add_sort_methods():
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_DURATION,xbmcplugin.SORT_METHOD_EPISODE]
    for method in sort_methods:
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=method)