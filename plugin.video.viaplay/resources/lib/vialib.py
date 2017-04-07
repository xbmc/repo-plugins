# -*- coding: utf-8 -*-
"""
A Kodi-agnostic library for Viaplay
"""
import codecs
import os
import cookielib
import calendar
import time
import re
import json
import uuid
import HTMLParser
from urllib import urlencode
from datetime import datetime, timedelta

import iso8601
import requests
import m3u8


class vialib(object):
    def __init__(self, username, password, settings_folder, country, debug=False):
        self.debug = debug
        self.username = username
        self.password = password
        self.country = country
        self.settings_folder = settings_folder
        self.cookie_jar = cookielib.LWPCookieJar(os.path.join(self.settings_folder, 'cookie_file'))
        self.tempdir = os.path.join(settings_folder, 'tmp')
        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)
        self.deviceid_file = os.path.join(settings_folder, 'deviceId')
        self.http_session = requests.Session()
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

        return data['success']

    def validate_session(self):
        """Check if our session cookies are still valid."""
        url = 'https://login.viaplay.%s/api/persistentLogin/v1' % self.country
        payload = {
            'deviceKey': 'pc-%s' % self.country
        }
        data = self.make_request(url=url, method='get', payload=payload)

        return data['success']

    def verify_login_status(self, data):
        """Check if we're logged in. If we're not, try to.
        Raise errors as LoginFailure."""
        if 'MissingSessionCookieError' in data.values():
            if not self.validate_session():
                if not self.login(self.username, self.password):
                    raise self.LoginFailure('login failed')

    def get_video_urls(self, guid, pincode=None):
        """Return a dict with the stream URL:s and available subtitle URL:s."""
        video_urls = {}
        url = 'https://play.viaplay.%s/api/stream/byguid' % self.country
        payload = {
            'deviceId': self.get_deviceid(),
            'deviceName': 'web',
            'deviceType': 'pc',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'deviceKey': 'atv-%s' % self.country,
            'guid': guid,
            'pgPin': pincode
        }

        data = self.make_request(url=url, method='get', payload=payload)
        self.verify_login_status(data)
        # we might have to request the stream again after logging in
        if 'MissingSessionCookieError' in data.values():
            data = self.make_request(url=url, method='get', payload=payload)
        self.check_for_subscription(data)

        for x in xrange(3):  # retry if we get an encrypted playlist
            if not 'viaplay:encryptedPlaylist' in data['_links'].keys():
                break
            data = self.make_request(url=url, method='get', payload=payload)
        if 'viaplay:media' in data['_links'].keys():
            manifest_url = data['_links']['viaplay:media']['href']
        elif 'viaplay:fallbackMedia' in data['_links'].keys():
            manifest_url = data['_links']['viaplay:fallbackMedia'][0]['href']
        elif 'viaplay:playlist' in data['_links'].keys():
            manifest_url = data['_links']['viaplay:playlist']['href']
        else:
            self.log('Unable to retrieve stream URL.')
            return False

        video_urls['manifest_url'] = manifest_url
        video_urls['bitrates'] = self.parse_m3u8_manifest(manifest_url)
        video_urls['subtitle_urls'] = self.get_subtitle_urls(data)

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
            pass

    def get_categories(self, input, method=None):
        if method == 'data':
            data = input
        else:
            data = self.make_request(url=input, method='get')

        if data['pageType'] == 'root':
            categories = data['_links']['viaplay:sections']
        elif data['pageType'] == 'section':
            categories = data['_links']['viaplay:categoryFilters']

        return categories

    def get_sortings(self, url):
        data = self.make_request(url=url, method='get')
        try:
            sorttypes = data['_links']['viaplay:sortings']
        except KeyError:
            self.log('No sortings available for this category.')
            return None

        return sorttypes

    def get_letters(self, url):
        """Return a list of available letters for sorting in alphabetical order."""
        letters = []
        products = self.get_products(input=url, method='url')
        for item in products:
            letter = item['group'].encode('utf-8')
            if letter not in letters:
                letters.append(letter)

        return letters

    def get_products(self, input, method=None, filter_event=False):
        """Return a list of all available products."""
        if method == 'data':
            data = input
        else:
            data = self.make_request(url=input, method='get')

        if 'list' in data['type']:
            products = data['_embedded']['viaplay:products']
        elif data['type'] == 'product':
            products = data['_embedded']['viaplay:product']
        else:
            products = self.get_products_block(data)['_embedded']['viaplay:products']

        try:
            # try adding additional info to sports dict
            aproducts = []
            for product in products:
                if product['type'] == 'sport':
                    product['event_date'] = self.parse_datetime(product['epg']['start'], localize=True)
                    product['event_status'] = self.get_event_status(product)
                aproducts.append(product)
            products = aproducts
        except TypeError:
            pass

        if filter_event:
            fproducts = []
            for product in products:
                for event in filter_event:
                    if event == product['event_status']:
                        fproducts.append(product)
            products = fproducts

        return products

    def get_seasons(self, url):
        """Return all available series seasons as a list."""
        seasons = []
        data = self.make_request(url=url, method='get')

        items = data['_embedded']['viaplay:blocks']
        for item in items:
            if item['type'] == 'season-list':
                seasons.append(item)

        return seasons

    def get_subtitle_urls(self, data):
        """Return all subtitle SAMI URL:s in a list."""
        subtitle_urls = []
        try:
            for subtitle in data['_links']['viaplay:sami']:
                subtitle_urls.append(subtitle['href'])
        except KeyError:
            self.log('No subtitles found for guid: %s' % data['socket2']['productGuid'])

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

            subpattern = re.search(r'[_]([a-z]+)', suburl)
            if subpattern:
                sublang = subpattern.group(1)
            else:
                sublang = 'unknown'
                self.log('Unable to identify subtitle language.')

            path = os.path.join(self.tempdir, '%s.sami') % sublang
            with open(path, 'w') as subfile:
                subfile.write(subtitle)
            subtitle_paths.append(path)

        return subtitle_paths

    def get_deviceid(self):
        """"Read/write deviceId (generated UUID4) from/to file and return it."""
        try:
            with open(self.deviceid_file, 'r') as deviceid:
                return deviceid.read()
        except IOError:
            deviceid = str(uuid.uuid4())
            with open(self.deviceid_file, 'w') as idfile:
                idfile.write(deviceid)
            return deviceid

    def get_event_status(self, data):
        """Return whether the event is live/upcoming/archive."""
        now = datetime.utcnow()
        producttime_start = self.parse_datetime(data['epg']['start'])
        producttime_start = producttime_start.replace(tzinfo=None)
        if 'isLive' in data['system']['flags']:
            status = 'live'
        elif producttime_start >= now:
            status = 'upcoming'
        else:
            status = 'archive'

        return status

    def get_sports_dates(self, url, event_date=None):
        """Return the available sports dates.
        Filter upcoming/previous dates with the event_date parameter."""
        dates = []
        data = self.make_request(url=url, method='get')
        dates_data = data['_links']['viaplay:days']
        now = datetime.now()

        for date in dates_data:
            date_obj = datetime(*(time.strptime(date['date'], '%Y-%m-%d')[0:6]))  # http://forum.kodi.tv/showthread.php?tid=112916
            if event_date == 'upcoming':
                if date_obj.date() > now.date():
                    dates.append(date)
            elif event_date == 'archive':
                if date_obj.date() < now.date():
                    dates.append(date)
            else:
                dates.append(date)

        return dates

    def parse_m3u8_manifest(self, manifest_url):
        """Return the stream URL along with its bitrate."""
        streams = {}
        auth_cookie = None
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
            elif 'hdntl' in req.cookies.keys():
                hdntl_cookie = req.cookies['hdntl']
                auth_cookie = 'hdntl=%s' % hdntl_cookie
            elif 'lvlt_tk' in req.cookies.keys():
                lvlt_tk_cookie = req.cookies['lvlt_tk']
                auth_cookie = 'lvlt_tk=%s' % lvlt_tk_cookie
            else:
                self.log('No auth cookie found.')
        else:
            self.log('Stream request didn\'t contain any cookies.')

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
        blocks = []
        blocks_data = data['_embedded']['viaplay:blocks']
        for block in blocks_data:
            # example: https://content.viaplay.se/pc-se/sport
            if 'viaplay:products' in block['_embedded'].keys():
                blocks.append(block)
        return blocks[-1]  # the last block is always (?) the right one

    def utc_to_local(self, utc_dt):
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)

    def parse_datetime(self, iso8601_string, localize=False):
        """Parse ISO8601 string to datetime object."""
        datetime_obj = iso8601.parse_date(iso8601_string)
        if localize:
            return self.utc_to_local(datetime_obj)
        else:
            return datetime_obj
