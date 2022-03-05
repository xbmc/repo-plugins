"""
xmltv.py - Python interface to XMLTV format, based on XMLTV.pm

Copyright (C) 2001 James Oakley <jfunk@funktronics.ca>

This library is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation; either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this software; if not, see <http://www.gnu.org/licenses/>.
"""

# Stolen from https://bitbucket.org/jfunk/python-xmltv/src/default/xmltv.py

import datetime
import os
import re
import time
import xml.etree.ElementTree as ET

import pytz
import urlquick
from codequick import Script
from kodi_six import xbmcvfs
from resources.lib.py_utils import compute_md5

try:
    # Temp fix of #592
    from tzlocal import get_localzone
except Exception:
    get_localzone = None
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# python-xmltv package (https://pypi.org/project/python-xmltv/)

# The Python-XMLTV version
VERSION = "1.4.3"

# The date format used in XMLTV (the %Z will go away in 0.6)
date_format = '%Y%m%d%H%M%S %Z'
date_format_notz = '%Y%m%d%H%M%S'


def set_attrs(d, elem, attrs):
    """
    set_attrs(d, elem, attrs) -> None

    Add any attributes in 'attrs' found in 'elem' to 'd'
    """
    for attr in attrs:
        if attr in elem.keys():
            d[attr] = elem.get(attr)


def set_boolean(d, name, elem):
    """
    set_boolean(d, name, elem) -> None

    If element, 'name' is found in 'elem', set 'd'['name'] to a boolean
    from the 'yes' or 'no' content of the node
    """
    node = elem.find(name)
    if node is not None:
        if node.text.lower() == 'yes':
            d[name] = True
        elif node.text.lower() == 'no':
            d[name] = False


def append_text(d, name, elem, with_lang=True):
    """
    append_text(d, name, elem, with_lang=True) -> None

    Append any text nodes with 'name' found in 'elem' to 'd'['name']. If
    'with_lang' is 'True', a tuple of ('text', 'lang') is appended
    """
    for node in elem.findall(name):
        if name not in d.keys():
            d[name] = []
        if with_lang:
            d[name].append((node.text, node.get('lang', '')))
        else:
            d[name].append(node.text)


def set_text(d, name, elem, with_lang=True):
    """
    set_text(d, name, elem, with_lang=True) -> None

    Set 'd'['name'] to the text found in 'name', if found under 'elem'. If
    'with_lang' is 'True', a tuple of ('text', 'lang') is set
    """
    node = elem.find(name)
    if node is not None:
        if with_lang:
            d[name] = (node.text, node.get('lang', ''))
        else:
            d[name] = node.text


def append_icons(d, elem):
    """
    append_icons(d, elem) -> None

    Append any icons found under 'elem' to 'd'
    """
    for iconnode in elem.findall('icon'):
        if 'icon' not in d.keys():
            d['icon'] = []
        icond = {}
        set_attrs(icond, iconnode, ('src', 'width', 'height'))
        d['icon'].append(icond)


def elem_to_channel(elem):
    """
    elem_to_channel(Element) -> dict

    Convert channel element to dictionary
    """
    d = {'id': elem.get('id'),
         'display-name': []}

    append_text(d, 'display-name', elem)
    append_icons(d, elem)
    append_text(d, 'url', elem, with_lang=False)

    return d


