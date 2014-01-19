'''
    resources.lib.leesrtlxl
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching RTLxl

    :copyright: (c) 2012 by Jonathan Beluch (Documentary.net xbmc addon)    
    :license: GPLv3, see LICENSE.txt for more details.

    RTLxl = Made by Bas Magre (Opvolger)    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

'''
import urllib2,re
from operator import itemgetter, attrgetter
import time
from datetime import datetime

#
# Item class
#
class RtlItem:
        def __init__(self, init_title, init_TimeStamp, init_thumbnail, init_samenvattingkort, init_movie, init_classname,init_serienaam) :
            self.title  = init_title 
            self.TimeStamp = init_TimeStamp
            self.thumbnail = init_thumbnail
            self.samenvattingkort = init_samenvattingkort
            self.movie = init_movie
            self.classname = init_classname
            self.serienaam = init_serienaam

#
# OverzichtItem class
#
class RtlOverzichtItem:
        def __init__( self,init_serienaam,init_itemsperserie_url ,init_seriescoverurl) :
            self.serienaam = init_serienaam
            self.itemsperserie_url  = init_itemsperserie_url 
            self.seriescoverurl = init_seriescoverurl
#
# RtlBaseData class
#
class RtlBaseData:
        #
        # Init
        #
        def __init__( self,init_url='http://www.rtl.nl/system/s4m/ipadfd/d=ipad/') :
            self.url = init_url

        def ophalen(self):
            req = urllib2.Request(self.url)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            rtlitemlist = list()
            for match in re.compile('<serieitem>(.+?)</serieitem>').findall(link):
                itemsperserie_url = re.compile('<itemsperserie_url>(.+?)</itemsperserie_url>').findall(match)
                serienaam = re.compile('<serienaam>(.+?)</serienaam>').findall(match)
                seriescoverurl = re.compile('<seriescoverurl>(.+?)</seriescoverurl>').findall(match)
                rtlitem = RtlOverzichtItem(serienaam[0],itemsperserie_url[0],seriescoverurl[0])
                rtlitemlist.append(rtlitem)
            return sorted(rtlitemlist, key=attrgetter('serienaam'))

#
# RtlItemData class
#
class RtlItemData:
        #
        # Init
        #
        def __init__( self,init_url) :
            self.url = init_url

        def ophalenitems(self):
            req = urllib2.Request(self.url)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            rtlitemlist = list()
            for match in re.compile('<item>(.+?)</item>').findall(link):
                TimeStamp = re.compile('<TimeStamp>(.+?)</TimeStamp>').findall(match)
                classname = re.compile('<classname>(.+?)</classname>').findall(match)
                samenvattingkort = re.compile('<samenvattingkort>(.+?)</samenvattingkort>').findall(match)
                thumbnail = re.compile('<thumbnail>(.+?)</thumbnail>').findall(match)
                title = re.compile('<title>(.+?)</title>').findall(match)
                movie = re.compile('<movie>(.+?)</movie>').findall(match)
                serienaam = re.compile('<serienaam>(.+?)</serienaam>').findall(match)
                if len(title) == 1 and len(TimeStamp) == 1 and len(thumbnail) == 1 and len(samenvattingkort) == 1 and len(movie) == 1 and len(classname) == 1 and len(serienaam) == 1:
                    rtlitem = RtlItem(title[0],TimeStamp[0],thumbnail[0],samenvattingkort[0],movie[0],classname[0],serienaam[0])
                    rtlitemlist.append(rtlitem)
            return rtlitemlist

def get_overzicht():
    rtloverzicht = RtlBaseData()
    return [{        
        'title': show.serienaam, ##serienaam zoals RTL NIEUWS
        'url': show.itemsperserie_url, ##url met alle items
        'thumbnail': show.seriescoverurl ##cover url
    } for show in rtloverzicht.ophalen()]            

def get_categories(url):
    items = get_items_alles(url)
    aantaluitzendingen = [item for item in items if _is_uitzending(item)]
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
        'title': 'alles: (' + str(len(items)) + ')', ##aantal alles
        'url': url, ##url met alle items
    })
    return terug

def get_items_uitzending(url):
    ##filter op alles, alleen uitzendingen weergeven
    rtlshowitems = RtlItemData(url)
    items = [_build_item(i,False) for i in rtlshowitems.ophalenitems()]
    return [item for item in items if _is_uitzending(item)]

def _is_uitzending(item):
    return item['classname'] == 'uitzending'
    
def get_items_alles(url):
    rtlshowitems = RtlItemData(url)
    items = [_build_item(i,True) for i in rtlshowitems.ophalenitems()]
    return items

def _build_item(post,alles):    
    ##item op tijd gesorteerd zodat ze op volgorde staan.
    if (alles):
        title = '(' + post.TimeStamp.split('T')[1] + ') - ' + post.title + ' ('+post.classname+')'
    else:
        title = '(' + post.TimeStamp.split('T')[1] + ') - ' + post.title

    item = {
        'title': title,
        'excerpt': post.samenvattingkort,
        'content': post.samenvattingkort,
        'classname': post.classname,
        'date': stringnaardatumnaarstring(post.TimeStamp),
        'video_url': post.movie,
        'thumbnail': post.thumbnail,
        'serienaam': post.serienaam,
    }
    return item       

def stringnaardatumnaarstring(datumstring):
    b = datetime(*(time.strptime(datumstring.split('T')[0], "%Y-%m-%d")[0:6]))
    return b.strftime("%d-%m-%Y")
