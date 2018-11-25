# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
from urlparse import urlparse
import xbmcgui
import xbmcplugin
import requests
import re
import json
import CommonFunctions
import time

common = CommonFunctions
# from bs4 import BeautifulSoup

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

# Free sample videos are provided by www.vidsplay.com
# Here we use a fixed set of properties simply for demonstrating purposes
# In a "real life" plugin you will need to get info and links to video files/streams
# from some web-site or online service.
VIDEOS = {'https://www.tamilmv.app': [{'name': 'Chicken',
                    'thumb': 'http://www.vidsplay.com/wp-content/uploads/2017/05/bbq_chicken-screenshot.jpg',
                    'video': 'http://www.vidsplay.com/wp-content/uploads/2017/05/bbqchicken.mp4',
                    'genre': 'Food'}],
          'https://movieretina.me': [{'name': 'Chicken',
                    'thumb': 'http://www.vidsplay.com/wp-content/uploads/2017/05/bbq_chicken-screenshot.jpg',
                    'video': 'http://www.vidsplay.com/wp-content/uploads/2017/05/bbqchicken.mp4',
                    'genre': 'Food'}],
          'https://hdhub4u.mobi': [{'name': 'Chicken',
                    'thumb': 'http://www.vidsplay.com/wp-content/uploads/2017/05/bbq_chicken-screenshot.jpg',
                    'video': 'http://www.vidsplay.com/wp-content/uploads/2017/05/bbqchicken.mp4',
                    'genre': 'Food'}]}


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def is_playable(content_url):
    print('is playable called for ')
    print(content_url)
    if content_url.startswith('https://linkstaker.club') or content_url.startswith('https://mvlinks.ooo'):
        return True
    elif is_uptostream_domain(content_url):
        return True
    else:
        return False


def is_uptostream_domain(content_url):
    return urlparse(content_url).netloc.endswith('uptostream.com')


def get_categories():
    """
    Get the list of video categories.

    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.

    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: types.GeneratorType
    """
    return VIDEOS.iterkeys()


def get_folder_content(category):
    """
    Get the list of videofiles/streams.

    Here you can insert some parsing code that retrieves
    the list of video streams in the given category from some site or server.

    .. note:: Consider using `generators functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :param category: Category name
    :type category: str
    :return: the list of videos in the category
    :rtype: list
    """

    if category.startswith('https://movieretina.me'):
        # Display the list of videos in a provided category.
        return get_movie_retina(category)
    elif category.startswith('https://hdhub4u.mobi'):
        # Play a video from a provided URL.
        return get_hdhub(category)
    elif category.startswith('https://linkscare.net'):
        return get_linkscare(category)
    elif category.startswith('https://uptobox.com'):
        return uptobox(category)
    elif category.startswith('https://www.tamilmv.app'):
        return get_tamilmv(category)
    else:
        return VIDEOS[category]


def get_movie_retina(content_url):
    movieList = []
    genre = 'movie'
    headers = {
        'User-Agent': 'Mozilla'
    }
    page = requests.get(content_url, headers=headers)
    # print(page)

    detail_page_container = common.parseDOM(page.text, 'div', attrs={'class': 'bw_desc'})

    if len(detail_page_container) > 0:
        print('found detail page container')
        thumb = ''
        movie_thumb = common.parseDOM(detail_page_container, 'img', ret='src')
        if len(movie_thumb) > 0:
            print('found detail page thumb')
            thumb = movie_thumb[0]
        movie_links = common.parseDOM(detail_page_container, 'tr')
        for row in movie_links:
            print('iterating movie links')
            movie_links_title = common.parseDOM(row, 'th')
            if len(movie_links_title) > 0:
                print(movie_links_title)
                movie_title = common.stripTags(movie_links_title[0])
                print('movie link title found')
                movie_links_details = common.parseDOM(row, 'td')
                if len(movie_links_details) > 0:
                    print('movie link details found')
                    first_td = movie_links_details[0]
                    print(first_td)
                    regex_result = re.findall("https://mvlinks.*'", first_td)
                    if len(regex_result) > 0:
                        result = regex_result[0][:-1]
                        video_url = result
                        movieList.append({'name': movie_title,
                                          'thumb': thumb,
                                          'video': video_url,
                                          'genre': genre}
                                         )
    else:
        upper = common.parseDOM(page.text, 'div', attrs={'class': 'bw_thumb_title'})
        # soup = BeautifulSoup(page.text, 'html.parser')
        # upper = soup.find_all('div', attrs={'class': 'bw_thumb_title'})
        print('iterating the thumb titles')
        print(upper)
        for row in upper:
            thumb = common.parseDOM(row, 'img', ret='src')[0]
            # print(thumb)
            figure_caption = common.parseDOM(row, 'h1')[0]
            # print(figure_caption)
            title = common.stripTags(figure_caption)
            # print(title)
            video_url = common.parseDOM(row, 'a', ret='href')[0]

            movieList.append({'name': title,
                              'thumb': thumb,
                              'video': video_url,
                              'genre': genre}
                             )
        next_page_link_container = common.parseDOM(page.text, 'div', attrs={'class': 'nav-previous alignleft'})
        if len(next_page_link_container) > 0:
            next_page_link = common.parseDOM(next_page_link_container, 'a', ret='href')
            if len(next_page_link) > 0:
                next_link = next_page_link[0]
                movieList.append({'name': 'Next',
                                  'thumb': 'thumb',
                                  'video': next_link,
                                  'genre': genre
                                  })
    return movieList


