#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import object
from datetime import datetime, timedelta
import os
import requests
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import json

from resources.lib.dumpert_const import LANGUAGE, IMAGES_PATH, SETTINGS, convertToUnicodeString, log, SFW_HEADERS, \
    NSFW_HEADERS, \
    DAY, WEEK, MONTH, DAY_TOPPERS_URL, WEEK_TOPPERS_URL, MONTH_TOPPERS_URL, LATEST_URL, VIDEO_QUALITY_MOBILE, \
    VIDEO_QUALITY_TABLET, VIDEO_QUALITY_720P


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

        # log("ARGV", repr(sys.argv))

        # Parse parameters
        try:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.next_page_possible = \
            urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except KeyError:
            self.plugin_category = LANGUAGE(30001)
            self.next_page_possible = "True"
        try:
            self.period = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['period'][0]
        except KeyError:
            self.period = ""
        try:
            self.days_deducted_from_today = \
            urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['days_deducted_from_today'][0]
        except KeyError:
            self.days_deducted_from_today = "0"
        try:
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        except KeyError:
            # If the only-show-new-videos-category switch is turned on, this will be empty the first time
            if self.period == "":
                self.video_list_page_url = LATEST_URL
            # If period is filled in we will construct the url
            else:
                self.video_list_page_url = ""

        log("self.video_list_page_url", self.video_list_page_url)

        self.next_url = ""

        # Constuct the next url based on days_deducted_from_today
        if self.period == DAY or self.period == WEEK or self.period == MONTH:
            # For some strange reason converting a string to a datetime object does NOT work here :(
            # Thus we have to do this silly stuff to be able to determine the next_url
            current_url_datetime_object = datetime.now()
            next_url_datetime_object = datetime.now()

            # log("self.days_deducted_from_today", self.days_deducted_from_today)

            self.days_deducted_from_today = int(self.days_deducted_from_today)
            if self.period == DAY:
                # If we don't have a current video list page url, lets construct it
                if self.video_list_page_url == "":
                    current_url_datetime_object = current_url_datetime_object - timedelta(
                        days=self.days_deducted_from_today)
                    # https://api-live.dumpert.nl/mobile_api/json/video/top5/dag/2019-09-19/
                    self.video_list_page_url = DAY_TOPPERS_URL + current_url_datetime_object.strftime('%Y-%m-%d')

                    # log("Generated self.video_list_page_url day", self.video_list_page_url)

                self.days_deducted_from_today = self.days_deducted_from_today + 1
                # Let's deduct all the cumulated days
                next_url_datetime_object = next_url_datetime_object - timedelta(days=self.days_deducted_from_today)
                self.days_deducted_from_today = str(self.days_deducted_from_today)
                # https://api-live.dumpert.nl/mobile_api/json/video/top5/dag/2019-09-18/
                # This should be an url of the day before the date of the current video url
                self.next_url = DAY_TOPPERS_URL + next_url_datetime_object.strftime('%Y-%m-%d')

            elif self.period == WEEK:
                # If we don't have a current video list page url, lets construct it
                if self.video_list_page_url == "":
                    current_url_datetime_object = current_url_datetime_object - timedelta(
                        days=self.days_deducted_from_today)
                    # For some reason date.strftime('%Y%W') will now contain the weeknumber that is 1 below the weeknumber should be for the site
                    # Let's add a week to fix that
                    current_url_datetime_object = current_url_datetime_object + timedelta(days=7)
                    # https://api-live.dumpert.nl/mobile_api/json/video/top5/week/201938/
                    self.video_list_page_url = WEEK_TOPPERS_URL + current_url_datetime_object.strftime('%Y%W')

                    # log("Generated self.video_list_page_url week", self.video_list_page_url)

                # For some reason date.strftime('%Y%W') will now contain the weeknumber that is 1 below the weeknumber should be for the site
                # Let's add a week to fix that
                next_url_datetime_object = next_url_datetime_object + timedelta(days=7)
                # Let's deduct all the cumulated days
                self.days_deducted_from_today = self.days_deducted_from_today + 7
                next_url_datetime_object = next_url_datetime_object - timedelta(days=self.days_deducted_from_today)

                # Let's skip week "00"
                if next_url_datetime_object.strftime('%W') == "00":
                    # log("skipping week 00", "skipping week 00")

                    self.days_deducted_from_today = self.days_deducted_from_today + 7
                    next_url_datetime_object = next_url_datetime_object - timedelta(days=7)

                self.days_deducted_from_today = str(self.days_deducted_from_today)
                # https://api-live.dumpert.nl/mobile_api/json/video/top5/week/201937/
                self.next_url = WEEK_TOPPERS_URL + next_url_datetime_object.strftime('%Y%W')

            elif self.period == MONTH:
                # If we don't have a current video list page url, lets construct it
                if self.video_list_page_url == "":
                    current_url_datetime_object = current_url_datetime_object - timedelta(
                        days=self.days_deducted_from_today)
                    # https://api-live.dumpert.nl/mobile_api/json/video/top5/maand/201909/
                    self.video_list_page_url = MONTH_TOPPERS_URL + current_url_datetime_object.strftime('%Y%m')

                    # log("Generated self.video_list_page_url month", self.video_list_page_url)

                current_url_datetime_object = current_url_datetime_object - timedelta(
                    days=self.days_deducted_from_today)

                self.days_deducted_from_today = self.days_deducted_from_today + 27
                # Let's deduct all the cumulated days
                next_url_datetime_object = next_url_datetime_object - timedelta(days=self.days_deducted_from_today)

                # If the year/month didn't change, up the days deducted some more
                if current_url_datetime_object.strftime('%Y%m') == next_url_datetime_object.strftime('%Y%m'):
                    # log("forcing next month", "forcing next month")

                    self.days_deducted_from_today = self.days_deducted_from_today + 5
                    # Let's deduct 5 more days
                    next_url_datetime_object = next_url_datetime_object - timedelta(days=5)

                self.days_deducted_from_today = str(self.days_deducted_from_today)
                # https://api-live.dumpert.nl/mobile_api/json/video/top5/maand/201908/
                self.next_url = MONTH_TOPPERS_URL + next_url_datetime_object.strftime('%Y%m')

            log("self.next_url", self.next_url)

        # "https://api-live.dumpert.nl/mobile_api/json/video/latest/0/"
        else:
            # Determine current page number and base_url
            # find last slash
            pos_of_last_slash = self.video_list_page_url.rfind('/')
            # remove last slash
            self.video_list_page_url = self.video_list_page_url[0: pos_of_last_slash]
            pos_of_last_slash = self.video_list_page_url.rfind('/')
            self.base_url = self.video_list_page_url[0: pos_of_last_slash + 1]
            self.current_page = self.video_list_page_url[pos_of_last_slash + 1:]
            self.current_page = int(self.current_page)
            # add last slash
            self.video_list_page_url = str(self.video_list_page_url) + "/"

            log("self.video_list_page_url", self.video_list_page_url)

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
        listing = []

        if SETTINGS.getSetting('nsfw') == 'true':
            response = requests.get(self.video_list_page_url, headers=NSFW_HEADERS)
        else:
            response = requests.get(self.video_list_page_url, headers=SFW_HEADERS)

        # response.status
        json_source = response.text
        json_source = convertToUnicodeString(json_source)
        data = json.loads(json_source)
        if not data['success']:
            xbmcplugin.endOfDirectory(self.plugin_handle)
            return

        max_video_quality = SETTINGS.getSetting('video')

        for item in data['items']:
            title = item['title']
            title = convertToUnicodeString(title)

            description = item['description']
            description = convertToUnicodeString(description)
            description = description.replace("<p>", "").replace("</p>", "")
            description = description.replace("&#x27;", "'")
            description = description.capitalize()

            thumbnail_url = item['stills']['still-large']
            for i in item['media']:
                duration = i.get('duration', False)

            # {"gentime":1568796074,"items":[{"date":"2019-09-18T10:28:07+02:00","description":"FUCK DE EU!!!","id":"7757567_fac144f2","media":[{"description":"","duration":57,"mediatype":"VIDEO","variants":[{"uri":"https://media.dumpert.nl/tablet/fac144f2_Fuck_Europa.mp4.mp4.mp4","version":"tablet"},{"uri":"https://media.dumpert.nl/mobile/fac144f2_Fuck_Europa.mp4.mp4.mp4","version":"mobile"},{"uri":"https://media.dumpert.nl/720p/fac144f2_Fuck_Europa.mp4.mp4.mp4","version":"720p"}]}],"nopreroll":false,"nsfw":false,"stats":{"kudos_today":82,"kudos_total":82,"views_today":2202,"views_total":2202},"still":"https://media.dumpert.nl/stills/7757567_fac144f2.jpg","stills":{"still":"https://media.dumpert.nl/stills/7757567_fac144f2.jpg","still-large":"https://media.dumpert.nl/stills/large/7757567_fac144f2.jpg","still-medium":"https://media.dumpert.nl/stills/medium/7757567_fac144f2.jpg","thumb":"https://media.dumpert.nl/sq_thumbs/7757567_fac144f2.jpg","thumb-medium":"https://media.dumpert.nl/sq_thumbs/medium/7757567_fac144f2.jpg"},"tags":"videofuck fuck willem koning prinsjesdag troonrede willy alexander eu nexit","thumbnail":"https://media.dumpert.nl/sq_thumbs/7757567_fac144f2.jpg","title":"Willem heeft er genoeg van!","upload_id":""},{"date":"2019-

            file = ""

            # Only process video items
            try:
                video_type = item['media'][0]['mediatype']
                if video_type == 'VIDEO':
                    process_item = True
                else:
                    process_item = False
            except IndexError:
                process_item = False

            if process_item:
                # is it an embedded youtube link?
                # {"version":"embed","uri":"youtube:wOeZB7bnoxw"}
                # Skipping embedded Youtube videos as these seem to kill kodi for some reason.
                if item['media'][0]['variants'][0]['version'] == 'embed':
                    if str(item['media'][0]['variants'][0]['uri']).find("youtube:") >= 0:
                        youtube_id = str(item['media'][0]['variants'][0]['uri']).replace("youtube:", "")
                        log("skipping embedded youtube video", youtube_id)
                    else:
                        log("skipping mediatype", str(item['media'][0]['variants'][0]['uri']))

                    # go to the next item in the loop
                    continue
                else:
                    # max video quality 0: low, 1: medium, 2: high
                    # Lets find a video with the desired quality or lower
                    if max_video_quality == "0":
                        file = self.find_mobile_video(file, item)
                    elif max_video_quality == "1":
                        file = self.find_tablet_video(file, item)
                        file = self.find_mobile_video(file, item)
                    elif max_video_quality == "2":
                        file = self.find_720p_video(file, item)
                        file = self.find_tablet_video(file, item)
                        file = self.find_mobile_video(file, item)

                # log("title", title)

                log("json file", file)

                list_item = xbmcgui.ListItem(label=title)
                list_item.setInfo("video",
                                  {"title": title, "studio": "Dumpert", "mediatype": "video",
                                   "plot": description, "duration": duration})
                list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                                  'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
                list_item.setProperty('IsPlayable', 'true')

                # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs of the parameters
                title = title.encode('ascii', 'ignore')

                parameters = {"action": "play-file",
                              "file": file,
                              "title": title}
                url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
                is_folder = False
                # Add refresh option to context menu
                list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
                # Add our item to the listing as a 3-element tuple.
                listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            thumbnail_url = os.path.join(IMAGES_PATH, 'next-page.png')
            list_item = xbmcgui.ListItem(LANGUAGE(30503))
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            # If the next url is still empty, we have to make one
            # "https://api-live.dumpert.nl/mobile_api/json/video/latest/1/"
            if self.next_url == "":
                next_page = self.current_page + 1
                self.next_url = str(self.base_url) + str(next_page) + '/'
            parameters = {"action": "json",
                          "plugin_category": self.plugin_category,
                          "url": self.next_url,
                          "period": self.period,
                          "next_page_possible": self.next_page_possible,
                          "days_deducted_from_today": self.days_deducted_from_today}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by one via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)

    def find_720p_video(self, file, item):
        if file == "":
            try:
                if item['media'][0]['variants'][0]['version'] == VIDEO_QUALITY_720P:
                    file = item['media'][0]['variants'][0]['uri']
            except IndexError:
                pass
        if file == "":
            try:
                if item['media'][0]['variants'][1]['version'] == VIDEO_QUALITY_720P:
                    file = item['media'][0]['variants'][1]['uri']
            except IndexError:
                pass
        if file == "":
            try:
                if item['media'][0]['variants'][2]['version'] == VIDEO_QUALITY_720P:
                    file = item['media'][0]['variants'][2]['uri']
            except IndexError:
                pass
        return file

    def find_tablet_video(self, file, item):
        if file == "":
            try:
                if item['media'][0]['variants'][0]['version'] == VIDEO_QUALITY_TABLET:
                    file = item['media'][0]['variants'][0]['uri']
            except IndexError:
                pass
        if file == "":
            try:
                if item['media'][0]['variants'][1]['version'] == VIDEO_QUALITY_TABLET:
                    file = item['media'][0]['variants'][1]['uri']
            except IndexError:
                pass
        if file == "":
            try:
                if item['media'][0]['variants'][2]['version'] == VIDEO_QUALITY_TABLET:
                    file = item['media'][0]['variants'][2]['uri']
            except IndexError:
                pass
        return file

    def find_mobile_video(self, file, item):
        if file == "":
            try:
                if item['media'][0]['variants'][0]['version'] == VIDEO_QUALITY_MOBILE:
                    file = item['media'][0]['variants'][0]['uri']
            except IndexError:
                pass
        if file == "":
            try:
                if item['media'][0]['variants'][1]['version'] == VIDEO_QUALITY_MOBILE:
                    file = item['media'][0]['variants'][1]['uri']
            except IndexError:
                pass
        if file == "":
            try:
                if item['media'][0]['variants'][2]['version'] == VIDEO_QUALITY_MOBILE:
                    file = item['media'][0]['variants'][2]['uri']
            except IndexError:
                pass
        return file
