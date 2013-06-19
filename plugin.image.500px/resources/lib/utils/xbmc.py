
import os
import sys
import urllib
import urlparse

import xbmcgui
import xbmcplugin

addon_path = os.getcwd()
addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
addon_params = dict(urlparse.parse_qsl(sys.argv[2][1:]))


def encode_child_url(mode, **kwargs):
    params = {
        'mode': mode
    }
    params.update(kwargs)

    return "%s?&%s" % (addon_url, urllib.urlencode(params))


def add_dir(name, url):
    def enhance_name(value):
        return value.replace('_', ' ').title()

    name = enhance_name(name)
    item = xbmcgui.ListItem(name)
    item.setInfo(type="Image", infoLabels={"Title": name})
    xbmcplugin.addDirectoryItem(addon_handle, url, item, True)


def add_image(image):
    item = xbmcgui.ListItem(image.name, thumbnailImage=image.thumb_url)
    xbmcplugin.addDirectoryItem(addon_handle, image.url, item)

def end_of_directory():
    xbmcplugin.endOfDirectory(addon_handle)