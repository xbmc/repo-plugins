# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Benjamin Bertrand
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
# http://www.gnu.org/copyleft/gpl.html

import re
import pickle
import requests
from xbmcswift2 import xbmc
from BeautifulSoup import SoupStrainer, BeautifulSoup
import config

URLASI = 'http://www.arretsurimages.net'


def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log('ASI scraper: %s' % msg.encode('utf-8'), level)


def debug(msg):
    log(msg, xbmc.LOGDEBUG)


def error(msg):
    log(msg, xbmc.LOGERROR)


def get_html(url):
    """Return the content of the HTTP GET request in unicode"""
    # Try to load the cookie
    try:
        with open(config.cookie_file, 'rb') as f:
            cookies = pickle.load(f)
    except:
        cookies = {}
    try:
        debug('HTTP request: %s' % url)
        r = requests.get(url, cookies=cookies)
        return r.text
    except (requests.ConnectionError, requests.HTTPError):
        error('HTTP request failed' % url)


def get_json(url):
    """Return the json-encode content of the HTTP GET request"""
    try:
        debug('JSON request: %s' % url)
        r = requests.get(url)
        return r.json()
    except (requests.ConnectionError, requests.HTTPError):
        error('JSON request failed' % url)


def get_soup(url):
    html = get_html(url)
    return BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)


def is_logged_in(username):
    """Return True if @username is already logged in,
    False otherwise"""
    url_moncompte = 'http://www.arretsurimages.net/forum/control.php?panel=summary'
    soup = get_soup(url_moncompte)
    if soup.title.string == u'Arrêt sur images – Mon compte':
        # Already logged in, check that the username is still the same
        user_text = soup.find(text=re.compile(u'L’e-mail que vous utilisez pour @si est.*'))
        if user_text and user_text.next.string == username:
            debug('User already logged in')
            return True
        else:
            debug('Already logged in, but username does not match...')
    debug('User not logged in')
    return False


def login(username=None, password=None):
    """Try to login using @username and @password.
    Return True if successful, False otherwise"""
    if username and password:
        payload = {'forum_id': 0,
                   'redir': 'http://www.arretsurimages.net/forum/list.php',
                   'username': username,
                   'password': password}
        url_login = 'http://www.arretsurimages.net/forum/login.php'
        r = requests.post(url_login, data=payload)
        soup = BeautifulSoup(r.text, convertEntities=BeautifulSoup.HTML_ENTITIES)
        if soup.title.string == u'Le Forum Arrêt Sur Images':
            debug('User login successful')
            # We are on the forum page - login successful
            # Save the cookie
            with open(config.cookie_file, 'wb') as f:
                pickle.dump(r.cookies, f, 2)
                debug('cookie saved')
            return True
    return False


class Programs:
    """Class used to get all programs and navigation items
    from an url"""

    def __init__(self, url):
        # Load the current page
        self.html = get_html(url)

    def get_programs(self):
        """Return all programs from the current page"""
        # Remove the double double quotes in title
        # (otherwise beautifulsoup just get an empty string)
        html = re.sub('title=""(.+)">', 'title="\\1>', self.html)
        # Couldn't parse properly the file using "'div', {'class':'bloc-contenu-8'}"
        # BeautifulSoup returns nothing in that class
        # So use 'contenu-descr-8 ' and find previous tag
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        for media in soup.findAll('div', {'class': 'contenu-descr-8 '}):
            tag = media.findPrevious('a')
            # Get link, title and thumb
            if tag['href'].startswith('http'):
                media_link = tag['href']
            else:
                media_link = URLASI + tag['href']
            media_title = tag['title'].encode('utf-8')
            media_thumb = URLASI + tag.find('img', attrs={'src': re.compile('.+?\.[png|jpg]')})['src']
            yield {'url': media_link, 'title': media_title, 'thumb': media_thumb}

    def get_nav_items(self):
        """Return the navigation items from the current page"""
        nav_items = {'next': None, 'previous': None}
        filterContainer = SoupStrainer(attrs={'class': re.compile('rech-filtres-droite')})
        # There are two 'rech-filtres-droite' per page. Look only in the first one (contents[0])
        try:
            for tag in BeautifulSoup(self.html, parseOnlyThese=filterContainer).contents[0].findAll('a'):
                if tag.string == '&gt;':
                    nav_items['next'] = True
                elif tag.string == '&lt;':
                    nav_items['previous'] = True
        except IndexError:
            # No rech-filtres-droite in the page (Nos cinq dernières émissions)
            pass
        return nav_items


