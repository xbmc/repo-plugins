'''
    resources.lib.uzg
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching Uitzendinggemist(NPO)
   
    :license: GPLv3, see LICENSE.txt for more details.

    Uitzendinggemist (NPO) = Made by Bas Magre (Opvolger)    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

'''
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, Request    
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, Request    
import re ,time ,json
from datetime import datetime

class Uzg:
        def __overzicht(self):        
            req = Request('http://apps-api.uitzendinggemist.nl/series.json')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urlopen(req)
            link=response.read()
            response.close()
            json_data = json.loads(link)
            uzgitemlist = list()
            for serie in json_data:
                uzgitem = {
                    'label': serie['name'],
                    'nebo_id': serie['nebo_id'],
                    'thumbnail': serie['image'],
                    'genres': serie['genres'],
                    'plot': serie['description'],
                    'studio': ', '.join(serie['broadcasters']),
                }
                uzgitemlist.append(uzgitem)                
            return sorted(uzgitemlist, key=lambda x: x['label'], reverse=False)
            
        def __items(self, nebo_id):
            req = Request('http://apps-api.uitzendinggemist.nl/series/'+nebo_id+'.json')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urlopen(req)
            link=response.read()
            response.close()
            json_data = json.loads(link)
            uzgitemlist = list()
            for aflevering in json_data['episodes']:
                urlcover = ''
                if aflevering['stills']:
                    urlcover = aflevering['stills'][0]['url']
                uzgitem = { 'label': aflevering['name']
                            , 'count': int(aflevering['broadcasted_at'])
                            , 'aired': datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y-%m-%d')
                            , 'premiered': datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y-%m-%d')
                            , 'date': datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%d-%m-%Y')
                            , 'year': datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y')
                            , 'TimeStamp': datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y-%m-%dT%H:%M')
                            , 'thumbnail': urlcover
                            , 'genres': aflevering['genres']
                            , 'duration': aflevering['duration']
                            , 'serienaam': json_data['name']
                            , 'plot': aflevering['description']
                            , 'studio': ', '.join(aflevering['broadcasters'])
                            , 'whatson_id': aflevering['whatson_id']}
                uzgitemlist.append(uzgitem)
                #print(uzgitem['date'])
            return uzgitemlist

        def __get_data_from_url(self, url):
            req = Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urlopen(req)
            data=response.read()
            response.close()
            return data    

        def get_ondertitel(self, whatson_id):
            return 'https://tt888.omroep.nl/tt888/'+whatson_id
            
        def get_play_url(self, whatson_id):
            ##token aanvragen
            data = self.__get_data_from_url('http://ida.omroep.nl/app.php/auth')
            token = re.search(r'token\":"(.*?)"', data.decode('utf-8')).group(1)
            ##video lokatie aanvragen
            data = self.__get_data_from_url('http://ida.omroep.nl/app.php/'+whatson_id+'?adaptive&adaptive=yes&part=1&token='+token)
            json_data = json.loads(data)
            ##video file terug geven vanaf json antwoord
            streamdataurl = json_data['items'][0][0]['url']
            streamurl = str(streamdataurl.split("?")[0]) + '?extension=m3u8'
            data = self.__get_data_from_url(streamurl)
            json_data = json.loads(data)
            url_play = json_data['url']
            return url_play
            
        def get_overzicht(self):
            return self.__overzicht()         


        def get_items(self, nebo_id):
            items = self.__items(nebo_id)
            show_time_in_label = False
            
            for item in items:
                for ref in items:
                    if (item['date'] == ref['date'] and item['whatson_id'] != ref['whatson_id']):
                        # Er zijn meerdere afleveringen op dezelfde
                        # dag: toon de tijd in het label.
                        show_time_in_label = True

            return [self.__build_item(i, show_time_in_label) for i in items]
    
        def __build_item(self, post, show_time_in_label):    
            ##item op tijd gesorteerd zodat ze op volgorde staan.
            if (len(post['label']) == 0):
                titelnaam = post['serienaam']
            else:
                titelnaam = post['label']

            if (show_time_in_label):
                titelnaam += ' (' + post['TimeStamp'].split('T')[1] + ')'

            item = post
            item['label'] = titelnaam
            return item

        def __stringnaardatumnaarstring(self, datumstring):
            b = datetime(*(time.strptime(datumstring.split('T')[0], "%Y-%m-%d")[0:6]))
            return b.strftime("%d-%m-%Y")
