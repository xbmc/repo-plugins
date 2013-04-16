# -*- coding: utf-8 -*-
#
#
#      Copyright (C) 2013 David Gray (N3MIS15)
#      N3MIS15@gmail.com
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt. If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import xbmcaddon
import xbmcgui
import urllib2
from xbmcswift2 import Plugin

plugin = Plugin()

__plugin__= "plugin.video.gametrailerscom"
__addon__ = xbmcaddon.Addon(__plugin__)
__version__ = __addon__.getAddonInfo("version")
icon = __addon__.getAddonInfo("icon")

import CommonFunctions
common = CommonFunctions
common.plugin = common.plugin = __plugin__ + __version__

video_base =        "http://www.gametrailers.com/feeds/mediagen/?uri="
video_info_base =   "http://www.gametrailers.com/feeds/mrss?uri="
video_list_base =   "http://www.gametrailers.com/feeds/line_listing_results/video_hub/6bc9c4b7-0147-4861-9dac-7bfe8db9a141/?sortBy=most_recent"

console_list_base = {
    "xbox360":  "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/7735689f-1a2a-4784-b6af-7ebe6edc3dc5/?sortBy=most_recent",
    "ps4":      "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/d73075e8-95dd-4697-80df-67973db75705/?sortBy=most_recent",
    "ps3":      "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/bf20b32b-16b6-4507-8402-ed038d7aa9ed/?sortBy=most_recent",
    "wii-u":    "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/38970bbb-36e6-4403-a050-57edc1de0af2/?sortBy=most_recent",
    "pc":       "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/b74234d8-657f-40fd-9730-87c7df53376c/?sortBy=most_recent",
    "vita":     "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/dbfa0494-af9e-4ef4-97ed-a10ef49ef4f1/?sortBy=most_recent",
    "3ds":      "http://www.gametrailers.com/feeds/line_listing_results/platform_video_index/ed694cc0-8950-4ea3-8593-a98a51c2d4cb/?sortBy=most_recent"
}


def get_string(string_id):
    return __addon__.getLocalizedString(string_id).encode("utf-8", "ignore")


def get_bool_setting(setting):
    try:
        return int(__addon__.getSetting(setting))
    except ValueError:
        return 0


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


@plugin.route("/")
def index():
    return [
        {"label": get_string(40000), "icon": icon, "path": plugin.url_for("get_shows")},
        {"label": get_string(40001), "icon": icon, "path": plugin.url_for("get_consoles")},
        {"label": get_string(40002), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base, page=1, multi_part=False)},
        {"label": get_string(40003), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base + "&category=Trailer", page=1, multi_part=False)},
        {"label": get_string(40004), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base + "&category=Gameplay", page=1, multi_part=False)},
        {"label": get_string(40005), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base + "&category=Interview", page=1, multi_part=False)},
        {"label": get_string(40006), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base + "&category=Features", page=1, multi_part=False)},
        {"label": get_string(40007), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base + "&category=Preview", page=1, multi_part=False)},
        {"label": get_string(40008), "icon": icon, "path": plugin.url_for("get_videos", url=video_list_base + "&category=Review", page=1, multi_part=False)},
    ]


@plugin.route("/get_consoles/")
def get_consoles():
    return [
        {"label": get_string(40010), "icon": icon, "path": plugin.url_for("get_console_categories", console="xbox360")},
        {"label": get_string(40011), "icon": icon, "path": plugin.url_for("get_console_categories", console="ps4")},
        {"label": get_string(40012), "icon": icon, "path": plugin.url_for("get_console_categories", console="ps3")},
        {"label": get_string(40013), "icon": icon, "path": plugin.url_for("get_console_categories", console="wii-u")},
        {"label": get_string(40014), "icon": icon, "path": plugin.url_for("get_console_categories", console="pc")},
        {"label": get_string(40015), "icon": icon, "path": plugin.url_for("get_console_categories", console="vita")},
        {"label": get_string(40016), "icon": icon, "path": plugin.url_for("get_console_categories", console="3ds")}
    ]


@plugin.route("/get_console_categories/<console>")
def get_console_categories(console):
    return [
        {"label": get_string(40002), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console], page=1, multi_part=False)},
        {"label": get_string(40003), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console] + "&category=Trailer", page=1, multi_part=False)},
        {"label": get_string(40004), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console] + "&category=Gameplay", page=1, multi_part=False)},
        {"label": get_string(40005), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console] + "&category=Interview", page=1, multi_part=False)},
        {"label": get_string(40006), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console] + "&category=Features", page=1, multi_part=False)},
        {"label": get_string(40007), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console] + "&category=Preview", page=1, multi_part=False)},
        {"label": get_string(40008), "icon": icon, "path": plugin.url_for("get_videos", url=console_list_base[console] + "&category=Review", page=1, multi_part=False)},
    ]


