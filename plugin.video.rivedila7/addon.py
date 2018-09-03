# -*- coding: utf-8 -*-
from resources.lib import plugin

import json
from contextlib import contextmanager

@contextmanager
def enabled_addon(addon):
    data = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","params":{"addonid":"'+addon+'","properties":["enabled","installed"]},"id":5}'))
    if "result" in data:
        xbmc.log("Addon is installed. Enabling if disabled.")
        if not data["result"]["addon"]["enabled"]:
            result_enabled = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"'+addon+'","enabled":true},"id":9}')
    else:
        xbmc.log("Addon not installed. Prompt an error to the user.")
    yield


def run():
    with enabled_addon("inputstream.adaptive"):
        xbmc.log('Add-on InputStream Adaptive enabled',xbmc.LOGNOTICE)
        plugin.show_root_menu()


run()


