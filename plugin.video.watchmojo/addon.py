# -*- coding: utf-8 -*-
# Copyright: (c) 2016 - 2017 William Forde (willforde+kodi@gmail.com)
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
from codequick import Route, Resolver, Listitem, run, utils

# Localized string Constants
TAGS = 20459

# Base url constructor
url_constructor = utils.urljoin_partial("http://www.watchmojo.com")


# ###### Functions ###### #

def extract_videos(lbl_tags, elem, date_format):
    item = Listitem()
    item.label = elem.findtext(".//div[@class='hptitle']").replace("\t", " ").strip()
    item.art["thumb"] = url_constructor(elem.find(".//img").get("src"))

    duration = elem.find(".//img[@class='hpplay']").tail
    if duration:
        item.info["duration"] = duration.strip(";")

    url = elem.find("a").get("href")
    item.info.date(elem.findtext(".//div[@class='hpdate']").strip(), date_format)
    item.context.container(lbl_tags, tags, url=url)
    item.context.related(related, url=url)
    item.set_callback(play_video, url=url)
    return item


# ###### Callbacks ###### #

@Route.register
def root(plugin):
    """
    Lists all categories and link's to 'Shows', 'MsMojo' and 'All videos'.

    site: http://www.watchmojo.com

    :param Route plugin: Tools related to callback.
    :return: A generator of listitems.
    """
    # Item youtube link as a all videos option
    yield Listitem.youtube("UCaWd5_7JhbQBe4dknZhsHJg")

    url = url_constructor("/")
    source = plugin.request.get(url)

    # Parse only the main category elements
    root_elem = source.parse()
    for elem in root_elem.find(".//div[@id='owl-demo4']").iterfind("div"):
        # Image element contains image url and label as the alt attribute
        img_tag = elem.find("./a/img")

        item = Listitem()
        item.label = img_tag.get("alt")
        item.art["thumb"] = url_constructor(img_tag.get("src"))
        item.set_callback(video_list, url=elem.find("a").get("href").replace("/i/home/", "http://"))
        yield item

    # Parse only the show category elements
    menu_elem = root_elem.find(".//ul[@class='top-ul left']")
    for elem in menu_elem.iterfind(".//a"):
        url = elem.get("href")
        if url and elem.text and (url.startswith("/shows/") or url.startswith("/msmojo/")):
            item = Listitem()
            item.label = elem.text
            item.set_callback(video_list, url=url)
            yield item


@Route.register
def video_list(plugin, url):
    """
    List all video for given url.

    site: http://www.watchmojo.com/shows/Top%2010

    :param Route plugin: Tools related to Route callbacks.
    :param unicode url: The url to a list of videos.
    :return: A generator of listitems.
    """
    url = url_constructor(url)
    source = plugin.request.get(url)
    lbl_tags = plugin.localize(TAGS)

    # Parse all the video elements
    root_elem = source.parse()
    for elem in root_elem.iterfind(".//div[@class='item']"):
        yield extract_videos(lbl_tags, elem, "%b %d, %Y")

    # Add link to next page if available
    next_page = root_elem.find(".//div[@class='cat-next']")
    if next_page is not None:
        url = next_page.find("a").get("href")
        yield Listitem.next_page(url=url)


@Route.register
def related(plugin, url):
    """
    List all related videos to selected video.

    site: http://www.watchmojo.com/video/id/19268/

    :param Route plugin: Tools related to Route callbacks.
    :param unicode url: The url to a video.
    :return: A generator of listitems.
    """
    url = url_constructor(url)
    source = plugin.request.get(url)
    lbl_tags = plugin.localize(TAGS)

    # Parse all the video elements
    root_elem = source.parse("div", attrs={"id": "owl-demo1"})
    for elem in root_elem.iterfind(".//div[@class='item']"):
        yield extract_videos(lbl_tags, elem, "%B %d, %Y")


@Route.register
def tags(plugin, url):
    """
    List tags for a video.

    site: http://www.watchmojo.com/video/id/19268/

    :param Route plugin: Tools related to Route callbacks.
    :param unicode url: The url to a video.
    :return: A generator of listitems.
    """
    url = url_constructor(url)
    source = plugin.request.get(url)

    # Parse all video tags
    root_elem = source.parse("div", attrs={"id": "tags"})
    for elem in root_elem.iterfind("a"):
        item = Listitem()
        item.label = elem.text.title()
        item.set_callback(video_list, url=elem.get("href"))
        yield item


@Resolver.register
def play_video(plugin, url):
    """
    Resolve video url.

    site: http://www.watchmojo.com/video/id/19268/

    :param Resolver plugin: Tools related to Resolver callbacks.
    :param unicode url: The url to a video.
    :return: A playable video url.
    """
    url = url_constructor(url)
    return plugin.extract_source(url)


if __name__ == "__main__":
    run()
