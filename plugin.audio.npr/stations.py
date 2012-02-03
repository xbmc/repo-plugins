# FOO

import csv, urllib, sys, time
from xml.etree.ElementTree import ElementTree


def read_in_station_data(path):
# File format as follows in the CSV file:
#
# name|sid|call|icon|city|state|tagline
    data = {}
    with open(path, 'rt') as f:
	reader = csv.DictReader(f, delimiter='|')
	for d in reader:
	    print "Debug: " + repr(d)
	    data[int(d['sid'])] = d

    return data

def get_station_data(sid = 0):
    ''' Acquire station data for the provided station ID '''
    url = 'http://api.npr.org/stations.php'
    query = {
        'apiKey' : 'MDA4NTkxNTA1MDEzMjI0NDk1MzM0YjliOA001',
        'id'     : sid,
        }
    _MAX_SIZE = 4096
    streams = {}

    params = urllib.urlencode(query)
    data = urllib.urlopen(url + "?" + params)

    tree = ElementTree()
    tree.parse(data)

    return tree

def get_station_streams(tree):
    ''' Extract all station streams from etree of NPR station data '''
    streams = {}
    elist = tree.findall('station/url')
    for e in elist:
	url_id = e.get('typeId')
        if  url_id == '10' or url_id == '15':
            title = e.get('title')
            text = e.text
            streams[text] = title

    return streams


def get_station_info(tree):
    ''' Extract general station info from etree of NPR station data '''
    data = {}
    tags = [
	'band',
	'callLetters',
	'frequency',
	'image',
	'marketCity',
	'name',
	'state',
	'tagline',
	]

    for tag in tags:
	e = tree.find('station/' + tag)
	if e is None:
	    data[tag] = ''
	else:
	    data[tag] = e.text

    return data

minimum = 1
maximum = 1325
try:
    minimum = int(sys.argv[1])
    maximum = int(sys.argv[2])
except:
    pass

if minimum < 0:
    minimum = 0
if minimum > maximum:
    maximum = minimum

# IDs that cause the DB to hang.
bad_ids = [435, 436, 437, 444, 945, 1180, 1282, 1283]

ids = range(minimum, maximum + 1)
print 'name|sid|call|icon|city|state|tagline'
for i in ids:
    if i in bad_ids:
	continue
    sd = get_station_data(i)
    info = get_station_info(sd)
    streams = get_station_streams(sd)
    if info['name'] is '' \
	    or info['name'] is 'None' \
	    or len(streams) == 0:
	continue
    print "%s|%d|%s|%s|%s|%s|%s" % (info['name'],
				    i,
				    info['callLetters'],
				    info['image'],
				    info['marketCity'],
				    info['state'],
				    info['tagline'])
