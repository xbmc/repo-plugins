'''
    resources.lib.leesrtlxl
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching RTLxl

    :copyright: (c) 2012 by Jonathan Beluch (Documentary.net xbmc addon)    
    :license: GPLv3, see LICENSE.txt for more details.

    RTLxl = Made by Bas Magre (Opvolger)    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

    ## low
	## http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az/output=xml
	## http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=a2t/fmt=progressive/ak=216992/output=xml/pg=1/
	## http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=abstract/pg=1/output=xml/ak=283771/sk=301653
	## http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=abstract/uuid=6937d7bb-bf40-4f51-9590-c2c8131bccc7/output=xml/
    ## http://pg.us.rtl.nl//rtlxl/network/a2t/progressive/components/videorecorder/28/283771/301653/6937d7bb-bf40-4f51-9590-c2c8131bccc7.ssm/6937d7bb-bf40-4f51-9590-c2c8131bccc7.mp4       
'''
import urllib2,re
from operator import itemgetter, attrgetter
import time
from datetime import datetime
import xml.etree.ElementTree as ET

class RtlXL:
    def __init__(self):
        self.overzichtcache = 'leeg'
        self.items = 'leeg'
    
    def __gettextitem(self, element, elementnaam):
        el = element.find(elementnaam)
        if el is None:
            return ''
        return el.text
    
    def __overzicht(self):
        req = urllib2.Request('http://www.rtl.nl/system/s4m/ipadfd/d=ipad/')
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
        req.add_header('Accept-Encoding', 'utf-8')
        response = urllib2.urlopen(req)
        xmlstring = response.read()
        response.close()
        tree = ET.ElementTree(ET.fromstring(xmlstring))
        root = tree.getroot()
        rtlitemlist = list()
        for serieitem in root.findall('serieitem'):
            itemsperserie_url = self.__gettextitem(serieitem,'itemsperserie_url')
            serienaam = self.__gettextitem(serieitem,'serienaam')
            seriescoverurl = self.__gettextitem(serieitem,'seriescoverurl')
            rtlitem = {'label': serienaam, 'url': itemsperserie_url, 'thumbnail': seriescoverurl}
            rtlitemlist.append(rtlitem)
        self.overzichtcache = sorted(rtlitemlist, key=lambda x: x['label'], reverse=False)
        
    def get_overzicht(self):
        self.items = 'leeg' ## we zijn terug in overzicht
        if (self.overzichtcache == 'leeg'):
            self.__overzicht()    
        return self.overzichtcache            

    def __items(self, url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
        req.add_header('Accept-Encoding', 'utf-8')
        response = urllib2.urlopen(req)
        xmlstring = response.read()
        response.close()
        rtlitemlist = list()
        tree = ET.ElementTree(ET.fromstring(xmlstring))
        root = tree.getroot()
        rtlitemlist = list()
        for item in root.findall('item'):
            TimeStamp = self.__gettextitem(item,'TimeStamp')
            classname = self.__gettextitem(item,'classname')
            samenvattingkort = self.__gettextitem(item,'samenvattingkort')
            thumbnail = self.__gettextitem(item,'thumbnail')
            title = self.__gettextitem(item,'title')
            movie = self.__gettextitem(item,'movie')
            serienaam = self.__gettextitem(item,'serienaam')
            rtlitem = {'label': title,'TimeStamp': TimeStamp,'thumbnail': thumbnail,'path': movie,'classname': classname}
            rtlitemlist.append(rtlitem)
        self.items = rtlitemlist    
    
    def __is_uitzending(self,item):
        return item['classname'] == 'uitzending'
        
    def get_categories(self, url):
        if (self.items == 'leeg'):
            self.__items(url)
        aantaluitzendingen = [item for item in self.items if self.__is_uitzending(item)]
        terug = list()
        terug.append({        
            'keuze': 'afleveringen',
            'selected': True,
            'title': 'uitzendingen: (' + str(len(aantaluitzendingen)) + ')', ##aantal uitzendingen
            'url': url, ##url met alle items
        })
        terug.append({        
            'keuze': 'alles',
            'selected': False,
            'title': 'alles: (' + str(len(self.items)) + ')', ##aantal alles
            'url': url, ##url met alle items
        })
        return terug
        
    def __movie_trans(self, movie_url, mp4low):
        movie = movie_url        
        if (mp4low):
            beginmovie = movie.find('/components')
            if (beginmovie != -1):
                endemovie = movie.find('.m3u8',beginmovie)
                movie = 'http://pg.us.rtl.nl//rtlxl/network/a2t/progressive' + movie[beginmovie:endemovie] + '.mp4'
        return movie        

    def get_items(self, url, alles, mp4low):
        if (self.items == 'leeg'):
            self.__items(url)    
        items = [self.__build_item(i,alles, mp4low) for i in self.items]
        items = sorted(items, key=lambda x: x['label'], reverse=False)
        if (alles):
            return items
        return [item for item in items if self.__is_uitzending(item)]

    def __build_item(self, post, alles, mp4low):    
        ##item op tijd gesorteerd zodat ze op volgorde staan.
        if (alles):
            label = '(' + post['TimeStamp'].split('T')[1] + ') - ' + post['label'] + ' ('+post['classname']+')'
        else:
            label = '(' + post['TimeStamp'].split('T')[1] + ') - ' + post['label']
        item = {
            'label': label,
            'classname': post['classname'],
            'date': self.__stringnaardatumnaarstring(post['TimeStamp']),
            'path': self.__movie_trans(post['path'], mp4low),
            'thumbnail': post['thumbnail'],
        }
        return item       

    def __stringnaardatumnaarstring(self, datumstring):
        b = datetime(*(time.strptime(datumstring.split('T')[0], "%Y-%m-%d")[0:6]))
        return b.strftime("%d-%m-%Y")
