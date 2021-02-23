# -*- coding: utf-8 -*-
"""
The standalone update application environment module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import os
import sys
import argparse
import datetime
import resources.lib.mvutils as mvutils

import resources.lib.appContext as appContext
from resources.lib.loggerCommandline import LoggerCommandline
from resources.lib.settingsCommandline import SettingsCommandline
from resources.lib.notifierInterface import NotifierInterface
from resources.lib.monitorInterface import MonitorInterface

from xml.etree import ElementTree as ET
from resources.lib.updater import MediathekViewUpdater


class UpdateApp():
    """ The standalone updater application class """

    def __init__(self):
        self.scriptpath, self.scriptname = os.path.split(sys.argv[0])
        storederr = None
        self.version = '0.0'
        try:
            tree = ET.parse(os.path.join(self.scriptpath, 'addon.xml'))
            self.version = tree.getroot().attrib['version']
        # pylint: disable=broad-except
        except Exception:
            # cannot self.warn before super.__init__, so store for later
            storederr = sys.exc_info()
        #
        appContext.init()
        self.logger = LoggerCommandline(self.scriptname, self.version)
        appContext.initLogger(self.logger)
        #
        self.notifier = None
        appContext.initNotifier(NotifierInterface())
        #
        self.args = None
        self.verbosity = 0
        self.monitor = None
        self.updater = None
        self.settings = None
        if storederr is not None:
            self.logger.error("Unable to find version information: {} {}", storederr[0].__name__, storederr[1])

    def init(self):
        """ Startup of the application """
        # pylint: disable=line-too-long
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='This is the standalone database updater. It downloads the current database update from mediathekview.de and integrates it in a local database'
        )
        parser.add_argument(
            '-v', '--verbose',
            default=0,
            action='count',
            help='show progress messages'
        )
        subparsers = parser.add_subparsers(
            dest='dbtype',
            help='target database'
        )
        sqliteopts = subparsers.add_parser(
            'sqlite', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        sqliteopts.add_argument(
            '-v', '--verbose',
            default=0,
            action='count',
            help='show progress messages'
        )
        sqliteforce = sqliteopts.add_mutually_exclusive_group()
        sqliteforce.add_argument(
            '-f', '--force',
            default=False,
            action='store_true',
            help='ignore the minimum interval'
        )
        sqliteforce.add_argument(
            '-F', '--full',
            default=False,
            action='store_true',
            help='ignore the minimum interval and force a full update'
        )
        sqliteopts.add_argument(
            '-i', '--intervall',
            default=3500,
            type=int,
            action='store',
            help='minimum interval between updates'
        )
        sqliteopts.add_argument(
            '-b', '--updateBatchSize',
            default=10000,
            type=int,
            action='store',
            help='insert/update batch size'
        )
        sqliteopts.add_argument(
            '-p', '--path',
            dest='path',
            help='alternative path for the sqlite database',
            default='./'
        )
        sqliteopts.add_argument(
            '-n', '--native',
            default=False,
            action='store_true',
            help='allow native update'
        )
        mysqlopts = subparsers.add_parser(
            'mysql', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        mysqlopts.add_argument(
            '-v', '--verbose',
            default=0,
            action='count',
            help='show progress messages'
        )
        mysqlforce = mysqlopts.add_mutually_exclusive_group()
        mysqlforce.add_argument(
            '-f', '--force',
            default=False,
            action='store_true',
            help='ignore the minimum interval'
        )
        mysqlforce.add_argument(
            '-F', '--full',
            default=False,
            action='store_true',
            help='ignore the minimum interval and force a full update'
        )
        mysqlopts.add_argument(
            '-i', '--intervall',
            default=3600,
            type=int,
            action='store',
            help='minimum interval between updates'
        )
        mysqlopts.add_argument(
            '-b', '--updateBatchSize',
            default=10000,
            type=int,
            action='store',
            help='insert/update batch size'
        )
        mysqlopts.add_argument(
            '-H', '--host',
            dest='host',
            help='hostname or ip address',
            default='localhost'
        )
        mysqlopts.add_argument(
            '-P', '--port',
            dest='port',
            help='connection port',
            default='3306'
        )
        mysqlopts.add_argument(
            '-u', '--user',
            dest='user',
            help='connection username',
            default='mediathekview'
        )
        mysqlopts.add_argument(
            '-p', '--password',
            dest='password',
            help='connection password',
            default='mediathekview'
        )
        mysqlopts.add_argument(
            '-d', '--database',
            dest='database',
            default='mediathekview',
            help='database name'
        )
        self.args = parser.parse_args()
        self.verbosity = self.args.verbose
        # do it again to have proper loglevel (verbosity)
        self.logger = LoggerCommandline(self.scriptname, self.version, 'mvupdate', self.verbosity)
        appContext.initLogger(self.logger)
        #
        self.logger.debug('Startup')
        appContext.initSettings(SettingsCommandline(self.args))
        #
        self.monitor = MonitorInterface()
        appContext.initMonitor(self.monitor)
        self.updater = MediathekViewUpdater()
        #
        self.logger.info('Python Version' + sys.version)
        #
        return self.updater.init()

    def run(self):
        """ Execution of the application """
        self.logger.debug('Starting up...')
        self.updater.database.get_status()
        updateop = self.updater.doUpdate()
        self.logger.debug('Exiting...')

    def exit(self):
        """ Shutdown of the application """
        self.updater.exit()
