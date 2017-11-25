# -*- coding: utf-8 -*-
# Copyright: (c) 2016 William Forde (willforde+kodi@gmail.com)
#
# License: GPLv2, see LICENSE for more details
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import unicode_literals
from codequick import Route, Resolver, Listitem, utils, run
import xbmcgui
import re

# Localized string Constants
VIDEO_OF_THE_DAY = 30004
WATCHING_NOW = 30005
TOP_VIDEOS = 30002
SELECT_TOP = 30001
PARTY_MODE = 589

# Base url constructor
url_constructor = utils.urljoin_partial("http://metalvideo.com")


# noinspection PyUnusedLocal
@Route.register
def root(plugin, content_type):
    """
    :param Route plugin: The plugin parent object.
    :param str content_type: The type of content been listed e.g. video, music. This is passed in from kodi and
                             we have no use for it as of yet.
    """
    yield Listitem.recent(recent_videos)
    yield Listitem.from_dict(plugin.localize(TOP_VIDEOS), top_videos)
    yield Listitem.from_dict(plugin.localize(WATCHING_NOW), watching_now)
    yield Listitem.search(video_list)

    # Fetch HTML Source
    url = url_constructor("/mobile/category.html")
    html = plugin.request.get(url, headers={"Cookie": "COOKIE_DEVICE=mobile"})
    root_elem = html.parse(u"ul", attrs={"id": "category_listing"})
    for elem in root_elem.iterfind("li"):
        a_tag = elem.find("a")
        item = Listitem()

        # Set label with video count added
        item.label = "%s (%s)" % (a_tag.text, elem.find("span").text)
        item.set_callback(video_list, cat=a_tag.get("href"))
        yield item

    # Add the video items here so that show at the end of the listing
    yield Listitem.from_dict(plugin.localize(VIDEO_OF_THE_DAY), play_video, params={"url": "index.html"})
    yield Listitem.from_dict(plugin.localize(PARTY_MODE), party_play, params={"url": "randomizer.php"})


@Route.register
def recent_videos(plugin, url="newvideos.php"):
    """
    :param Route plugin: The plugin parent object.
    :param unicode url: The url resource containing recent videos.
    """
    # Fetch HTML Source
    url = url_constructor(url)
    html = plugin.request.get(url)
    root_elem = html.parse("div", attrs={"id": "browse_main"})
    node = root_elem.find("./div[@id='newvideos_results']")[0]
    for elem in node.iterfind("./tr"):
        if not elem.attrib:
            item = Listitem()
            item.art["thumb"] = elem.find(".//img").get("src")

            artist = elem[1].text
            track = elem[1][0][0].text
            item.label = "%s - %s" % (artist, track)
            item.info["artist"] = [artist]

            url = elem.find(".//a").get("href")
            item.context.related(related, url=url)
            item.set_callback(play_video, url=url)
            yield item

    # Fetch next page url
    next_tag = root_elem.findall("./div[@class='pagination']/a")
    if next_tag and next_tag[-1].text.startswith("next"):
        yield Listitem.next_page(url=next_tag[-1].get("href"))


@Route.register
def watching_now(plugin):
    # Fetch HTML Source
    url = url_constructor("/index.html")
    html = plugin.request.get(url)
    root_elem = html.parse("ul", attrs={"id": "mycarousel"})
    for elem in root_elem.iterfind("li"):
        a_tag = elem.find(".//a[@title]")
        item = Listitem()

        # Fetch label & thumb
        item.label = a_tag.text
        item.art["thumb"] = elem.find(".//img").get("src")

        url = a_tag.get("href")
        item.context.related(related, url=url)
        item.set_callback(play_video, url=url)
        yield item


@Route.register
def top_videos(plugin):
    """:param Route plugin: The plugin parent object."""
    # Fetch HTML Source
    url = url_constructor("/topvideos.html")
    html = plugin.request.get(url)
    titles = []
    urls = []

    # Parse categories
    root_elem = html.parse("select", attrs={"name": "categories"})
    for group in root_elem.iterfind("optgroup"):
        for elem in group:
            urls.append(elem.get("value"))
            titles.append(elem.text.strip())

    # Display list for Selection
    dialog = xbmcgui.Dialog()
    ret = dialog.select(plugin.localize(SELECT_TOP), titles)
    if ret >= 0:
        # Fetch HTML Source
        url = urls[ret]
        html = plugin.request.get(url)
        root_elem = html.parse("div", attrs={"id": "topvideos_results"})
        for elem in root_elem.iterfind(".//tr"):
            if not elem.attrib:
                item = Listitem()
                a_tag = elem[3][0]

                artist = elem[2].text
                item.label = "%s %s - %s" % (elem[0].text, artist, a_tag.text)
                item.art["thumb"] = elem.find(".//img").get("src")
                item.info["count"] = elem[4].text.replace(",", "")
                item.info["artist"] = [artist]

                url = a_tag.get("href")
                item.context.related(related, url=url)
                item.set_callback(play_video, url=url)
                yield item


