# -*- coding: utf-8 -*-
"""
The MySQL database support module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
"""
# pylint: disable=too-many-lines,line-too-long

import time
import mysql.connector

import resources.lib.mvutils as mvutils
import resources.lib.appContext as appContext
from resources.lib.storeQuery import StoreQuery


class StoreMySQL(StoreQuery):
    """
    The local MySQL database class
    
    con.query('SET GLOBAL connect_timeout=28800')
con.query('SET GLOBAL interactive_timeout=28800')
con.query('SET GLOBAL wait_timeout=28800')
SET SESSION MAX_EXECUTION_TIME=2000;
SET GLOBAL MAX_EXECUTION_TIME=2000;
    """

    def __init__(self):
        super(StoreMySQL, self).__init__()
        self.logger = appContext.MVLOGGER.get_new_logger('StoreMySQL')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        self.conn = None

    def getConnection(self):
        if self.conn is None:
            self.logger.debug('Using MySQL connector version {}',
                             mysql.connector.__version__)
            # TODO Kodi 19 - we can update to mysql connector which supports auth_plugin parameter
            connectargs = {
                'host': self.settings.getDatabaseHost(),
                'port': self.settings.getDatabasePort(),
                'user': self.settings.getDatabaseUser(),
                'password': self.settings.getDatabasePassword(),
                'connect_timeout':24 * 60 * 60,
                'charset':'utf8',
                'use_unicode':True

            }
            if mysql.connector.__version_info__ > (1, 2):
                connectargs['auth_plugin'] = 'mysql_native_password'
            else:
                self.logger.debug('Not using auth_plugin parameter')
            if mysql.connector.__version_info__ > (2, 1) and mysql.connector.HAVE_CEXT:
                connectargs['use_pure'] = True
                self.logger.debug('Forcefully disabling C extension')
            self.conn = mysql.connector.connect(**connectargs)
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT VERSION()')
                (version,) = cursor.fetchone()
                self.logger.debug(
                    'Connected to server {} running {}', self.settings.getDatabaseHost(), version)
            # pylint: disable=broad-except
            except Exception:
                self.logger.debug('Connected to server {}', self.settings.getDatabaseHost())
            # select database
            try:
                self.conn.database = self.settings.getDatabaseSchema()
            except Exception:
                pass
            #
            cursor.close()
        return self.conn

    def execute(self, aStmt, aParams=None):
        aStmt = aStmt.replace('?', '%s')
        return super(StoreMySQL, self).execute(aStmt, aParams)

    def executeUpdate(self, aStmt, aParams=None):
        aStmt = aStmt.replace('?', '%s')
        return super(StoreMySQL, self).executeUpdate(aStmt, aParams)

    def executemany(self, aStmt, aParams=None):
        aStmt = aStmt.replace('?', '%s')
        return super(StoreMySQL, self).executemany(aStmt, aParams)

    def getImportPreparedStmtInsert(self):
        aStmt = super(StoreMySQL, self).getImportPreparedStmtInsert()
        aStmt = aStmt.replace('?', '%s')
        return aStmt

    def getImportPreparedStmtUpdate(self):
        aStmt = super(StoreMySQL, self).getImportPreparedStmtUpdate()
        aStmt = aStmt.replace('?', '%s')
        return aStmt

    def exit(self):
        if self.conn is not None:
            self.conn.close();
            self.conn = None
