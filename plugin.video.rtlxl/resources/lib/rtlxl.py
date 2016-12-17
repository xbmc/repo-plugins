'''
    resources.lib.leesrtlxl
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching RTLxl

    :copyright: (c) 2012 by Jonathan Beluch (Documentary.net xbmc addon)    
    :license: GPLv3, see LICENSE.txt for more details.

    RTLxl = Made by Bas Magre (Opvolger)    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

        adaptive progressive smooth

    ## low
	## http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az/output=xml
	## http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=a2t/fmt=progressive/ak=216992/output=xml/pg=1/
	## http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=abstract/pg=1/output=xml/ak=283771/sk=301653
	## http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=abstract/uuid=6937d7bb-bf40-4f51-9590-c2c8131bccc7/output=xml/
    ## http://pg.us.rtl.nl//rtlxl/network/a2t/progressive/components/videorecorder/28/283771/301653/6937d7bb-bf40-4f51-9590-c2c8131bccc7.ssm/6937d7bb-bf40-4f51-9590-c2c8131bccc7.mp4       

    http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az ## deze met a2t omdat deze geen drm doet!
    http://www.rtl.nl/system/s4m/vfd/version=2/d=pc/output=json/fun=az/fmt=smooth
    http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1
    http://www.rtl.nl/system/s4m/vfd/version=2/uuid=1b10429e-7dd9-3506-b558-0a3de42bae1e/fmt=adaptive/output=json/

'''
import urllib2, re, json
from operator import itemgetter, attrgetter
import time
from datetime import datetime
import xml.etree.ElementTree as ET

class RtlXL:
    def __init__(self):
        self.overzichtcache = 'leeg'
        self.items = 'leeg'
        self.videohost = ''
    
    def __gettextitem(self, element, elementnaam):
        el = element.find(elementnaam)
        if el is None:
            return ''
        return el.text
    
    def __overzicht(self):
        req = urllib2.Request('http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fmt=progressive/fun=az')
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
        req.add_header('Accept-Encoding', 'utf-8')
        response = urllib2.urlopen(req)
        jsonstring = response.read()
        response.close()
        json_data = json.loads(jsonstring)
        rtlitemlist = list()
        poster_base_url = json_data['meta']['poster_base_url']
        for serie in json_data['abstracts']:
            item = { 'label': serie['name'], 'url': serie['itemsurl'], 'thumbnail': poster_base_url + serie['coverurl'] }
            rtlitemlist.append(item)
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
        jsonstring = response.read()
        response.close()
        json_data = json.loads(jsonstring)
        rtlitemlist = list()
        cover_base_url = json_data['meta']['cover_base_url']
        for material in json_data['material']:
            rtlitem = {'label': '','TimeStamp': material['display_date'],'thumbnail': cover_base_url + material['image'], 'uuid': material['uuid'],'classname': material['classname']}
            for episode in json_data['episodes']:
                if episode['key'] == material['episode_key']:
                    rtlitem['label'] = episode['name']
            if material['episode_key']:
                rtlitemlist.append(rtlitem)
        self.items = rtlitemlist    
    
    def __is_uitzending(self,item):
        return item['classname'] == 'uitzending'

    def __heeft_url(self,item):
        return item['path']
        
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
        
    def __movie_trans(self, uuid, videotype):
        url = 'http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/uuid=' + uuid + '/fmt=' + videotype + '/output=json/'
        if videotype == 'progressive':
            url = 'http://www.rtl.nl/system/s4m/vfd/version=2/d=a2t/fun=abstract/uuid=' + uuid + '/fmt=' + videotype + '/output=json/'
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
        req.add_header('Accept-Encoding', 'utf-8')
        response = urllib2.urlopen(req)
        jsonstring = response.read()
        response.close()
        json_data = json.loads(jsonstring)
        if json_data['meta']['nr_of_videos_total'] == 0:
            return ''
        movie = json_data['meta']['videohost'] + json_data['material'][0]['videopath']
        return movie        

    def get_items(self, url, alles, videotype):
        if (self.items == 'leeg'):
            self.__items(url)    
        items = [self.__build_item(i,alles, videotype) for i in self.items]
        items = sorted(items, key=lambda x: x['label'], reverse=False)
        ## lege streams verwijderen
        items = [item for item in items if self.__heeft_url(item)]
        if (alles):
            return items
        return [item for item in items if self.__is_uitzending(item)]

    def __build_item(self, post, alles, videotype):    
        ##item op tijd gesorteerd zodat ze op volgorde staan.
        if (alles):
            label = post['label'] + ' ('+post['classname']+')'
        else:
            label = post['label']
        item = {
            'label': label,
            'classname': post['classname'],
            'date': self.__stringnaardatumnaarstring(post['TimeStamp']),
            'path': self.__movie_trans(post['uuid'], videotype),
            'thumbnail': post['thumbnail'],
        }
        return item       

    def __stringnaardatumnaarstring(self, datumstring):
        b = datetime.fromtimestamp(int(datumstring))
        return b.strftime("%d-%m-%Y")
