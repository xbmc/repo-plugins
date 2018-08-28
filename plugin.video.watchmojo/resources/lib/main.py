# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, utils, run
import urlquick

# Localized string Constants
TAGS = 20459

# Base url constructor
url_constructor = utils.urljoin_partial("https://www.watchmojo.com")


# ###### Functions ###### #

def extract_videos(lbl_tags, elem, date_format):
    item = Listitem()
    item.label = elem.findtext(".//div[@class='hptitle']").replace("\t", " ").strip()
    item.art["thumb"] = url_constructor(elem.find(".//img").get("src"))

    duration = elem.find(".//img[@class='hpplay']")
    if duration is not None and duration.tail:
        item.info["duration"] = duration.tail.strip(";")

    date = elem.findtext(".//div[@class='hpdate']").strip()
    if date:
        item.info.date(date, date_format)

    url = elem.find("a").get("href")
    item.context.container(tags, lbl_tags, url=url)
    item.context.related(related, url=url)
    item.set_callback(play_video, url=url)
    return item


# ###### Callbacks ###### #

@Route.register
def root(_):
    """
    Lists all categories and link's to 'Shows', 'MsMojo' and 'All videos'.
    site: http://www.watchmojo.com
    """
    # Add links to watchmojo youtube channels
    yield Listitem.youtube("UCaWd5_7JhbQBe4dknZhsHJg")  # WatchMojo
    yield Listitem.youtube("UCMm0YNfHOCA-bvHmOBSx-ZA", label="WatchMojo UK")
    yield Listitem.youtube("UC3rLoj87ctEHCcS7BuvIzkQ", label="MsMojo")

    url = url_constructor("/")
    source = urlquick.get(url)
    root_elem = source.parse()

    # Parse only the show category elements
    menu_elem = root_elem.find(".//ul[@class='top-ul left']/li/ul")
    for elem in menu_elem.iterfind(".//a"):
        url = elem.get("href")
        if url and elem.text and elem.text != "MsMojo":
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
    """
    url = url_constructor(url)
    source = urlquick.get(url)
    lbl_tags = plugin.localize(TAGS)

    # Parse all the video elements
    root_elem = source.parse()

    for line in root_elem.iterfind(".//div[@class='owl-carousel margin-bottom']"):
        for elem in line.iterfind(".//div[@class='item']"):
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
    """
    url = url_constructor(url)
    source = urlquick.get(url)
    lbl_tags = plugin.localize(TAGS)

    # Parse all the video elements
    root_elem = source.parse("div", attrs={"id": "owl-demo1"})
    for elem in root_elem.iterfind(".//div[@class='item']"):
        yield extract_videos(lbl_tags, elem, "%B %d, %Y")


@Route.register
def tags(plugin, url):
    """
    List tags for a video.
    site: https://www.watchmojo.com/video/id/19268/

    :param Route plugin: Tools related to Route callbacks.
    :param unicode url: The url to a video.
    """
    plugin.category = plugin.localize(TAGS)
    url = url_constructor(url)
    source = urlquick.get(url)

    # Parse all video tags
    root_elem = source.parse("div", attrs={"id": "tags"})
    for elem in root_elem.iterfind("a"):
        item = Listitem()
        item.label = elem.text.title()
        item.set_callback(video_list, url="%s1" % elem.get("href"))
        yield item


@Resolver.register
def play_video(plugin, url):
    """
    Resolve video url.
    site: https://www.watchmojo.com/video/id/19268/

    :param Resolver plugin: Tools related to Resolver callbacks.
    :param unicode url: The url to a video.
    """
    url = url_constructor(url)
    return plugin.extract_source(url)
