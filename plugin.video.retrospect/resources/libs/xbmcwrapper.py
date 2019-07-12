#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import time
import os

import xbmcgui
import xbmc

from backtothefuture import basestring
from retroconfig import Config
from locker import LockWithDialog


class XbmcDialogProgressWrapper(object):
    def __init__(self, title, line1, line2=""):
        """ Initialises a XbmcDialogProgressWrapper that wraps an Kodi DialogProgress object.

        :param str title: Title of it
        :param str line1: The first line to show
        :param str line2: The second line to show

        """

        self.Title = title
        self.Line1 = line1
        self.Line2 = line2
        self.progressBarDialog = xbmcgui.DialogProgress()
        self.progressBarDialog.create(title, line1)

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
            self.progressBarDialog.update(int(perc), self.Line1, self.Line2, status)
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

    def __init__(self):
        pass

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
        notification_icon = os.path.join(Config.rootDir, "icon.png")
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
    def show_yes_no(title, lines):
        """ Shows a dialog yes/no box with title and text

        :param str title:           The title of the box.
        :param list[str] lines:     The lines to display.

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

        if len(lines) == 0:
            ok = msg_box.yesno(header, "")
        elif isinstance(lines, basestring):
            # it was just a string, no list or tuple
            ok = msg_box.yesno(header, lines)
        else:
            ok = False
        return ok

    @staticmethod
    def show_dialog(title, lines):
        """ Shows a dialog box with title and text

        :param str|None title:          The title of the box
        :param list[str]|str lines:     The lines to display.

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

        if len(lines) == 0:
            ok = msg_box.ok(header, "")
        elif isinstance(lines, basestring):
            # it was just a string, no list or tuple
            ok = msg_box.ok(header, lines)
        elif len(lines) == 1:
            ok = msg_box.ok(header, lines[0])
        elif len(lines) == 2:
            ok = msg_box.ok(header, lines[0], lines[1])
        else:
            ok = msg_box.ok(header, lines[0], lines[1], lines[2])
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

    @staticmethod
    def wait_for_player_to_start(player, timeout=10, logger=None, url=None):
        """ Waits for the status of the player to start.

        Requires: <import addon="xbmc.python" version="2.0"/>

        :param xbmc.Player player:  The Kodi player.
        :param int timeout:         The time-out to wait for.
        :param any logger:          A `Logger` instance for logging.
        :param str url:             The URL that should be playing.

        :return: Indication whether or not the player is playing.
        :rtype: bool

        """
        return XbmcWrapper.__wait_for_player(player, 1, timeout, logger, url)

    @staticmethod
    def wait_for_player_to_end(player, timeout=10, logger=None):
        """ waits for the status of the player to end

        Requires: <import addon="xbmc.python" version="2.0"/>

        :param xbmc.Player player:  The Kodi player.
        :param int timeout:         The time-out to wait for.
        :param any logger:          A `Logger` instance for logging.

        :return: indication if player has stopped.
        :rtype: bool

        """

        return XbmcWrapper.__wait_for_player(player, 0, timeout, logger, None)

    @staticmethod
    def __wait_for_player(player, play_state, timeout, logger, url):  # NOSONAR
        """ waits for the status of the player to be the desired value

        Requires: <import addon="xbmc.python" version="2.0"/>

        :param xbmc.Player player:  The Kodi player.
        :param in play_state:         The desired play value (1 = start, 0 = stop).
        :param int timeout:         The time-out to wait for.
        :param any logger:          A `Logger` instance for logging.
        :param str|None url:        The URL that should be playing.

        :return: indication if player has started or has stopped.
        :rtype: bool

        """

        start = time.time()

        if logger:
            logger.debug("Waiting for Player status '%s'", play_state)
            if url is None:
                logger.debug("player.isPlaying is '%s', preferred value is '%s'", player.isPlaying(), play_state)
            else:
                logger.debug("player.isPlaying is '%s', preferred value is %s and stream: '%s'",
                             player.isPlaying(), play_state, url)

        while time.time() - start < timeout:
            if player.isPlaying() == play_state:
                if url is None:
                    # the player stopped in time
                    if logger:
                        logger.debug("player.isPlaying obtained the desired value '%s'", play_state)
                    return True

                playing_file = player.getPlayingFile()
                if url == playing_file:
                    if logger:
                        logger.debug("player.isPlaying obtained the desired value '%s' and correct stream.", play_state)
                    return True

                if logger:
                    logger.debug("player.isPlaying obtained the desired value '%s', but incorrect stream: %s",
                                 play_state, playing_file)

            if logger:
                logger.debug("player.isPlaying is %s, waiting a cycle", player.isPlaying())
            time.sleep(1.)

        # a time out occurred
        return False
