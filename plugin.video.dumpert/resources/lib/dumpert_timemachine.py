#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
from datetime import datetime, timedelta
import time

from resources.lib.dumpert_const import LANGUAGE, IMAGES_PATH, log, DAY, WEEK, MONTH, \
    DAY_TOPPERS_URL_PART_1, DAY_TOPPERS_URL_PART_2, WEEK_TOPPERS_URL_PART_1, \
    WEEK_TOPPERS_URL_PART_2, MONTH_TOPPERS_URL_PART_1, MONTH_TOPPERS_URL_PART_2


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

        self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        # Ask the user for a date
        date = xbmcgui.Dialog().numeric(1, LANGUAGE(30509))
        if date is None:
            date = datetime.now()
        else:
            date = date.replace(' ', '')
            try:
                try:
                    date = datetime.strptime(date, '%d/%m/%Y')
                except TypeError:
                    date = datetime(*(time.strptime(date, '%d/%m/%Y')[0:6]))
            except ValueError:
                date = datetime.now()

        # If the date is in the future or too old, set it to the current date
        if date > datetime.now() or date < datetime(2006, 1, 1):
            date = datetime.now()

        # days
        daily_toppers_url = DAY_TOPPERS_URL_PART_1 + date.strftime('%Y-%m-%d') + DAY_TOPPERS_URL_PART_2
        
        date_now = datetime.now()
        delta = date_now - date
        days_deducted_from_today = delta.days

        # log("days_deducted_from_today for days", str(days_deducted_from_today))

        title = LANGUAGE(30510) % (date.strftime('%d %b %Y'))
        parameters = {"action": "json",
                      "plugin_category": self.plugin_category,
                      "url": daily_toppers_url,
                      "period": DAY,
                      "next_page_possible": self.next_page_possible,
                      "days_deducted_from_today": days_deducted_from_today}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        self.add_folder(parameters, title)

        # weeks.
        weekly_toppers_url = WEEK_TOPPERS_URL_PART_1 + date.strftime('%Y%W') + WEEK_TOPPERS_URL_PART_2
        title = LANGUAGE(30511) % (date.strftime('%W'), date.strftime('%Y'))

        delta = date_now - date
        days_deducted_from_today = delta.days

        # log("days_deducted_from_today for weeks", str(days_deducted_from_today))

        parameters = {"action": "json",
                      "plugin_category": self.plugin_category,
                      "url": weekly_toppers_url,
                      "period": WEEK,
                      "next_page_possible": self.next_page_possible,
                      "days_deducted_from_today": days_deducted_from_today}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        self.add_folder(parameters, title)

        # months
        monthly_toppers_url = MONTH_TOPPERS_URL_PART_1 +  date.strftime('%Y%m') + MONTH_TOPPERS_URL_PART_2

        delta = date_now - date
        days_deducted_from_today = delta.days

        # log("days_deducted_from_today for months", str(days_deducted_from_today))

        title = LANGUAGE(30512) % (date.strftime('%b %Y'))
        parameters = {"action": "json",
                      "plugin_category": self.plugin_category,
                      "url": monthly_toppers_url,
                      "period": MONTH,
                      "next_page_possible": self.next_page_possible,
                      "days_deducted_from_today": days_deducted_from_today}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        self.add_folder(parameters, title)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)

    def add_folder(self, parameters, title):
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(title)
        thumbnail_url = 'DefaultFolder.png'
        list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)