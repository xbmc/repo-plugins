import xbmcplugin
import xbmcgui
import xbmc
from xbmcaddon import Addon

import sys
import inputstreamhelper

if sys.version_info[0] == 3:
    from urllib.parse import quote
else:
    from urllib import quote

from resources.lib.helpers.dynamic_headers import UA, widevine_payload_package


PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
LICENSE_URL = 'https://lwvdrm.yelo.prd.telenet-ops.be/WvLicenseProxy'


class KodiWrapper:
    """ All Kodi controls are programmed here """
    def __init__(self, globals):
        self.globals = globals
        self.__addon = Addon()
        self.routing = globals['routing']
        self.__handle = globals['routing'].handle
        self.__url = globals['routing'].base_url


    def create_list_item(self, label, logo, fanart, extra_info = None, playable = "false"):
        list_item = xbmcgui.ListItem()
        list_item.setLabel(label)
        list_item.setArt({'fanart': fanart, 'icon' : logo, 'thumb': logo})

        info = {'title': label}
        if extra_info:
            info.update(extra_info)

        list_item.setInfo('video', info)
        list_item.setProperty('IsPlayable', playable)

        return list_item

    def get_app_handle(self):
        return self.__handle

    def get_app_url(self):
        return self.__url

    def sort_method(self, sort_method):
        xbmcplugin.addSortMethod(self.__handle, sort_method)

    def get_addon_url(self):
        return self.__url

    def add_dir_items(self, listing):
        xbmcplugin.addDirectoryItems(self.__handle, listing, len(listing))

    def add_dir_item(self, url, item, total_items, isFolder=False):
        xbmcplugin.addDirectoryItem(self.__handle, url, item, isFolder, total_items)

    def end_directory(self):
        xbmcplugin.endOfDirectory(self.__handle)

    def get_setting(self, setting_id):
        return self.__addon.getSetting(setting_id)

    def get_addon_data_path(self):
        global profile
        if sys.version_info[0] == 3:
            profile = xbmc.translatePath(self.__addon.getAddonInfo('profile'))
        else:
            profile = xbmc.translatePath(self.__addon.getAddonInfo('profile')).decode("utf-8")

        return profile

    def url_for(self, name, *args, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return self.routing.url_for(self.globals[name], *args, **kwargs)

    @staticmethod
    def dialog_yes_no(header, message):
        dialog = xbmcgui.Dialog()
        return dialog.yesno(header, message)

    @staticmethod
    def dialog_ok(header, message):
        dialog = xbmcgui.Dialog()
        return dialog.ok(header, message)

    def open_settings(self):
        self.__addon.openSettings()

    def get_localized_string(self, number):
        return self.__addon.getLocalizedString(number)


    def play_live_stream(self, device_Id, customer_Id, stream_url, max_bandwith):
        """ Payload needs to be base64encoded as well as the whole message send to the server """
        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():
            play_item = xbmcgui.ListItem(path=stream_url)
            play_item.setMimeType('application/xml+dash')
            play_item.setContentLookup(False)
            play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            play_item.setProperty('inputstream.adaptive.license_type', DRM)
            play_item.setProperty('inputstream.adaptive.max_bandwidth', max_bandwith)
            play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            play_item.setProperty('inputstream.adaptive.stream_headers', 'user-agent =' + UA)
            play_item.setProperty('inputstream.adaptive.license_key',
                                  LICENSE_URL + '|Content-Type=text%2Fplain%3Bcharset%3DUTF-8&User-Agent=' + quote(UA) +
                                  '|' + 'b{' +
                                  widevine_payload_package(device_Id, customer_Id) + '}' +
                                  '|JBlicense')
            play_item.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
            xbmcplugin.setResolvedUrl(self.__handle, True, listitem=play_item)
