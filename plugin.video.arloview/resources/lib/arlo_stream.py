from __future__ import absolute_import, division, unicode_literals

import datetime
import json
import os
import threading
import time

import arlo
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from resources.lib import *

try:
    # For Python 3.0 and later
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib import urlencode
    from urlparse import parse_qsl


# Plugin Info
ADDON_ID = 'plugin.video.arloview'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC = py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
ADDON_PATH = py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))) 
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')


def get_params(args):
    return dict(parse_qsl(args[2][1:]))


def get_url(url, **kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """

    url = '{0}?{1}'.format(url, urlencode(kwargs))
    return url


class ArloStream(object):

    def __init__(self, sys_args):
        self._url = sys_args[0]
        self._handle = int(sys_args[1])
        self._args = sys_args
        self.arlo = None
        self.basestation = None
        self.cameras = None
        self.addon_debug_logging = REAL_SETTINGS.getSettingBool('enable_debug')

    def log(self, msg, level=xbmc.LOGNOTICE):

        # Only log messages (via this function) if debug-logging is turned on in plugin settings
        if self.addon_debug_logging :
            if level < xbmc.LOGNOTICE:
                level = xbmc.LOGNOTICE
            xbmc.log("[{}-{}] {}".format(ADDON_ID, ADDON_VERSION, msg), level)

    def main_menu(self):
        for camera in self._get_arlo_cameras():
            camera_info = self._get_camera_info(camera)
            list_item = xbmcgui.ListItem(label=camera["deviceName"])
            list_item.setInfo('video', {'title': camera["deviceName"],
                                        'plot': camera_info,
                                        'mediatype': 'video'})
            list_item.setProperty('IsPlayable', 'true')
            snapshot_file = self._get_camera_snapshot(camera['deviceId'])
            list_item.setArt({'thumb': snapshot_file,
                              'icon': snapshot_file,
                              'poster': snapshot_file,
                              'clearart': snapshot_file,
                              'clearlogo': snapshot_file})
            # Create a URL for a plugin recursive call.
            url = get_url("plugin://" + ADDON_ID,
                          cameraName=camera["deviceName"],
                          cameraId=camera["deviceId"])
            # Add the list item to a virtual Kodi folder.
            # is_folder = False means that this item won't open any sub-list.
            is_folder = False
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(self._handle, url, list_item, is_folder)
        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self._handle)


    def _get_arlo_cameras(self):
        if self.cameras is None:
            self.log("Retrieving cameras...", xbmc.LOGDEBUG)
            self.cameras = self.arlo.GetDevices("camera")
            self._update_arlo_cameras_details()
            #self.log(json.dumps(self.cameras, indent=4), xbmc.LOGDEBUG)

        return self.cameras

    def _update_arlo_cameras_details(self):
        if not self.cameras is None:
            detail_camera_info = self.arlo.GetCameraState(self.basestation)
            for idx, camera in enumerate(self.cameras, start=0):
                camera['batteryLevel'] = ""
                camera['signalStrength'] = ''
                camera['hwVersion'] = ''
                camera['swVersion'] = ''
                for camera_detail in detail_camera_info['properties']:
                    if camera['deviceId'] == camera_detail['serialNumber']:
                        camera['batteryLevel'] = camera_detail['batteryLevel']
                        camera['signalStrength'] = camera_detail['signalStrength']
                        camera['hwVersion'] = camera_detail['hwVersion']
                        camera['swVersion'] = camera_detail['swVersion']
                        self.cameras[idx] = camera
                        break

    def _get_camera(self, device_id):
        tgt_camera = None
        self.log("BEGIN _get_camera() deviceID: {}".format(device_id), xbmc.LOGDEBUG)
        for camera in self._get_arlo_cameras():
            if device_id == camera["deviceId"]:
                tgt_camera = camera
                break
        self.log("END   _get_camera() returns: {}".format(tgt_camera['deviceName']), xbmc.LOGDEBUG)
        return tgt_camera

    def _get_camera_info(self, camera):
        fmt_str = "Device ID : {0}\n" + \
                  "Model ID  : {1}\n" + \
                  "Batt Lvl  : {2}\n" + \
                  "Sig Str   : {3}\n"
        return fmt_str.format(camera['deviceId'],
                              camera['properties']['modelId'],
                              camera['batteryLevel'],
                              camera['signalStrength'])

    
    def _get_camera_snapshot(self, device_id):
        if not REAL_SETTINGS.getSettingBool('show_snapshots'):
            snapshot_file = "{0}/resources/ArloCamera.png".format(ADDON_PATH)
        else:
            snapshot_path = "{0}/resources/media".format(SETTINGS_LOC)
            if not os.path.exists(snapshot_path):
                os.makedirs(snapshot_path)
            snapshot_file = self._refresh_snapshot(device_id, snapshot_path)

        self.log("Snapshot file: {}".format(snapshot_file), xbmc.LOGDEBUG)
        return snapshot_file

    def _refresh_snapshot(self, device_id, snapshot_path):
        camera = self._get_camera(device_id)
        snapshot_type = REAL_SETTINGS.getSetting('snapshot_type')
        snapshot_file_prefix = ''.join(ch for ch in snapshot_type if ch.isupper())
        snapshot_file = "{0}/{1}_{2}.jpg".format(snapshot_path, snapshot_file_prefix, camera['deviceId'])
        if self._snapshot_expired(snapshot_file):
            snapshot_url = camera[snapshot_type]
            try:
                self.log("Download {} into {}_{}".format(snapshot_type, snapshot_file_prefix, camera['deviceId']),xbmc.LOGNOTICE)
                self.arlo.DownloadSnapshot(snapshot_url, snapshot_file, 4096)
                if os.path.getsize(snapshot_file) < 1024:
                    # File seems to be invalid, ?remove so it will try again the next time?
                    self.log("Invalid jpg? FILE: {}".format(snapshot_file), xbmc.LOGERROR)
                    snapshot_file = "{0}/resources/ArloCamera.png".format(ADDON_PATH)
            except Exception as err:
                self.log("Unable to download snapshot: {0}".format(err), xbmc.LOGERROR)
                snapshot_file = "{0}/resources/ArloCamera.png".format(ADDON_PATH)

        return snapshot_file

    def _snapshot_expired(self, snapshot_file):
        expired = False
        if not os.path.exists(snapshot_file):
            self.log("_snapshot_expired() - file does not exist", xbmc.LOGDEBUG)
            expired = True
        elif os.path.getsize(snapshot_file) < 1024:
            self.log("_snapshot_expired() - file appears to be invalid, check contents with editor", xbmc.LOGDEBUG)
            expired = True
        else:
            snapshot_created_time = os.path.getctime(snapshot_file) 
            days_old = (time.time() - snapshot_created_time) // (24 * 3600)
            if days_old >= 7:
                self.log("_snapshot_expired() - file is {} days old".format(days_old), xbmc.LOGDEBUG)
                expired = True
            else:
                self.log("Found cached snapshot, will use it.", xbmc.LOGDEBUG)

        return expired

    def _stop_camera(self):
        pass

    def _play_camera(self, device_id):
        # Send the command to start the stream and return the stream url.
        camera = self._get_camera(device_id)
        stream_url = self.arlo.StartStream(self.basestation, camera)

        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=stream_url, label=camera['deviceName'])
        play_item.setProperty("isPlayable", "true")
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)

    def _arlo_login(self):
        self.log("BEGIN _arlo_login()", xbmc.LOGDEBUG)
        user_name = REAL_SETTINGS.getSetting('userid')
        password = REAL_SETTINGS.getSetting('password')
        self.arlo = arlo.Arlo(user_name, password)
        self.basestation = self.arlo.GetDevices('basestation')[0]
        #self.log(json.dumps(self.basestation, indent=4), xbmc.LOGDEBUG)
        self.log("END   _arlo_login()", xbmc.LOGDEBUG)

    def _arlo_logout(self):
        self.log("_arlo_logout() in progress...")
        self.arlo.Logout()

    def check_first_run(self):
        if REAL_SETTINGS.getSetting("userid") == "":
            self.log("check_first_run()- userid NOT set!", xbmc.LOGNOTICE)
            msg = "Set ARLO credentials, otherwise...\nVideo will not stream correctly!"
            icon = REAL_SETTINGS.getAddonInfo('icon')
            xbmcgui.Dialog().notification(ADDON_NAME, msg, icon, 5000)
            REAL_SETTINGS.openSettings()
            self.addon_debug_logging = REAL_SETTINGS.getSettingBool('enable_debug')


    def run(self):
        params = get_params(self._args)
        # Set plugin category. It is displayed in some skins as the name
        # of the current section.
        xbmcplugin.setPluginCategory(self._handle, 'Arlo Cameras')
        # Set plugin content. It allows Kodi to select appropriate views
        # for this type of content.
        xbmcplugin.setContent(self._handle, 'files')

        self.check_first_run()

        if REAL_SETTINGS.getSetting("userid") == "":
            xbmc.log("ArloView: Settings not established, ending...", xbmc.LOGERROR)
            msg = "Set ARLO credentials, ArloView Exiting!"
            icon = REAL_SETTINGS.getAddonInfo('icon')
            xbmcgui.Dialog().notification(ADDON_NAME, msg, icon, 5000)
        else:
            try:
                _cam_name = urllib.parse.unquote(params["cameraName"])
            except:
                _cam_name = None

            try:
                _cam_id = params["cameraId"]
            except:
                _cam_id = None

            self._arlo_login()
            if _cam_id is None:
                self.main_menu()
            else:
                self._play_camera(_cam_id)

            self._arlo_logout()
