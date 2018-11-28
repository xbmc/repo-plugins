# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, utils, run
import urlquick

# Localized string Constants
TAGS = 20459
FEATURED_VIDEO = 30001

# Base url constructor
BASE_URL = "https://www.watchmojo.com"
url_constructor = utils.urljoin_partial(BASE_URL)


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
    yield Listitem.search(search_results)
    yield Listitem.youtube("UCMm0YNfHOCA-bvHmOBSx-ZA", label="WatchMojo UK")
    yield Listitem.youtube("UC9_eukrzdzY91jjDZm62FXQ", label="MojoTravels")
    yield Listitem.youtube("UC4HnC-AS714lT2TCTJ-A1zQ", label="MojoPlays")
    yield Listitem.youtube("UC88y_sxutS1mnoeBDroS74w", label="MojoTalks")
    yield Listitem.youtube("UC3rLoj87ctEHCcS7BuvIzkQ", label="MsMojo")
    yield Listitem.youtube("UCYJyrEdlwxUu7UwtFS6jA_Q", label="UnVeiled")

    source = urlquick.get(BASE_URL)
    root_elem = source.parse()

    # Find each category and fetch the image for the first video in the list
    for elem in root_elem.iterfind("./body/section/div[@class='line']"):
        # If we have a 'link' tag with class=more, then we are in the right section
        tag = elem.find("a[@class='more']")
        if tag is not None:
            url = tag.get("href")
            # Only list category entrys
            if url.startswith("/categories"):
                item = Listitem()

                item.label = elem.find("h2").text.strip().title()
                item.art["thumb"] = url_constructor(elem.find(".//img").get("src"))
                item.set_callback(video_list, url=url)
                yield item

    # Add link to exclusive watchmojo video
    yield Listitem.from_dict(video_list, "Exclusive", params={"url": "/exclusive/1"},
                             art={"thumb": "https://www.watchmojo.com/uploads/blipthumbs/Fi-M-Top10-Well-"
                                           "Regarded-Controversial-Films_R7D2Y7-720p30-C_480.jpg"})
    # Add Featured Video
    # yield Listitem.from_dict(play_featured_video, plugin.localize(FEATURED_VIDEO))
    # This will be disabled for now, as watchmojo has disabled it on there site but may enable it again later on


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
        url = elem.get("href")
        urlparams = utils.parse_qs(url)
        if "q" in urlparams:
            search_term = urlparams["q"]
        else:
            continue

        item = Listitem()
        item.label = elem.text.title()
        item.set_callback(search_results, search_term)
        yield item


@Route.register
def search_results(_, search_query):
    """
    List search results

    :param Route _: Tools related to Route callbacks.
    :param search_query: The search term to find results for.
    """
    url = url_constructor("/search/search_1018.php?q={}&query=like".format(search_query))
    source = urlquick.get(url)
    root_elem = source.parse()

    for elem in root_elem.iterfind(".//li"):
        item = Listitem()
        atag = elem.find("a")
        item.art["thumb"] = url_constructor(atag.find("img").get("src"))

        # Extrac all title segments and join
        title = [atag.text]
        for i in atag:
            title.append(i.text)
            title.append(i.tail)
        item.label = "".join(filter(None, title))

        # Extract plot
        plot_node = elem.find("div")
        plots = [plot_node.text]
        for node in plot_node:
            plots.append(node.text)
            plots.append(node.tail)
        item.info["plot"] = "".join(text.strip() for text in plots if text is not None)

        url = atag.get("href")
        item.set_callback(play_video, url=url)
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


# @Resolver.register
def play_featured_video(plugin):
    """
    Resolve video url.
    site: https://www.watchmojo.com/video/id/19268/

    :param Resolver plugin: Tools related to Resolver callbacks.
    """
    video_url = play_video(plugin, BASE_URL)
    resp = urlquick.get(BASE_URL)
    try:
        elem = resp.parse("div", attrs={"class": "cal_title"})
    except RuntimeError:
        return None
    else:
        title = elem[0].text
        if video_url:
            # Using xbmcgui.ListItem just for setting plot info
            item = __import__("xbmcgui").ListItem(title, path=video_url)
            item.setInfo("video", {"title": title, "plot": title})
            return item
