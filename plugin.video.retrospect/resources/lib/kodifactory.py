# SPDX-License-Identifier: GPL-3.0-or-later

import xbmcgui

from resources.lib.addonsettings import AddonSettings
__kodi_version = AddonSettings.get_kodi_major_version()


def list_item(label="", label2=""):
    """ ListItem class. Creates a new ListItem.

    :param str label:           Label1 text.
    :param str label2:          Label2 text.

    *Note, You can use the above as keywords for arguments and skip certain optional arguments.
       Once you use a keyword, all following arguments require the keyword.

    :returns: an instance of xbmcgui.ListItem
    :rtype: xbmcgui.ListItem

    """

    if __kodi_version < AddonSettings.KodiLeia:
        return xbmcgui.ListItem(label, label2)

    return xbmcgui.ListItem(label, label2, offscreen=True)

