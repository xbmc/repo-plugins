import xbmcplugin
import sys

if sys.version_info[0] == 3:
    from urllib.parse import quote
else:
    from urllib import quote

import inputstreamhelper
import xbmcgui
import xbmc
from resources.lib.helpers.dynamic_headers import UA, widevine_payload_package


PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
LICENSE_URL = 'https://lwvdrm.yelo.prd.telenet-ops.be/WvLicenseProxy'


class KodiWrapper:
    """ All Kodi controls are programmed here """

    def __init__(self, handle, url, addon):
        self.__handle = handle
        self.__url = url
        self.__addon = addon

    def create_list_item(self, label, logo, fanart, playable):
        list_item = xbmcgui.ListItem()
        list_item.setLabel(label)
        list_item.setArt({'fanart': fanart, 'icon' : logo})
        list_item.setInfo('video', {'title': label})
        list_item.setProperty('IsPlayable', playable)

        return list_item

    def get_app_handle(self):
        return self.__handle

    def get_app_url(self):
        return self.__url

    def sort_method(self, sort_method):
        xbmcplugin.addSortMethod(self.__handle, sort_method)

    def construct_url(self, route, *args):
        url = route.format(self.__url, args[0])
        return url

    def add_dir_item(self, listing):
        xbmcplugin.addDirectoryItems(self.__handle, listing, len(listing))

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