@Route.register
def related(plugin, url):
    """
    :param Route plugin: The plugin parent object.
    :param unicode url: The url of a video.
    """
    # Fetch HTML Source
    url = url_constructor(url)
    html = plugin.request.get(url)
    root_elem = html.parse("div", attrs={"id": "tabs_related"})

    # Parse the xml
    for elem in root_elem.iterfind(u"div"):
        a_tag = elem.find("./a[@class='song_name']")

        item = Listitem()
        item.label = a_tag.text
        item.art["thumb"] = elem.find("./a/img").get("src")

        url = a_tag.get("href")
        item.context.related(related, url=url)
        item.set_callback(play_video, url=url)
        yield item


@Route.register
def video_list(plugin, url=None, cat=None, search_query=None):
    """
    :param Route plugin: The plugin parent object.
    :param unicode url: The url resource containing lists of videos or next page.
    :param unicode cat: A category url e.g. Alternative, Folk Metal.
    :param unicode search_query: The video search term to use for searching.
    """
    if search_query:
        url = url_constructor("search.php?keywords=%s&btn=Search" % search_query)
    elif cat:
        sortby = (u"date.html", u"artist.html", u"rating.html", u"views.html")[plugin.setting.get_int("sort")]
        base, _ = url_constructor(cat).rsplit("-", 1)
        url = "-".join((base, sortby))
    else:
        url = url_constructor(url)

    html = plugin.request.get(url)
    root_elem = html.parse("div", attrs={"id": "browse_main"})
    for elem in root_elem.iterfind(u".//div[@class='video_i']"):
        item = Listitem()
        item.art["thumb"] = elem.find(".//img").get("src")

        # Extract url and remove first 'a' tag section
        # This makes it easir to extract 'artist' and 'song' name later
        a_tag = elem.find("a")
        url = a_tag.get("href")
        elem.remove(a_tag)

        # Fetch title
        span_tags = tuple(node.text for node in elem.findall(".//span"))
        item.label = "%s - %s" % span_tags
        item.info["artist"] = [span_tags[0]]

        # Add related video context item
        item.context.related(related, url=url)
        item.set_callback(play_video, url=url)
        yield item

    # Fetch next page url
    next_tag = root_elem.findall(".//div[@class='pagination']/a")
    if next_tag and next_tag[-1].text.startswith("next"):
        yield Listitem.next_page(url=next_tag[-1].get("href"))


@Resolver.register
def play_video(plugin, url):
    """
    :param Resolver plugin: The plugin parent object.
    :param unicode url: The url of a video.
    :returns: A playable video url.
    """
    # Attemp to find url using extract_source(YTDL) first
    url = url_constructor(url)
    source_url = plugin.extract_source(url)
    if source_url:
        return source_url

    # Fallback to search for direct file
    html = plugin.request.get(url).text
    search_regx = 'file:\s+\'(\S+?)\''
    match = re.findall(search_regx, html)
    if match:
        return match[0]


@Resolver.register
def party_play(plugin, url):
    """
    :param Resolver plugin: The plugin parent object.
    :param unicode url: The url to a video.
    :return: A playlist with the first item been a playable video url and the seconde been a callback url that
             will fetch the next video url to play.
    """
    # Attempt to fetch a video url 3 times
    attempts = 0
    while attempts < 3:
        try:
            url = play_video(plugin, url)
        except Exception as e:
            # Raise the Exception if we are on the last run of the loop
            if attempts == 2:
                raise e
        else:
            if url:
                # Break from loop when we have a url
                return plugin.create_loopback(url)

        # Increment attempts counter
        attempts += 1

    # All 3 attemps failed to resolve a url
    return None


# Initiate Startup
if __name__ == "__main__":
    run()
