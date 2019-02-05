import json
import threading
import time
import urllib
import urlparse
import datetime

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import arlo

# Plugin Info
ADDON_ID = 'plugin.video.arloview'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
# LANGUAGE = REAL_SETTINGS.getLocalizedString

# # GLOBALS ##
# TIMEOUT = 15
# CONTENT_TYPE = 'files'


def get_params(args):
    return dict(urlparse.parse_qsl(args[2][1:]))


def get_url(url, **kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """

    url = '{0}?{1}'.format(url, urllib.urlencode(kwargs))
    return url


class ArloStream(object):

    def __init__(self, sys_args):
        self.log_level = int(REAL_SETTINGS.getSetting("log_level"))
        # self.log("BEGIN __init__, sys_args: " + str(sys_args), xbmc.LOGDEBUG)
        self._url = sys_args[0]
        self._handle = int(sys_args[1])
        self._args = sys_args
        self.arlo = None
        self.basestation = None
        self.cameras = None
        self.debug_mode = REAL_SETTINGS.getSetting('enable_debug') == 'true'
        # self.log("END   __init__", xbmc.LOGDEBUG)

    def log(self, msg, level=xbmc.LOGNOTICE):
        """
        Log to the kodi log file.  Only output messages with a level
        equal to or higher than the self.log_level (dflt NOTICE)
        """
        if level < self.log_level:
            return
        xbmc.log("[{}-{}] {}".format(ADDON_ID, ADDON_VERSION, msg), level)

    def check_first_run(self):

        if REAL_SETTINGS.getSetting("userid") == "":
            self.log("check_first_run()- userid NOT set!", xbmc.LOGNOTICE)
            msg = "Set ARLO credentials, otherwise...\nVideo will not stream correctly!"
            icon = REAL_SETTINGS.getAddonInfo('icon')
            xbmcgui.Dialog().notification(ADDON_NAME, msg, icon, 5000)
            REAL_SETTINGS.openSettings()
            self.debug_mode = REAL_SETTINGS.getSetting('enable_debug') == 'true'
            self.log_level = int(REAL_SETTINGS.getSetting("log_level"))

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

        # Update the gui to reflect signal and battery strength
        # TODO: Find a better way to update the gui
        # gui_update_timer = threading.Timer(120, self._refresh_gui)
        # gui_update_timer.start()

    def _refresh_gui(self):
        # self.log("Refresh container UI", xbmc.LOGDEBUG)
        xbmc.executebuiltin('Container.Refresh')

    def _get_arlo_cameras(self):
        if self.cameras is None:
            self.log("Retrieving cameras...", xbmc.LOGDEBUG)
            self.cameras = self.arlo.GetDevices("camera")
            self._update_arlo_cameras_details()
            if self.debug_mode:
                # Only print if user has enabled DEBUG mode in settings
                self.log(json.dumps(self.cameras, indent=4), xbmc.LOGNOTICE)

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
        if REAL_SETTINGS.getSetting('show_snapshots'):
            camera = self._get_camera(device_id)
            snapshot_file = "{0}/resources/media/{1}.jpg".format(ADDON_PATH, camera['deviceId'])
            snapshot_url = camera['presignedFullFrameSnapshotUrl']
            #self.log("*** file: {}".format(snapshot_file))
            #self.log("*** URL : {}".format(snapshot_url))
            try:
                self.arlo.DownloadSnapshot(snapshot_url, snapshot_file, 4096)
            except:
                self.log("Unable to download snapshot: {0}".format(snapshot_url), xbmc.LOGERROR)
                snapshot_file = "{0}/resources/ArloCamera.png".format(ADDON_PATH)
        else:
            snapshot_file = "{0}/resources/ArloCamera.png".format(ADDON_PATH)
        self.log("  snapshot_file name = {0}".format(snapshot_file), xbmc.LOGDEBUG)
        return snapshot_file

    def stop_camera(self):
        pass

    def play_camera(self, device_id):
        # Send the command to start the stream and return the stream url.
        camera = self._get_camera(device_id)
        stream_url = self.arlo.StartStream(self.basestation, camera)

        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=stream_url, label=camera['deviceName'])
        play_item.setProperty("isPlayable", "true")
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)

        #wait_secs = 5
        #is_playing = False
        #timed_out = False
        #start_time = time.time()
        #while not (is_playing or timed_out):
        #    is_playing = xbmc.Player().isPlaying()
        #    if is_playing:
        #        self.log("Player has started...", xbmc.LOGDEBUG)
        #    else:
        #        if time.time() - start_time < wait_secs:
        #            self.log("Waiting for player to start..", xbmc.LOGDEBUG)
        #            time.sleep(1)
        #        else:
        #            self.log("Timed out waiting for player to start", xbmc.LOGWARNING)
        #            timed_out = True

        #while is_playing:
        #    # self.log("Player is playing...", xbmc.LOGDEBUG)
        #    time.sleep(1)
        #    is_playing = xbmc.Player().isPlaying()
        #    if not is_playing:
        #        self.log("Player has stopped.", xbmc.LOGDEBUG)

        # TODO: Figure out how to update the UI
        # Update camera details after viewing (battery strength, signal strength,...)
        # Code below does it for current camera, but should we do it for all cameras?
        # doesn't update UI, need some kind of refresh?
        #self._update_arlo_cameras_details()
        #camera = self._get_camera(device_id)
        #camera_info = self._get_camera_info(camera)
        #play_item.setInfo('video', {'title': camera["deviceName"],
        #                            'plot': camera_info,
        #                            'mediatype': 'video'})

    def arlo_login(self):
        self.log("BEGIN arlo_login()", xbmc.LOGDEBUG)
        user_name = REAL_SETTINGS.getSetting('userid')
        password = REAL_SETTINGS.getSetting('password')
        self.arlo = arlo.Arlo(user_name, password)
        self.basestation = self.arlo.GetDevices('basestation')[0]
        if self.debug_mode:
            # Only print if user has enabled DEBUG mode in settings
            self.log(json.dumps(self.basestation, indent=4), xbmc.LOGNOTICE)
        self.log("END   arlo_login()", xbmc.LOGDEBUG)

    def arlo_logout(self):
        self.arlo.Logout()

    def run(self):
        params = get_params(self._args)
        # Set plugin category. It is displayed in some skins as the name
        # of the current section.
        xbmcplugin.setPluginCategory(self._handle, 'Arlo Cameras')
        # Set plugin content. It allows Kodi to select appropriate views
        # for this type of content.
        xbmcplugin.setContent(self._handle, 'files')

        self.check_first_run()

        if REAL_SETTINGS.getSetting("userid") != "":
            try:
                _cam_name = urllib.unquote(params["cameraName"])
            except:
                _cam_name = None

            try:
                _cam_id = params["cameraId"]
            except:
                _cam_id = None

            self.arlo_login()
            if _cam_id is None:
                self.main_menu()
                self.arlo_logout()
            else:
                self.play_camera(_cam_id)
                self.arlo_logout()
