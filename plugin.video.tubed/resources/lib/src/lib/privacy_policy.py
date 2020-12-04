# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants import PRIVACY_POLICY_MARKDOWN
from ..constants import PRIVACY_POLICY_REVISION
from .logger import Log

LOG = Log('lib', __file__)
DIALOG = xbmcgui.Dialog()
MONITOR = xbmc.Monitor()


def show_privacy_policy(context):
    last_revision_accepted = context.settings.get_privacy_policy()
    if last_revision_accepted != PRIVACY_POLICY_REVISION:
        LOG.debug('User has not accepted the current revision '
                  'of the privacy policy, prompting now...')

        with open(PRIVACY_POLICY_MARKDOWN, 'r') as file_handle:
            privacy_policy = file_handle.read()

        privacy_policy = privacy_policy.replace('## ', '').replace('<br />', '').replace('*', '')

        DIALOG.textviewer(context.i18n('Privacy Policy'), privacy_policy)
        result = DIALOG.yesno(
            context.i18n('Privacy Policy'),
            context.i18n('Further use of Tubed will be subject to this privacy policy'),
            context.i18n('Decline'),
            context.i18n('Accept'),
        )

        if not result:
            LOG.debug('User has declined acceptance of the current revision of the privacy policy')
            return False

        LOG.debug('User has accepted the current revision of the privacy policy')
        context.settings.set_privacy_policy(PRIVACY_POLICY_REVISION)

    return True
