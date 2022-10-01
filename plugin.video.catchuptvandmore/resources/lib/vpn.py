# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

import os
from builtins import str

from codequick import Script, storage
from kodi_six import xbmc, xbmcgui
from resources.lib import openvpn as vpnlib

IP = "127.0.0.1"
PORT = 1337

VPN_DISCONNECTED = 0
VPN_CONNECTED = 1


def disconnect_openvpn():
    Script.log('OpenVPN: Disconnecting OpenVPN')
    try:
        vpnlib.disconnect(IP, PORT)
        Script.log('OpenVPN: Disconnect OpenVPN successful')
        Script.notify(
            "OpenVPN",
            Script.localize(30355),
            display_time=3000)
    except Exception as e:
        xbmcgui.Dialog().ok(
            'OpenVPN',
            Script.localize(30362))
        Script.log('OpenVPN: OpenVPN error: ' + str(e))


def connect_openvpn(config, sudopassword=None):
    Script.log('OpenVPN: Connecting OpenVPN configuration: [%s]' % config)

    if Script.setting.get_boolean('vpn.sudo') and \
            Script.setting.get_boolean('vpn.sudopsw') and sudopassword is None:

        keyboard = xbmc.Keyboard()
        keyboard.setHeading(Script.localize(30353))
        keyboard.setHiddenInput(True)
        keyboard.doModal()
        if keyboard.isConfirmed():
            sudopassword = keyboard.getText()
        else:
            return

    openvpn = vpnlib.OpenVPN(
        Script.setting.get_string('vpn.openvpnfilepath'),
        config,
        ip=IP,
        port=PORT,
        args=Script.setting.get_string('vpn.args'),
        sudo=Script.setting.get_boolean('vpn.sudo'),
        sudopwd=sudopassword)

    try:
        openvpn.connect()
        Script.notify(
            "OpenVPN",
            Script.localize(30354),
            display_time=3000)
    except Exception as e:
        xbmcgui.Dialog().ok(
            'OpenVPN',
            Script.localize(30358))
        Script.log('OpenVPN: OpenVPN error: ' + str(e))


@Script.register
def import_ovpn(*args, **kwargs):
    path = xbmcgui.Dialog().browse(
        1,
        Script.localize(30342),
        'files',
        mask='.ovpn|.conf',
        enableMultiple=False)

    if path and os.path.exists(path) and os.path.isfile(path):
        Script.log('OpenVPN: Import: [%s]' % path)

        keyboard = xbmc.Keyboard(
            default='',
            heading=Script.localize(30348),
            hidden=False)
        keyboard.doModal()
        if keyboard.isConfirmed() and len(keyboard.getText()) > 0:
            name = keyboard.getText()

            ovpnfiles = {}
            with storage.PersistentDict('vpn') as db:
                ovpnfiles = db['ovpnfiles']
                db.flush()

            if name in ovpnfiles and not xbmcgui.Dialog().yesno(
                    'OpenVPN',
                    Script.localize(30349)):
                xbmcgui.Dialog().ok(
                    'OpenVPN', Script.localize(30350))

            else:
                ovpnfiles[name] = path
                with storage.PersistentDict('vpn') as db:
                    db['ovpnfiles'] = ovpnfiles
                    db.flush()
        else:
            xbmcgui.Dialog().ok(
                'OpenVPN',
                Script.localize(30351))


def select_ovpn():
    ovpnfiles = {}
    with storage.PersistentDict('vpn') as db:
        try:
            ovpnfiles = db['ovpnfiles']
        except KeyError:
            db['ovpnfiles'] = ovpnfiles
        db.flush()

    if len(ovpnfiles) == 0:
        return None

    configs = []
    ovpnfileslist = []
    for name, configfilepath in list(ovpnfiles.items()):
        configs.append(name)
        ovpnfileslist.append(configfilepath)

    idx = xbmcgui.Dialog().select(
        Script.localize(30352),
        configs)
    if idx < 0:
        return ''

    Script.log('OpenVPN: Select conf: [%s]' % ovpnfileslist[idx])
    return ovpnfileslist[idx]


@Script.register
def delete_ovpn(*args, **kwargs):
    ovpnfiles = {}
    with storage.PersistentDict('vpn') as db:
        try:
            ovpnfiles = db['ovpnfiles']
        except KeyError:
            db['ovpnfiles'] = ovpnfiles
        db.flush()

    if len(ovpnfiles) == 0:
        return None

    configs = []
    ovpnfileslist = []
    for name, configfilepath in list(ovpnfiles.items()):
        configs.append(name)
        ovpnfileslist.append(configfilepath)

    idx = xbmcgui.Dialog().select(
        Script.localize(30360),
        configs)

    if idx < 0:
        return ''

    Script.log('Select: [%s]' % ovpnfileslist[idx])
    new_ovpnfiles = {}
    for name, configfilepath in list(ovpnfiles.items()):
        if configfilepath != ovpnfileslist[idx]:
            new_ovpnfiles[name] = configfilepath
    with storage.PersistentDict('vpn') as db:
        db['ovpnfiles'] = new_ovpnfiles
        db.flush()


@Script.register
def vpn_item_callback(plugin):
    if vpnlib.is_running(IP, PORT):
        disconnect_openvpn()
    else:
        ovpn = select_ovpn()
        if ovpn is None:
            import_ovpn()

        # Case when the user cancel the import dialog
        if ovpn is None:
            return False

        if len(ovpn) > 0:
            connect_openvpn(ovpn)

    xbmc.executebuiltin('Container.Refresh()')


def add_vpn_context(item):
    item.context.script(vpn_item_callback, Script.localize(30361))
