# -*- coding: utf-8 -*-
"""
A Kodi-agnostic library for Viaplay
"""
import codecs
import os
import cookielib
from datetime import datetime
from urllib import urlencode
import re
import json
import uuid
import HTMLParser

import dateutil.parser
import requests
import m3u8


class vialib(object):
    def __init__(self, username, password, cookie_file, deviceid_file, tempdir, country, ssl, debug=False):
        self.debug = debug
        self.username = username
        self.password = password
        self.country = country
        self.ssl = ssl
        self.deviceid_file = deviceid_file
        self.tempdir = tempdir
        self.http_session = requests.Session()
        self.cookie_jar = cookielib.LWPCookieJar(cookie_file)
        self.base_url = 'https://content.viaplay.%s/pc-%s' % (self.country, self.country)
        try:
            self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        except IOError:
            pass
        self.http_session.cookies = self.cookie_jar

    class LoginFailure(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    class AuthFailure(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def log(self, string):
        if self.debug:
            try:
                print '[vialib]: %s' % string
            except UnicodeEncodeError:
                # we can't anticipate everything in unicode they might throw at
                # us, but we can handle a simple BOM
                bom = unicode(codecs.BOM_UTF8, 'utf8')
                print '[vialib]: %s' % string.replace(bom, '')
            except:
                pass

    def url_parser(self, url):
        """Sometimes, Viaplay adds some weird templated stuff to the URL
        we need to get rid of. Example: https://content.viaplay.se/androiddash-se/serier{?dtg}"""
        if not self.ssl:
            url = url.replace('https', 'http')  # http://forum.kodi.tv/showthread.php?tid=270336
        template = re.search(r'\{.+?\}', url)
        if template:
            url = url.replace(template.group(), '')

        return url

    def make_request(self, url, method, payload=None, headers=None):
        """Make an HTTP request. Return the JSON response in a dict."""
        self.log('URL: %s' % url)
        parsed_url = self.url_parser(url)
        if parsed_url != url:
            url = parsed_url
            self.log('Parsed URL: %s' % url)
        if method == 'get':
            req = self.http_session.get(url, params=payload, headers=headers, allow_redirects=False, verify=False)
        else:
            req = self.http_session.post(url, data=payload, headers=headers, allow_redirects=False, verify=False)
        self.log('Response code: %s' % req.status_code)
        self.log('Response: %s' % req.content)
        self.cookie_jar.save(ignore_discard=True, ignore_expires=False)

        return json.loads(req.content)

    def login(self, username, password):
        """Login to Viaplay. Return True/False based on the result."""
        url = 'https://login.viaplay.%s/api/login/v1' % self.country
        payload = {
            'deviceKey': 'pc-%s' % self.country,
            'username': username,
            'password': password,
            'persistent': 'true'
        }
        data = self.make_request(url=url, method='get', payload=payload)
        if data['success'] is False:
            return False
        else:
            return True

    def validate_session(self):
        """Check if our session cookies are still valid."""
        url = 'https://login.viaplay.%s/api/persistentLogin/v1' % self.country
        payload = {
            'deviceKey': 'pc-%s' % self.country
        }
        data = self.make_request(url=url, method='get', payload=payload)
        if data['success'] is False:
            return False
        else:
            return True

    def verify_login_status(self, data):
        """Check if we're logged in. If we're not, try to.
        Raise errors as LoginFailure."""
        if 'MissingSessionCookieError' in data.values():
            if not self.validate_session():
                if not self.login(self.username, self.password):
                    raise self.LoginFailure('login failed')

        return True

    def get_video_urls(self, guid):
        """Return a dict with the stream URL:s and available subtitle URL:s."""
        video_urls = {}
        url = 'https://play.viaplay.%s/api/stream/byguid' % self.country
        payload = {
            'deviceId': self.get_deviceid(),
            'deviceName': 'web',
            'deviceType': 'pc',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'deviceKey': 'pchls-%s' % self.country,
            'guid': guid
        }

        data = self.make_request(url=url, method='get', payload=payload)
        if self.verify_login_status(data):
            # we might have to request the stream again after logging in
            if 'MissingSessionCookieError' in data.values():
                data = self.make_request(url=url, method='get', payload=payload)
            if self.check_for_subscription(data):
                manifest_url = data['_links']['viaplay:playlist']['href']
                video_urls['manifest_url'] = manifest_url
                video_urls['bitrates'] = self.parse_m3u8_manifest(manifest_url)
                video_urls['subtitle_urls'] = self.get_subtitle_urls(data, guid)

                return video_urls

    def check_for_subscription(self, data):
        """Check if the user is authorized to watch the requested stream. 
        Raise errors as AuthFailure."""
        try:
            if data['success'] is False:
                subscription_error = data['name']
                raise self.AuthFailure(subscription_error)
        except KeyError:
            # 'success' won't be in response if it's successful
            return True

    def get_categories(self, input, method=None):
        if method == 'data':
            data = input
        else:
            data = self.make_request(url=input, method='get')

        pagetype = data['pageType']
        try:
            sectiontype = data['sectionType']
        except KeyError:
            sectiontype = None
        if sectiontype == 'sportPerDay':
            categories = data['_links']['viaplay:days']
        elif pagetype == 'root':
            categories = data['_links']['viaplay:sections']
        elif pagetype == 'section':
            categories = data['_links']['viaplay:categoryFilters']

        return categories

    def get_sortings(self, url):
        data = self.make_request(url=url, method='get')
        sorttypes = data['_links']['viaplay:sortings']
        return sorttypes

    def get_letters(self, url):
        """Return a list of available letters for sorting in alphabetical order."""
        letters = []
        products = self.get_products(input=url, method='url')
        for item in products:
            letter = item['group']
            if letter not in letters:
                letters.append(letter)

        return letters

    def get_products(self, input, method=None):
        if method == 'data':
            data = input
        else:
            data = self.make_request(url=input, method='get')

        if data['type'] == 'season-list' or data['type'] == 'list':
            products = data['_embedded']['viaplay:products']
        elif data['type'] == 'product':
            products = data['_embedded']['viaplay:product']
        else:
            products = self.get_products_block(data)['_embedded']['viaplay:products']

        return products

    def get_seasons(self, url):
        """Return all available series seasons as a list."""
        data = self.make_request(url=url, method='get')
        seasons = []

        items = data['_embedded']['viaplay:blocks']
        for item in items:
            if item['type'] == 'season-list':
                seasons.append(item)

        return seasons

    def get_subtitle_urls(self, data, guid):
        """Return all subtitle SAMI URL:s in a list."""
        subtitle_urls = []
        try:
            for subtitle in data['_links']['viaplay:sami']:
                subtitle_urls.append(subtitle['href'])
        except KeyError:
            self.log('No subtitles found for guid %s' % guid)

        return subtitle_urls

    def download_subtitles(self, suburls):
        """Download the SAMI subtitles, decode the HTML entities and save to temp directory.
        Return a list of the path to the downloaded subtitles."""
        subtitle_paths = []
        for suburl in suburls:
            req = requests.get(suburl)
            sami = req.content.decode('utf-8', 'ignore').strip()
            htmlparser = HTMLParser.HTMLParser()
            subtitle = htmlparser.unescape(sami).encode('utf-8')
            subtitle = subtitle.replace('  ', ' ')  # replace two spaces with one

            if '_sv' in suburl:
                path = os.path.join(self.tempdir, 'swe.smi')
            elif '_no' in suburl:
                path = os.path.join(self.tempdir, 'nor.smi')
            elif '_da' in suburl:
                path = os.path.join(self.tempdir, 'dan.smi')
            elif '_fi' in suburl:
                path = os.path.join(self.tempdir, 'fin.smi')
            f = open(path, 'w')
            f.write(subtitle)
            f.close()
            subtitle_paths.append(path)

        return subtitle_paths

    def get_deviceid(self):
        """"Read/write deviceId (generated UUID4) from/to file and return it."""
        try:
            deviceid = open(self.deviceid_file, 'r').read()
            return deviceid
        except IOError:
            deviceid = str(uuid.uuid4())
            fhandle = open(self.deviceid_file, 'w')
            fhandle.write(deviceid)
            fhandle.close()
            return deviceid

    def get_sports_status(self, data):
        """Return whether the event is live/upcoming/archive."""
        now = datetime.utcnow()
        producttime_start = dateutil.parser.parse(data['epg']['start'])
        producttime_start = producttime_start.replace(tzinfo=None)
        if 'isLive' in data['system']['flags']:
            status = 'live'
        elif producttime_start >= now:
            status = 'upcoming'
        else:
            status = 'archive'

        return status

    def parse_m3u8_manifest(self, manifest_url):
        """Return the stream URL along with its bitrate."""
        streams = {}
        req = requests.get(manifest_url)
        m3u8_manifest = req.content
        self.log('HLS manifest: \n %s' % m3u8_manifest)
        if req.cookies:
            self.log('Cookies: %s' % req.cookies)
            # the auth cookie differs depending on the CDN
            if 'hdntl' and 'hdnts' in req.cookies.keys():
                hdntl_cookie = req.cookies['hdntl']
                hdnts_cookie = req.cookies['hdnts']
                auth_cookie = 'hdntl=%s; hdnts=%s' % (hdntl_cookie, hdnts_cookie)
            elif 'lvlt_tk' in req.cookies.keys():
                lvlt_tk_cookie = req.cookies['lvlt_tk']
                auth_cookie = 'lvlt_tk=%s' % lvlt_tk_cookie
            else:
                hdntl_cookie = req.cookies['hdntl']
                auth_cookie = 'hdntl=%s' % hdntl_cookie
        else:
            auth_cookie = None

        m3u8_header = {'Cookie': auth_cookie}
        m3u8_obj = m3u8.loads(m3u8_manifest)
        for playlist in m3u8_obj.playlists:
            bitrate = int(playlist.stream_info.bandwidth) / 1000
            if playlist.uri.startswith('http'):
                stream_url = playlist.uri
            else:
                stream_url = manifest_url[:manifest_url.rfind('/') + 1] + playlist.uri
            streams[str(bitrate)] = stream_url + '|' + urlencode(m3u8_header)

        return streams

    def get_next_page(self, data):
        """Return the URL to the next page if the current page count is less than the total page count."""
        # first page is always (?) from viaplay:blocks
        if data['type'] == 'page':
            data = self.get_products_block(data)
        if int(data['pageCount']) > int(data['currentPage']):
            next_page_url = data['_links']['next']['href']
            return next_page_url

    def get_products_block(self, data):
        """Get the viaplay:blocks containing all product information."""
        blocks = data['_embedded']['viaplay:blocks']
        for block in blocks:
            # example: https://content.viaplay.se/pc-se/film/disney?sort=alphabetical
            if block['type'] != 'cms':
                product_block = block
        return product_block
