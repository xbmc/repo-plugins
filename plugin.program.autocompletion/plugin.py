# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import simplejson
import AutoCompletion

ADDON = xbmcaddon.Addon()
ADDON_VERSION = ADDON.getAddonInfo('version')


def get_kodi_json(method, params):
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, params))
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    return simplejson.loads(json_query)


def start_info_actions(infos, params):
    for info in infos:
        if info == 'autocomplete':
            data = AutoCompletion.get_autocomplete_items(params["id"], params.get("limit", 10)), "AutoComplete"
        elif info == 'selectautocomplete':
            resolve_url(params.get("handle"))
            try:
                window_id = xbmcgui.getCurrentWindowDialogId()
                window = xbmcgui.Window(window_id)
            except:
                return None
            window.setFocusId(300)
            get_kodi_json(method="Input.SendText",
                          params='{"text":"%s", "done":false}' % params.get("id"))
            # xbmc.executebuiltin("SendClick(103,32)")
        listitems, prefix = data
        pass_list_to_skin(name=prefix,
                          data=listitems,
                          prefix=params.get("prefix", ""),
                          handle=params.get("handle", ""),
                          limit=params.get("limit", 20))


def pass_list_to_skin(name="", data=[], prefix="", handle=None, limit=False):
    if data and limit and int(limit) < len(data):
        data = data[:int(limit)]
    if not handle:
        return None
    if data:
        items = create_listitems(data)
        itemlist = [(item.getProperty("path"), item, bool(item.getProperty("directory"))) for item in items]
        xbmcplugin.addDirectoryItems(handle=handle,
                                     items=itemlist,
                                     totalItems=len(itemlist))
    xbmcplugin.endOfDirectory(handle)


def create_listitems(data=None):
    INT_INFOLABELS = ["year", "episode", "season", "top250", "tracknumber", "playcount", "overlay"]
    FLOAT_INFOLABELS = ["rating"]
    STRING_INFOLABELS = ["genre", "director", "mpaa", "plot", "plotoutline", "title", "originaltitle",
                         "sorttitle", "duration", "studio", "tagline", "writer", "tvshowtitle", "premiered",
                         "status", "code", "aired", "credits", "lastplayed", "album", "votes", "trailer", "dateadded"]
    if not data:
        return []
    itemlist = []
    for (count, result) in enumerate(data):
        listitem = xbmcgui.ListItem('%s' % (str(count)))
        for (key, value) in result.iteritems():
            if not value:
                continue
            value = unicode(value)
            if key.lower() in ["name", "label"]:
                listitem.setLabel(value)
            elif key.lower() in ["label2"]:
                listitem.setLabel2(value)
            elif key.lower() in ["title"]:
                listitem.setLabel(value)
                listitem.setInfo('video', {key.lower(): value})
            elif key.lower() in ["thumb"]:
                listitem.setThumbnailImage(value)
                listitem.setArt({key.lower(): value})
            elif key.lower() in ["icon"]:
                listitem.setIconImage(value)
                listitem.setArt({key.lower(): value})
            elif key.lower() in ["path"]:
                listitem.setPath(path=value)
                # listitem.setProperty('%s' % (key), value)
            # elif key.lower() in ["season", "episode"]:
            #     listitem.setInfo('video', {key.lower(): int(value)})
            #     listitem.setProperty('%s' % (key), value)
            elif key.lower() in ["poster", "banner", "fanart", "clearart", "clearlogo", "landscape",
                                 "discart", "characterart", "tvshow.fanart", "tvshow.poster",
                                 "tvshow.banner", "tvshow.clearart", "tvshow.characterart"]:
                listitem.setArt({key.lower(): value})
            elif key.lower() in INT_INFOLABELS:
                try:
                    listitem.setInfo('video', {key.lower(): int(value)})
                except:
                    pass
            elif key.lower() in STRING_INFOLABELS:
                listitem.setInfo('video', {key.lower(): value})
            elif key.lower() in FLOAT_INFOLABELS:
                try:
                    listitem.setInfo('video', {key.lower(): "%1.1f" % float(value)})
                except:
                    pass
            # else:
            listitem.setProperty('%s' % (key), value)
        listitem.setProperty("index", str(count))
        itemlist.append(listitem)
    return itemlist


def resolve_url(handle):
    if handle:
        xbmcplugin.setResolvedUrl(handle=int(handle),
                                  succeeded=False,
                                  listitem=xbmcgui.ListItem())


class Main:

    def __init__(self):
        xbmc.log("version %s started" % ADDON_VERSION)
        self._parse_argv()
        if self.infos:
            start_info_actions(self.infos, self.params)

    def _parse_argv(self):
        args = sys.argv[2][1:]
        self.handle = int(sys.argv[1])
        self.control = "plugin"
        self.infos = []
        self.params = {"handle": self.handle,
                       "control": self.control}
        if args.startswith("---"):
            delimiter = "&"
            args = args[3:]
        else:
            delimiter = "&&"
        for arg in args.split(delimiter):
            param = arg.replace('"', '').replace("'", " ")
            if param.startswith('info='):
                self.infos.append(param[5:])
            else:
                try:
                    self.params[param.split("=")[0].lower()] = "=".join(param.split("=")[1:]).strip()
                except:
                    pass

if (__name__ == "__main__"):
    Main()
xbmc.log('finished')

