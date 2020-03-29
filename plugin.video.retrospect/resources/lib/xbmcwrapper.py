# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os

import xbmcgui
import xbmc
import xbmcaddon

from resources.lib.backtothefuture import unichr
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.retroconfig import Config
from resources.lib.locker import LockWithDialog


class XbmcDialogProgressWrapper(object):
    def __init__(self, title, message):
        """ Initialises a XbmcDialogProgressWrapper that wraps an Kodi DialogProgress object.

        :param str title: Title of it
        :param str message: The first line to show

        """

        self.title = title
        self.message = message
        self.progressBarDialog = xbmcgui.DialogProgress()
        self.progressBarDialog.create(title, message)

    def __call__(self, *args):
        return self.progress_update(*args)

    # noinspection PyUnusedLocal
    def progress_update(self, retrieved_size, total_size, perc, completed, status):
        """ Updates the dialog

        NOTE: this method signature is the same as the XbmcDialogProgressBgWrapper.Update

        :param int retrieved_size:  The bytes received
        :param int total_size:      The total bytes to receive
        :param int perc:            The percentage done
        :param bool completed:      Are we done?
        :param str status:          What is the status?

        :return: True if canceled.
        :rtype: bool

        """

        if not completed:
            message = "{}\n\n{}".format(self.message, status)
            self.progressBarDialog.update(int(perc), message)
        else:
            self.progressBarDialog.close()

        return self.progressBarDialog.iscanceled()

    def close(self):
        """ Close the progress dialog. """
        self.progressBarDialog.close()


class XbmcDialogProgressBgWrapper:
    def __init__(self, heading, message):
        """ Initialises a XbmcDialogProgressWrapper that wraps an Kodi DialogProgress object.

        :param str heading: Title of it
        :param str message: The first line to show

        """

        self.Heading = heading
        self.Message = message
        self.progressBarDialog = xbmcgui.DialogProgressBG()
        self.progressBarDialog.create(heading, message)
        # it does not reset?
        self.progressBarDialog.update(percent=1, heading=heading, message=message)

    def __call__(self, *args):
        return self.progress_update(*args)

    # noinspection PyUnusedLocal
    def progress_update(self, retrieved_size, total_size, perc, completed, status):
        """ Updates the dialog

        NOTE: this method signature is the same as the XbmcDialogProgressWrapper.Update

        :param int retrieved_size:  The bytes received
        :param int total_size:      The total bytes to receive
        :param int perc:            The percentage done
        :param bool completed:      Are we done?
        :param str status:          What is the status?

        :return: True if canceled.
        :rtype: bool

        """

        if not completed:
            # noinspection PyTypeChecker
            self.progressBarDialog.update(percent=int(perc), heading=self.Heading, message=status)
        else:
            self.progressBarDialog.close()

        # no cancel
        return False

    def close(self):
        """ Close the progress dialog. """
        self.progressBarDialog.close()


