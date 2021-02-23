# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base settings module

Copyright 2020, Mediathekview
"""


class SettingsInterface(object):

    def __init__(self):
        pass

    def getDatapath(self):
        return ""

    def getKodiVersion(self):
        return 0
    # General

    def getPreferHd(self):
        return True

    def getAutoSub(self):
        return True

    def getNoFutur(self):
        return True

    def getMinLength(self):
        return 0

    def getGroupShow(self):
        return True

    def getMaxResults(self):
        return 1000

    def getMaxAge(self):
        return 84400

    def getRecentMode(self):
        return 0

    def getFilmSortMethod(self):
        return 1

    def getUpdateCheckIntervel(self):
        return 10

    def getContentType(self):
        return ''

    def getBlacklist(self):
        return ''

    def getUseStaticViewId(self):
        return True

    # Database

    def getDatabaseType(self):
        return 0

    def getDatabaseHost(self):
        return 'localhost'

    def getDatabasePort(self):
        return 3306

    def getDatabaseUser(self):
        return 'mediathekview'

    def getDatabasePassword(self):
        return 'mediathekview'

    def getDatabaseSchema(self):
        return 'mediathekview'

    def getDatabaseUpateMode(self):
        return '3'

    def getDatabaseUpdateNative(self):
        return True

    def getCaching(self):
        return True

    def getDatabaseUpdateInvterval(self):
        return 3600

    def getDatabaseImportBatchSize(self):
        return 10000

    # Download

    def getDownloadPathEpisode(self):
        return ''

    def getDownloadPathMovie(self):
        return ''

    def getUseMovieFolder(self):
        return True

    def getMovieNameWithShow(self):
        return True

    def getReviewName(self):
        return False

    def getDownloadSubtitle(self):
        return True

    def getMakeInfo(self):
        return 2

    # FLOW CONTROL
    def is_update_triggered(self):
        return False

    def set_update_triggered(self, aValue):
        pass

    def getLastFullUpdate(self):
        return 0

    def setLastFullUpdate(self, aLastFullUpdate):
        pass

    def getLastUpdate(self):
        return 0

    def setLastUpdate(self, aLastUpdate):
        pass

    def getDatabaseStatus(self):
        return 'UNINIT'

    def setDatabaseStatus(self, aStatus):
        pass

    def getDatabaseVersion(self):
        return '0'

    def setDatabaseVersion(self, aVersion):
        pass

    def is_user_alive(self):
        pass

    def user_activity(self):
        pass

    def getUserAgentString(self):
        return ''

    def getDelayStartupSec(self):
        return 1
