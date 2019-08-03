# -*- coding: utf-8 -*-
from resources.lib import plugin

import json
from contextlib import contextmanager

@contextmanager
def enabled_addon(addon):
    data = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","params":{"addonid":"'+addon+'","properties":["enabled","installed"]},"id":5}'))
    if "result" in data:
        xbmc.log('Add-on InputStream Adaptive installed',xbmc.LOGDEBUG)
        if data["result"]["addon"]["enabled"]:
            xbmc.log('Add-on InputStream Adaptive enabled',xbmc.LOGDEBUG)
        else:
            xbmc.log('Add-on InputStream Adaptive enabling',xbmc.LOGDEBUG)
            result_enabled = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"'+addon+'","enabled":true},"id":9}')
            xbmc.log('Add-on InputStream Adaptive enabled',xbmc.LOGDEBUG)
    else:
        xbmc.log('Add-on InputStream Adaptive not installed',xbmc.LOGDEBUG)
    yield


def run():
    with enabled_addon("inputstream.adaptive"):
        plugin.show_root_menu()


run()