def get_hdhub(content_url):
    genre = 'movie'
    movieList = []
    print('downloading hdhub content url')
    print(content_url)
    page = requests.get(content_url)
    print(page.status_code)
    all_links = common.parseDOM(page.text, 'a', ret='href')
    thumb = 'https://www.jiopic.com/images/2018/11/16/vlcsnap-2018-11-16-00h23m58s651.png'  # sample only
    found_link = False
    for row in all_links:
        print('printing all_links element second time')
        if row.startswith('https://linkstaker.club') or row.startswith('https://linkscare.net'):
            print('found one useful link')
            print(row)
            found_link = True
            movieList.append({'name': row,
                              'thumb': thumb,
                              'video': row,
                              'genre': genre}
                             )
    if not found_link:
        upper = common.parseDOM(page.text, 'figure')
        print(upper)
        # soup = BeautifulSoup(page.text, 'html.parser')
        # upper = soup.find_all('div', attrs={'class': 'bw_thumb_title'})
        for row in upper:
            # print(row)
            thumb = common.parseDOM(row, 'img', ret='src')[0]
            # print(thumb)
            figure_caption = common.parseDOM(row, 'figcaption')[0]
            # print(figure_caption)
            title = common.stripTags(figure_caption)
            # print(title)
            video_url = common.parseDOM(figure_caption, 'a', ret='href')[0]
            # print(video_url)
            movieList.append({'name': title,
                              'thumb': thumb,
                              'video': video_url,
                              'genre': genre}
                             )
        next_page_link = common.parseDOM(page.text, 'a', attrs={'class': 'next page-numbers'}, ret='href')
        if len(next_page_link) > 0:
            next_link = next_page_link[0]
            movieList.append({'name': 'Next',
                              'thumb': 'thumb',
                              'video': next_link,
                              'genre': genre
                              })
    return movieList


def get_tamilmv(content_url):
    movieList = []
    genre = 'movie'
    headers = {
        'User-Agent': 'Mozilla'
    }
    page = requests.get(content_url, headers=headers)
    # print(page)
    print(content_url)
    print(page.status_code)
    print('getting pln container')
    pln_container = common.parseDOM(page.text, 'span', attrs={'class': 'pln'})
    print(len(pln_container))

    if len(pln_container) > 0:
        all_links = pln_container[0].splitlines()
        for row in all_links:
            print(row)
            movieList.append({'name': row,
                              'thumb': '',
                              'video': row,
                              'genre': genre}
                             )
        print(all_links)
    else:
        upper_container = common.parseDOM(page.text, 'div', attrs={'class': 'ipsWidget_inner '})
        print(len(upper_container))
        upper = common.parseDOM(upper_container, 'a', ret='href')
        print(upper[0])
        # soup = BeautifulSoup(page.text, 'html.parser')
        # upper = soup.find_all('div', attrs={'class': 'bw_thumb_title'})
        print('iterating the thumb titles')
        print(len(upper))
        print(upper)
        for row in upper:
            print(row)
            thumb = ''  # common.parseDOM(row, 'img', ret='src')[0]
            # print(thumb)
            title = row
            if title.endswith('/'):
                title = title[:-1]

            title = title.rsplit('/', 1)[-1]
            # print(title)
            video_url = row

            movieList.append({'name': title,
                              'thumb': thumb,
                              'video': video_url,
                              'genre': genre}
                             )
    return movieList

