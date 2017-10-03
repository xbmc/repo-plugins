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
from codequick import Route, Resolver, Listitem, run, utils

# Base url constructor
url_constructor = utils.urljoin_partial("http://johnlocker.com")


@Route.register
def root(plugin):
    """
    Lists all categories and link's to 'Shows', 'MsMojo' and 'All videos'.

    site: http://johnlocker.com

    :param Route plugin: Tools related to callback.
    :return: A generator of listitems.
    """
    url = url_constructor("/us")
    source = plugin.request.get(url)

    # Add link to recent videos
    yield Listitem.recent(recent)

    # Parse the categories
    root_elem = source.parse("ul", attrs={"id": "menu-category-items primary-menu"})
    for elem in root_elem.iterfind("./li/a"):
        item = Listitem()
        item.label = elem.text
        item.set_callback(video_list, url=elem.get("href"))
        yield item


@Route.register
def recent(plugin):
    """
    List all recent videos from the rss feed.

    :param Route plugin: Tools related to Route callbacks.
    :return: A generator of listitems.
    """
    url = "http://feeds.feedburner.com/johnlockerv3"
    source = plugin.request.get(url)

    # Pars all the videos
    root_elem = source.xml()
    for elem in root_elem.iterfind("./channel/item"):
        item = Listitem()

        date = elem.findtext("pubDate")
        item.info.date(date[:date.find("+") - 1], "%a, %d %b %Y %H:%M:%S")
        item.info["genre"] = elem.findall("category")[0].text

        # Split title into label and plot
        title, _, plot = elem.findtext("title").partition("\u2013")
        item.info["plot"] = plot.split("(", 1)[0].strip()
        item.label = title.split("(", 1)[0].strip()

        item.set_callback(play_video, url=elem.findtext("comments"))
        yield item


@Route.register
def video_list(plugin, url):
    """
    List all videos for given url.

    site: http://johnlocker.com/category/science-tech/

    :param Route plugin: Tools related to Route callbacks.
    :param unicode url: The url to a list of videos.
    :return: A generator of listitems.
    """
    url = url_constructor(url)
    source = plugin.request.get(url)

    # Parse video content
    root_elem = source.parse("main", attrs={"id": "main"})
    for elem in root_elem.iterfind("./div/article"):
        a_tag = elem.find(".//a[@rel='bookmark']")
        item = Listitem()
        item.label = a_tag.text.split("(", 1)[0].strip()
        url = a_tag.get("href")

        date = elem.find(".//time[@datetime]").get("datetime")
        item.info.date(date[:date.find("+")], "%Y-%m-%dT%H:%M:%S")
        item.info["count"] = elem.find(".//span[@class='entry-view']").text.split(" ", 1)[0].replace(",", "")

        # Extract video source url using post id to help with search
        post_id = elem.get("id").split("-", 1)[-1]
        iframe_node = elem.find("./div[@id='entry-video-%s']//iframe" % post_id)
        if iframe_node is not None:
            url = iframe_node.get("src")

        thumb = elem.find("./a/img")
        if thumb is not None:
            item.art["thumb"] = thumb.get("src")

        item.set_callback(play_video, url=url)
        yield item

    next_page = root_elem.find(".//nav/a[@class='next page-numbers']")
    if next_page is not None:
        yield Listitem.next_page(url=next_page.get("href"))


@Resolver.register
def play_video(plugin, url):
    """
    Resolve video url.

    site: http://johnlocker.com/science-tech/bbc-horizon-secrets-of-the-solar-system-2015-dailymotion-com/

    :param Resolver plugin: Tools related to Resolver callbacks.
    :param unicode url: The url to a video.
    :return: A playable video url.
    """
    url = url_constructor(url)
    return plugin.extract_source(url)


if __name__ == "__main__":
    run()
