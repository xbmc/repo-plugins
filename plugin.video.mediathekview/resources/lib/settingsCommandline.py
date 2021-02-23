# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base settings module

Copyright 2020, Mediathekview
"""

from resources.lib.settingsInterface import SettingsInterface


class SettingsCommandline(SettingsInterface):
    """ Standalone implementation of the settings class """

    def __init__(self, args):
        self.__datapath = args.path if args.dbtype == 'sqlite' else './'
        self.__type = {'sqlite': 0, 'mysql': 1}.get(args.dbtype, 0)
        if self.__type == 0:
            self.__updnative = args.native
        elif self.__type == 1:
            self.__host = args.host
            self.__port = int(args.port)
            self.__user = args.user
            self.__password = args.password
            self.__database = args.database
        self.__updmode = 4
        self.__updinterval = args.intervall
        self.__force = args.force
        self.__full = args.full
        self.__updateBatchSize = args.updateBatchSize
        #
        self._lastFullUpdate = 0
        self._lastUpdate = 0
        self._databaseStatus = 'UNINIT'
        self._databaseVersion = 0

    def getDatapath(self):
        return self.__datapath

    # Database

    def getDatabaseType(self):
        return self.__type

    def getDatabaseHost(self):
        return self.__host

    def getDatabasePort(self):
        return self.__port

    def getDatabaseUser(self):
        return self.__user

    def getDatabasePassword(self):
        return self.__password

    def getDatabaseSchema(self):
        return self.__database

    def getDatabaseUpateMode(self):
        if self.__full:
            return 9
        else:
            return self.__updmode

    def getDatabaseUpdateNative(self):
        return self.__updnative

    def getDatabaseUpdateInvterval(self):
        if self.__force:
            return 1
        else:
            return self.__updinterval

    def getDatabaseImportBatchSize(self):
        return self.__updateBatchSize

    # RUNTIME
    def is_user_alive(self):
        return True

    #
    def getLastFullUpdate(self):
       return self._lastFullUpdate

    def setLastFullUpdate(self, aLastFullUpdate):
        self._lastFullUpdate = (aLastFullUpdate)

    def getLastUpdate(self):
        return self._lastUpdate

    def setLastUpdate(self, aLastUpdate):
        self._lastUpdate = (aLastUpdate)

    def getDatabaseStatus(self):
        return self._databaseStatus

    def setDatabaseStatus(self, aStatus):
        self._databaseStatus = aStatus

    def getDatabaseVersion(self):
        return self._databaseVersion

    def setDatabaseVersion(self, aVersion):
        self._databaseVersion = aVersion