def elem_to_programme(elem):
    """
    elem_to_programme(Element) -> dict

    Convert programme element to dictionary
    """
    d = {'start': elem.get('start'),
         'channel': elem.get('channel'),
         'title': []}

    set_attrs(d, elem, ('stop', 'pdc-start', 'vps-start', 'showview',
                        'videoplus', 'clumpidx'))

    append_text(d, 'title', elem)
    append_text(d, 'sub-title', elem)
    append_text(d, 'desc', elem)

    crednode = elem.find('credits')
    if crednode is not None:
        creddict = {}
        # TODO: actor can have a 'role' attribute
        for credtype in ('director', 'actor', 'writer', 'adapter', 'producer',
                         'presenter', 'commentator', 'guest', 'composer',
                         'editor'):
            append_text(creddict, credtype, crednode, with_lang=False)
        d['credits'] = creddict

    set_text(d, 'date', elem, with_lang=False)
    append_text(d, 'category', elem)
    set_text(d, 'language', elem)
    set_text(d, 'orig-language', elem)

    lennode = elem.find('length')
    if lennode is not None:
        lend = {'units': lennode.get('units'),
                'length': lennode.text}
        d['length'] = lend

    append_icons(d, elem)
    append_text(d, 'url', elem, with_lang=False)
    append_text(d, 'country', elem)

    for epnumnode in elem.findall('episode-num'):
        if 'episode-num' not in d.keys():
            d['episode-num'] = []
        d['episode-num'].append((epnumnode.text,
                                 epnumnode.get('system', 'xmltv_ns')))

    vidnode = elem.find('video')
    if vidnode is not None:
        vidd = {}
        for name in ('present', 'colour'):
            set_boolean(vidd, name, vidnode)
        for videlem in ('aspect', 'quality'):
            venode = vidnode.find(videlem)
            if venode is not None:
                vidd[videlem] = venode.text
        d['video'] = vidd

    audnode = elem.find('audio')
    if audnode is not None:
        audd = {}
        set_boolean(audd, 'present', audnode)
        stereonode = audnode.find('stereo')
        if stereonode is not None:
            audd['stereo'] = stereonode.text
        d['audio'] = audd

    psnode = elem.find('previously-shown')
    if psnode is not None:
        psd = {}
        set_attrs(psd, psnode, ('start', 'channel'))
        d['previously-shown'] = psd

    set_text(d, 'premiere', elem)
    set_text(d, 'last-chance', elem)

    if elem.find('new') is not None:
        d['new'] = True

    for stnode in elem.findall('subtitles'):
        if 'subtitles' not in d.keys():
            d['subtitles'] = []
        std = {}
        set_attrs(std, stnode, ('type',))
        set_text(std, 'language', stnode)
        d['subtitles'].append(std)

    for ratnode in elem.findall('rating'):
        if 'rating' not in d.keys():
            d['rating'] = []
        ratd = {}
        set_attrs(ratd, ratnode, ('system',))
        set_text(ratd, 'value', ratnode, with_lang=False)
        append_icons(ratd, ratnode)
        d['rating'].append(ratd)

    for srnode in elem.findall('star-rating'):
        if 'star-rating' not in d.keys():
            d['star-rating'] = []
        srd = {}
        set_attrs(srd, srnode, ('system',))
        set_text(srd, 'value', srnode, with_lang=False)
        append_icons(srd, srnode)
        d['star-rating'].append(srd)

    for revnode in elem.findall('review'):
        if 'review' not in d.keys():
            d['review'] = []
        rd = {}
        set_attrs(rd, revnode, ('type', 'source', 'reviewer',))
        set_text(rd, 'value', revnode, with_lang=False)
        d['review'].append(rd)

    return d


def read_programmes(fp, only_current_programmes=False):
    """
    read_current_programmes(fp) -> list

    Return a list of programme dictionaries from file object 'fp'
    If 'only_current_programmes', only considere current program based on current time.
    """

    if only_current_programmes:
        # Get the current UTC datetime
        current_utc_time = datetime.datetime.now(pytz.UTC)
        current_utc_time = int(current_utc_time.strftime(date_format_notz))

        # Parse the xmltv file to only keep current programs
        # It is faster to parse the xmltv file line by line and remove unwanted programmes
        # than parsing the whole xmltv file with elementtree
        # (x10 faster)
        xmltv_l = []
        with open(fp, 'rb') as f:
            take_line = True
            for line in f:
                # Match the beginning of a program
                if b'<programme ' in line:
                    start = int(re.search(b'start="(.*?)"', line).group(1))  # UTC start time
                    try:
                        stop = int(re.search(b'stop="(.*?)"', line).group(1))  # UTC stop time
                    except Exception:
                        stop = 50000000000000
                    if current_utc_time >= start and current_utc_time <= stop:
                        pass
                    else:
                        take_line = False
                        continue

                # Keep this line if needed
                if take_line:
                    xmltv_l.append(line)

                # Match the end of a program
                if b'</programme>' in line:
                    take_line = True

        # Parse the reduced xmltv string with elementtree
        # and convert each programme to a dict
        tree = ET.fromstring(b''.join(xmltv_l))
    else:
        tree = ET.parse(fp)
    programmes = []
    for elem in tree.findall('programme'):
        programmes.append(elem_to_programme(elem))
    return programmes


# CUTV&M functions

def datetime_strptime(s, f):
    """Simple workaroung to fix https://forum.kodi.tv/showthread.php?tid=112916

    """
    try:
        return datetime.datetime.strptime(s, f)
    except TypeError:
        return datetime.datetime(*(time.strptime(s, f)[0:6]))


