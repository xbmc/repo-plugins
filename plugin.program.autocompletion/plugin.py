# -*- coding: utf8 -*-
# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import AutoCompletion

ADDON = xbmcaddon.Addon()
ADDON_VERSION = ADDON.getAddonInfo('version')


def get_kodi_json(method, params):
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, params))
    return json.loads(json_query)


def start_info_actions(infos, params):
    for info in infos:
        if info == 'autocomplete':
            listitems = AutoCompletion.get_autocomplete_items(params["id"], params.get("limit", 10))
        elif info == 'selectautocomplete':
            if params.get("handle"):
                xbmcplugin.setResolvedUrl(handle=int(params.get("handle")),
                                          succeeded=False,
                                          listitem=xbmcgui.ListItem())
            try:
                window = xbmcgui.Window(10103)
            except Exception:
                return None
            window.setFocusId(300)
            get_kodi_json(method="Input.SendText",
                          params='{"text":"%s", "done":false}' % params.get("id"))
            return None

        pass_list_to_skin(data=listitems,
                          handle=params.get("handle", ""),
                          limit=params.get("limit", 20))


def pass_list_to_skin(data=[], handle=None, limit=False):
    if data and limit and int(limit) < len(data):
        data = data[:int(limit)]
    if not handle:
        return None
    if data:
        items = create_listitems(data)
        xbmcplugin.addDirectoryItems(handle=handle,
                                     items=[(i.getProperty("path"), i, False) for i in items],
                                     totalItems=len(items))
    xbmcplugin.endOfDirectory(handle)


def create_listitems(data=None):
    if not data:
        return []
    itemlist = []
    for (count, result) in enumerate(data):
        listitem = xbmcgui.ListItem(str(count))
        for (key, value) in result.items():
            if not value:
                continue
            if key.lower() in ["label"]:
                listitem.setLabel(value)
            elif key.lower() in ["search_string"]:
                path = "plugin://plugin.program.autocompletion/?info=selectautocomplete&&id=%s" % value
                listitem.setPath(path=path)
                listitem.setProperty('path', path)
        listitem.setProperty("index", str(count))
        listitem.setProperty("isPlayable", "false")
        itemlist.append(listitem)
    return itemlist


if (__name__ == "__main__"):
    xbmc.log("version %s started" % ADDON_VERSION)
    args = sys.argv[2][1:]
    handle = int(sys.argv[1])
    infos = []
    params = {"handle": handle}
    delimiter = "&&"
    for arg in args.split(delimiter):
        param = arg.replace('"', '').replace("'", " ")
        if param.startswith('info='):
            infos.append(param[5:])
        else:
            try:
                params[param.split("=")[0].lower()] = "=".join(param.split("=")[1:]).strip()
            except Exception:
                pass
    if infos:
        start_info_actions(infos, params)