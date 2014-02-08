'''
    resources.lib.uzg
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching Uitzendinggemist(NPO)

    :copyright: (c) 2012 by Jonathan Beluch (Documentary.net xbmc addon)    
    :license: GPLv3, see LICENSE.txt for more details.

    Uitzendinggemist (NPO) = Made by Bas Magre (Opvolger)    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

'''
import urllib2,re
from operator import itemgetter, attrgetter
from datetime import datetime
import time
import json

#
# Item class
#
class UzgItem:
        def __init__(self, init_title, init_TimeStamp, init_thumbnail, init_classname,init_serienaam, init_playerid) :
            self.title  = init_title 
            self.TimeStamp = init_TimeStamp
            self.thumbnail = init_thumbnail
            self.classname = init_classname
            self.serienaam = init_serienaam
            self.playerid = init_playerid

#
# OverzichtItem class
#
class UzgOverzichtItem:
        def __init__( self,init_serienaam,init_nebo_id,init_seriescoverurl) :
            self.serienaam = init_serienaam
            self.nebo_id  = init_nebo_id 
            self.seriescoverurl = init_seriescoverurl
#
# uzgBaseData class
#
class UzgBaseData:
        #
        # Init
        #
        def __init__( self,init_url='http://apps-api.uitzendinggemist.nl/series.json') :
            self.url = init_url

        def ophalen(self):
            req = urllib2.Request(self.url)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            json_data = json.loads(link)
            uzgitemlist = list()
            for serie in json_data:
                uzgitem = UzgOverzichtItem(serie['name'],serie['nebo_id'],serie['image'])
                uzgitemlist.append(uzgitem)
            return sorted(uzgitemlist, key=attrgetter('serienaam'))

#
# UzgItemData class
#
class UzgItemData:
        #
        # Init
        #
        def __init__( self,init_nebo_id) :
            self.nebo_id = init_nebo_id

        def ophalenitems(self):
            req = urllib2.Request('http://apps-api.uitzendinggemist.nl/series/'+self.nebo_id+'.json')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            json_data = json.loads(link)
            uzgitemlist = list()
            for aflevering in json_data['episodes']:
                urlcover = ''
                if not aflevering['stills']:
                    urlcover = ''
                else:
                    urlcover = aflevering['stills'][0]['url']
                uzgitem = UzgItem(aflevering['name'],datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y-%m-%dT%H:%M:%S'),urlcover,'uitzending',json_data['name'],aflevering['whatson_id'])
                uzgitemlist.append(uzgitem)
            return uzgitemlist


def get_data_from_url(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    return data    

def get_ondertitel(playerid):
	return 'http://apps-api.uitzendinggemist.nl/webvtt/'+playerid+'.webvtt'
	
def get_url(playerid):
    ##token aanvragen
    data=get_data_from_url('http://ida.omroep.nl/npoplayer/i.js')
    token = re.compile('.token\s*=\s*"(.*?)"', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
    ##video lokatie aanvragen
    data = get_data_from_url('http://ida.omroep.nl/odi/?prid='+playerid+'&puboptions=adaptive&adaptive=yes&part=1&token='+token)
    ## old not working any more data = get_data_from_url('http://ida.omroep.nl/odiplus/?prid='+playerid+'&puboptions=adaptive&adaptive=yes&part=1&token='+token)
    json_data = json.loads(data)
    ##video file terug geven vanaf json antwoord
    streamdataurl = json_data['streams'][0]
    streamurl = str(streamdataurl.split("?")[0]) + '?extension=m3u8'
    data = get_data_from_url(streamurl)
    json_data = json.loads(data)
    url_play = json_data['url']
    return url_play


def get_overzicht():
    uzgoverzicht = UzgBaseData()
    return [{        
        'title': show.serienaam,
        'nebo_id': show.nebo_id, 
        'thumbnail': show.seriescoverurl ##cover url
    } for show in uzgoverzicht.ophalen()]            


def get_items_uitzending(url):
    ##filter op alles, alleen uitzendingen weergeven
    uzgshowitems = UzgItemData(url)
    return [_build_item(i,False) for i in uzgshowitems.ophalenitems()]
    
def _build_item(post,alles):    
    ##item op tijd gesorteerd zodat ze op volgorde staan.
    if (len(post.title) == 0):
        titelnaam = post.serienaam
    else:
        titelnaam = post.title

    item = {
        'title': '(' + post.TimeStamp.split('T')[1] + ') - ' + titelnaam,
        'classname': post.classname,
        'date': stringnaardatumnaarstring(post.TimeStamp),
        'thumbnail': post.thumbnail,
        'serienaam': post.serienaam,
        'playerid': post.playerid,
    }
    return item       

def stringnaardatumnaarstring(datumstring):
    b = datetime(*(time.strptime(datumstring.split('T')[0], "%Y-%m-%d")[0:6]))
    return b.strftime("%d-%m-%Y")
