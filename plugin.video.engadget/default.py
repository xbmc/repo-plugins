import os
import urllib
import urllib2
import re
import json
import StorageServer
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from urlparse import parse_qs, urlparse
import sys
# Do extra imports including from local addon dir
from bs4 import BeautifulSoup

__author__ = "divingmule, and Hans van den Bogert"
__copyright__ = "Copyright 2015"
__license__ = "GPL"
__version__ = "2"
__maintainer__ = "Hans van den Bogert"
__email__ = "hansbogert@gmail.com"

addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
addon_dir = xbmc.translatePath(addon.getAddonInfo('path'))
sys.path.append(os.path.join(addon_dir, 'resources', 'lib'))


cache = StorageServer.StorageServer("engadget", 1)
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString
base_url = 'http://www.engadget.com'


def addon_log(string):

    """

    :type string: string
    """
    try:
        log_message = string.encode('utf-8', 'ignore')
    except UnicodeEncodeError:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" % (addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url):
    addon_log('Request URL: %s' % url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': base_url
        }
    try:
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' % e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)


def display_all_items():
    def get_item_as_tuple(item):
        item_title = item['title']
        embed_html = None
        video_url = None
        image_url = None

        for i in item['media_content']:

            if i['media_medium'] == "image":
                image_url = i['url']
            elif i['media_medium'] == "video":
                embed_html = i['media_html']
                video_url = i['url']
            else:
                addon_log("Other format")

        return item_title, embed_html, video_url, image_url

    feed_url = "http://feeds.contenthub.aol.com/syndication/2.0/feeds/article" \
        "?sid=6d83dd23075648c2924a6469c80026c7&articleText=7&max=100"

    # Try two times to retrieve the feed. At moment of writing the contenthub seems to fail often.
    s_data = make_request(feed_url)
    if s_data is None:
        s_data = make_request(feed_url)

    addon_log("AOL feed data:" + str(s_data))
    json_data = json.loads(s_data)

    items = [get_item_as_tuple(x) for x in (json_data['channel']['item'])]

    # It is a video if a item tuple contains an video url
    video_items = [x for x in items if x[1] is not None]

    # Big assumption here, the video is the 2nd item in the json list gotten by the AOL CDN
    for (title, embed_url, url, image) in video_items:
        add_dir(title, embed_url, url, image, 'resolve_url', False)


def resolve_item(embed_url, url):
    domain = urlparse(url).netloc
    addon_log("Domain of media url is: " + domain)

    retrievers = {
        "on.aol.com": retrieve_url_for_aol,
        "www.youtube.com": retrieve_url_for_youtube,
        # TODO: Taking the easy way out, this should be more robust.
        "": retrieve_url_for_vidible

    }
    retriever = retrievers.get(domain, nothing)

    addon_log("returning embed_url  and url for playback: " + embed_url + " " + url)
    return retriever(embed_url, url)


# TODO: Not very functional, find a better place to pop up the Dialog.
def nothing(embed_url, url):
    xbmcgui.Dialog().ok(addon_name, "The video source is not playable")
    return None


def retrieve_url_for_vidible(embed_url, url):
    javascript_embed_tag = BeautifulSoup(embed_url, 'html.parser')
    addon_log("embed tag: " + str(javascript_embed_tag))
    javascript_source = javascript_embed_tag.find('script').get('src')
    addon_log("javascript source from embed code" + str(javascript_source))
    javascript_blob = make_request("http:" + javascript_source)
    pattern = re.compile('"videoUrls":\[".*?"\]')
    # Necessary dirty step, it's actually javascript, which happens to be JSON.
    s_urls = pattern.findall(javascript_blob)[0]
    # pre and post pend curly brace, to make it valid JSON
    s_urls_with_curly = "{" + s_urls + "}"

    addon_log("url strings retrieved from javascript blob: " + s_urls_with_curly)
    json_urls = json.loads(s_urls_with_curly)
    addon_log("Sending url to Kodi: " + json_urls['videoUrls'][0])
    return json_urls['videoUrls'][0]


def retrieve_url_for_aol(embed_url, url):
    javascript_embed_tag = BeautifulSoup(embed_url, 'html.parser')
    addon_log(str(javascript_embed_tag))
    javascript_source = javascript_embed_tag.find('script').get('src')
    addon_log("javascript source from embed code" + str(javascript_source))
    javascript_blob = make_request(javascript_source)
    # addon_log("the javascript blob" + javascript_blob)
    pattern = re.compile('"videoUrls":\[".*?"\]')
    # Necessary dirty step, it's actually javascript, which happens to be JSON.
    s_urls = pattern.findall(javascript_blob)[0]
    # pre and post pend curly brace, to make it valid JSON
    s_urls_with_curly = "{" + s_urls + "}"

    addon_log("url strings retrieved from javascript blob: " + s_urls_with_curly)
    json_urls = json.loads(s_urls_with_curly)
    addon_log("Sending url to Kodi: " + json_urls['videoUrls'][0])
    return json_urls['videoUrls'][0]


def retrieve_url_for_youtube(embed_url, url):
    qs = parse_qs(urlparse(url).query)
    video_id = qs['v'][0]
    addon_log("Youtube videoId:" + video_id)
    return "plugin://plugin.video.youtube/play/?video_id={0}".format(video_id)


def add_dir(name, embed_url, url, icon_image, dir_mode, is_folder=True):
    dir_params = {'embed_url': embed_url, 'url': url, 'mode': dir_mode}
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(dir_params))
    list_item = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=icon_image)
    if not is_folder:
        list_item.setProperty('IsPlayable', 'true')
    list_item.setInfo(type="Video", infoLabels={'Title': name})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, is_folder)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def main():
    params = get_params()
    addon_log(repr(params))

    mode = params.get('mode')

    if mode is None:
        display_all_items()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    elif mode == 'resolve_url':
        success = False
        resolved_url = resolve_item(params.get('embed_url', ""), params.get('url', ""))
        if resolved_url:
            success = True
        else:
            resolved_url = ''
        item = xbmcgui.ListItem(path=resolved_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)

if __name__ == "__main__":
    main()
