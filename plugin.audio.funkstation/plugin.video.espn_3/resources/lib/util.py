#!/usr/bin/python2

import xbmc
import os
import time
import urllib
import urllib2
import json
import xml.etree.ElementTree as ET
import hashlib
import re

from globals import ADDON_PATH_PROFILE

TAG = 'ESPN3 util: '


def is_file_valid(cache_file, timeout):
    if os.path.isfile(cache_file):
        modified_time = os.path.getmtime(cache_file)
        current_time = time.time()
        return current_time - modified_time < timeout
    return False


def fetch_file(url, cache_file):
    urllib.urlretrieve(url, cache_file)


def clear_cache(url):
    cache_file = hashlib.sha224(url).hexdigest()
    cache_file = os.path.join(ADDON_PATH_PROFILE, cache_file + '.xml')
    try:
        os.remove(cache_file)
    except:
        pass


def get_url_as_xml_soup_cache(url, cache_file = None, timeout = 300):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(ADDON_PATH_PROFILE, cache_file + '.xml')
    if not is_file_valid(cache_file, timeout):
        xbmc.log(TAG + 'Fetching config file %s from %s' % (cache_file, url), xbmc.LOGDEBUG)
        fetch_file(url, cache_file)
    else:
        xbmc.log(TAG + 'Using cache %s for %s' % (cache_file, url), xbmc.LOGDEBUG)
    with open(cache_file) as xml_file:
        xml_data = xml_file.read()
        return load_element_tree(xml_data)


def get_url_as_xml_soup(url):
    config_data = urllib2.urlopen(url).read()
    return load_element_tree(config_data)


# ESPN files are in iso-8859-1 and sometimes do not have the xml preamble
def load_element_tree(data):
    try:
        parser = ET.XMLParser(encoding='iso-8859-1')
        data_tree = ET.fromstring(data, parser)
    except:
        if '<?xml version' not in data:
            xbmc.log(TAG + 'Fixing up data because of no xml preamble', xbmc.LOGDEBUG)
            try:
                data_tree = ET.fromstring('<?xml version="1.0" encoding="ISO-8859-1" ?>' + data)
            except:
                try:
                    data_tree = ET.fromstring('<?xml version="1.0" encoding="windows-1252" ?>' + data)
                except:
                    # One last chance to fix up the data
                    xbmc.log(TAG + 'removing invalid xml characters', xbmc.LOGDEBUG)
                    data = re.sub('[\\x00-\\x1f]', '', data)
                    data = re.sub('[\\x7f-\\x9f]', '', data)
                    data_tree = ET.fromstring('<?xml version="1.0" encoding="ISO-8859-1" ?>' + data)
        else:
            data_tree = ET.fromstring(data)

    return data_tree


def get_url_as_json(url):
    response = urllib2.urlopen(url)
    return json.load(response)


def get_url_as_json_cache(url, cache_file = None, timeout = 300):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(ADDON_PATH_PROFILE, cache_file + '.json')
    if not is_file_valid(cache_file, timeout):
        xbmc.log(TAG + 'Fetching config file %s from %s' % (cache_file, url), xbmc.LOGDEBUG)
        fetch_file(url, cache_file)
    else:
        xbmc.log(TAG + 'Using cache %s for %s' % (cache_file, url), xbmc.LOGDEBUG)
    with open(cache_file) as json_file:
        json_data = json_file.read()
        json_file.close()
        if json_data.startswith('ud='):
            json_data = json_data.replace('ud=', '')
            json_data = json_data.replace('\'', '"')
        return json.loads(json_data)


# espn.page.loadSportPage('url');
# -> url
def parse_url_from_method(method):
    http_start = method.find('http')
    end = method.find('\')')
    return method[http_start:end]


# espn.page.loadMore('loadMoreLiveAndUpcoming', 'nav-0', 'url')
def parse_method_call(method):
    p = re.compile('([\\w\\.:/&\\?=%,-]{2,})')
    return p.findall(method)
