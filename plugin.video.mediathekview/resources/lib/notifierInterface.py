# -*- coding: utf-8 -*-
"""
UI Notifier module

Copyright (c) 2017-2018, Leo Moll
SPDX-License-Identifier: MIT
"""


class NotifierInterface(object):
    """ The UI notifier class """

    def __init__(self):
        pass

    def show_database_error(self, err):
        pass

    def show_download_error(self, name, err):
        pass

    def show_missing_extractor_error(self):
        pass

    def show_limit_results(self, maxresults):
        pass

    def show_outdated_unknown(self):
        pass

    def show_outdated_known(self, status):
        pass

    def show_download_progress(self):
        pass

    def update_download_progress(self, percent, message=None):
        pass

    def hook_download_progress(self, blockcount, blocksize, totalsize):
        pass

    def close_download_progress(self):
        pass

    def show_update_progress(self):
        pass

    def update_update_progress(self, percent, count, insertCount, updateCount):
        pass

    def close_update_progress(self):
        pass

    def show_updating_scheme(self):
        pass

    def show_update_scheme_progress(self):
        pass

    def update_update_scheme_progress(self, percent):
        pass

    def close_update_scheme_progress(self):
        pass

    def get_entered_text(self, deftext=None, heading=None, hidden=False):
        pass

    def show_notification(self, heading, message):
        pass
