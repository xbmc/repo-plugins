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

import urllib, re, time
from BeautifulSoup import BeautifulSoup
import xbmcaddon

id = xbmcaddon.Addon(id="plugin.video.nrk").getSetting("quality")
QUALITY = {'0' : '400', '1' : '800', '2' : '1200' }[id]
QUALITY_STR = {'0' : 'l', '1' : 'm', '2' : 'h' }[id]

def getLive():
    items = []
    items.append(DataItem(title="NRK 1", url="mms://straumv.nrk.no/nrk_tv_direkte_nrk1_"+QUALITY_STR+"?UseSilverlight=1", isPlayable=True))
    items.append(DataItem(title="NRK 2", url="mms://straumv.nrk.no/nrk_tv_direkte_nrk2_"+QUALITY_STR+"?UseSilverlight=1", isPlayable=True))
    items.append(DataItem(title="NRK 3", url="mms://straumv.nrk.no/nrk_tv_direkte_nrk3_"+QUALITY_STR+"?UseSilverlight=1", isPlayable=True))
    return items


def getLatest():
    soup = BeautifulSoup(urllib.urlopen("http://www.nrk.no/nett-tv/"))
    li = soup.find('div', attrs={'class' : 'nettv-latest'}).findAll('li')
    items = []
    for e in li:
        anc = e.find('a', attrs={'href' : re.compile('^/nett-tv/klipp/[0-9]+')})
        items.append( _getVideoById(anc['href'].split('/').pop()) )
    return items


def getByLetter(ch):
    url = "http://www.nrk.no/nett-tv/bokstav/" + urllib.quote(ch)
    soup = BeautifulSoup(urllib.urlopen(url))
    
    items = []
    li = soup.find('div', attrs={'class' : 'nettv-category clearfix'}).findAll('li') 
    for e in li:
        anc = e.find('a', attrs={'href' : re.compile('^/nett-tv/prosjekt/[0-9]+')})
        title = anc['title']
        url   = anc['href']
        items.append( DataItem(title=title, url=url) )
    return items


def getByUrl(url):
    if (url.startswith("/nett-tv/prosjekt")):
        url = "http://www.nrk.no" + url
    elif url.startswith("/nett-tv/kategori"):
        url = "http://www.nrk.no/nett-tv/menyfragment.aspx?type=category&id=" + url.split('/').pop()
    
    soup = BeautifulSoup(urllib.urlopen(url))
        
    items = []
    items.extend(_getAllKlipp(soup))
    items.extend(_getAllKategori(soup))
    return items


def _getAllKlipp(soup):
    items = soup.findAll('a', attrs={'class':re.compile('icon-video-black.*'), 'href':re.compile('.*nett-tv/klipp/[0-9]+$')})
    return [ _getVideoById(e['href'].split('/').pop()) for e in items ]

    
def _getAllKategori(soup):
    items = soup.findAll('a', attrs={'class':re.compile('icon-closed-black.*'), 'href':re.compile('^/nett-tv/kategori/[0-9]+')})
    return [ DataItem(title=e['title'], url=e['href']) for e in items ]


def _getVideoById(id):
    url = "http://www.nrk.no/nett-tv/silverlight/getmediaxml.ashx?id=" + id + "&hastighet=" + QUALITY
    soup = BeautifulSoup(urllib.urlopen(url))
    title = soup.find('title').string
    
    url = soup.find('mediaurl').string
    #some uri's contais illegal chars so need to fix this
    url = url.split("mms://", 1)[1]
    url = url.encode('latin-1') #urllib cant unicode
    url = urllib.quote(url)
    url = "mms://" + url + "?UseSilverlight=1"
    
    return DataItem(title=title, url=url, isPlayable=True)


class DataItem:
    def __init__(self, title="", description="", date="", author="", category="", image="", url="", isPlayable=False):
        self._title = title
        self._description = description
        self._date = date
        self._author = author
        self._category = category
        self._image = image
        self._url = url
        self._isPlayable = isPlayable
    
    @property
    def isPlayable(self):
        return self._isPlayable
    
    @property
    def title(self):
        return self._title
    
    @property
    def description(self):
        return self._description
    
    @property
    def date(self):
        return self._date
    
    @property
    def author(self):
        return self._author
    
    @property
    def category(self):
        return self._category
    
    @property
    def image(self):
        return self._image
    
    @property
    def url(self):
        return self._url

    
