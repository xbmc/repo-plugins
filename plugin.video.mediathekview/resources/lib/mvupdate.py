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

from xml.etree import ElementTree as ET
from resources.lib.base.logger import Logger
from resources.lib.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------


class Settings(object):
    """ Standalone implementation of the settings class """

    def __init__(self, args):
        self.datapath = args.path if args.dbtype == 'sqlite' else './'
        self.type = {'sqlite': 0, 'mysql': 1}.get(args.dbtype, 0)
        if self.type == 0:
            self.updnative = args.native
        elif self.type == 1:
            self.host = args.host
            self.port = int(args.port)
            self.user = args.user
            self.password = args.password
            self.database = args.database
        self.autosub = False
        self.nofuture = True
        self.minlength = 0
        self.maxage = 86400
        self.recentmode = 0
        self.groupshows = False
        self.updmode = 3
        self.updinterval = args.intervall

    @staticmethod
    def reload():
        """
        Reloads the configuration of the addon and returns
        `True` if the database type has changed
        """
        return False

    @staticmethod
    def is_update_triggered():
        """
        Returns `True` if a database update has been triggered
        by another part of the addon
        """
        return True

    @staticmethod
    def is_user_alive():
        """ Returns `True` if there was recent user activity """
        return True

    @staticmethod
    def trigger_update():
        """ Triggers an asynchronous database update """
        return True

    @staticmethod
    def reset_user_activity():
        """ Signals that a user activity has occurred """
        pass


class AppLogger(Logger):
    """ Standalone implementation of the logger class """

    def __init__(self, name, version, topic=None, verbosity=0):
        super(AppLogger, self).__init__(name, version, topic)
        self.verbosity = verbosity

    def get_new_logger(self, topic=None):
        """
        Generates a new logger instance with a specific topic

        Args:
            topic(str, optional): the topic of the new logger.
                Default is the same topic of `self`
        """
        return AppLogger(self.name, self.version, topic, self.verbosity)

    def debug(self, message, *args):
        """ Outputs a debug message """
        self._log(2, message, *args)

    def info(self, message, *args):
        """ Outputs an info message """
        self._log(1, message, *args)

    def warn(self, message, *args):
        """ Outputs a warning message """
        self._log(0, message, *args)

    def error(self, message, *args):
        """ Outputs an error message """
        self._log(-1, message, *args)

    def _log(self, level, message, *args):
        parts = []
        for arg in args:
            part = arg
            if isinstance(arg, str):
                part = mvutils.py2_encode(arg)
            parts.append(part)
        output = '{} {} {}{}'.format(
            datetime.datetime.now(),
            {-1: 'ERROR', 0: 'WARNING', 1: 'INFO', 2: 'DEBUG'}.get(level, 2),
            self.prefix,
            message.format(*parts)
        )

        if level < 0:
            # error
            sys.stderr.write(output + '\n')
            sys.stderr.flush()
        elif self.verbosity >= level:
            # other message
            # pylint: disable=superfluous-parens
            print(output)