def get_linkscare(content_url):
    movieList = []
    page = requests.get(content_url)
    print('fetching links care url')
    print(content_url)
    print(page.status_code)
    csrf_token_name = common.parseDOM(page.text, 'input', attrs={'type': 'hidden'}, ret='name')[0]
    csrf_token_value = common.parseDOM(page.text, 'input', attrs={'type': 'hidden'}, ret='value')[0]
    payload = {csrf_token_name: csrf_token_value}
    print('post payload ready to post')
    print(payload)
    post_result = requests.post(content_url, data=payload)
    print(post_result.status_code)
    container_div = \
    common.parseDOM(post_result.text, 'div', attrs={'class': 'col-sm-8 col-sm-offset-2 well view-well'})[0]
    upper = common.parseDOM(container_div, 'a', ret='href')
    print(upper)
    for row in upper:
        video_url = row
        genre = 'movie'
        thumb = 'https://www.jiopic.com/images/2018/11/16/vlcsnap-2018-11-16-00h23m58s651.png'  # sample only
        print(video_url)
        movieList.append({'name': video_url,
                          'thumb': thumb,
                          'video': video_url,
                          'genre': genre}
                         )
    return movieList


def uptobox(content_url):
    content_url = content_url.replace('uptobox.com', 'uptostream.com')
    movieList = []
    print('fetching uptobox/uptostream url')
    print(content_url)
    page = requests.get(content_url)
    print(page.status_code)

    result = re.findall('poster.*,', page.text)[0]
    print('regex 1 found match')
    print(result)
    thumb = result.split("'")[1]

    result2 = re.findall('window\.sources.*;', page.text)[0]
    print('regex 2 found match')
    print(result2)
    json_urls = result2.split("'")[1]

    j = json.loads(json_urls)

    for row in j:
        video_url = row['src']
        genre = 'movie'
        print(video_url)
        movieList.append({'name': video_url,
                          'thumb': thumb,
                          'video': video_url,
                          'genre': genre}
                         )
    return movieList


def get_mvlinks_playable_path(content_url):
    print('fetching mvlinks url')
    print(content_url)
    headers = {
        'User-Agent': 'Mozilla'
    }
    page = requests.get(content_url, headers=headers)
    print(page.status_code)
    result = re.findall("https://elinks.*'", page.text)[0]
    result = result[:-1]
    print('found elinks for the mvlink content')
    print(result)
    elinks_requests = requests.session()
    elinks_page = elinks_requests.get(result, headers=headers)
    print(elinks_page.status_code)
    print(elinks_page.headers)
    name_collection = common.parseDOM(elinks_page.text, 'input', ret='name')
    value_collection = common.parseDOM(elinks_page.text, 'input', ret='value')
    print('found the nv collection this time')
    print(name_collection)
    print(value_collection)
    payload = {}
    for n, v in zip(name_collection, value_collection):
        payload[str(n)] = str(v)
    print('post payload ready to post')
    print(payload)
    data_to_send = str(urlencode(payload))
    print('sending the data below')
    print(data_to_send)
    headers['x-requested-with'] = 'XMLHttpRequest'
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    time.sleep(16)  # Waiting for 16 seconds
    post_result = elinks_requests.post('https://elinks.ooo/links/go', headers=headers, data=data_to_send)
    print('trying to investigate the request...')
    # print(post_result.request.headers)
    print(post_result.text)
    print(post_result.status_code)
    json_object = json.loads(post_result.text)
    gdfiles_url = json_object['url']

    headers = {
        'User-Agent': 'Mozilla',
        'referer': result
    }
    gdfiles_url_result = requests.get(gdfiles_url, headers=headers)
    print('gdfiles_url processing completed with status code')
    print(gdfiles_url_result.status_code)
    print(gdfiles_url_result.headers)
    refresh_header_value = gdfiles_url_result.headers['refresh']
    refresh_header_url_value = re.findall('https.*', refresh_header_value)[0]
    return refresh_header_url_value


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'My Video Collection')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
                          'icon': VIDEOS[category][0]['thumb'],
                          'fanart': VIDEOS[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': category,
                                    'genre': category,
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_contents(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    videos = get_folder_content(category)
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': video['name'],
                                    'genre': video['genre'],
                                    'mediatype': 'video'})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        print('getting url of the video link')
        print(video['video'])
        if is_playable(video['video']):
            url = get_url(action='play', video=video['video'])
            is_folder = False
        else:
            url = get_url(action='listing', category=video['video'])
            is_folder = True
        # url = get_url(action='play', video=video['video'])
        # check via url whether this is a folder or playable url
        # url = video['video']
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """

    if path.startswith('https://linkstaker.club'):
        page = requests.get(path)
        print('fetching links care url')
        print(path)
        print(page.status_code)
        result = re.findall('https.*e=download', page.text)[0]
        print('regex found match')
        print(result)
        path = result
    elif path.startswith('https://mvlinks.ooo'):
        path = get_mvlinks_playable_path(path)
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_contents(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
