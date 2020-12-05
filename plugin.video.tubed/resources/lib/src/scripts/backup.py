# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os
import time

import xbmcgui  # pylint: disable=import-error

from ..constants import ADDONDATA_PATH
from ..constants.media import LOGO_SMALL
from ..lib.zip_utils import compress
from ..lib.zip_utils import decompress

BACKUP_LIST = [
    os.path.join(ADDONDATA_PATH, 'users.xml'),
    os.path.join(ADDONDATA_PATH, 'settings.xml'),
    os.path.join(ADDONDATA_PATH, 'api_keys.json'),
    os.path.join(ADDONDATA_PATH, 'channels', '', ''),
    os.path.join(ADDONDATA_PATH, 'playlists', '', ''),
    os.path.join(ADDONDATA_PATH, 'search', '', ''),
]

DIALOG = xbmcgui.Dialog()


def invoke(context, action):
    addon_name = context.addon.getAddonInfo('name')

    if action == 'backup':
        backup_location = DIALOG.browseSingle(
            3, context.i18n('Choose a location to create backup'), ""
        )

        if not backup_location:
            return

        try:
            zip_filename = '%s-%s-bak.zip' % (addon_name.lower(), time.strftime('%Y%m%d-%H%M%S'))
            zip_path = os.path.join(backup_location, zip_filename)

            compress(zip_path, BACKUP_LIST, 'x')
            if not os.path.exists(zip_path):
                raise Exception

            xbmcgui.Dialog().notification(
                addon_name,
                context.i18n('Backup successfully created at %s') % backup_location,
                LOGO_SMALL,
                sound=False
            )
            return

        except:  # pylint: disable=bare-except
            xbmcgui.Dialog().notification(
                addon_name,
                context.i18n('Failed to create backup at %s') % backup_location,
                LOGO_SMALL,
                sound=False
            )
            return

    if action == 'restore':
        backup_location = DIALOG.browseSingle(
            1, context.i18n('Choose a backup to restore'), "", mask='.zip'
        )

        if not backup_location:
            return

        rollback_filename = '%s-rollback.zip' % (addon_name.lower())
        rollback_path = os.path.join(ADDONDATA_PATH, rollback_filename)

        try:
            # create a rollback zip in case there is an issue during restoration
            compress(rollback_path, BACKUP_LIST)
            if not os.path.exists(rollback_path):
                raise Exception

            decompress(backup_location, ADDONDATA_PATH)

            xbmcgui.Dialog().notification(
                addon_name,
                context.i18n('Backup successfully restored from %s') % backup_location,
                LOGO_SMALL,
                sound=False
            )
            return

        except:  # pylint: disable=bare-except
            xbmcgui.Dialog().notification(
                addon_name,
                context.i18n('Failed to restore backup from %s') % backup_location,
                LOGO_SMALL,
                sound=False
            )

            if os.path.exists(rollback_path):
                decompress(rollback_path, ADDONDATA_PATH)
            return
