
import os
import sys
import urllib
import urlparse
import string

import xbmcgui
import xbmcplugin
import xbmcaddon

__addon__ = xbmcaddon.Addon()
addon_path = __addon__.getAddonInfo('path')
addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
addon_params = dict(urlparse.parse_qsl(sys.argv[2][1:]))


def encode_child_url(mode, **kwargs):
    params = {
        'mode': mode
    }
    params.update(kwargs)

    return "%s?&%s" % (addon_url, urllib.urlencode(params))


def add_dir(name, url, thumb=None):
    def enhance_name(value):
        return string.capwords(value.replace('_', ' '))

    name = enhance_name(name)
    item = xbmcgui.ListItem(name)
    item.setInfo(type="Image", infoLabels={"Title": name})
    if thumb:
        item.setArt({'thumb': thumb})
    xbmcplugin.addDirectoryItem(addon_handle, url, item, True)


def add_image(image):
    item = xbmcgui.ListItem(image.name)
    item.setArt({'thumb': image.thumb_url})
    item.setInfo(
        type='pictures',
        infoLabels={
            "title": image.name,
            "picturepath": image.url,
            "exif:path": image.url
        }
    )

    if not 'ctxsearch' in addon_params:
        label = "More from %s" % image.userfullname # i18n
        url = encode_child_url('search', term=image.username, ctxsearch=True)
        action = "XBMC.Container.Update(%s)" % url
        item.addContextMenuItems([(label, action,)])

    xbmcplugin.addDirectoryItem(addon_handle, image.url, item)

def end_of_directory():
    xbmcplugin.endOfDirectory(addon_handle)
