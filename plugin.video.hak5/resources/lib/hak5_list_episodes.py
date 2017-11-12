#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import requests
import sys
import urllib
import urlparse
import re
import HTMLParser
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from hak5_const import ADDON, LANGUAGE, IMAGES_PATH, HEADERS, DATE, VERSION

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

        # Parse parameters
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        self.video_list_page_url = str(self.video_list_page_url).replace('https', 'http')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                 xbmc.LOGDEBUG)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            pos_of_page = self.video_list_page_url.rfind('page/')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('page/'):pos_of_page + len('page/') + len('000')])
                page_number = int(page_number_str)
                page_number_next = page_number + 1
                if page_number_next >= 100:
                    page_number_next_str = str(page_number_next)
                elif page_number_next >= 10:
                    page_number_next_str = '0' + str(page_number_next)
                else:
                    page_number_next_str = '00' + str(page_number_next)
                self.next_url = str(self.video_list_page_url).replace(page_number_str, page_number_next_str)

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
        previous_video_page_url = ''
        after_tab_episodes = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(self.video_list_page_url, headers=HEADERS)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

        # Parse response
        soup = BeautifulSoup(html_source)

        # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
        #     ADDON, VERSION, DATE, "html_source", str(html_source)), xbmc.LOGDEBUG)

        # <div id="post-8843" class="video-item post-8843 post type-post status-publish format-video has-post-thumbnail hentry category-episodes category-hak5 category-season-22 tag-darren-kitchen tag-hack-across-the-planet tag-hak-5 tag-pseudocode-for-life post_format-post-format-video">
        # <div class="item-thumbnail">
        # <a href="https://www.hak5.org/episodes/hak5-2216-pseudocode-for-life-2-hack-across-the-planet">
        # <img width="520" height="293" src="https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-520x293.jpg" class="attachment-thumb_520x293 size-thumb_520x293 wp-post-image" alt="" srcset="https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-520x293.jpg 520w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-150x84.jpg 150w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-300x169.jpg 300w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-1024x576.jpg 1024w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-260x146.jpg 260w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-356x200.jpg 356w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-370x208.jpg 370w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-180x101.jpg 180w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-130x73.jpg 130w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-748x421.jpg 748w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2-624x351.jpg 624w, https://www.hak5.org/wp-content/uploads/2017/06/hak5-2216-pseudocode-for-life-2.jpg 1280w" sizes="(max-width: 520px) 100vw, 520px" /> <div class="link-overlay fa fa-play"></div>
        # </a>
        # </div>
        # <div class="item-head">
        # <h3><a href="https://www.hak5.org/episodes/hak5-2216-pseudocode-for-life-2-hack-across-the-planet" rel="8843" title="Hak5 2216 – Pseudocode for Life 2 – Hack Across the Planet">Hak5 2216 &#8211; Pseudocode for Life 2 &#8211; Hack Across the Planet</a>
        # </h3>
        # <div class="item-info hidden">
        # <span class="item-author"><a href="https://www.hak5.org/author/snubs" title="Posts by Shannon Morse" rel="author">Shannon Morse</a></span>
        # <span class="item-date">June 28, 2017</span>
        # <div class="item-meta">
        # <span><i class="fa fa-eye"></i> 0</span> <span><i class="fa fa-comment"></i> 0</span> <span><i class="fa fa-thumbs-up"></i> 1</span>
        # </div>
        # </div>
        # </div>
        # <div class="item-content hidden">
        # <p>It&#8217;s better to regret something you have done than something you haven&#8217;t. Regular episodes resume August 2nd. UK meetups July 10-14. Sign up at https://HackAcrossThePlanet.com https://HackAcrossThePlanet.com &#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;- Shop: http://www.hakshop.com Support: http://www.patreon.com/threatwire Subscribe: http://www.youtube.com/hak5 Our Site: http://www.hak5.org Contact Us: http://www.twitter.com/hak5 Threat Wire RSS: https://shannonmorse.podbean.com/feed/ Threat Wire iTunes: https://itunes.apple.com/us/podcast/threat-wire/id1197048999 Help us with Translations! http://www.youtube.com/timedtext_cs_panel?tab=2&#038;c=UC3s0BtrBJpwNDaflRSoiieQ &#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8212;</p>
        # </div>
        # <div class="clearfix"></div>
        # </div>

        episodes = soup.findAll('div', attrs={'id': re.compile("^" + 'post')})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "len(episodes)", str(len(episodes))), xbmc.LOGDEBUG)

        for episode in episodes:

            # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            #     ADDON, VERSION, DATE, "episode", str(episode)), xbmc.LOGDEBUG)

            video_page_url = episode.a['href']

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGDEBUG)

            try:
                thumbnail_url = episode.img['src']
            except:
                thumbnail_url = ''

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGDEBUG)

            pos_of_title_start = str(episode).find('title="') + len('title="')
            pos_of_title_end = str(episode).find('"', pos_of_title_start)
            title = str(episode)[pos_of_title_start:pos_of_title_end]

            # Clean up title
            try:
                title = title.encode('utf-8')
            except:
                pass

            title = title.replace('-', ' ')
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
            title = title.replace('  ', ' ')
            # welcome to unescaping-hell
            title = title.replace('&amp;#039;', "'")
            title = title.replace('&amp;#39;', "'")
            title = title.replace('&amp;quot;', '"')
            title = title.replace("&#039;", "'")
            title = title.replace("&#39;", "'")
            title = title.replace('&amp;amp;', '&')
            title = title.replace('&amp;', '&')
            title = title.replace('&quot;', '"')
            title = title.replace('&ldquo;', '"')
            title = title.replace('&rdquo;', '"')
            title = title.replace('&rsquo;', "'")

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "title", str(title)), xbmc.LOGDEBUG)

            # lets find the blog date month and year
            search_for_string = 'https://www.hak5.org/wp-content/uploads/'
            blog_date = episode.findAll('img', attrs={'src': re.compile('^' + search_for_string)})
            blog_date = str(blog_date)
            blog_date_year_start_pos = blog_date.find(search_for_string) + len(search_for_string)
            blog_date_year_end_pos = blog_date.find('/', blog_date_year_start_pos)
            blog_date_year = blog_date[blog_date_year_start_pos: blog_date_year_end_pos]

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "blog_date_year", str(blog_date_year)), xbmc.LOGDEBUG)

            blog_date_month_start_pos = blog_date_year_end_pos + 1
            blog_date_month_end_pos = blog_date_month_start_pos + 2
            blog_date_month = blog_date[blog_date_month_start_pos:blog_date_month_end_pos]

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "blog_date_month", str(blog_date_month)), xbmc.LOGDEBUG)

            # lets find the blog date day
            blog_date = episode.findAll('span', attrs={'class': re.compile("^" + 'item-date')})

            if len(blog_date) == 0:
                blog_date_day = '00'
            else:
                blog_date = str(blog_date[0].text)
                blog_date_day_start_pos = blog_date.find(',') - 2
                blog_date_day_end_pos = blog_date_day_start_pos + 2
                blog_date_day = blog_date[blog_date_day_start_pos:blog_date_day_end_pos]

                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "blog_date_day", str(blog_date_day)), xbmc.LOGDEBUG)

            video_date = blog_date_year + '-' + blog_date_month + '-' + blog_date_day + ' 00:00:01'

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_date", str(video_date)), xbmc.LOGDEBUG)

            # Unescaping the plot
            try:
                plot =  HTMLParser.HTMLParser().unescape(episode.p.text)
            except:
                plot = title

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "plot", str(plot)), xbmc.LOGDEBUG)

            add_sort_methods()

            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
            # Add episode  info to context menu
            context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video",
                              {"title": title, "studio": ADDON, "dateadded": video_date, "year": blog_date_year,
                               "plot": plot})
            list_item.setInfo("mediatype", "video")
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url, "title": title}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = False
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            list_item = xbmcgui.ListItem(LANGUAGE(30200), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-episodes", "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
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