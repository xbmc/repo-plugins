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
from codequick import Route, Resolver, Listitem, run

# Localized string Constants
RECENT_VIDEOS = 30001
RECENT_AUDIO = 30002
LIST_AUDIO = 30003
LIST_VIDEO = 30004


@Route.register
def root(plugin):
    """:type plugin: Route"""
    # Set context parameters based on default view setting
    if plugin.setting.get_int("defaultview") == 0:
        context_label = plugin.localize(LIST_AUDIO)
        context_type = "segment"
        item_type = "video"
    else:
        context_label = plugin.localize(LIST_VIDEO)
        context_type = "video"
        item_type = "segment"

    # Fetch HTML Source
    url = "https://www.sciencefriday.com/explore/"
    html = plugin.request.get(url)

    # Parse for the content
    root_elem = html.parse("form", attrs={"class": "searchandfilter"})
    sfid = root_elem.get("data-sf-form-id")

    # Add Youtube & Recent Content
    yield Listitem.youtube("UUDjGU4DP3b-eGxrsipCvoVQ")

    # Add Recent Videos link
    yield Listitem.from_dict(label=plugin.localize(RECENT_VIDEOS), callback=content_lister,
                             params={"sfid": sfid, "ctype": "video"})
    # Add Recent Audio link
    yield Listitem.from_dict(label=plugin.localize(RECENT_AUDIO), callback=content_lister,
                             params={"sfid": sfid, "ctype": "segment"})

    # List all topics
    for elem in root_elem.iterfind(".//option[@data-sf-cr]"):
        item = Listitem()
        item.label = elem.text

        # Add context item to link to the opposite content type. e.g. audio if video is default
        item.context.container(context_label, content_lister, topic=elem.attrib["value"], sfid=sfid, ctype=context_type)
        item.set_callback(content_lister, topic=elem.attrib["value"], ctype=item_type, sfid=sfid)
        yield item


@Route.register
def content_lister(plugin, sfid, ctype, topic=None, page_count=1):
    """
    :type plugin: Route
    :type sfid: unicode
    :type ctype: unicode
    :type topic: unicode
    :type page_count: int
    """
    # Add link to Alternitve Listing
    if page_count == 1 and topic:
        params = {"sfid": sfid, "ctype": u"segment" if ctype == u"video" else u"video", "topic": topic}
        label = plugin.localize(LIST_AUDIO) if ctype == u"video" else plugin.localize(LIST_VIDEO)
        item_dict = {"label": label, "callback": content_lister, "params": params}
        yield Listitem.from_dict(**item_dict)

    # Create content url
    if topic:
        url = "https://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=%(next)s&" \
              "sfid=%(sfid)s&post_types=%(ctype)s&_sft_topic=%(topic)s" % \
              {"sfid": sfid, "ctype": ctype, "topic": topic, "next": page_count}
    else:
        url = "https://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=%(next)s&" \
              "sfid=%(sfid)s&post_types=%(ctype)s" % \
              {"sfid": sfid, "ctype": ctype, "next": page_count}

    # Fetch & parse HTML Source
    ishd = bool(plugin.setting.get_int("video_quality", addon_id="script.module.youtube.dl"))
    root_elem = plugin.request.get(url).parse()

    # Fetch next page
    next_url = root_elem.find(".//a[@rel='next']")
    if next_url is not None:
        yield Listitem.next_page(sfid=sfid, ctype=ctype, page_count=page_count+1)

    # Parse the elements
    for element in root_elem.iterfind(".//article"):
        tag_a = element.find(".//a[@rel='bookmark']")
        item = Listitem()
        item.label = tag_a.text
        item.stream.hd(ishd)

        # Fetch plot & duration
        tag_p = element.findall(".//p")
        if tag_p and tag_p[0].get("class") == "run-time":
            item.info["duration"] = tag_p[0].text
            item.info["plot"] = tag_p[1].text
        elif tag_p:
            item.info["plot"] = tag_p[0].text

        # Fetch image if exists
        img = element.find(".//img[@data-src]")
        if img is not None:
            item.art["thumb"] = img.get("data-src")

        # Fetch audio/video url
        tag_audio = element.find(".//a[@data-audio]")
        if tag_audio is not None:
            audio_url = tag_audio.get("data-audio")
            item.set_callback(audio_url)
        else:
            item.set_callback(play_video, url=tag_a.get("href"))

        yield item


@Resolver.register
def play_video(plugin, url):
    """
    :type plugin: Resolver
    :type url: unicode
    """
    # Run SpeedForce to atempt to strip Out any unneeded html tags
    root_elem = plugin.request.get(url).parse("section", attrs={"class": "video-section bg-lightgrey"})

    # Search for youtube iframe
    iframe = root_elem.find("./div/iframe")
    return plugin.extract_source(iframe.get("src"))


# Initiate add-on
if __name__ == "__main__":
    run()
