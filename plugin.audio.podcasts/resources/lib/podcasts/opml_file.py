import re

import xbmcaddon
import xbmcvfs
import xmltodict


def parse_opml(data: str, limit=0) -> 'tuple[str,list[dict]]':

    def parse_outlines_from_opml(outline):

        if type(outline) is not list:
            outline = [outline]

        entries = []
        for i, o in enumerate(outline):
            name = o["@title"] if "@title" in o else o["@text"]
            if not name and "@xmlUrl" in o:
                m = re.match(
                    "^https?:\/\/([^\/]+).*\/?.*\/([^\/]+)\/?$", o["@xmlUrl"])
                if m:
                    name = "%s %s...%s" % (xbmcaddon.Addon().getLocalizedString(
                        32053), m.groups()[0][:20], m.groups()[1][-40:])

            entry = {
                "path": str(i),
                "name": name,
                "node": []
            }

            if "@type" in o and o["@type"] == "rss" and "@xmlUrl" in o:
                entry["params"] = [{
                    "rss": o["@xmlUrl"],
                    "limit": str(limit)
                }]
                entries.append(entry)

            elif "outline" in o:
                entry["node"] = parse_outlines_from_opml(
                    o["outline"])
                entries.append(entry)

        return entries

    opml_data = xmltodict.parse(data)

    if "opml" in opml_data and "head" in opml_data["opml"] and "title" in opml_data["opml"]["head"]:
        title = opml_data["opml"]["head"]["title"]

    else:
        title = ""

    if "opml" in opml_data and "body" in opml_data["opml"] and "outline" in opml_data["opml"]["body"]:
        entries = parse_outlines_from_opml(
            opml_data["opml"]["body"]["outline"])
    else:
        entries = []

    return title, entries


def open_opml_file(path: str) -> str:

    with xbmcvfs.File(path, 'r') as _opml_file:
        return _opml_file.read()
