#!/usr/bin/env python
# encoding: UTF-8

import requests
import html5lib
import re

def get_document(url):
    print "Slód: '{0}'".format(url)
    r = requests.get(url)
    source = r.content
    doc = html5lib.parse(source, treebuilder='lxml', namespaceHTMLElements=False)

    return doc

def get_episodes(url):
    "Find playable files on a shows page"
    episodes = []
    doc = get_document(url)

    #Generic look
    for ep in doc.xpath("//a[contains(@title, 'Spila')]"):
        episodes.append((ep.text, ep.get('href')))

    if episodes:
        return episodes

    #"Special" page
    for ep in doc.xpath("//div[contains(@class,'mm-mynd')]"):
        episode_date = ep.getparent().find('span').text
        url = u'http://www.ruv.is{0}'.format(ep.find('a').attrib.get('href'))
        episodes.append((episode_date, url))

    return episodes

def get_tabs():
    doc = get_document("http://www.ruv.is/sarpurinn")
    xpathstring = "//div[@class='menu-block-ctools-menu-sarpsmynd-1 menu-name-menu-sarpsmynd parent-mlid-_active:0 menu-level-2']/ul/li/a"
    tabs = []

    for a in doc.xpath(xpathstring):
        tabs.append((a.text, a.get('href')))

    return tabs

def get_showtree():
    doc = get_document('http://dagskra.ruv.is/thaettir/')
    showtree = []

    for i, channel in enumerate(doc.xpath("//div[@style]")):
        channel_name = channel.find("h1").text
        showtree.append({"name": channel_name, "categories": []})

        try:
            print channel_name.encode('utf-8')
        except AttributeError:
            print "nochan"

        for group in channel.find("div").iterchildren():
            if group.tag == 'h2':
                showtree[i]["categories"].append({"name":group.text, "shows":[]})
            elif group.tag == 'div':
                for show in group.findall("div"):
                    hyperlink = show.find("a")
                    show_info = (hyperlink.text, hyperlink.get('href'))
                    showtree[i]["categories"][-1]['shows'].append(show_info)
    return showtree

def get_stream_info(page_url):
    "Get a page url and finds the url of the rtmp stream"
    doc = get_document(page_url)

    #Get urls for the swf player and playpath
    params = doc.xpath('//param')
    swfplayer = 'http://ruv.is{0}'.format(params[0].get('value'))
    details = params[1].get('value')
    playpath = re.search('streamer=(.*?)&(file=.*?)&stre', details).group(2)

    # Get the url of the actual rtmp stream
    source_tags = doc.xpath('//source')
    if source_tags and source_tags[0].attrib.get('src'): #RÚV
        rtmp_url = source_tags[0].get('src')
    else: #RÁS 1 & 2
        # The ip address of the stream server is returned in another page
        cache_url = doc.xpath("//script[contains(@src, 'load.cache.is')]")[0].get('src')
        cache_content = res = requests.get(cache_url)
        cache_ip = re.search('"([^"]+)"', res.content).group(1)

        # Now that we have the ip address we can insert it into the URL
        source_js = doc.xpath("//script[contains(., 'tengipunktur')]")[0].text
        source_url = re.search("'file': '(http://' \+ tengipunktur \+ '[^']+)", source_js).group(1)

        rtmp_url = source_url.replace("' + tengipunktur + '", cache_ip)

    return (playpath, rtmp_url, swfplayer)

def get_tab_items(url):
    "Find playable items on the 'recent' pages"
    doc = get_document(url)
    episodes = []

    #Every tab has a player with the newest/featured item. Get the name of it.
    featured_item = doc.xpath("//div[@class='kubbur sarpefst']/div/h1")
    if featured_item:
        featured_name = featured_item[0].text
        episodes.append((featured_name, url))

    #Get the listed items
    for item in doc.xpath("//ul[@class='sarplisti']/li"):
        item_link = item.xpath("a")[0].attrib
        item_date = item.xpath("em")[0].text
        page_url = u"http://www.ruv.is{0}".format(item_link['href'])
        title = u"{0} - {1}".format(item_link.get('title'), item_date)
        episodes.append((title, page_url))

    return episodes

def get_podcast_shows():
    """Gets the names and rss urls of all the Podcasts"""
    doc = get_document("http://www.ruv.is/podcast")
    shows = []

    for show in doc.xpath("//ul[@class='hladvarp-info']"):
        title = show.xpath('li/h4')[0].text
        url = show.xpath("li/a[contains(@href,'http')]")[0].attrib.get('href')
        shows.append((title, url))

    return shows

def get_podcast_episodes(url):
    """Gets the items from the rss feed"""
    doc = get_document(url)
    episodes = []

    for item in doc.findall("//guid"):
        url = item.text
        for el in item.itersiblings():
            if el.tag == 'pubdate':
                date = el.text

        #date = item.xpath('pubdate')[0].text
        #url = item.xpath('guid')[0].text
        episodes.append((date,url))

    return episodes

def get_live_url(channel='ruv'):
    page_urls = {
        'ruv': "http://ruv.is/ruv"
        }

    doc = get_document(page_urls.get(channel))
    return doc.xpath("//div[@id='spilarinn']/video/source")[0].attrib['src']


if __name__ == '__main__':
    None
    #print get_episodes('')
