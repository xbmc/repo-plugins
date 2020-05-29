# -*- coding: utf-8 -*-
"""
The addon settings module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""
# -- Imports ------------------------------------------------
import time
# pylint: disable=import-error
import xbmc
import xbmcaddon
import resources.lib.mvutils as mvutils

# -- Classes ------------------------------------------------



class Settings(object):
    """ The settings class """

    def __init__(self):
        self.load()

    def load(self):
        """ Loads the settings of the addon """
        # pylint: disable=attribute-defined-outside-init
        addon = xbmcaddon.Addon()
        self.datapath = mvutils.py2_decode(xbmc.translatePath(addon.getAddonInfo('profile')))  ### TODO .decode('utf-8')
        self.firstrun = addon.getSetting('firstrun') == 'true'
        # general
        self.preferhd = addon.getSetting('quality') == 'true'
        self.autosub = addon.getSetting('autosub') == 'true'
        self.nofuture = addon.getSetting('nofuture') == 'true'
        self.minlength = int(float(addon.getSetting('minlength'))) * 60
        self.groupshows = addon.getSetting('groupshows') == 'true'
        self.maxresults = int(addon.getSetting('maxresults'))
        self.maxage = int(addon.getSetting('maxage')) * 86400
        self.recentmode = int(addon.getSetting('recentmode'))
        self.filmSortMethod = int(addon.getSetting('filmuisortmethod'))
        self.updateCheckInterval = int(addon.getSetting('updateCheckInterval'))
        # database
        self.type = int(addon.getSetting('dbtype'))
        self.host = addon.getSetting('dbhost')
        self.port = int(addon.getSetting('dbport'))
        self.user = addon.getSetting('dbuser')
        self.password = addon.getSetting('dbpass')
        self.database = addon.getSetting('dbdata')
        self.updnative = addon.getSetting('updnative') == 'true'
        self.updmode = int(addon.getSetting('updmode'))
        self.caching = addon.getSetting('caching') == 'true'
        self.updinterval = int(float(addon.getSetting('updinterval'))) * 3600
        # download
        self.downloadpathep = mvutils.py2_decode(addon.getSetting('downloadpathep'))
        #TODO self.downloadpathep = unicode(self.downloadpathep, 'utf-8')
        self.downloadpathmv = mvutils.py2_decode(addon.getSetting('downloadpathmv'))
        #TODO self.downloadpathmv = unicode(self.downloadpathmv, 'utf-8')
        self.moviefolders = addon.getSetting('moviefolders') == 'true'
        self.movienamewithshow = addon.getSetting(
            'movienamewithshow') == 'true'
        self.reviewname = addon.getSetting('reviewname') == 'true'
        self.downloadsrt = addon.getSetting('downloadsrt') == 'true'
        self.makenfo = int(addon.getSetting('makenfo'))
        # update stuff from 0.4.3
        if not self.downloadpathep:
            self.downloadpathep = addon.getSetting('downloadpath')
            if self.downloadpathep:
                addon.setSetting('downloadpathep', self.downloadpathep)

    def reload(self):
        """
        Reloads the configuration of the addon and returns
        `True` if the database type has changed
        """
        addon = xbmcaddon.Addon()
        # check if the db configration has changed
        dbchanged = self.type != int(addon.getSetting('dbtype'))
        dbchanged = dbchanged or self.host != addon.getSetting('dbhost')
        dbchanged = dbchanged or self.port != int(addon.getSetting('dbport'))
        dbchanged = dbchanged or self.user != addon.getSetting('dbuser')
        dbchanged = dbchanged or self.password != addon.getSetting('dbpass')
        dbchanged = dbchanged or self.database != addon.getSetting('dbdata')
        # reload configuration
        self.load()
        # return change status
        return dbchanged

    @staticmethod
    def is_update_triggered():
        """
        Returns `True` if a database update has been triggered
        by another part of the addon
        """
        if xbmcaddon.Addon().getSetting('updatetrigger') == 'true':
            xbmcaddon.Addon().setSetting('updatetrigger', 'false')
            return True
        return False

    @staticmethod
    def is_user_alive():
        """ Returns `True` if there was recent user activity """
        return int(time.time()) - int(float(xbmcaddon.Addon().getSetting('lastactivity'))) < 7200

    @staticmethod
    def trigger_update():
        """ Triggers an asynchronous database update """
        xbmcaddon.Addon().setSetting('updatetrigger', 'true')

    @staticmethod
    def reset_user_activity():
        """ Signals that a user activity has occurred """
        xbmcaddon.Addon().setSetting('lastactivity', '{}'.format(int(time.time())))

    @staticmethod
    def save_update_instance(instanceid):
        """
        Store the instance id that will start a database
        update process into the persistent settings.

        Args:
            instanceid(str): instance id
        """
        xbmcaddon.Addon().setSetting('updateinid', instanceid)

    def handle_update_on_start(self):
        """
        When invoked, this method triggers an update if the update
        mode is configured as 'On Start' and this instance is not
        already performing a database update
        """
        if self.updmode == 2:
            # pylint: disable=line-too-long
            if xbmcaddon.Addon().getSetting('instanceid') != xbmcaddon.Addon().getSetting('updateinid'):
                self.trigger_update()

    def handle_first_run(self):
        """
        Returns `True` if the addon has never been executed before
        """
        # pylint: disable=attribute-defined-outside-init
        if self.firstrun:
            self.firstrun = False
            xbmcaddon.Addon().setSetting('firstrun', 'false')
            return True
        return False
