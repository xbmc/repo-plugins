# -*- coding: utf-8 -*-
"""
UI Notifier module

Copyright (c) 2017-2018, Leo Moll
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import datetime

# pylint: disable=import-error
from resources.lib.kodi.kodiui import KodiUI
from resources.lib.notifierInterface import NotifierInterface

# -- Classes ------------------------------------------------


class NotifierKodi(NotifierInterface):
    """ The UI notifier class """

    def __init__(self, pAddonClass):
        self.kodiUi = KodiUI()
        self.language = pAddonClass.getLocalizedString

    def show_database_error(self, err):
        """ Displays UI for a database error """
        self.kodiUi.show_error(30951, '{}'.format(err))

    def show_download_error(self, name, err):
        """ Displays UI for a download error """
        self.kodiUi.show_error(30952, self.language(30953).format(name, err))

    def show_missing_extractor_error(self):
        """ Disaplys UI for a missing extractor error """
        self.kodiUi.show_error(30952, 30954, time=10000)

    def show_limit_results(self, maxresults):
        """ Display UI for search result limited by configuration """
        self.kodiUi.show_notification(30980, self.language(30981).format(maxresults))

    def show_outdated_unknown(self):
        """ Display UI for never updated database """
        self.kodiUi.show_warning(30982, 30966)

    def show_outdated_known(self, status):
        """ Display UI for an outdated database """
        updatetype = self.language(
            30972 if status['lastFullUpdate'] > 0 else 30973)
        updatetime = datetime.datetime.fromtimestamp(
            status['lastUpdate']).strftime('%Y-%m-%d %H:%M:%S'),
        updinfo = self.language(30983)
        self.kodiUi.show_warning(30982, updinfo.format(updatetype, updatetime[0]))

    def show_download_progress(self):
        """ Display UI for a download in progress """
        self.kodiUi.show_progress_dialog(30955)

    def update_download_progress(self, percent, message=None):
        """ Update UI odometer for a download in progress """
        self.kodiUi.update_progress_dialog(percent, message=message)

    def hook_download_progress(self, blockcount, blocksize, totalsize):
        """ UI Report hook for functions like `url_retrieve` """
        self.kodiUi.hook_progress_dialog(blockcount, blocksize, totalsize)

    def close_download_progress(self):
        """ Hides the UI for a download in progress """
        self.kodiUi.close_progress_dialog()

    def show_update_progress(self):
        """ Display UI for a database update in progress """
        self.kodiUi.show_progress_dialog(30956)

    def update_update_progress(self, percent, count, insertCount, updateCount):
        """ Update UI odometer for a database update in progress """
        message = self.language(30957) % (percent, count, insertCount, updateCount)
        self.kodiUi.update_progress_dialog(percent, message=message)

    def close_update_progress(self):
        """ Hides the UI for a database update in progress """
        self.kodiUi.close_progress_dialog()

    def show_updating_scheme(self):
        """ SHow UI that the database schema is about to be updated """
        self.kodiUi.show_ok_dialog(30984, 30985)

    def show_update_scheme_progress(self):
        """ Display UI for a database schema update in progress """
        self.kodiUi.show_progress_dialog(30984)

    def update_update_scheme_progress(self, percent):
        """ Update UI odometer for a database schema update in progress """
        self.kodiUi.update_progress_dialog(percent, message='')

    def close_update_scheme_progress(self):
        """ Hides the UI for a database schema update in progress """
        self.kodiUi.close_progress_dialog()

    def get_entered_text(self, deftext=None, heading=None, hidden=False):
        return self.kodiUi.get_entered_text(deftext, heading, hidden)

    def get_entered_multiselect(self, heading=None, options=None, preselect=None):
        return self.kodiUi.get_entered_multiselect(heading, options, preselect)

    def get_entered_select(self, heading=None, list=None, preselect=None):
        return self.kodiUi.get_entered_select(heading, list, preselect)

    def show_error(self, pHeading, pMessage):
        """ Displays UI for a database error """
        self.kodiUi.show_error(pHeading, pMessage)

    def show_notification(self, heading, message):
        self.kodiUi.show_notification(heading, message)