class XbmcWrapper:
    """ Wraps some basic Kodi methods """

    Error = "error"
    Warning = "warning"
    Info = "info"

    __add_on_name_lookup = dict()

    def __init__(self):
        pass

    @staticmethod
    def get_external_add_on_label(add_on_url):
        """ Returns the formatting string for the label of an item with an external add-on url

        :param str add_on_url:   The plugin://-handle for the add-on
        
        :return: the name of the add-on or None if not installed
        :rtype: str

        """

        if add_on_url is None:
            return "{}"

        # We need the add-on ID
        add_on_id = add_on_url.split("/", 3)[2]
        add_on_label = XbmcWrapper.__add_on_name_lookup.get(add_on_id)
        if add_on_label is not None:
            return add_on_label

        try:
            add_on_name = xbmcaddon.Addon(add_on_id).getAddonInfo('name')
            via = LanguageHelper.get_localized_string(LanguageHelper.OtherAddon)
        except:
            add_on_name = add_on_id
            via = LanguageHelper.get_localized_string(LanguageHelper.MissingAddon)

        add_on_label = "{0} [COLOR gold]{1} '{2}'[/COLOR]".format(unichr(187), via, add_on_name)
        XbmcWrapper.__add_on_name_lookup[add_on_id] = add_on_label
        return add_on_label

    @staticmethod
    def show_key_board(default="", heading="", hidden=False):
        """ Displays the Kodi keyboard.

        :param str default:     The default value
        :param str heading:     The heading for the dialog
        :param bool hidden:     Should the input be hidden?

        :rtype: str
        :return: returns the text that was entered or None if cancelled.

        """

        # let's just unlock the interface, in case it's locked.
        LockWithDialog.close_busy_dialog()

        keyboard = xbmc.Keyboard(default, heading, hidden)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return None

        return keyboard.getText()

    @staticmethod
    def show_notification(title, lines, notification_type=Info, display_time=1500,
                          fallback=True, logger=None):
        """ Shows an Kodi Notification

        :param str|None title:          The title to show.
        :param str|list[str] lines:     The content to show.
        :param str notification_type:   The type of notification: info, error, warning.
        :param int display_time:        Time to display the notification. Defaults to 1500 ms.
        :param bool fallback:           Should we fallback on XbmcWrapper.show_dialog on error?
        :param any logger:              A possible `Logger` object.

        """

        # check for a title
        if title:
            notification_title = "%s - %s" % (Config.appName, title)
        else:
            notification_title = Config.appName

        # check for content and merge multiple lines. This is to stay compatible
        # with the LanguageHelper.get_localized_string that returns strings as arrays
        # if they are multiple lines (this is because XbmcWrapper.show_dialog needs
        # this for multi-line dialog boxes.
        if not lines:
            notification_content = ""
        else:
            if isinstance(lines, (tuple, list)):
                notification_content = " ".join(lines)
            else:
                notification_content = lines

        # determine the duration
        notification_type = notification_type.lower()
        if notification_type == XbmcWrapper.Warning and display_time < 2500:
            display_time = 2500
        elif notification_type == XbmcWrapper.Info and display_time < 5000:
            display_time = 5000
        elif display_time < 1500:
            # cannot be smaller then 1500 (API limit)
            display_time = 1500

        # Get an icon
        notification_icon = Config.icon
        if os.path.exists(notification_icon):
            # change the separators
            notification_icon = notification_icon.replace("\\", "/")
        else:
            notification_icon = notification_type

        if logger:
            logger.debug("Showing notification: %s - %s", notification_title, notification_content)

        try:
            xbmcgui.Dialog().notification(
                notification_title, notification_content, icon=notification_icon, time=display_time)
            return
        except:
            if fallback:
                XbmcWrapper.show_dialog(title or "", lines or "")
            # no reason to worry if this does not work on older XBMC's
            return

    @staticmethod
    def show_selection_dialog(title, options):
        """ Shows a Kodi Selection Dialog.

        :param str title:           The title of the dialog
        :param list[str]options:    The list options to show

        :return: The index of the selected item
        :rtype: int

        """

        input_dialog = xbmcgui.Dialog()
        return input_dialog.select(title, options)

    @staticmethod
    def show_yes_no(title, message):
        """ Shows a dialog yes/no box with title and text

        :param str title:       The title of the box.
        :param str message:     The message to display.

        :return: Ok or not OK (boolean)
        :rtype: bool

        """

        # let's just unlock the interface, in case it's locked.
        LockWithDialog.close_busy_dialog()

        msg_box = xbmcgui.Dialog()
        if title == "":
            header = Config.appName
        else:
            header = "%s - %s" % (Config.appName, title)

        ok = msg_box.yesno(header, message or "")
        return ok

    @staticmethod
    def show_dialog(title, message):
        """ Shows a dialog box with title and text

        :param str|None title:      The title of the box
        :param str message:         The lines to display.

        :return: True for OK, False for cancelled.
        :rtype: bool

        """

        # let's just unlock the interface, in case it's locked.
        LockWithDialog.close_busy_dialog()

        msg_box = xbmcgui.Dialog()
        if title == "":
            header = Config.appName
        else:
            header = "%s - %s" % (Config.appName, title)

        ok = msg_box.ok(header, message or "")
        return ok

    @staticmethod
    def show_folder_selection(title, default_path=None, dialog_type=3, mask=''):
        """ Shows a file/folder selection dialog for a given `dialog_type`:

        * 0 : ShowAndGetDirectory
        * 1 : ShowAndGetFile
        * 2 : ShowAndGetImage
        * 3 : ShowAndGetWriteableDirectory

        :param str title:           The title of the box.
        :param str default_path:     Default path or file.
        :param int dialog_type:      Type of file/folder selection type.
        :param str mask:            '|' separated file mask. (i.e. '.jpg|.png').

        :return: the selected file/folder.
        :rtype: str

        """

        if default_path is None:
            default_path = xbmc.translatePath("special://home")

        browse_dialog = xbmcgui.Dialog()
        dest_folder = browse_dialog.browse(dialog_type, title, 'files', mask, False, False, default_path)
        return dest_folder

    @staticmethod
    def execute_json_rpc(json, logger=None):
        """ Executes a Kodi JSON command.

        :param str json:    JSON formatted command.
        :param any logger:  A `Logger` object.

        :return: The response from the command
        :rtype: str

        """

        if logger:
            logger.trace("Sending command: %s", json)
        response = xbmc.executeJSONRPC(json)
        if logger:
            logger.trace("Received result: %s", response)
        return response
