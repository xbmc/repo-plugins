# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, run
from codequick.utils import urljoin_partial, bold
import urlquick
import xbmcgui
import re

# Localized string Constants
VIDEO_OF_THE_DAY = 30004
WATCHING_NOW = 30005
TOP_VIDEOS = 30002
SELECT_TOP = 30001
PARTY_MODE = 589

BASE_URL = "https://metalvideo.com"
url_constructor = urljoin_partial(BASE_URL)


# noinspection PyUnusedLocal
@Route.register
def root(plugin, content_type="video"):
    """
    :param Route plugin: The plugin parent object.
    :param str content_type: The type of content been listed e.g. video, music. This is passed in from kodi and
                             we have no use for it as of yet.
    """
    yield Listitem.recent(video_list, url="newvideos.html")
    yield Listitem.from_dict(top_videos, bold(plugin.localize(TOP_VIDEOS)))
    yield Listitem.from_dict(watching_now, bold(plugin.localize(WATCHING_NOW)))
    yield Listitem.search(search_videos)

    # Fetch HTML Source
    url = url_constructor("/browse.html")
    resp = urlquick.get(url)
    root_elem = resp.parse("div", attrs={"id": "primary"})
    for elem in root_elem.iterfind("ul/li"):
        img = elem.find(".//img")
        item = Listitem()

        # The image tag contains both the image url and title
        item.label = img.get("alt")
        item.art["thumb"] = img.get("src")

        url = elem.find("div/a").get("href")
        item.set_callback(video_list, url=url)
        yield item

    # Add the video items here so that show at the end of the listing
    bold_text = bold(plugin.localize(VIDEO_OF_THE_DAY))
    yield Listitem.from_dict(play_video, bold_text, params={"url": "/index.html"})
    yield Listitem.from_dict(party_play, plugin.localize(PARTY_MODE), params={"url": "/randomizer.php"})


@Route.register
def search_videos(plugin, search_query):
    url = url_constructor("/search.php?keywords={}&video-id=".format(search_query))
    return video_list(plugin, url)


@Route.register
def top_videos(plugin):
    """:param Route plugin: The plugin parent object."""
    # Fetch HTML Source
    url = url_constructor("/topvideos.html")
    resp = urlquick.get(url)
    titles = []
    urls = []

    # Parse categories
    root_elem = resp.parse("select", attrs={"name": "categories"})
    for group in root_elem.iterfind("optgroup[@label]"):
        if group.get("label").lower().startswith("by"):
            for node in group:
                urls.append(node.get("value"))
                titles.append(node.text.strip())

    # Display list for Selection
    dialog = xbmcgui.Dialog()
    ret = dialog.select("[B]{}[/B]".format(plugin.localize(SELECT_TOP)), titles)
    if ret >= 0:
        return video_list(plugin, url=urls[ret])
    else:
        return False


@Route.register
def watching_now(_):
    # Fetch HTML Source
    url = url_constructor("/index.html")
    resp = urlquick.get(url, max_age=0)
    try:
        root_elem = resp.parse("ul", attrs={"id": "pm-ul-wn-videos"})
    except RuntimeError:
        pass
    else:
        for elem in root_elem.iterfind("li/div"):
            img = elem.find(".//img")
            item = Listitem()

            # The image tag contains both the image url and title
            item.label = img.get("alt")
            item.art["thumb"] = img.get("src")

            url = elem.find("span/a").get("href")
            item.context.related(related, url=url)
            item.set_callback(play_video, url=url)
            yield item


@Route.register
def video_list(_, url):
    """
    :param Route _: The plugin parent object.
    :param unicode url: The url resource containing recent videos.
    """
    # Fetch HTML Source
    url = url_constructor(url)
    resp = urlquick.get(url)
    root_elem = resp.parse("div", attrs={"class": "primary-content"})
    for elem in root_elem.find("ul").iterfind("./li/div"):
        item = Listitem()
        item.art["thumb"] = elem.find(".//img").get("src")
        item.info["plot"] = elem.find("p").text.strip()

        # Find duration
        node = elem.find("span/span/span")
        if node is not None and "pm-label-duration" in node.get("class"):
            item.info["duration"] = node.text.strip()

        # View count
        views = elem.find("./div/span[@class='pm-video-attr-numbers']/small").text
        item.info["count"] = views.split(" ", 1)[0].strip()

        # Date of video
        date = elem.find(".//time[@datetime]").get("datetime")
        date = date.split("T", 1)[0]
        item.info.date(date, "%Y-%m-%d")  # 2018-10-19

        # Url to video & name
        a_tag = elem.find("h3/a")
        url = a_tag.get("href")
        item.label = a_tag.text

        # Extract the artist name from the title
        item.info["artist"] = [a_tag.text.split("-", 1)[0].strip()]

        item.context.related(related, url=url)
        item.set_callback(play_video, url=url)
        yield item

    # Fetch next page url
    next_tag = root_elem.find("./div[@class='pagination pagination-centered']/ul")
    if next_tag is not None:
        next_tag = next_tag.findall("li[@class='']/a")
        next_tag.reverse()
        for node in next_tag:
            if node.text == u"\xbb":
                yield Listitem.next_page(url=node.get("href"), callback=video_list)
                break


@Route.register
def related(_, url):
    """
    :param Route _: The plugin parent object.
    :param unicode url: The url of a video.
    """
    # Fetch HTML Source
    url = url_constructor(url)
    resp = urlquick.get(url)
    root_elem = resp.parse("div", attrs={"id": "bestincategory"})
    for elem in root_elem.iterfind("ul/li/div"):
        img = elem.find(".//img")
        item = Listitem()

        # The image tag contains both the image url and title
        item.label = img.get("alt")
        item.art["thumb"] = img.get("src")

        # Find duration
        node = elem.find("span/span/span")
        if node is not None and "pm-label-duration" in node.get("class"):
            item.info["duration"] = node.text.strip()

        # View count
        item.info["count"] = elem.find("div/span/small").text.split(" ")[0].strip()

        url = elem.find("span/a").get("href")
        item.context.related(related, url=url)
        item.set_callback(play_video, url=url)
        yield item


@Resolver.register
def play_video(plugin, url):
    """
    :param Resolver plugin: The plugin parent object.
    :param unicode url: The url of a video.
    :returns: A playable video url.
    :rtype: unicode
    """
    url = url_constructor(url)
    html = urlquick.get(url, max_age=0)

    # Attemp to find url using extract_source first
    # video_url = plugin.extract_source(url)
    # if video_url:
    #     return video_url

    # Attemp to find url using extract_youtube first
    youtube_video = plugin.extract_youtube(html.text)
    if youtube_video:
        return youtube_video

    # Attemp to search for flash file
    search_regx = 'clips.+?url:\s*\'(http://metalvideo\.com/videos.php\?vid=\S+)\''
    match = re.search(search_regx, html.text)
    plugin.logger.debug(match)
    if match is not None:
        return match.group(1)

    # Attemp to search for direct file
    search_regx = 'file:\s+\'(\S+?)\''
    match = re.search(search_regx, html.text)
    if match is not None:  # pragma: no branch
        return match.group(1)


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
            video_url = play_video(plugin, url)
        except Exception as e:
            # Raise the Exception if we are on the last run of the loop
            if attempts == 2:
                raise e
        else:
            if video_url:
                # Break from loop when we have a url
                return plugin.create_loopback(video_url)

        # Increment attempts counter
        attempts += 1
