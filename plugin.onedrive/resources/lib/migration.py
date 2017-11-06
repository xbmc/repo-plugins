#-------------------------------------------------------------------------------
# Copyright (C) 2017 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
# 
# This file is part of OneDrive for Kodi
# 
# OneDrive for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Cloud Drive Common Module for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import os
from clouddrive.common.utils import Utils
from clouddrive.common.ui.utils import KodiUtils
from ConfigParser import ConfigParser
from clouddrive.common.account import AccountManager
from clouddrive.common.ui.logger import Logger
from clouddrive.common.exception import UIException


class MigrateAccounts(object):
    def __init__(self):
        profile_path = Utils.unicode(KodiUtils.translate_path(KodiUtils.get_addon_info('profile')))
        ini_path = os.path.join(profile_path, 'onedrive.ini')
        if os.path.exists(ini_path):
            config = ConfigParser()
            account_manager = AccountManager(profile_path)
            config.read(ini_path)
            for driveid in config.sections():
                Logger.notice('Migrating drive %s...' % driveid)
                account = { 'id' : driveid, 'name' : config.get(driveid, 'name')}
                account['drives'] = [{
                    'id' : driveid,
                    'name' : '',
                    'type' : 'migrated'
                }]
                account['access_tokens'] = {
                    'access_token': config.get(driveid, 'access_token'),
                    'refresh_token': config.get(driveid, 'refresh_token'),
                    'expires_in': 0,
                    'date': 0
                }
                try:
                    account_manager.add_account(account)
                except Exception as e:
                    raise UIException(32021, e)
            os.remove(ini_path)
        KodiUtils.set_addon_setting('migrated', 'true')
    