@plugin.route("/get_shows/")
def get_shows():
    show_list = list()
    data = urllib2.urlopen("http://www.gametrailers.com/shows").read().decode("utf-8", "ignore")

    flagship = common.parseDOM(html=data, name="li", attrs={"itemtype": "http://schema.org/TVSeries"})
    others = common.parseDOM(html=data, name="div", attrs={"itemtype": "http://schema.org/TVSeries"})
    shows = flagship + others

    for show in shows:
        meta = common.parseDOM(html=show, name="meta", ret="content")
        title = meta[0]
        path = meta[1]
        image = meta[3]

        show_li = {"label": title, "icon": image}

        if show in flagship:
            show_li['path'] = plugin.url_for("get_show_episodes", url=path, multi_part=True)
        else:
            show_li['path'] = plugin.url_for("get_show_episodes", url=path, multi_part=False)

        show_list.append(show_li)

    return show_list

@plugin.route("/get_show_episodes/<url>/<multi_part>/")
def get_show_episodes(url, multi_part):
    data = urllib2.urlopen(url).read().decode("utf-8", "ignore")
    show_id = find_between(data, "data-contenturi=\"mgid:arc:content:gametrailers.com:", "\"")
    list_url = "%s&show=%s" % (video_list_base, show_id)
    return get_videos(url=list_url, page=1, multi_part=multi_part)


@plugin.route("/get_videos/<url>/<page>/<multi_part>/")
def get_videos(url, page, multi_part):
    list_items = list()
    data = urllib2.urlopen(url + "&currentPage=" + str(page)).read().decode("utf-8", "ignore")
    items = common.parseDOM(html=data, name="li")
    media_items = [x for x in items if "video_information" in x]
    pagination = common.parseDOM(html=data, name="div", attrs={"class": "pagination"})

    for item in media_items:
        item_id = common.parseDOM(html=item, name="div", ret="data-contentId")[0]
        title_a = common.replaceHTMLCodes(common.stripTags(common.parseDOM(html=item, name="h3")[0]))
        title_b = common.replaceHTMLCodes(common.stripTags(common.parseDOM(html=item, name="h4")[0]))
        title = "%s - %s" % (title_a, title_b)
        image = common.parseDOM(html=item, name="meta", attrs={"itemprop": "thumbnailUrl"}, ret="content")[0]
        is_playable = multi_part == "False"

        if is_playable == False:
            path = plugin.url_for("get_multi_part", video_id=item_id, image=image)
        else:
            path = plugin.url_for("play_video", path=video_base+item_id)

        li = {"label": title, "icon": image, "path": path, "is_playable": is_playable}

        list_items.append(li)

    if pagination:
        if common.parseDOM(html=pagination[0], name="li", attrs={"class": "next"}):
            list_items.append({"label": get_string(40009), "icon": icon, "path": plugin.url_for("get_videos", url=url, page=int(page)+1, multi_part=multi_part)})

    return list_items


@plugin.route("/get_multi_part/<video_id>/<image>/")
def get_multi_part(video_id, image):
    act_list = list()
    url = video_info_base + video_id
    data = urllib2.urlopen(url).read().decode("utf-8", "ignore")

    acts = common.parseDOM(html=data, name="item")
    for act in acts:
        title = common.parseDOM(html=act, name="title")[0].replace("<![CDATA[", "").replace("]]>", "")
        path = common.parseDOM(html=act, name="media:content", ret="url")[0]

        act_list.append({"label": title, "thumbnail": image, "path": plugin.url_for("play_video", path=path), "is_playable": True})
    
    return act_list


@plugin.route("/play/<path>/")
def play_video(path):
    video_xml = urllib2.urlopen(path).read().decode("utf-8", "ignore")
    quality_setting = get_bool_setting("prefered_quality")
    quality_i = -1

    if quality_setting == 0:
        video_quality_list = list()

        for i in range(len(common.parseDOM(html=video_xml, name="rendition"))):
            height = common.parseDOM(html=video_xml, name="rendition", ret="height")[i]
            width = common.parseDOM(html=video_xml, name="rendition", ret="width")[i]
            title = "%sx%s" % (height, width)
            video_quality_list.append(title)

        dialog = xbmcgui.Dialog()
        quality_i = dialog.select(get_string(30002), video_quality_list)

    else:
        quality_i = quality_setting - 1

    if quality_i != -1:
        video = common.parseDOM(html=video_xml, name="src")[quality_i]
        video = plugin.set_resolved_url(video)


if __name__ == '__main__':
    plugin.run()
