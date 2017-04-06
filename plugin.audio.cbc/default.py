# https://docs.python.org/2.7/
import os
import sys
import urllib
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin
import re
import urllib2
from HTMLParser import HTMLParser

def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)
    
def get_page(url):
    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
    headers = { 'User-Agent' : user_agent }
    req = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(req)
    page = response.read()
    response.close()
    return page
    
def parse_page(page):
    streams = {}
    h = HTMLParser()
    for item in re.findall(r'(<h3>(.|\n)+?<\/p>)', page):
        result = re.findall(r'([A-Za-z-\s&#;0-9.]{5,})<|(http:\/\/.*cbc[^<]*)', item[0])
        city = h.unescape(result[0][0])
        city = city.replace("\t", " ")
        city = city.strip()
        station = result[1][1]
        if "cbc_r2" in station:
            city = "CBC 2 - " + city
        elif "CBCR2" in station:
            city = "CBC 2 - " + city
        else:
            city = "CBC 1 - " + city

        streams[city] = station
    return streams
    
def build_stream_list(streams):
    stream_list = []
    for city, station in sorted(streams.items()):
        # create a list item for the label
        li = xbmcgui.ListItem(label=city)
        # set list item mediatype
        li.setInfo('video', { 'studio': 'cbc', 'mediatype': 'video' })
        # set the list item to playable
        li.setProperty('IsPlayable', 'true')
        # build the plugin url for Kodi
        url = build_url({'mode': 'stream', 'url': station, 'title': city})
        # add the current list item to a list
        stream_list.append((url, li, False))

    # add list to Kodi per Martijn
    xbmcplugin.addDirectoryItems(addon_handle, stream_list, len(stream_list))
    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
    
def play_stream(url):
    # set the path of the station to a list item
    play_item = xbmcgui.ListItem(path=url)
    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    
def main():
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    
    # initial launch of add-on
    if mode is None:
        page = get_page('http://www.cbc.ca/radio/includes/stream.html')
        content = parse_page(page)
        build_stream_list(content)
    # a station from the list has been selected
    elif mode[0] == 'stream':
        play_stream(args['url'][0])
    
if __name__ == '__main__':   
    addon_handle = int(sys.argv[1])
    main()
