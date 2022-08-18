# -*- coding: utf-8 -*-
"""
The Kodi addons module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import xbmc
import xbmcgui
import xbmcaddon
import resources.lib.mvutils as mvutils


class KodiUI(object):
    """ Generic helper class for Kodi UI operations """

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.language = self.addon.getLocalizedString
        self.pgdialog = KodiProgressDialog()

    def get_entered_text(self, deftext=None, heading=None, hidden=False):
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
        heading = self.language(heading) if isinstance(heading, int) else heading if heading is not None else ''
        deftext = self.language(deftext) if isinstance(deftext, int) else deftext if deftext is not None else ''
        keyboard = xbmc.Keyboard(deftext, heading, 1 if hidden else 0)
        keyboard.doModal()
        if keyboard.isConfirmed():
            enteredText = keyboard.getText();
            enteredText = mvutils.py2_decode(enteredText);
            return (enteredText, True, )
        return (deftext, False, ) ##TODO deftext.encode('utf-8')

    def show_ok_dialog(self, heading=None, line1=None, line2=None, line3=None):
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
        heading = self.language(heading) if isinstance(heading, int) else heading if heading is not None else ''
        line1 = self.language(line1) if isinstance(line1, int) else line1 if line1 is not None else ''
        line2 = self.language(line2) if isinstance(line2, int) else line2 if line2 is not None else ''
        line3 = self.language(line3) if isinstance(line3, int) else line3 if line3 is not None else ''
        dialog = xbmcgui.Dialog()
        retval = dialog.ok(heading, line1 + "\n" + line2 + "\n" + line3)
        del dialog
        return retval

    # pylint: disable=line-too-long
    def show_notification(self, heading, message, icon=xbmcgui.NOTIFICATION_INFO, time=5000, sound=True):
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
        heading = self.language(heading) if isinstance(
            heading, int) else heading
        message = self.language(message) if isinstance(
            message, int) else message
        xbmcgui.Dialog().notification(heading, message, icon, time, sound)

    def show_warning(self, heading, message, time=5000, sound=True):
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
        self.show_notification(
            heading, message, xbmcgui.NOTIFICATION_WARNING, time, sound)

    def show_error(self, heading, message, time=8000, sound=True):
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
        self.show_notification(
            heading, message, xbmcgui.NOTIFICATION_ERROR, time, sound)

    def show_progress_dialog(self, heading=None, message=None):
        """
        Shows a progress dialog to the user

        Args:
            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        self.pgdialog.create(heading, message)

    def update_progress_dialog(self, percent, heading=None, message=None):
        """
        Updates a progress dialog

        Args:
            percent(int): percentage of progress

            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        self.pgdialog.update(percent, heading, message)

    def hook_progress_dialog(self, blockcount, blocksize, totalsize):
        """
        A hook function that will be passed to functions like `url_retrieve`

        Args:
            blockcount(int): Count of blocks transferred so far

            blocksize(int): Block size in bytes

            totalsize(int): Total size of the file
        """
        self.pgdialog.url_retrieve_hook(blockcount, blocksize, totalsize)

    def close_progress_dialog(self):
        """ Closes a progress dialog """
        self.pgdialog.close()


class KodiProgressDialog(object):
    """ Kodi Progress Dialog Class """

    def __init__(self):
        self.language = xbmcaddon.Addon().getLocalizedString
        self.pgdialog = None

    def __del__(self):
        self.close()

    def create(self, heading=None, message=None):
        """
        Shows a progress dialog to the user

        Args:
            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        heading = self.language(heading) if isinstance(
            heading, int) else heading
        message = self.language(message) if isinstance(
            message, int) else message
        if self.pgdialog is None:
            self.pgdialog = xbmcgui.DialogProgressBG()
            self.pgdialog.create(heading, message)
        else:
            self.pgdialog.update(0, heading, message)

    def update(self, percent, heading=None, message=None):
        """
        Updates a progress dialog

        Args:
            percent(int): percentage of progress

            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        if self.pgdialog is not None:
            heading = self.language(heading) if isinstance(
                heading, int) else heading
            message = self.language(message) if isinstance(
                message, int) else message
            self.pgdialog.update(percent, heading, message)

    def url_retrieve_hook(self, blockcount, blocksize, totalsize):
        """
        A hook function that will be passed to functions like `url_retrieve`

        Args:
            blockcount(int): Count of blocks transferred so far

            blocksize(int): Block size in bytes

            totalsize(int): Total size of the file
        """
        downloaded = blockcount * blocksize
        if totalsize > 0:
            percent = int((downloaded * 100) / totalsize)
            if self.pgdialog is not None:
                self.pgdialog.update(percent)

    def close(self):
        """ Closes a progress dialog """
        if self.pgdialog is not None:
            self.pgdialog.close()
            del self.pgdialog
            self.pgdialog = None
