# Gnu General Public License - see LICENSE.TXT

import socket
import json
from urlparse import urlparse

import xbmcaddon
import xbmcgui
import xbmc

from kodi_utils import HomeWindow
from downloadutils import DownloadUtils
from simple_logging import SimpleLogging
from translation import i18n

log = SimpleLogging(__name__)

__addon__ = xbmcaddon.Addon(id='plugin.video.embycon')
__addon_name__ = __addon__.getAddonInfo('name')
downloadUtils = DownloadUtils()


def getServerDetails():
    log.debug("Getting Server Details from Network")

    MESSAGE = "who is EmbyServer?"
    MULTI_GROUP = ("<broadcast>", 7359)
    #MULTI_GROUP = ("127.0.0.1", 7359)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(4.0)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)  # timeout
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.SO_REUSEADDR, 1)

    log.debug("MutliGroup       : " + str(MULTI_GROUP))
    log.debug("Sending UDP Data : " + MESSAGE)
    sock.sendto(MESSAGE, MULTI_GROUP)

    servers = []

    # while True:
    try:
        data, addr = sock.recvfrom(1024)  # buffer size
        servers.append(json.loads(data))
    except Exception as e:
        log.error("Read UPD responce: %s" % e)
        # break

    log.debug("Found Servers: %s" % servers)
    return servers


def checkServer(force=False, change_user=False, notify=False):
    log.debug("checkServer Called")

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    serverUrl = ""

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
            serverNames.append(server.get("Name", i18n('n/a')))
        if serverNames:
            return_index = xbmcgui.Dialog().select(i18n('select_server'), serverNames)
        else:
            xbmcgui.Dialog().ok(__addon_name__, i18n('no_server_detected'))
            return_index = -1

        if (return_index == -1):
            xbmc.executebuiltin("ActivateWindow(Home)")
            return

        serverUrl = serverInfo[return_index]["Address"]
        log.debug("Selected server: " + serverUrl)

        # parse the url
        url_bits = urlparse(serverUrl)
        server_address = url_bits.hostname
        server_port = str(url_bits.port)
        server_protocol = url_bits.scheme
        log.debug("Detected server info " + server_protocol + " - " + server_address + " - " + server_port)

        # save the server info
        settings.setSetting("port", server_port)
        settings.setSetting("ipaddress", server_address)

        if server_protocol == "https":
            settings.setSetting("use_https", "true")
        else:
            settings.setSetting("use_https", "false")

        if notify:
            xbmcgui.Dialog().ok(i18n('server_detect_succeeded'), i18n('found_server'),
                                i18n('address:') + server_address, i18n('server_port:') + server_port)

    # we need to change the user
    current_username = settings.getSetting("username")

    # if asked or we have no current user then show user selection screen
    if change_user or len(current_username) == 0:
        # get a list of users
        log.debug("Getting user list")
        jsonData = downloadUtils.downloadUrl(serverUrl + "/emby/Users/Public?format=json", authenticate=False)

        log.debug("jsonData : " + str(jsonData))
        result = json.loads(jsonData)
        if result is None:
            result = []

        names = []
        user_list = []
        secured = []
        for user in result:
            config = user.get("Configuration")
            if (config != None):
                if (config.get("IsHidden") is None) or (config.get("IsHidden") is False):
                    name = user.get("Name")
                    user_list.append(name)
                    if (user.get("HasPassword") is True):
                        secured.append(True)
                        name = i18n('username_secured') % name
                    else:
                        secured.append(False)
                    names.append(name)

        if (len(current_username) > 0) and (not any(n == current_username for n in user_list)):
            names.insert(0, i18n('username_userdefined') % current_username)
            user_list.insert(0, current_username)
            secured.insert(0, True)

        names.insert(0, i18n('username_userinput'))
        user_list.insert(0, '')
        secured.insert(0, True)
        log.debug("User List : " + str(names))
        log.debug("User List : " + str(user_list))

        return_value = xbmcgui.Dialog().select(i18n('select_user'), names)

        if (return_value > -1):
            log.debug("Selected User Index : " + str(return_value))
            if return_value == 0:
                kb = xbmc.Keyboard()
                kb.setHeading(i18n('username:'))
                kb.doModal()
                if kb.isConfirmed():
                    selected_user = kb.getText()
                else:
                    selected_user = None
            else:
                selected_user = user_list[return_value]

            log.debug("Selected User Name : " + str(selected_user))

            if selected_user:
                # we have a user so save it
                log.debug("Saving Username : " + selected_user)
                settings.setSetting("username", selected_user)
                if secured[return_value] is True:
                    kb = xbmc.Keyboard()
                    kb.setHeading(i18n('password:'))
                    kb.setHiddenInput(True)
                    kb.doModal()
                    if kb.isConfirmed():
                        log.debug("Saving Password for Username : " + selected_user)
                        settings.setSetting('password', kb.getText())
                else:
                    settings.setSetting('password', '')

        home_window = HomeWindow()
        home_window.clearProperty("userid")
        home_window.clearProperty("AccessToken")

        xbmc.executebuiltin("ActivateWindow(Home)")