def get_main_video(url):
    """Return the main video title and download link"""
    title = None
    link = None
    download_page = ''
    soup = get_soup(url)
    # Look for the "bouton-telecharger" class (new version)
    telecharger = soup.find('a', attrs={'class': 'bouton-telecharger'})
    if telecharger:
        download_page = telecharger['href']
    else:
        # Look for the "bouton-telecharger" image (old version)
        img = soup.find('img', attrs={'src': 'http://www.arretsurimages.net/images/boutons/bouton-telecharger.png'})
        if img:
            download_page = img.findParent()['href']
    if download_page.endswith(('.avi', '.mp4')):
        title = download_page.split('/')[-1]
        soup = get_soup(download_page)
        click = soup.find(text=re.compile('cliquer ici'))
        if click:
            link = click.findParent()['href']
            debug('Main video link found: %s' % link)
        else:
            debug('No \"cliquer ici\" found')
    else:
        debug('No main video found')
    return {'title': title, 'url': link}


def get_program_parts(url, name, icon):
    """Return all parts of a program

    Returns the url of the main video if found
    For dailymotion video, no url is returned, but the video id"""
    html = get_html(url)
    soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    parts = []
    # Check if the xvid video exists
    fullvideo = get_main_video(url)
    if fullvideo['url']:
        # Add the full length video
        parts.append({'url': fullvideo['url'],
                      'title': fullvideo['title'],
                      'thumb': icon})
    part = 1
    # Get all movie id
    for param in soup.findAll('param', attrs={'name': 'movie'}):
        try:
            video_id = param.parent["id"]
        except KeyError:
            continue
        title = name + ' - Acte %d' % part
        # Try to get the icon linked to the iPhone video on that page
        # That's faster than getting it from the json request (see getVideoDetails),
        # which would require one extra HTML request for each part
        try:
            media = param.parent.parent.find(text=re.compile(u'img src='))
            match = re.search(u'img src="(.*?)"', media)
            thumb = URLASI + match.group(1)
        except (TypeError, AttributeError):
            thumb = icon
        parts.append({'video_id': video_id,
                      'title': title,
                      'thumb': thumb})
        part += 1
    # Change title for @ux sources
    if u'ux sources' in soup.title.string.lower() and part == 3:
        if len(parts) == 3:
            # parts[0] is the full length video
            idx = 1
        else:
            idx = 0
        # '@ux sources' is not cut in parts but getting the title is not
        # easy as it's not in a field linked to the video
        # Use a hack: since 20111110, "version intégrale" is first
        if re.search('Voici la version int&eacute;grale', html):
            parts[idx]['title'] = name + u' - intégrale'.encode('utf-8')
            parts[idx + 1]['title'] = name + u' - aperçu'.encode('utf-8')
        else:
            # Before 20111104, the short video (version montée) was first
            parts[idx]['title'] = name + u' - montée'.encode('utf-8')
            parts[idx + 1]['title'] = name + u' - intégrale'.encode('utf-8')
    return parts


def get_video_by_id(video_id, streams):
    """Return the dailymotion video title and url"""
    # Run the json request using the video id
    json_url = 'http://www.dailymotion.com/json/video/%s?fields=title,thumbnail_url,stream_h264_hq_url,stream_h264_url'
    result = get_json(json_url % video_id)
    # The stream quality chosen might not be available
    # -> get the first video link available (following the streams quality order)
    for stream in streams:
        if result[stream]:
            debug("Found %s link" % stream)
            link = result[stream]
            break
    else:
        log("No video link found for this video id %s" % video_id)
        link = 'None'
    title = result["title"] + '.mp4'
    return {'title': title, 'url': link}


def get_bestof_videos(page, sort_method):
    """Use dailymotion API to get ASI videos

    Return a dictionary with the videos in the 'list' item
    The 'has_more' key can be used to know if there are more pages
    """
    bestof_videos = 'https://api.dailymotion.com/user/asi/videos?fields=id,title,thumbnail_url&page=%s&sort=%s'
    return get_json(bestof_videos % (page, sort_method))
