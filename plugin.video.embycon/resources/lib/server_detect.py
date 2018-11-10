# Gnu General Public License - see LICENSE.TXT

import socket
import json
from urlparse import urlparse
import time
import hashlib

import xbmcaddon
import xbmcgui
import xbmc

from kodi_utils import HomeWindow
from downloadutils import DownloadUtils
from simple_logging import SimpleLogging
from translation import string_load

log = SimpleLogging(__name__)

__addon__ = xbmcaddon.Addon()
__addon_name__ = __addon__.getAddonInfo('name')
downloadUtils = DownloadUtils()


def getServerDetails():
    log.debug("Getting Server Details from Network")
    servers = []

    MESSAGE = "who is EmbyServer?"
    MULTI_GROUP = ("<broadcast>", 7359)
    #MULTI_GROUP = ("127.0.0.1", 7359)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(4.0)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)  # timeout
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.SO_REUSEADDR, 1)

    log.debug("MutliGroup: {0}", MULTI_GROUP)
    log.debug("Sending UDP Data: {0}", MESSAGE)

    # while True:
    try:
        sock.sendto(MESSAGE, MULTI_GROUP)
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                servers.append(json.loads(data))
            except:
                break
    except Exception as e:
        log.error("UPD Discovery Error: {0}", e)
        # break

    log.debug("Found Servers: {0}", servers)
    return servers


def checkServer(force=False, change_user=False, notify=False):
    log.debug("checkServer Called")

    settings = xbmcaddon.Addon()
    serverUrl = ""
    something_changed = False

    if force is False:
        # if not forcing use server details from settings
        svr = downloadUtils.getServer()
        if svr is not None:
            serverUrl = svr

    # if the server is not set then try to detect it
    if serverUrl == "":
        serverInfo = getServerDetails()

        serverNames = []
        for server in serverInfo:
            serverNames.append(server.get("Name", string_load(30063)))
        if serverNames:
            return_index = xbmcgui.Dialog().select(string_load(30166), serverNames)
        else:
            xbmcgui.Dialog().ok(__addon_name__, string_load(30282))
            return_index = -1

        if (return_index == -1):
            xbmc.executebuiltin("ActivateWindow(Home)")
            return

        serverUrl = serverInfo[return_index]["Address"]
        log.debug("Selected server: {0}", serverUrl)

        # parse the url
        url_bits = urlparse(serverUrl)
        server_address = url_bits.hostname
        server_port = str(url_bits.port)
        server_protocol = url_bits.scheme
        log.debug("Detected server info {0} - {1} - {2}", server_protocol, server_address, server_port)

        # save the server info
        settings.setSetting("port", server_port)
        settings.setSetting("ipaddress", server_address)

        if server_protocol == "https":
            settings.setSetting("use_https", "true")
        else:
            settings.setSetting("use_https", "false")

        something_changed = True
        if notify:
            xbmcgui.Dialog().ok(string_load(30167), string_load(30168),
                                string_load(30169) + server_address, string_load(30001) + server_port)

    # we need to change the user
    current_username = settings.getSetting("username")
    current_username = unicode(current_username, "utf-8")

    # if asked or we have no current user then show user selection screen
    if change_user or len(current_username) == 0:

        # stop playback when switching users
        xbmc.Player().stop()

        # get a list of users
        log.debug("Getting user list")
        jsonData = downloadUtils.downloadUrl(serverUrl + "/emby/Users/Public?format=json", authenticate=False)

        # TODO: add a setting to enable this
        show_manual = False

        log.debug("jsonData: {0}", jsonData)
        try:
            result = json.loads(jsonData)
        except:
            result = None

        if result is None:
            xbmcgui.Dialog().ok(string_load(30135),
                                string_load(30201),
                                string_load(30169) + serverUrl)
        else:
            selected_id = -1
            names = []
            user_list = []
            secured = []
            for user in result:
                config = user.get("Configuration")
                if config is not None:
                    if config.get("IsHidden", False) is False:
                        name = user.get("Name")
                        user_list.append(name)
                        if current_username == name:
                            selected_id = len(user_list) - 1

                        if (user.get("HasPassword") is True):
                            secured.append(True)
                            name = string_load(30060) % name
                        else:
                            secured.append(False)

                        names.append(name)

            if (len(current_username) > 0) and (not any(n == current_username for n in user_list)):
                names.insert(0, string_load(30061) % current_username)
                user_list.insert(0, current_username)
                secured.insert(0, True)

            if show_manual:
                names.append(string_load(30062))
                user_list.append('')
                secured.append(True)

            log.debug("User List: {0}", names)
            log.debug("User List: {0}", user_list)

            if current_username:
                selection_title = string_load(30180) + " (" + current_username + ")"
            else:
                selection_title = string_load(30180)

            return_value = xbmcgui.Dialog().select(selection_title, names, preselect=selected_id, autoclose=20000)

            if return_value > -1 and return_value != selected_id:

                log.debug("Selected User Index: {0}", return_value)
                if show_manual and return_value == (len(user_list) -1):
                    kb = xbmc.Keyboard()
                    kb.setHeading(string_load(30005))
                    kb.doModal()
                    if kb.isConfirmed():
                        selected_user = kb.getText()
                    else:
                        selected_user = None
                else:
                    selected_user = user_list[return_value]

                log.debug("Selected User Name: {0}", selected_user)

                if selected_user:
                    something_changed = True
                    # we have a user so save it
                    if secured[return_value] is True:
                        # we need a password, check the settings first
                        m = hashlib.md5()
                        m.update(selected_user)
                        hashed_username = m.hexdigest()
                        saved_password = settings.getSetting("saved_user_password_" + hashed_username)

                        if saved_password:
                            log.debug("Saving username and password: {0}", selected_user)
                            log.debug("Using stored password for user: {0}", hashed_username)
                            settings.setSetting("username", selected_user)
                            settings.setSetting('password', saved_password)
                        else:
                            kb = xbmc.Keyboard()
                            kb.setHeading(string_load(30006))
                            kb.setHiddenInput(True)
                            kb.doModal()
                            if kb.isConfirmed():
                                log.debug("Saving username and password: {0}", selected_user)
                                settings.setSetting("username", selected_user)
                                settings.setSetting('password', kb.getText())

                                # should we save the password
                                save_password = xbmcgui.Dialog().yesno( "Save Password?",
                                                                        "Do you want to save the password?")
                                if save_password:
                                    log.debug("Saving password for fast user switching: {0}", hashed_username)
                                    settings.setSetting("saved_user_password_" + hashed_username, kb.getText())
                    else:
                        log.debug("Saving username is no password: {0}", selected_user)
                        settings.setSetting("username", selected_user)
                        settings.setSetting('password', '')

        if something_changed:
            home_window = HomeWindow()
            home_window.clearProperty("userid")
            home_window.clearProperty("AccessToken")
            home_window.clearProperty("userimage")
            home_window.setProperty("embycon_widget_reload", str(time.time()))
            download_utils = DownloadUtils()
            download_utils.authenticate()
            download_utils.getUserId()
            xbmc.executebuiltin("ActivateWindow(Home)")
            xbmc.executebuiltin("ReloadSkin()")

