# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import json
import sys
from urllib.parse import parse_qsl

import AutoCompletion

ADDON = xbmcaddon.Addon()
ADDON_VERSION = ADDON.getAddonInfo('version')


def get_kodi_json(method, params):
    query_params = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    json_query = xbmc.executeJSONRPC(json.dumps(query_params))

    return json.loads(json_query)


def start_info_actions(infos, params):
    listitems = []
    for info in infos:
        if info == 'autocomplete':
            listitems = AutoCompletion.get_autocomplete_items(params["id"], params.get("limit", 10))
        elif info == 'selectautocomplete':
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            xbmc.sleep(500)
            get_kodi_json(
                method="Input.SendText",
                params={"text": params.get("id"), "done": False},
            )
            xbmc.executebuiltin('ActivateWindowAndFocus(virtualkeyboard,300,0)')

        pass_list_to_skin(
            data=listitems,
            handle=params.get("handle", ""),
            limit=params.get("limit", 20),
        )


def pass_list_to_skin(data=[], handle=None, limit=False):
    if data and limit and int(limit) < len(data):
        data = data[: int(limit)]

    if handle and data:
        items = create_listitems(data)
        xbmcplugin.addDirectoryItems(
            handle=handle,
            items=[(i.getProperty("path"), i, False) for i in items],
            totalItems=len(items),
        )
        xbmc.executebuiltin('Dialog.Close(busydialog)')
    xbmcplugin.endOfDirectory(handle)


def create_listitems(data=None):
    if not data:
        return []
    itemlist = []
    for count, result in enumerate(data):
        listitem = xbmcgui.ListItem(str(count))
        for key, value in result.items():
            if not value:
                continue
            if key.lower() in ["label"]:
                listitem.setLabel(value)
            elif key.lower() in ["search_string"]:
                path = f"plugin://plugin.program.autocompletion/?info=selectautocomplete&id={value}"
                listitem.setPath(path=path)
                listitem.setProperty('path', path)
        listitem.setProperty("index", str(count))
        listitem.setProperty("isPlayable", "false")
        itemlist.append(listitem)
    return itemlist


if __name__ == "__main__":
    xbmc.log(f"version {ADDON_VERSION} started")
    args = sys.argv[2][1:]
    handle = int(sys.argv[1])
    infos = []
    params = {"handle": handle}
    params.update(dict(parse_qsl(args, keep_blank_values=True)))

    if "info" in params:
        infos.append(params['info'])

    if infos:
        start_info_actions(infos, params)

xbmc.log('finished')
