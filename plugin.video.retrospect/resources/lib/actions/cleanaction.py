# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os

from resources.lib.actions.addonaction import AddonAction
from resources.lib.envcontroller import EnvController
from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.languagehelper import LanguageHelper


class CleanAction(AddonAction):
    def execute(self):
        title = LanguageHelper.get_localized_string(LanguageHelper.CleanupCache)[:-1]
        clean = \
            XbmcWrapper.show_yes_no(title, LanguageHelper.CleanupConfirmation)
        if not clean:
            Logger.warning("Clean-up cancelled")
            return

        files_to_remove = {
            "channelindex.json": "Cleaning: Channel Index",
            "cookiejar.dat": "Cleaning: Cookies in cookiejar.dat",
            "xot.session.lock": "Cleaning: Session lock"
        }
        for file_name, log_line in files_to_remove.items():
            Logger.info(log_line)
            files_to_remove = os.path.join(Config.profileDir, file_name)
            if os.path.isfile(files_to_remove):
                os.remove(files_to_remove)

        Logger.info("Cleaning: PickeStore objects")
        self.parameter_parser.pickler.purge_store(Config.addonId, age=0)

        Logger.info("Cleaning: Cache objects in cache folder")
        env_ctrl = EnvController(Logger.instance())
        env_ctrl.cache_clean_up(Config.cacheDir, 0)

    def __init__(self, parameter_parser):
        """ Cleans the cache and cookies

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        """

        super(CleanAction, self).__init__(parameter_parser)
