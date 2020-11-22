"""
Management of recent searches

Copyright (c) 2018, Leo Moll
SPDX-License-Identifier: MIT
"""

import os
import json
import time

from contextlib import closing
from operator import itemgetter
from codecs import open
# pylint: disable=import-error
import xbmcplugin


class RecentSearches(object):
    """
    The recent searches class

    Args:
        plugin(MediathekView): the plugin object

        extendedsearch(bool): if `True` the class
            stores extended searches

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`
    """

    def __init__(self, plugin, extendedsearch, sortmethods=None):
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.sortmethods = sortmethods if sortmethods is not None else [
            xbmcplugin.SORT_METHOD_TITLE]
        self.extendedsearch = extendedsearch
        self.recents = []
        self.datafile = os.path.join(
            self.plugin.settings.datapath,
            'recent_ext_searches.json' if extendedsearch else 'recent_std_searches.json'
        )

    def load(self):
        """ Loads the recent searches list """
        try:
            with closing(open(self.datafile, encoding='utf-8')) as json_file:
                data = json.load(json_file)
                if isinstance(data, list):
                    self.recents = sorted(
                        data, key=itemgetter('when'), reverse=True)
        # pylint: disable=broad-except
        except Exception as err:
            self.plugin.error(
                'Failed to load last searches file {}: {}', self.datafile, err)
        return self

    def save(self):
        """ Saves the recent searches list """
        data = sorted(self.recents, key=itemgetter('when'), reverse=True)
        try:
            with closing(open(self.datafile, 'w', encoding='utf-8')) as json_file:
                json.dump(data, json_file)
        # pylint: disable=broad-except
        except Exception as err:
            self.plugin.error(
                'Failed to write last searches file {}: {}', self.datafile, err)
        return self

    def add(self, search):
        """
        Adds a recent search entry to the list

        Args:
            search(str): search string
        """
        slow = search.lower()
        try:
            for entry in self.recents:
                if entry['search'].lower() == slow:
                    entry['when'] = int(time.time())
                    return self
        # pylint: disable=broad-except
        except Exception as err:
            self.plugin.error(
                'Recent searches list is broken (error {}) - cleaning up', err)
            self.recents = []
        self.recents.append({
            'search':			search,
            'when':				int(time.time())
        })
        return self

    def delete(self, search):
        """
        Deletes a recent search entry from the list

        Args:
            search(str): search string
        """
        slow = search.lower()
        try:
            for entry in self.recents:
                if entry['search'].lower() == slow:
                    self.recents.remove(entry)
                    return self
        # pylint: disable=broad-except
        except Exception as err:
            self.plugin.error(
                'Recent searches list is broken (error {}) - cleaning up', err)
            self.recents = []
        return self

    def populate(self):
        """ Populates a directory with the recent serach list """
        for entry in self.recents:
            self.plugin.add_folder_item(
                entry['search'],
                {
                    'mode': "research",
                    'search': entry['search'],
                    'extendedsearch': self.extendedsearch
                },
                [
                    (
                        self.plugin.language(30932),
                        'RunPlugin({})'.format(
                            self.plugin.build_url({
                                'mode': "delsearch",
                                'search': entry['search'],
                                'extendedsearch': self.extendedsearch
                            })
                        )
                    )
                ],
                icon=os.path.join(
                    self.plugin.path,
                    'resources',
                    'icons',
                    'results-m.png'
                )
            )