class Notifier(object):
    """ Standalone implementation of the notifier class """

    def __init__(self):
        pass

    # pylint: disable=unused-argument
    @staticmethod
    def get_entered_text(deftext=None, heading=None, hidden=False):
        """
        Asks the user to enter a text. The method returnes a tuple with
        the text and the confirmation status: `( "Entered Text", True, )`

        Args:
            deftext(str|int, optional): Default text in the text entry box.
                Can be a string or a numerical id to a localized text. This
                text will be returned if the user selects `Cancel`

            heading(str|int, optional): Heading text of the text entry UI.
                Can be a string or a numerical id to a localized text.

            hidden(bool, optional): If `True` the entered text is not
                desplayed. Placeholders are used for every char. Default
                is `False`
        """
        return (deftext, False, )

    @staticmethod
    def show_ok_dialog(heading=None, line1=None, line2=None, line3=None):
        """
        Shows an OK dialog to the user

        Args:
            heading(str|int, optional): Heading text of the OK Dialog.
                Can be a string or a numerical id to a localized text.

            line1(str|int, optional): First text line of the OK Dialog.
                Can be a string or a numerical id to a localized text.

            line2(str|int, optional): Second text line of the OK Dialog.
                Can be a string or a numerical id to a localized text.

            line3(str|int, optional): Third text line of the OK Dialog.
                Can be a string or a numerical id to a localized text.
        """
        pass

    @staticmethod
    def show_notification(heading, message, icon=None, time=5000, sound=True):
        """
        Shows a notification to the user

        Args:
            heading(str|int): Heading text of the notification.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the notification.
                Can be a string or a numerical id to a localized text.

            icon(id, optional): xbmc id of the icon. Can be `xbmcgui.NOTIFICATION_INFO`,
                `xbmcgui.NOTIFICATION_WARNING` or `xbmcgui.NOTIFICATION_ERROR`.
                Default is `xbmcgui.NOTIFICATION_INFO`

            time(int, optional): Number of milliseconds the notification stays
                visible. Default is 5000.

            sound(bool, optional): If `True` a sound is played. Default is `True`
        """
        pass

    @staticmethod
    def show_warning(heading, message, time=5000, sound=True):
        """
        Shows a warning notification to the user

        Args:
            heading(str|int): Heading text of the notification.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the notification.
                Can be a string or a numerical id to a localized text.

            time(int, optional): Number of milliseconds the notification stays
                visible. Default is 5000.

            sound(bool, optional): If `True` a sound is played. Default is `True`
        """
        pass

    @staticmethod
    def show_error(heading, message, time=5000, sound=True):
        """
        Shows an error notification to the user

        Args:
            heading(str|int): Heading text of the notification.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the notification.
                Can be a string or a numerical id to a localized text.

            time(int, optional): Number of milliseconds the notification stays
                visible. Default is 5000.

            sound(bool, optional): If `True` a sound is played. Default is `True`
        """
        pass

    @staticmethod
    def show_progress_dialog(heading=None, message=None):
        """
        Shows a progress dialog to the user

        Args:
            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        pass

    @staticmethod
    def update_progress_dialog(percent, heading=None, message=None):
        """
        Updates a progress dialog

        Args:
            percent(int): percentage of progress

            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        pass

    @staticmethod
    def hook_progress_dialog(blockcount, blocksize, totalsize):
        """
        A hook function that will be passed to functions like `url_retrieve`

        Args:
            blockcount(int): Count of blocks transferred so far

            blocksize(int): Block size in bytes

            totalsize(int): Total size of the file
        """
        pass

    @staticmethod
    def close_progress_dialog():
        """
        Closes a progress dialog
        """
        pass

    @staticmethod
    def show_database_error(err):
        """ Displays UI for a database error """
        pass

    @staticmethod
    def show_download_error(name, err):
        """ Displays UI for a download error """
        pass

    @staticmethod
    def show_missing_extractor_error():
        """ Disaplys UI for a missing extractor error """
        pass

    @staticmethod
    def show_limit_results(maxresults):
        """ Display UI for search result limited by configuration """
        pass

    @staticmethod
    def show_outdated_unknown():
        """ Display UI for never updated database """
        pass

    @staticmethod
    def show_outdated_known(status):
        """ Display UI for an outdated database """
        pass

    @staticmethod
    def show_download_progress():
        """ Display UI for a download in progress """
        pass

    @staticmethod
    def update_download_progress(percent, message=None):
        """ Update UI odometer for a download in progress """
        pass

    @staticmethod
    def hook_download_progress(blockcount, blocksize, totalsize):
        """ UI Report hook for functions like `url_retrieve` """
        pass

    @staticmethod
    def close_download_progress():
        """ Hides the UI for a download in progress """
        pass

    @staticmethod
    def show_update_progress():
        """ Display UI for a database update in progress """
        pass

    @staticmethod
    def update_update_progress(percent, count, channels, shows, movies):
        """ Update UI odometer for a database update in progress """
        pass

    @staticmethod
    def close_update_progress():
        """ Hides the UI for a database update in progress """
        pass

    @staticmethod
    def show_updating_scheme():
        """ SHow UI that the database schema is about to be updated """
        pass

    @staticmethod
    def show_update_scheme_progress():
        """ Display UI for a database schema update in progress """
        pass

    @staticmethod
    def update_update_scheme_progress(percent):
        """ Update UI odometer for a database schema update in progress """
        pass

    @staticmethod
    def close_update_scheme_progress():
        """ Hides the UI for a database schema update in progress """
        pass


class MediathekViewMonitor(object):
    """ Standalone implementation of the monitor class """
    @staticmethod
    def abort_requested():
        """
        Returns `True`if either this instance is not the registered
        instance or Kodi is shutting down
        """
        return False


class UpdateApp(AppLogger):
    """ The standalone updater application class """

    def __init__(self):
        scriptpath, scriptname = os.path.split(sys.argv[0])
        storederr = None
        version = '0.0'
        try:
            tree = ET.parse(os.path.join(scriptpath, 'addon.xml'))
            version = tree.getroot().attrib['version']
        # pylint: disable=broad-except
        except Exception:
            # cannot self.warn before super.__init__, so store for later
            storederr = sys.exc_info()
        AppLogger.__init__(self, scriptname, version)
        self.args = None
        self.verbosity = 0
        self.notifier = None
        self.monitor = None
        self.updater = None
        self.settings = None
        if storederr is not None:
            self.warn("Unable to find version information: {} {}", storederr[0].__name__, storederr[1])
        self.info('Python Version' + sys.version)

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
            default=3600,
            type=int,
            action='store',
            help='minimum interval between updates'
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
            default=None
        )
        mysqlopts.add_argument(
            '-d', '--database',
            dest='database',
            default='mediathekview',
            help='database name'
        )
        self.args = parser.parse_args()
        self.verbosity = self.args.verbose

        self.info('Startup')
        self.settings = Settings(self.args)
        self.notifier = Notifier()
        self.monitor = MediathekViewMonitor()
        self.updater = MediathekViewUpdater(
            self.get_new_logger('MediathekViewUpdater'),
            self.notifier,
            self.settings,
            self.monitor
        )
        return self.updater.init(convert=True)

    def run(self):
        """ Execution of the application """
        self.info('Starting up...')
        updateop = self.updater.get_current_update_operation(
            self.args.force, self.args.full)
        if updateop == 1:
            # full update
            self.info('Initiating full update...')
            self.updater.update(True)
        elif updateop == 2:
            # differential update
            self.info('Initiating differential update...')
            self.updater.update(False)
        self.info('Exiting...')

    def exit(self):
        """ Shutdown of the application """
        self.updater.exit()