def programme_post_treatment(programme):
    """Prepare the programme to be used in the Live TV menu of CUTV&M

    """
    for k in ['title', 'desc', 'sub-title', 'country', 'category']:
        if k in programme:
            s = ''
            for t in programme[k]:
                s = s + t[0] + ' - '
            s = s[:-3]
            programme[k] = s

    if 'icon' in programme:
        programme['icon'] = programme['icon'][0]['src']

    # Listitem need duration in seconds
    if 'length' in programme:
        duration = int(programme['length']['length'])
        if programme['length']['units'] == 'minutes':
            duration = duration * 60
        elif programme['length']['units'] == 'hours':
            duration = duration * 3600
        programme['length'] = duration

    # For start and stop we use a string in %Hh%m format in our local timezone

    # Get local timezone
    if get_localzone is None:
        local_tz = pytz.timezone('Europe/Paris')
    else:
        try:
            local_tz = get_localzone()
        except Exception:
            # Hotfix issue #102
            local_tz = pytz.timezone('Europe/Paris')

    for elt in ['start', 'stop']:
        if elt in programme:
            # Get UTC start and stop datetime
            elt_s = programme[elt]
            # Convert start and stop on naive datetime object
            elt_dt = datetime_strptime(elt_s, date_format_notz)

            # Add UTC timezone to start and stop
            utc_tz = pytz.UTC
            elt_dt = utc_tz.localize(elt_dt)

            # Move to our timezone
            elt_dt = elt_dt.astimezone(local_tz)

            programme[elt] = elt_dt.strftime("%Hh%M")

    return programme


def programme_post_treatment_iptvmanager(programme):
    """Prepare the programme to be used by IPTV Manager

    """
    # Titles, etc..
    for k in ['title', 'desc', 'sub-title', 'country', 'category']:
        if k in programme:
            s = ''
            for t in programme[k]:
                s = s + t[0] + ' - '
            s = s[:-3]
            programme[k] = s

    # Icon
    if 'icon' in programme:
        programme['icon'] = programme['icon'][0]['src']

    # Episode (e.g 'episode-num': [('0.9.', 'xmltv_ns')])
    if 'episode-num' in programme:
        for episode_num, episode_format in programme['episode-num']:
            if episode_format == 'xmltv_ns':
                splitted_episode_num = episode_num.split('.')
                season = splitted_episode_num[0]
                episode = splitted_episode_num[1]
                part = splitted_episode_num[2]

                final_string = ''
                if season != '':
                    season = int(season) + 1
                    final_string += 'S' + str(season).zfill(2)
                if episode != '':
                    episode = int(episode) + 1
                    final_string += 'E' + str(episode).zfill(2)
                if part != '':
                    part = int(part) + 1
                    final_string += '/' + str(part).zfill(2)
                programme['episode'] = final_string
                break

    # For start and stop we use ISO-8601 format in UTC
    # (e.g YYYY-MM-DDTHH:MM:SS)
    ISO_8601_FORMAT = '%Y-%m-%dT%H:%M:%S'

    # But in our xmltv file we have datetime in
    # %Y%m%d%H%M%S format (e.g. 20210202224100)

    for elt in ['start', 'stop']:
        if elt in programme:
            # Get UTC start and stop datetime
            elt_s = programme[elt]

            # Convert start and stop on naive datetime object
            elt_dt = datetime_strptime(elt_s, date_format_notz)

            # Add UTC timezone to start and stop
            utc_tz = pytz.UTC
            elt_dt = utc_tz.localize(elt_dt)

            # Use correct format
            programme[elt] = elt_dt.strftime(ISO_8601_FORMAT)

    return programme


xmltv_infos = {
    'fr_live':
        {
            'url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_fr_{}.xml',
            'md5_url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_fr_{}_md5.txt',
            'keyword': 'tv_guide_fr_'
        },
    'be_live':
        {
            'url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_be_{}.xml',
            'md5_url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_be_{}_md5.txt',
            'keyword': 'tv_guide_be_'
        },
    'ch_live':
        {
            'url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_ch_{}.xml',
            'md5_url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_ch_{}_md5.txt',
            'keyword': 'tv_guide_ch_'
        },
    'uk_live':
        {
            'url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_uk_{}.xml',
            'md5_url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_uk_{}_md5.txt',
            'keyword': 'tv_guide_uk_'
        },
    'it_live':
        {
            'url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_it_{}.xml',
            'md5_url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_it_{}_md5.txt',
            'keyword': 'tv_guide_it_'
        },
    'wo_live':
        {
            'url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_wo_{}.xml',
            'md5_url': 'https://github.com/Catch-up-TV-and-More/xmltv/raw/master/tv_guide_wo_{}_md5.txt',
            'keyword': 'tv_guide_wo_'
        }
}


def get_xmltv_url(country_id, day_delta=0):
    """Get URL of the xmltv file

    Args:
        country_id (str)
        day_delta (int): 0: Today, 1: Tomorrow,...
    Returns:
        str: xmltv URL
    """
    xmltv_date = datetime.date.today() + datetime.timedelta(days=day_delta)
    xmltv_date_s = xmltv_date.strftime('%Y%m%d')
    return xmltv_infos[country_id]['url'].format(xmltv_date_s)


