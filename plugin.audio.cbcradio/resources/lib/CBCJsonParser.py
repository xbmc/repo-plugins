import json, re, urllib2, os
DIR = os.path.dirname(__file__)
DATA_DIR =os.path.join(DIR, os.pardir, 'data', '')

'''
Gets the names of every region served by Radio1
Args:
    channel: radio1 or radio2
Retruns:
    List containing the names of the regions served by Radio1
'''
def get_regions(channel):
    a = []
    filename = DATA_DIR + channel + '.json'
    data = json.load(open(filename, 'r'))
    for station in data:
        a.append(station['region'].encode('utf-8'))
    return a

'''
Args:
    region: The region served by Radio1
Returns:
    A tuple contating:
    first element, the .pls url to the high quality stream (AAC)
    second element, the .pls url to the low quality stream (MP3)
'''
def get_R1_streams(region):
    data = json.load(open(DATA_DIR + 'radio1.json', 'r'))
    for station in data:
        if station['region'] == region:
            return (station['high_quality_url'], station['low_quality_url'])

'''
Args:
    region: The region served by Radio2
Returns:
    The url to the .pls file for region
'''
def get_R2_streams(region):
    data = json.load(open(DATA_DIR + 'radio2.json', 'r'))
    for station in data:
        if station['region'] == region:
            return station['url']

'''
Return URL of stream from .pls file
args:
    pls_url: Return single stream from .pls file
'''
def parse_pls(playlist):
    playlist = urllib2.urlopen(playlist)
    playlist_text = playlist.read()
    url = re.findall(r"(?<=File1\=).*C",playlist_text)[0]
    return url
