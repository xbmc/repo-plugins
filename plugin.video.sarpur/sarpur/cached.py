#!/usr/bin/env python
# encoding: UTF-8

import os
import json
import sarpur
import sarpur.scraper as scraper
from datetime import datetime


DATA_PATH = os.path.join(sarpur.ADDON.getAddonInfo('path'), 'resources', 'data')
SHOWTREEFILE_LOCATION = os.path.join(DATA_PATH, 'showtree.dat')
TABFILE_LOCATION = os.path.join(DATA_PATH, 'tabs.dat')

class Categories(object):
    def __init__(self):

        try:
            last_modified = os.path.getmtime(SHOWTREEFILE_LOCATION)
            delta = datetime.now() - datetime.fromtimestamp(last_modified)

            if sarpur.ALWAYS_REFRESH or delta.days > 0:
                showtree = self.update_showtree()
                tabs = self.update_tabs()
            else:
                tabs = json.load(file(TABFILE_LOCATION, 'rb'))
                showtree = json.load(file(SHOWTREEFILE_LOCATION, 'rb'))

        except OSError:
            if not os.path.exists(DATA_PATH):
                os.makedirs(DATA_PATH)
            showtree = self.update_showtree()
            tabs = self.update_tabs()
        except IOError:
            try:
                os.unlink(SHOWTREEFILE_LOCATION)
                os.unlink(TABFILE_LOCATION)
            except OSError:
                None
            showtree = self.update_showtree()
            tabs = self.update_tabs()

        self.tabs = tabs
        self.showtree = showtree

    def update_tabs(self):
        "populate latest_groups"

        tabs = scraper.get_tabs()

        json.dump(tabs, file(TABFILE_LOCATION, 'wb'))
        self.tabs = tabs


    def update_showtree(self):
        """
        Update the data file with the show list.
        The data structure should look something like this:

        [
            {
                'name': channel_name,
                'categories':
                    [
                        {
                            'name': category_name,
                            'shows':
                                [
                                    (show_name, http_url),
                                    (show_name, http_url),
                                    (show_name, http_url),
                                    ...
                                ]
                        }

                    ]
            }
        ]

        """

        showtree = scraper.get_showtree()
        json.dump(showtree, file(SHOWTREEFILE_LOCATION, 'wb'))
        self.showtree = showtree
