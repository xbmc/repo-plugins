# -*- coding: utf-8 -*-
'''
    NRK plugin for XBMC
    Copyright (C) 2010 Thomas Amland

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import urllib, re
from BeautifulSoup import BeautifulSoup
from DataItem import DataItem
from dataStatic import *
from utils import *


global BITRATES, BITRATE_ID
def setQuality(id):
    global BITRATES, BITRATE_ID
    BITRATE_ID = id
    BITRATES = ['400', '800', '1200']


def getLive():
    url_1 = [
        'http://a897.l11601532896.c116015.g.lm.akamaistream.net/D/897/116015/v0001/reflector:32896',
        'http://a48.l11601648047.c116016.g.lm.akamaistream.net/D/48/116016/v0001/reflector:48047',
        'http://a1377.l11673952706.c116739.g.lm.akamaistream.net/D/1377/116739/v0001/reflector:52706'
        ][BITRATE_ID]
    
    url_2 = [
        'http://a1562.l11601643115.c116016.g.lm.akamaistream.net/D/1562/116016/v0001/reflector:43115',
        'http://a1382.l11674038974.c116740.g.lm.akamaistream.net/D/1382/116740/v0001/reflector:38974',
        'http://a746.l11674151924.c116741.g.lm.akamaistream.net/D/746/116741/v0001/reflector:51924'
        ][BITRATE_ID]
    
    url_3 = [
        'http://a397.l11601753777.c116017.g.lm.akamaistream.net/D/397/116017/v0001/reflector:53777',
        'http://a805.l11674254919.c116742.g.lm.akamaistream.net/D/805/116742/v0001/reflector:54919',
        'http://a1372.l11674333102.c116743.g.lm.akamaistream.net/D/1372/116743/v0001/reflector:33102'
        ][BITRATE_ID]
    
    return [DataItem(title="NRK 1", url=url_1, thumb=os.path.join(R_PATH, "nrk1.jpg"), isPlayable=True),
            DataItem(title="NRK 2", url=url_2, thumb=os.path.join(R_PATH, "nrk2.jpg"), isPlayable=True),
            DataItem(title="NRK 3", url=url_3, thumb=os.path.join(R_PATH, "nrk3.jpg"), isPlayable=True)]


def getLatest():
    soup = BeautifulSoup(urllib.urlopen("http://www.nrk.no/nett-tv/"))
    li = soup.find('div', attrs={'class' : 'nettv-latest'}).findAll('li')
    items = []
    for e in li:
        anc = e.find('a', attrs={'href' : re.compile('^/nett-tv/klipp/[0-9]+')})
        items.append( _getVideo(anc['href']) )
    return items


def getSearchResults(query):
    url = "http://www.nrk.no/nett-tv/sok/" + urllib.quote(query)
    return _getSearchResults(url)

def _getSearchResults(url):
    soup = BeautifulSoup(urllib.urlopen(url))
    li = soup.find('div', attrs={'id' : 'search-results'}).findAll('li')
    items = []
    for e in li:
        url = e.find('em').string
        if contains(url, "klipp"):
            items.append( _getVideo(url) )
        elif contains(url, "prosjekt"):
            title = decodeHtml(e.find('a').string)
            descr = decodeHtml(e.find('p').string)
            items.append( DataItem(title=title, description=descr, url="/nett-tv/prosjekt/"+getId(url)) )
    #next page
    url = soup.find('a', attrs={'id' : 'ctl00_contentPlaceHolder_ucSearch_nextLink'})['href']
    if not (url.endswith('0') or url.endswith('1')):
        items.append(DataItem(title="Neste »", url=url))
    return items


def getMostWatched(days):
    url = "http://www.nrk.no/nett-tv/ml/topp12.aspx?dager=%s" % days
    soup = BeautifulSoup(urllib.urlopen(url))
    li = soup.findAll('li')
    items = []
    for e in li:
        url = e.find('a')['href']
        if contains(url, "klipp"):
            items.append( _getVideo(url))
    return items


def getByUrl(url):
    if (url.startswith("/nett-tv/tema") or url.startswith("/nett-tv/bokstav")):
        url = "http://www.nrk.no" + url
        soup = BeautifulSoup(urllib.urlopen(url))
        return _getAllProsjekt(soup)
    
    elif (url.startswith("/nett-tv/sok")):
        url = "http://www.nrk.no" + url
        return _getSearchResults(url)
    
    elif (url.startswith("/nett-tv/prosjekt")):
        url = "http://www.nrk.no" + url
        
    elif (url.startswith("/nett-tv/kategori")):
        url = "http://www.nrk.no/nett-tv/menyfragment.aspx?type=category&id=" + getId(url)
    
    soup = BeautifulSoup(urllib.urlopen(url))
    items = []
    items.extend(_getAllKlipp(soup))
    items.extend(_getAllKategori(soup))
    return items


def _getAllKlipp(soup):
    items = soup.findAll('a', attrs={'class':re.compile('icon-(video|sound)-black.*'), 'href':re.compile('.*nett-tv/klipp/[0-9]+$')})
    return [ _getVideo(e['href']) for e in items ]


def _getAllKategori(soup):
    items = soup.findAll('a', attrs={'class':re.compile('icon-closed-black.*'), 'href':re.compile('^/nett-tv/kategori/[0-9]+')})
    return [ DataItem(title=decodeHtml(e['title']), url=e['href']) for e in items ]


def _getAllProsjekt(soup):
    items = []
    li = soup.find('div', attrs={'class' : 'nettv-category clearfix'}).findAll('li') 
    for e in li:
        anc = e.find('a', attrs={'href' : re.compile('^/nett-tv/prosjekt/[0-9]+')})
        title = decodeHtml(anc['title'])
        url   = anc['href']
        img   = _getImg(e.find('img')['src'])
        descr = decodeHtml(str(e.find('div', attrs={'class':'summary'}).find('p').string))
        
        items.append( DataItem(title=title, description=descr, thumb=img, url=url) )
    return items


def _getVideo(url):
    id = getId(url)
    (soup, url) = _findVideoUrl(id, BITRATE_ID)
    url = url.split("mms://", 1)[1] #some uri's contais illegal chars so need to fix this
    url = url.encode('latin-1') #urllib cant unicode
    url = urllib.quote(url)
    url = "mms://%s?UseSilverlight=1" % url
    
    title = decodeHtml(soup.find('title').string)
    descr = decodeHtml(str(soup.find('description').string))
    img   = _getImg(soup.find('imageurl').string)
    return DataItem(title=title, description=descr, thumb=img, url=url, isPlayable=True)


def _findVideoUrl(id, bitrate):
    if bitrate >= len(BITRATES):
        return (None, None)
    url = "http://www.nrk.no/nett-tv/silverlight/getmediaxml.ashx?id=%s&hastighet=%s" % (id, BITRATES[bitrate])
    soup = BeautifulSoup(urllib.urlopen(url))
    url = soup.find('mediaurl').string
    if not url:
        return _findVideoUrl(id, bitrate+1)
    return (soup, url)
     

def _getImg(url):
    return re.sub("^(.*cropid.*)w[0-9]+$", "\\1w650", url)