def get_remote_xmltv_md5(country_id, day_delta=0):
    """Get MD5 of the remote xmltv file

    Args:
        country_id (str)
        day_delta (int): 0: Today, 1: Tomorrow,...
    Returns:
        str: xmltv MD5 value
    """
    xmltv_date = datetime.date.today() + datetime.timedelta(days=day_delta)
    xmltv_date_s = xmltv_date.strftime('%Y%m%d')
    url = xmltv_infos[country_id]['md5_url'].format(xmltv_date_s)
    return urlquick.get(url, max_age=120).text


def download_xmltv_file(country_id, day_delta=0):
    """Try to download XMLTV file of country_id for today + day_delta.

    Args:
        country_id (str)
        day_delta (int): 0: Today, 1: Tomorrow,...
    Returns:
        str: xmltv filepath.
    """
    # Retrieve URL
    xmltv_url = get_xmltv_url(country_id, day_delta=day_delta)
    Script.log('xmltv url of {} country with day_delta {}: {}'.format(country_id, day_delta, xmltv_url))

    # Compute dst filepath
    xmltv_fn = os.path.basename(urlparse(xmltv_url).path)
    Script.log('xmltv filename: {}'.format(xmltv_fn))
    xmltv_fp = os.path.join(Script.get_info('profile'), xmltv_fn)

    # Remove old xmltv files of this country
    dirs, files = xbmcvfs.listdir(Script.get_info('profile'))
    today = datetime.date.today()
    for fn in files:
        if xmltv_infos[country_id]['keyword'] not in fn:
            continue
        try:
            file_date_s = fn.split(xmltv_infos[country_id]['keyword'])[1].split('.xml')[0]
            file_date = datetime_strptime(file_date_s, '%Y%m%d').date()
            if file_date < today:
                Script.log('Remove old xmltv file: {}'.format(fn))
                xbmcvfs.delete(os.path.join(Script.get_info('profile'), fn))
        except Exception:
            pass

    # Check if we need to download a fresh xmltv file
    need_to_downlod_xmltv_file = False
    if not xbmcvfs.exists(xmltv_fp):
        Script.log("xmltv file of {} for today does not exist, let's download it".format(country_id))
        need_to_downlod_xmltv_file = True
    else:
        # Check if we have the last version of the file
        current_file_md5 = compute_md5(xmltv_fp)
        remote_file_md5 = get_remote_xmltv_md5(country_id, day_delta=day_delta)
        if current_file_md5 != remote_file_md5:
            Script.log("A new version of xmltv file of {} for today exists, let's download it".format(country_id))
            need_to_downlod_xmltv_file = True

    if need_to_downlod_xmltv_file:
        r = urlquick.get(xmltv_url, max_age=-1)
        with open(xmltv_fp, 'wb') as f:
            f.write(r.content)
    return xmltv_fp


def grab_programmes(country_id, day_delta):
    """Retrieve programmes of channels of country_id at day today + day_detla.

    Args:
        country_id (str)
        day_delta (int)
    Returns:
        list: Programmes.
    """
    if country_id not in xmltv_infos:
        return []
    try:
        # Download, if needed, xmltv file
        xmltv_fp = download_xmltv_file(country_id, day_delta=day_delta)

        # Grab programmes in xmltv file
        programmes = read_programmes(xmltv_fp, only_current_programmes=False)
        programmes_post_treated = []
        for programme in programmes:
            programmes_post_treated.append(programme_post_treatment_iptvmanager(programme))
        return programmes_post_treated
    except Exception as e:
        Script.log('xmltv module failed with error: {}'.format(e), lvl=Script.ERROR)
        return []


def grab_current_programmes(country_id):
    """Retrieve current programmes of channels of country_id.

    Args:
        country_id (str)
    Returns:
        dict: (key: xmltv_id, value: current programme)
    """
    if country_id not in xmltv_infos:
        return {}
    try:
        # Download, if needed, xmltv file of today
        xmltv_fp = download_xmltv_file(country_id)

        # Grab current programmes in xmltv file
        programmes = read_programmes(xmltv_fp, only_current_programmes=True)

        # Use the channel as key
        tv_guide = {}
        for programme in programmes:
            programme = programme_post_treatment(programme)
            tv_guide[programme['channel']] = programme

        return tv_guide
    except Exception as e:
        Script.notify(
            Script.localize(30722),
            Script.localize(30723),
            display_time=7000)
        Script.log('xmltv module failed with error: {}'.format(e), lvl=Script.ERROR)
        return {}
