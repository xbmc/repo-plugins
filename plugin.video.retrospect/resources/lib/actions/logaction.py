# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.actions.addonaction import AddonAction
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.locker import LockWithDialog
from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.xbmcwrapper import XbmcWrapper


class LogAction(AddonAction):
    def __init__(self, parameter_parser):
        super(LogAction, self).__init__(parameter_parser)

    @LockWithDialog(logger=Logger.instance())
    def execute(self):
        """ Send log files via Pastbin or Gist. """

        from resources.lib.helpers.logsender import LogSender
        sender_mode = 'hastebin'
        log_sender = LogSender(Config.logSenderApi, logger=Logger.instance(), mode=sender_mode)
        try:
            title = LanguageHelper.get_localized_string(LanguageHelper.LogPostSuccessTitle)
            url_text = LanguageHelper.get_localized_string(LanguageHelper.LogPostLogUrl)
            files_to_send = [Logger.instance().logFileName,
                             Logger.instance().logFileName.replace(".log", ".old.log")]
            paste_url = log_sender.send_file(Config.logFileNameAddon, files_to_send[0])
            XbmcWrapper.show_dialog(title, url_text % (paste_url,))
        except Exception as e:
            Logger.error("Error sending %s", Config.logFileNameAddon, exc_info=True)

            title = LanguageHelper.get_localized_string(LanguageHelper.LogPostErrorTitle)
            error_text = LanguageHelper.get_localized_string(LanguageHelper.LogPostError)
            error = error_text % (str(e),)
            XbmcWrapper.show_dialog(title, error.strip(": "))
