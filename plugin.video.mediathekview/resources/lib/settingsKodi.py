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
import xbmcvfs
import resources.lib.mvutils as mvutils
from resources.lib.settingsInterface import SettingsInterface
# -- Classes ------------------------------------------------


class SettingsKodi(SettingsInterface):
    """ The settings class """

    def __init__(self, pAddonClass):
        xbmc.log("SettingsKodi:init", xbmc.LOGDEBUG)
        self._addonClass = pAddonClass
        pass

    # self.datapath
    def getDatapath(self):
        if self.getKodiVersion() > 18:
            return mvutils.py2_decode(xbmcvfs.translatePath(self._addonClass.getAddonInfo('profile')))
        else:
            return mvutils.py2_decode(xbmc.translatePath(self._addonClass.getAddonInfo('profile')))

    def getKodiVersion(self):
        """
        Get Kodi major version
        Returns:
            int: Kodi major version (e.g. 18)
        """
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")

        return int(xbmc_version.split('-')[0].split('.')[0])

    # General
    # self.preferhd
    def getPreferHd(self):
        return self._addonClass.getSetting('quality') == 'true'

    # self.autosub
    def getAutoSub(self):
        return self._addonClass.getSetting('autosub') == 'true'

    # self.nofuture
    def getNoFutur(self):
        return self._addonClass.getSetting('nofuture') == 'true'

    # self.minlength
    def getMinLength(self):
        return int(float(self._addonClass.getSetting('minlength')))

    # self.groupshows
    def getGroupShow(self):
        return self._addonClass.getSetting('groupshows') == 'true'

    # self.maxresults
    def getMaxResults(self):
        return int(self._addonClass.getSetting('maxresults'))

    # self.maxage
    def getMaxAge(self):
        return int(self._addonClass.getSetting('maxage')) * 86400

    # self.recentmode
    def getRecentMode(self):
        return int(self._addonClass.getSetting('recentmode'))

    # self.filmSortMethod
    def getFilmSortMethod(self):
        return int(self._addonClass.getSetting('filmuisortmethod'))

    # self.updateCheckInterval
    def getUpdateCheckIntervel(self):
        return int(self._addonClass.getSetting('updateCheckInterval'))

    def getDatabaseImportBatchSize(self):
        return int(self._addonClass.getSetting('updateBatchSize'))

    # self.contentType
    def getContentType(self):
        contentType = ''
        if self._addonClass.getSetting('contentType') == '1':
            contentType = 'videos'
        elif self._addonClass.getSetting('contentType') == '2':
            contentType = 'movies'
        elif self._addonClass.getSetting('contentType') == '3':
            contentType = 'episodes'
        elif self._addonClass.getSetting('contentType') == '4':
            contentType = 'tvshows'
        return contentType

    def getBlacklist(self):
        return self._addonClass.getSetting('blacklist')

    def getUseStaticViewId(self):
        return self._addonClass.getSetting('staticViewIds') == 'true'

    # Database

    # self.type
    def getDatabaseType(self):
        return int(self._addonClass.getSetting('dbtype'))

    # self.host
    def getDatabaseHost(self):
        return self._addonClass.getSetting('dbhost')

    # self.port
    def getDatabasePort(self):
        return int(self._addonClass.getSetting('dbport'))

    # self.user
    def getDatabaseUser(self):
        return self._addonClass.getSetting('dbuser')

    # self.password
    def getDatabasePassword(self):
        return self._addonClass.getSetting('dbpass')

    # self.database
    def getDatabaseSchema(self):
        return self._addonClass.getSetting('dbdata')

    # self.updmode
    def getDatabaseUpateMode(self):
        return int(self._addonClass.getSetting('updmode'))

    # self.updnative
    def getDatabaseUpdateNative(self):
        return self._addonClass.getSetting('updnative') == 'true'

    # self.caching
    def getCaching(self):
        return self._addonClass.getSetting('caching') == 'true'

    # self.updinterval
    def getDatabaseUpdateInvterval(self):
        return int(float(self._addonClass.getSetting('updinterval'))) * 3600

    # Download

    # self.downloadpathep
    def getDownloadPathEpisode(self):
        return mvutils.py2_decode(self._addonClass.getSetting('downloadpathep'))

    # self.downloadpathmv
    def getDownloadPathMovie(self):
        return mvutils.py2_decode(self._addonClass.getSetting('downloadpathmv'))

    # self.moviefolders
    def getUseMovieFolder(self):
        return self._addonClass.getSetting('moviefolders') == 'true'

    # self.movienamewithshow
    def getMovieNameWithShow(self):
        return self._addonClass.getSetting('movienamewithshow') == 'true'

    # self.reviewname
    def getReviewName(self):
        return self._addonClass.getSetting('reviewname') == 'true'

    # self.downloadsrt
    def getDownloadSubtitle(self):
        return self._addonClass.getSetting('downloadsrt') == 'true'

    # self.makenfo
    def getMakeInfo(self):
        return int(self._addonClass.getSetting('makenfo'))

    # RUNTIME
    def is_update_triggered(self):
        return self._addonClass.getSetting('updatetrigger') == 'true'

    def set_update_triggered(self, aValue):
        self._addonClass.setSetting('updatetrigger', aValue)

    def getLastFullUpdate(self):
       return int(self._addonClass.getSetting('lastFullUpdate'))

    def setLastFullUpdate(self, aLastFullUpdate):
        self._addonClass.setSetting('lastFullUpdate', str(aLastFullUpdate))

    def getLastUpdate(self):
        return int(self._addonClass.getSetting('lastUpdate'))

    def setLastUpdate(self, aLastUpdate):
        self._addonClass.setSetting('lastUpdate', str(aLastUpdate))

    def getDatabaseStatus(self):
        return self._addonClass.getSetting('databaseStatus')

    def setDatabaseStatus(self, aStatus):
        self._addonClass.setSetting('databaseStatus', aStatus)

    def getDatabaseVersion(self):
        return int(self._addonClass.getSetting('databaseVersion'))

    def setDatabaseVersion(self, aVersion):
        self._addonClass.setSetting('databaseVersion', str(aVersion))

    def is_user_alive(self):
        """ Returns `True` if there was recent user activity """
        return int(time.time()) - int(float(self._addonClass.getSetting('lastactivity'))) < 7200

    def user_activity(self):
        """ Signals that a user activity has occurred """
        if not(self.is_user_alive()):
            self._addonClass.setSetting('lastactivity', '{}'.format(int(time.time())))

    def getUserAgentString(self):
        return self._addonClass.getSetting('userAgentString')

    def getDelayStartupSec(self):
        return int(self._addonClass.getSetting('delayStartupSec'))

