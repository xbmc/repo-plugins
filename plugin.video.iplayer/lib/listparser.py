#
# Provides a simple and very quick way to parse list feeds
#

import re, utils, sys

from xml.etree import ElementTree as ET

if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json

class listentry(object):
     def __init__(self, title=None, id=None, image_base=None, date=None, summary=None, categories=None, series=None, episode=None):
         self.title      = title
         self.id         = id
         self.image_base = image_base
         self.date       = date
         self.summary    = summary
         self.categories = categories
         self.series     = series
         self.episode    = episode

class listentries(object):
     def __init__(self):
         self.entries = []

def parse(data, format):
    ret = None
    if format == 'xml':
        ret = parse_xml(data)
    if format == 'json':
        ret = parse_json(data)
    return ret

def process_entry(elist, entry):

    title = entry['complete_title']
    id = entry['id']
    image_base = entry['my_image_base_url']
    updated = entry['updated']

    if 'synopsis' in entry:
        summary = entry['synopsis']
    else:
        summary = None

    series = entry['toplevel_container_title']

    if 'position' in entry and len(entry['position']) > 0:
        episode = entry['position']
        episode = int(episode)
    else:
        episode = None

    e_categories = []
    for category in entry['categories']:
        e_categories.append(category['short_name'])

    elist.entries.append(listentry(title, id, image_base, updated, summary, e_categories, series, episode))

def parse_json(json):
    try:
        json = _json.loads(json)
    except:
        return None
    
    elist = listentries()
    for block in json['blocklist']:
        if 'series' in block:
            for series in block['series']:
                for entry in series['child_episodes']:
                    process_entry(elist, entry)
        elif 'child_episodes' in block:
            for entry in block['child_episodes']:
                process_entry(elist, entry)
        else:
            process_entry(elist, block)

    return elist

def parse_xml(xml):

    xml = utils.xml_strip_namespace(xml)

    try:
        root = ET.fromstring(xml)
    except:
        return None

    elist = listentries()
    for entry in root.getiterator('episode'):
        title = entry.find('complete_title').text
        id = entry.find('id').text
        date = entry.find('actual_start').text
        summary = entry.find('synopsis').text
        thumbnail = entry.find('my_image_base_url').text + id + "_640_360.jpg"

        series = entry.find('toplevel_container_title').text
        episode = entry.find('position').text
        if episode is not None:
            episode = int(episode)

        e_categories = []
        for category in entry.find('categories').findall('category'):
            e_categories.append(category.find('short_name').text)

        elist.entries.append(listentry(title, id, date, summary, e_categories, series, episode))

    return elist
