from datetime import datetime
import base64
import os
import re
import requests
import sys
import urllib.parse
import xmltodict

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

__PLUGIN_ID__ = "plugin.audio.podcasts"

# see https://forum.kodi.tv/showthread.php?tid=112916
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May",
           "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

GPODDER_API = {
    "login": "%s/api/2/auth/%s/login.json",
    "subscriptions": "%s/subscriptions/%s.%s"
}

settings = xbmcaddon.Addon(id=__PLUGIN_ID__)
addon_dir = xbmcvfs.translatePath(settings.getAddonInfo('path'))


class HttpStatusError(Exception):

    message = ""

    def __init__(self, msg):

        self.message = msg


class Mediathek:

    _GROUPS = 10
    _ENTRIES = 10

    addon_handle = None

    def __init__(self):

        pass

    def _parse_outlines_from_opml(self, outline):

        if type(outline) is not list:
            outline = [outline]

        entries = []
        for i, o in enumerate(outline):
            name = o["@title"] if "@title" in o else o["@text"]
            if not name and "@xmlUrl" in o:
                m = re.match(
                    "^https?:\/\/([^\/]+).*\/?.*\/([^\/]+)\/?$", o["@xmlUrl"])
                if m:
                    name = "%s %s...%s" % (settings.getLocalizedString(
                        32053), m.groups()[0][:20], m.groups()[1][-40:])

            entry = {
                "path": str(i),
                "name": name,
                "node": []
            }

            if "@type" in o and o["@type"] == "rss" and "@xmlUrl" in o:
                entry["params"] = [{
                    "rss": o["@xmlUrl"]
                }]
                entries.append(entry)

            elif "outline" in o:
                entry["node"] = self._parse_outlines_from_opml(
                    o["outline"])
                entries.append(entry)

        return entries

    def _play_latest(self, url):

        try:
            title, description, image, items = self._load_rss(url)
            item = items[0]
            li = self._create_list_item(item)
            xbmcplugin.setResolvedUrl(self.addon_handle, True, li)

        except HttpStatusError as error:

            xbmcgui.Dialog().notification(settings.getLocalizedString(32090), error.message)

    def _create_list_item(self, item):

        li = xbmcgui.ListItem(label=item["name"])

        if "description" in item:
            li.setProperty("label2", item["description"])

        if "stream_url" in item:
            li.setPath(item["stream_url"])

        if "type" in item:
            infos = {
                "title": item["name"]
            }

            if item["type"] == "video":
                infos["plot"] = item["description"] if "description" in item else ""

            if "duration" in item and item["duration"] >= 0:
                infos["duration"] = item["duration"]

            li.setInfo(item["type"], infos)

        if "icon" in item and item["icon"]:
            li.setArt({"icon": item["icon"]})
        else:
            li.setArt({"icon": os.path.join(
                addon_dir, "resources", "assets", "icon.png")}
            )

        if "date" in item and item["date"]:
            if "setDateTime" in dir(li):  # available since Kodi v20
                li.setDateTime(item["date"].strftime("%Y-%m-%dT%H:%M:%SZ"))
            else:
                pass

        if "specialsort" in item:
            li.setProperty("SpecialSort", item["specialsort"])

        return li

    def _add_list_item(self, entry, path):

        def _build_param_string(params, current=""):

            if params == None:
                return current

            for obj in params:
                for name in obj:
                    enc_value = base64.urlsafe_b64encode(
                        obj[name].encode("utf-8"))
                    current += "?" if len(current) == 0 else "&"
                    current += name + "=" + str(enc_value, "utf-8")

            return current

        if path == "/":
            path = ""

        item_path = path + "/" + entry["path"]

        param_string = ""
        if "params" in entry:
            param_string = _build_param_string(entry["params"],
                                               current=param_string)

        li = self._create_list_item(entry)

        if "stream_url" in entry:
            url = entry["stream_url"]

        else:
            url = "".join(
                ["plugin://", __PLUGIN_ID__, item_path, param_string])

        is_folder = "node" in entry
        li.setProperty("IsPlayable", "false" if is_folder else "true")

        xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                    listitem=li,
                                    url=url,
                                    isFolder=is_folder)

    def _http_request(self, url, headers={}, method="GET"):

        useragent = f"{settings.getAddonInfo('id')}/{settings.getAddonInfo('version')} (Kodi/{xbmc.getInfoLabel('System.BuildVersionShort')})"
        headers["User-Agent"] = useragent

        if method == "GET":
            req = requests.get
        elif method == "POST":
            req = requests.post
        else:
            raise HttpStatusError(settings.getLocalizedString(32091) % method)

        try:
            res = req(url, headers=headers)
        except requests.exceptions.RequestException as error:
            xbmc.log("Request Exception: %s" % str(error), xbmc.LOGERROR)
            raise HttpStatusError(settings.getLocalizedString(32092))

        if res.status_code == 200:
            return res.text, res.cookies

        else:
            raise HttpStatusError(settings.getLocalizedString(
                32093) % (res.status_code, url))

    def _load_rss(self, url):

        def _parse_item(_ci, fallback_image):

            if "enclosure" not in _ci or "@url" not in _ci["enclosure"]:
                return None

            item = {
                "name": _ci["title"],
                "description": _ci["description"] if "description" in _ci else "",
                "stream_url": _ci["enclosure"]["@url"],
                "type": "video" if _ci["enclosure"]["@type"].split("/")[0] == "video" else "music",
                "icon": _ci["itunes:image"]["@href"] if "itunes:image" in _ci and "@href" in _ci["itunes:image"] else fallback_image
            }

            if "pubDate" in _ci:
                _f = re.findall(
                    "(\d{1,2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2})", _ci["pubDate"])

                if _f:
                    _m = _MONTHS.index(_f[0][1]) + 1
                    item["date"] = datetime(year=int(_f[0][2]), month=_m, day=int(_f[0][0]), hour=int(
                        _f[0][3]), minute=int(_f[0][4]), second=int(_f[0][5]))

            if "itunes:duration" in _ci:
                try:
                    duration = 0
                    for i, s in enumerate(reversed(_ci["itunes:duration"].split(":"))):
                        duration += 60**i * int(s)

                    item["duration"] = duration

                except:
                    pass

            return item

        res, cookies = self._http_request(url)

        if not res.startswith("<?xml"):
            raise HttpStatusError("%s %s" % (
                settings.getLocalizedString(32094), url))

        else:
            rss_feed = xmltodict.parse(res)

        channel = rss_feed["rss"]["channel"]

        title = channel["title"] if "title" in channel else ""
        description = channel["description"] if "description" in channel else ""

        if "image" in channel and "url" in channel["image"]:
            image = channel["image"]["url"]
        elif "itunes:image" in channel:
            image = channel["itunes:image"]["@href"]
        else:
            image = None

        items = []
        _cis = channel["item"] if type(channel["item"]) is list else [
            channel["item"]]
        for _ci in _cis:
            item = _parse_item(_ci, image)
            if item is not None:
                items += [item]

        return title, description, image, items

    def _render_rss(self, path, url):

        def _update_Image(path, image):

            if path.startswith("/pod-"):
                _p = path[5:].split("/")
                settings.setSetting("group_%i_rss_%i_icon" %
                                    (int(_p[0]), int(_p[1])), image)

        try:
            title, description, image, items = self._load_rss(url)
            if image:
                _update_Image(path, image)

        except HttpStatusError as error:
            xbmc.log("HTTP Status Error: %s, path=%s" %
                     (error.message, path), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(settings.getLocalizedString(32090), error.message)

        else:
            if len(items) > 0 and settings.getSetting("anchor") == "true":
                entry = {
                    "path": "latest",
                    "name": "%s (%s)" % (title, settings.getLocalizedString(32052)),
                    "description": description,
                    "icon": image,
                    "date": datetime.now(),
                    "specialsort": "top",
                    "type": items[0]["type"],
                    "params": [
                        {
                            "play_latest": url
                        }
                    ]
                }
                self._add_list_item(entry, path)

            for item in items:
                li = self._create_list_item(item)
                xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                            listitem=li,
                                            url=item["stream_url"],
                                            isFolder=False)

            if "setDateTime" in dir(li):  # available since Kodi v20
                xbmcplugin.addSortMethod(
                    self.addon_handle, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.endOfDirectory(self.addon_handle)

    def _browse(self, dir_structure, path, updateListing=False):

        def _get_node_by_path(path):

            if path == "/":
                return dir_structure[0]

            tokens = path.split("/")[1:]
            node = dir_structure[0]

            while len(tokens) > 0:
                path = tokens.pop(0)
                for n in node["node"]:
                    if n["path"] == path:
                        node = n
                        break

            return node

        node = _get_node_by_path(path)
        for entry in node["node"]:
            self._add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_FULLPATH)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(
            self.addon_handle, updateListing=updateListing)

    def _parse_opml(self, data):

        opml_data = xmltodict.parse(data)

        entries = self._parse_outlines_from_opml(
            opml_data["opml"]["body"]["outline"])

        return opml_data["opml"]["head"]["title"], entries

    def _open_opml_file(self, path):

        with open(path) as _opml_file:
            return _opml_file.read()

    def _build_dir_structure(self):

        groups = []

        # opml files / podcasts lists
        for g in range(self._GROUPS):

            if settings.getSetting("opml_file_%i" % g) == "":
                continue

            path = os.path.join(
                addon_dir, settings.getSetting("opml_file_%i" % g))

            try:
                name, nodes = self._parse_opml(self._open_opml_file(path))
                groups.append({
                    "path": "opml-%i" % g,
                    "name": name,
                    "node": nodes
                })

            except:
                xbmc.log("Cannot read opml file %s" % path, xbmc.LOGERROR)

        #  rss feeds from settings
        for g in range(self._GROUPS):

            if settings.getSetting("group_%i_enable" % g) == "false":
                continue

            entries = []
            for e in range(self._ENTRIES):

                if settings.getSetting("group_%i_rss_%i_enable" % (g, e)) == "false":
                    continue

                icon = settings.getSetting("group_%i_rss_%i_icon"
                                           % (g, e))

                entries += [{
                    "path": "%i" % e,
                    "name": settings.getSetting("group_%i_rss_%i_name"
                                                % (g, e)),
                    "params": [
                        {
                            "rss": settings.getSetting("group_%i_rss_%i_url" % (g, e))
                        }
                    ],
                    "icon": icon,
                    "node": []
                }]

            groups += [{
                "path": "pod-%i" % g,
                "name": settings.getSetting("group_%i_name" % g),
                "node": entries
            }]

        return [
            {  # root
                "path": "",
                "node": groups
            }
        ]

    def handle(self, argv):

        def decode_param(encoded_param):

            return base64.urlsafe_b64decode(encoded_param).decode("utf-8")

        self.addon_handle = int(argv[1])

        path = urllib.parse.urlparse(argv[0]).path.replace("//", "/")
        url_params = urllib.parse.parse_qs(argv[2][1:])

        if "rss" in url_params:
            url = decode_param(url_params["rss"][0])
            self._render_rss(path, url)

        elif "play_latest" in url_params:
            url = decode_param(url_params["play_latest"][0])
            self._play_latest(url)

        else:
            _dir_structure = self._build_dir_structure()
            self._browse(dir_structure=_dir_structure, path=path)

    def _login_at_gpodder(self):

        auth_string = "%s:%s" % (settings.getSetting(
            "gpodder_username"), settings.getSetting("gpodder_password"))

        b64auth = {
            "Authorization": "Basic %s" % base64.urlsafe_b64encode(auth_string.encode("utf-8")).decode("utf-8")
        }
        response, cookies = self._http_request(
            GPODDER_API["login"] % (settings.getSetting("gpodder_hostname"),
                                    settings.getSetting("gpodder_username")), b64auth, "POST")

        if "sessionid" not in cookies:
            raise HttpStatusError(settings.getLocalizedString(32095))

        return cookies["sessionid"]

    def _load_gpodder_subscriptions(self, sessionid):

        session_cookie = {
            "Cookie": "%s=%s" % ("sessionid", sessionid)
        }
        response, cookies = self._http_request(
            GPODDER_API["subscriptions"] % (settings.getSetting("gpodder_hostname"),
                                            settings.getSetting(
                                                "gpodder_username"),
                                            "opml"), session_cookie)

        return response

    def _select_opml_file(self):

        path = xbmcgui.Dialog().browse(
            type=1, heading=settings.getLocalizedString(32070), shares="", mask=".xml|.opml")
        if path == "":
            return None, None

        try:
            return self._parse_opml(self._open_opml_file(path))

        except:
            xbmc.log("Cannot read opml file %s" % path, xbmc.LOGERROR)
            return None, None

    def _select_feeds(self, name, entries, freeslots):

        selection = [e["name"]
                     for e in entries if "params" in e and len(e["params"]) == 1 and "rss" in e["params"][0]]

        if len(selection) == 0:
            xbmcgui.Dialog().ok(
                settings.getLocalizedString(32071), settings.getLocalizedString(32088))
            return None

        ok = False
        while not ok:
            feeds = xbmcgui.Dialog().multiselect(
                settings.getLocalizedString(32071), selection)
            if feeds == None:
                ok = True
            elif len(feeds) == 0:
                xbmcgui.Dialog().ok(settings.getLocalizedString(32072),
                                    settings.getLocalizedString(32073))
            elif len(feeds) > freeslots:
                xbmcgui.Dialog().ok(settings.getLocalizedString(32074),
                                    settings.getLocalizedString(32075) % freeslots)
            else:
                ok = True

        return feeds

    def _select_target_group(self):

        names = list()
        freeslots = list()
        for g in range(self._GROUPS):
            free = sum("false" == settings.getSetting(
                "group_%i_rss_%i_enable" % (g, r)) for r in range(self._ENTRIES))

            freeslots.append(free)

            names.append("%s %i: %s (%i %s)" %
                         (
                             settings.getLocalizedString(32000),
                             g + 1,
                             settings.getSetting("group_%i_name" % g),
                             free,
                             settings.getLocalizedString(32077)
                         ))

        selected = xbmcgui.Dialog().select(settings.getLocalizedString(32076), names)
        if selected > -1 and freeslots[selected] == 0:
            xbmcgui.Dialog().ok(heading=settings.getLocalizedString(32078),
                                message=settings.getLocalizedString(32084))
            return -1, 0

        elif selected == -1:
            return -1, 0

        else:
            return selected, freeslots[selected]

    def _apply_to_group(self, entries, group, feeds):

        settings.setSetting("group_%i_enable" % group, "True")

        i, j = 0, 0
        while(i < self._ENTRIES):

            if j < len(feeds) and "false" == settings.getSetting("group_%i_rss_%i_enable" % (group, i)):
                settings.setSetting("group_%i_rss_%i_enable" %
                                    (group, i), "True")
                settings.setSetting("group_%i_rss_%i_name" %
                                    (group, i), entries[feeds[j]]["name"])
                settings.setSetting("group_%i_rss_%i_url" % (
                    group, i), entries[feeds[j]]["params"][0]["rss"])
                settings.setSetting("group_%i_rss_%i_icon" % (group, i), "")
                j += 1

            i += 1

    def _save_opml_file(self, data):

        opml = xmltodict.parse(data)
        filename = "%s.opml" % re.sub(
            "[^A-Za-z0-9']", " ", opml["opml"]["head"]["title"])

        path = xbmcgui.Dialog().browse(
            type=3, heading=settings.getLocalizedString(32080), shares="")

        if not path:
            return None, None

        try:
            fullpath = "%s%s" % (path, filename)
            with open(fullpath, "w") as _file:
                _file.write(data)

            return fullpath, filename

        except:
            xbmcgui.Dialog().ok(heading=settings.getLocalizedString(
                32081), message=settings.getLocalizedString(32082))

            return None, None

    def _select_target_opml_slot(self, heading, multi=False):

        selection = list()
        for g in range(self._GROUPS):
            filename = settings.getSetting("opml_file_%i" % g)
            selection.append("%s %i%s" % (settings.getLocalizedString(
                32023), g + 1, ": %s" % filename if filename else ""))

        dialog = xbmcgui.Dialog().multiselect if multi else xbmcgui.Dialog().select
        return dialog(heading, selection)

    def import_opml(self):

        # Step 1: Select target group
        group, freeslots = self._select_target_group()
        if group == -1:
            return

        # Step 2: Select file
        name, entries = self._select_opml_file()
        if name == None:
            return

        # Step 3: Select feeds
        feeds = self._select_feeds(name, entries, freeslots)
        if feeds == None:
            return

        # Step 4: Confirm
        self._apply_to_group(entries, group, feeds)

        # Success
        xbmcgui.Dialog().notification(settings.getLocalizedString(
            32085), settings.getLocalizedString(32086))

    def import_gpodder_subscriptions(self, only_new_ones=False):

        def _filter_new_ones(entries):
            _known_urls = list()
            for g in range(self._GROUPS):
                for e in range(self._ENTRIES):
                    if settings.getSetting("group_%i_rss_%i_enable" % (g, e)) == "true":
                        _known_urls.append(settings.getSetting(
                            "group_%i_rss_%i_url" % (g, e)))

            return [e for e in entries if "params" in e and len(e["params"]) == 1 and "rss" in e["params"][0] and e["params"][0]["rss"] not in _known_urls]

        # Step 1: Select target group
        group, freeslots = self._select_target_group()
        if group == -1:
            return

        # Step 2: query subscriptions from gPodder
        try:
            sessionid = self._login_at_gpodder()
            name, entries = self._parse_opml(
                self._load_gpodder_subscriptions(sessionid))

        except HttpStatusError as error:
            xbmcgui.Dialog().ok(settings.getLocalizedString(32090), error.message)
            return

        # Step 2.1: filter newbies
        if only_new_ones:
            entries = _filter_new_ones(entries)

        # Step 3: Select feeds
        feeds = self._select_feeds(name, entries, freeslots)
        if feeds == None:
            return

        # Step 4: Apply to group
        self._apply_to_group(entries, group, feeds)

        # Success
        xbmcgui.Dialog().notification(settings.getLocalizedString(
            32085), settings.getLocalizedString(32086))

    def download_gpodder_subscriptions(self):

        # Step 1: download subscriptions from gPodder
        try:
            sessionid = self._login_at_gpodder()
            opml_data = self._load_gpodder_subscriptions(sessionid)

        except HttpStatusError as error:
            xbmcgui.Dialog().ok(settings.getLocalizedString(32090), error.message)
            return

        # Step 2: Save file in folder
        path, filename = self._save_opml_file(opml_data)
        if not path:
            return

        # Success
        xbmcgui.Dialog().notification(settings.getLocalizedString(
            32085), "%s %s" % (settings.getLocalizedString(32083), filename))

        # Step 3: Select target opml slot
        slot = self._select_target_opml_slot(
            settings.getLocalizedString(32079))
        if slot == -1:
            return

        settings.setSetting("opml_file_%i" % slot, path)

        # Success
        xbmcgui.Dialog().notification(settings.getLocalizedString(
            32085), settings.getLocalizedString(32086))

    def unassign_opml(self):

        # Step 1: Select slots
        slots = self._select_target_opml_slot(
            settings.getLocalizedString(32087), multi=True)
        if slots == None or len(slots) == 0:
            return

        # Step 2: empty slots
        for slot in slots:
            settings.setSetting("opml_file_%i" % slot, " ")

        # Success
        xbmcgui.Dialog().notification(settings.getLocalizedString(
            32085), settings.getLocalizedString(32086))


if __name__ == '__main__':

    mediathek = Mediathek()

    if sys.argv[1] == "import_gpodder_subscriptions":
        mediathek.import_gpodder_subscriptions("True" == sys.argv[2])

    elif sys.argv[1] == "import_opml":
        mediathek.import_opml()

    elif sys.argv[1] == "download_gpodder_subscriptions":
        mediathek.download_gpodder_subscriptions()

    elif sys.argv[1] == "unassign_opml":
        mediathek.unassign_opml()

    else:
        mediathek.handle(sys.argv)
