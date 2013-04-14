# -*- coding: utf-8 -*-
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

import os
import xbmc
import xbmcaddon
import xbmcgui
import urllib2
import CommonFunctions
from xbmcswift2 import Plugin, ListItem

__plugin__= "plugin.video.screwattack"
__addon__ = xbmcaddon.Addon(__plugin__)
__version__ = __addon__.getAddonInfo("version")
icon = __addon__.getAddonInfo("icon")

plugin = Plugin()
common = CommonFunctions
common.plugin = __plugin__ + __version__
common.dbg = True
common.dbglevel = 3

base_url = "http://www.screwattack.com"
base_springboard = "http://cms.springboardplatform.com/xml_feeds_advanced/index/711/rss3/"
base_youtube = "plugin://plugin.video.youtube/?action=play_video&videoid="
base_bliptv = "plugin://plugin.video.bliptv/?path=/root/video&action=play_video&videoid="

def get_string(string_id):
    return __addon__.getLocalizedString(string_id).encode("utf-8", "ignore")


def get_bool_setting(setting):
    try:
        return int(__addon__.getSetting(setting))
    except ValueError:
        return 0


def notification(header, message, time=5000, icon=icon):
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i,%s)" % (header, message, time, icon))


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


@plugin.route("/")
def index():
    show_list = list()
    data = urllib2.urlopen(base_url).read()

    shows = common.parseDOM(html=data, name="li", attrs={"class": "menu-11731 menuparent menu-path-screwattackcom-shows-originals odd "})[0]
    for show in common.parseDOM(html=shows, name="li"):
        title = common.replaceHTMLCodes(common.stripTags(show))
        path = common.parseDOM(html=show, name="a", ret="href")[0]

        if title.lower() not in ["love/hate", "advantage content", "out of the box"]:
            show_list.append({
                "label": title,
                "icon": icon,
                "path": plugin.url_for("show_episodes", path=path, page=0)
            })


    live_shows = common.parseDOM(html=data, name="li", attrs={"class": "menu-22426 menuparent menu-path-screwattackcom-shows-originals even "})[0]
    for show in common.parseDOM(html=live_shows, name="li"):
        title = common.replaceHTMLCodes(common.stripTags(show))
        path = common.parseDOM(html=show, name="a", ret="href")[0]

        show_list.append({
            "label": title,
            "icon": icon,
            "path": plugin.url_for("show_episodes", path=path, page=0)
        })

    return show_list


@plugin.route("/show_episodes/<path>/<page>/")
def show_episodes(path, page):
    episode_list = list()

    if not path.startswith("http://"):
        path = base_url + path
    url = "%s?page=%s" % (path, page)

    data = urllib2.urlopen(url).read()
    body = common.parseDOM(html=data, name="div", attrs={"class": "body-container-middle"})

    content = common.parseDOM(html=body, name="div", attrs={"class": "view-content"})
    content = content[0] if not "profile-banner" in content[0] else content[1]
    episodes = common.parseDOM(html=content, name="span", attrs={"class": "field-content"})

    for episode in episodes:
        image = common.parseDOM(html=episode, name="img", ret="src")[0]
        ep_path = common.parseDOM(html=episode, name="a", ret="href")[0]
        title = common.replaceHTMLCodes(common.stripTags(common.parseDOM(html=episode, name="h2")[0]))
        plot = common.replaceHTMLCodes(common.stripTags(common.parseDOM(html=episode, name="div", attrs={"class": "info"})[0]))
        episode_list.append({"label": title, "thumbnail": image, "path": plugin.url_for("play_episode", path=ep_path), "is_playable": True})

    next = common.parseDOM(html=body, name="li", attrs={"class": "pager-next last"})
    if next:
        next = next[0]

    if "active" in next:
        episode_list.append({"label": get_string(92000), "icon": icon, "path": plugin.url_for("show_episodes", path=path, page=int(page)+1)})

    return episode_list


@plugin.route("/play/<path>/")
def play_episode(path):
    url = base_url + path
    quality = ["720", "360"][get_bool_setting("prefered_quality")]
    data = urllib2.urlopen(url).read()
    sa_player = common.parseDOM(html=data, name="div", attrs={"class": "player-regular"})
    if sa_player:
        sa_player = sa_player[0]

        if "scre004" in sa_player: # Springboard New
            print "[ScrewAttack] Trying springboard player"
            # Variation 1
            sa_id = find_between(sa_player, "/video/", "/scr")

            # Variation 2
            if not sa_id.isdigit():
                print "[ScrewAttack] Variation 1 Check Failed"
                sa_id = find_between(sa_player, "/711/", "/\"")

            # Variation 3
            if not sa_id.isdigit():
                print "[ScrewAttack] Variation 2 Check Failed"
                sa_id = find_between(sa_player, "scre004_", "\"")

            # Variation 4
            if not sa_id.isdigit():
                print "[ScrewAttack] Variation 3 Check Failed"
                # Springboard can also play youtube videos
                youtube_id = find_between(sa_player, "youtube/scre004/", "/")
                if youtube_id:
                    video = plugin.set_resolved_url(base_youtube + youtube_id)
                    return video

            if not sa_id.isdigit():
                # If we dont have an id by now give up and log the player tag so we can add a new variation.
                print "[ScrewAttack] Variation 4 Check Failed"
                print "[ScrewAttack] Could not find id in springboard player."
                print sa_player
                notification(get_string(90000), get_string(90001))
                return

            xml_url = base_springboard + sa_id
            xml = urllib2.urlopen(xml_url).read()

            video_heights = common.parseDOM(html=xml, name="media:content", ret="height")
            video_urls = common.parseDOM(html=xml, name="media:content", ret="url")
            video_url = None

            if video_urls: # Try to use prefered quality
                for i in range(len(video_heights)):
                    if quality == video_heights[i]:
                        video_url = video_urls[i]

                if not video_url:
                    video_url = video_urls[0]

                video = plugin.set_resolved_url(video_url)
            else:
                notification(get_string(90000), get_string(90001))

        elif "gorillanation" in sa_player: # Springboard Old
            xml_url = common.parseDOM(html=sa_player, name="object", ret="file")[0]
            xml = urllib2.urlopen(xml_url).read()
            video = plugin.set_resolved_url(common.parseDOM(html=xml, name="media:content", ret="url")[0])

        elif "youtube" in sa_player: # Youtube
            youtube_id = find_between(sa_player, "embed/", "?")
            video = plugin.set_resolved_url(base_youtube + youtube_id)

        elif "blip.tv" in sa_player: # Blip.tv
            blip_url = common.parseDOM(html=data, name="iframe", ret="src")[0]
            blip_data = urllib2.urlopen(blip_url).read()
            blip_id = common.parseDOM(html=blip_data, name="div", attrs={"id": "EpisodeInfo"}, ret="data-episode-id")[0]
            video = plugin.set_resolved_url(base_bliptv + blip_id)

        elif "twitch" in sa_player: # Twitch.tv
            video = plugin.set_resolved_url("plugin://plugin.video.twitch/playLive/screwattack/")

        else:
            print "[ScrewAttack] Unknown Player: " + sa_player
            notification(get_string(90000), get_string(90001))
            return

        return video

    else:
        notification(get_string(90000), get_string(90001))

if __name__ == '__main__':
    plugin.run()

