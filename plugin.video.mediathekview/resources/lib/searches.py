"""
Management of recent searches

Copyright (c) 2018, Leo Moll
SPDX-License-Identifier: MIT
"""

import os
import json
import time
import resources.lib.appContext as appContext

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

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`
    """

    def __init__(self, plugin, sortmethods=None):
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.sortmethods = sortmethods if sortmethods is not None else [xbmcplugin.SORT_METHOD_TITLE]
        self.recents = []
        self.datafile = os.path.join(
            appContext.MVSETTINGS.getDatapath(),
            'recent_std_searches.json'
        )
        self.logger = appContext.MVLOGGER.get_new_logger('RecentSearches')

    def load(self):
        """ Loads the recent searches list """
        self.logger.debug('load')
        start = time.time()
        #
        try:
            with closing(open(self.datafile, encoding='utf-8')) as json_file:
                data = json.load(json_file)
                if isinstance(data, list):
                    self.recents = sorted(
                        data, key=itemgetter('when'), reverse=True)
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to load last searches file {}: {}', self.datafile, err)
        self.logger.debug('loaded search: {} sec', time.time() - start)
        return self

    def save(self):
        """ Saves the recent searches list """
        self.logger.debug('save')
        start = time.time()
        #
        data = sorted(self.recents, key=itemgetter('when'), reverse=True)
        try:
            with closing(open(self.datafile, 'w', encoding='utf-8')) as json_file:
                json.dump(data, json_file)
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to write last searches file {}: {}', self.datafile, err)
        self.logger.debug('saved search: {} sec', time.time() - start)
        return self

    def add(self, search):
        """
        Adds a recent search entry to the list

        Args:
            search(str): search string
        """
        self.logger.debug('add')
        start = time.time()
        #
        slow = search.lower()
        try:
            for entry in self.recents:
                if entry['search'].lower() == slow:
                    entry['when'] = int(time.time())
                    self.logger.debug('added search: {} sec', time.time() - start)
                    return self
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Recent searches list is broken (error {}) - cleaning up', err)
            self.recents = []
        self.recents.append({
            'search':            search,
            'when':              int(time.time())
        })
        self.logger.debug('added search: {} sec', time.time() - start)
        return self

    def delete(self, search):
        """
        Deletes a recent search entry from the list

        Args:
            search(str): search string
        """
        self.logger.debug('delete')
        start = time.time()
        #
        slow = search.lower()
        try:
            for entry in self.recents:
                if entry['search'].lower() == slow:
                    self.recents.remove(entry)
                    self.logger.debug('deleted search: {} sec', time.time() - start)
                    return self
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Recent searches list is broken (error {}) - cleaning up', err)
            self.recents = []
        self.logger.debug('deleted search: {} sec', time.time() - start)
        return self

    def populate(self):
        """ Populates a directory with the recent serach list """
        self.logger.debug('populate')
        start = time.time()
        #
        for entry in self.recents:
            self.plugin.add_folder_item(
                entry['search'],
                {
                    'mode': "research",
                    'search': entry['search']
                },
                [
                    (
                        self.plugin.language(30932),
                        'RunPlugin({})'.format(
                            self.plugin.build_url({
                                'mode': "delsearch",
                                'search': entry['search']
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
        self.logger.debug('populate search: {} sec', time.time() - start)
