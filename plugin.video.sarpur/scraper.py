#!/usr/bin/env python
import urllib2, re, os, xbmcaddon
from BeautifulSoup import BeautifulSoup
from datetime import datetime
import simplejson as json

addon = xbmcaddon.Addon(id='plugin.video.sarpur')
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
data_path = os.path.join(addon.getAddonInfo('path'), 'resources','data')
showtreefile_location = os.path.join(data_path,'showtree.dat')
tabfile_location = os.path.join(data_path,'tabs.dat')
showtree = [] #All the shows under the thaettir menu
tabs = [] #Tabs in the Sarpur main page


def fetch_page(url):
    "Download URL"
    req = urllib2.Request(url.replace(' ','%20')) #Doesn't seem to like spaces
    req.add_header('User-Agent', user_agent)
    response = urllib2.urlopen(req)
    html = response.read()
    response.close()
    return html

def get_tabs():
    "populate latest_groups"
    html = fetch_page("http://www.ruv.is/sarpurinn")
    soup = BeautifulSoup(html)
    div = soup.find("div", attrs={"class": "menu-block-ctools-menu-sarpsmynd-1 menu-name-menu-sarpsmynd parent-mlid-_active:0 menu-level-2"})
    for li in div.findAll("li"):
        tabs.append((li.a.contents[0], li.a['href']))


def parse_show_index(html):
    "Take the html from the show index and create a data structure"
    global showtree
    showtree = []
    soup = BeautifulSoup(html)
    stodvar = soup.findAll("div", attrs={"style":re.compile("width:280px;float:left;.*")}) #0: Stod 1 #1: Ras 1 #2: Ras 2
    
    for i,stod in enumerate(stodvar):
        showtree.append({"name":stod.h1.contents[0], "categories":[]})
        for flokkur in stod.div:
            if hasattr(flokkur, 'name'):
                if flokkur.name == 'h2':
                    showtree[i]["categories"].append({"name":flokkur.contents[0], "shows":[]})
                elif flokkur.name == 'div':
                    for show in flokkur.findAll("div"):
                        showtree[i]["categories"][-1]['shows'].append((show.a.contents[0], show.a['href']))
    
def get_episodes(url):
    "Find playable files on a shows page"
    episodes = []
    html = fetch_page(url)
    soup = BeautifulSoup(html)
    for episode in soup.findAll("a", attrs={"title": re.compile("Spila . Sarp")}):
        episodes.append((episode.contents[0], episode['href']))

    if episodes: #Venjulegt utlit
        return episodes

    #Hitt utlitid
    innri = soup.find("div", attrs={"class": "kubbur ahugavert"})
    if innri:
        for episode in innri.findAll("li"):
            url = 'http://www.ruv.is%s' % episode.div.a['href']
            episodes.append((episode.span.contents[0], url))

    if not episodes and 'dagskra' in url:
        #Sumir thaettir eru a dagskra.ruv.is i listanum en notandinn er faerdur a www.ruv.is
        return get_episodes(url.replace('dagskra','www'))
    return episodes

def get_latest_episodes(url):
    "Find playable files on the 'recent' pages"
    html = fetch_page(url)
    soup = BeautifulSoup(html)

    spilari = soup.find("div", attrs={'class':'kubbur sarpefst'})
    #dags = re.search(r'\d{1,2}\. \w{3} \d{4} \| \d\d:\d\d',repr(spilari), re.UNICODE).group()
    featured = spilari.h1.contents[0]

    episodes = [(featured, url)]

    for li in soup.find("ul", attrs={'class':'sarplisti'}).findAll("li"):
        title = "%s %s" % (li.h4.a.contents[0], li.em.contents[0])
        pageurl = u"http://www.ruv.is%s" % li.h4.a['href']
        episodes.append((title , pageurl))

    return episodes

def get_stream_info(page_url):
    "Get a page url and finds the url of the rtmp stream"
    html = fetch_page(page_url)

    access_point_hyperlink = re.search('"http://load.cache.is.*?"', html).group()[1:-1]
    javascript = fetch_page(access_point_hyperlink)
    access_point = re.search('"(.*?)"', javascript).group(1)
    path = re.search('ruv(vod)?\?key=\d+', html).group()
    rtmp_url = "rtmp://%s/%s" % (access_point, path)
    playpath = re.findall("\'file\': \'(.*?)\'", html)[-1] #.group(1)

    return {'playpath': playpath, 'rtmp_url': rtmp_url}

def update_index():
    "Update the data file with the show list"
    print "Update Sarpur data files."
    html = fetch_page('http://dagskra.ruv.is/thaettir/')
    parse_show_index(html)
    
    #showtree.append(time.time())
    json.dump(showtree, file(showtreefile_location,'wb'))
    get_tabs()
    json.dump(tabs, file(tabfile_location,'wb'))

def get_podcast_shows():
    """Gets the names and rss urls of all the Podcasts"""
    html = fetch_page("http://www.ruv.is/podcast")
    soup = BeautifulSoup(html)
    
    shows = []
    
    for ul in soup.findAll("ul", attrs={'class':'hladvarp-info'}):
        title = ul('li')[1].h4.contents[0]
        pageurl = ul('li')[4].a['href']
        shows.append((title , pageurl))
        
    return shows
    
def get_podcast_recordings(url):
    """Gets the dates and mp3 urls of all the Podcast recordings"""
    html = fetch_page(url)
    soup = BeautifulSoup(html)
    recordings = []
    
    for item in soup.findAll('item'):
        date = item.pubdate.contents[0]
        url = item.guid.contents[0]
        recordings.append((date,url))
    
    return recordings

## init
try:
    delta = datetime.now() - datetime.fromtimestamp(os.path.getmtime(showtreefile_location))
    if delta.days > 0:
        update_index()
    else:
        tabs = json.load(file(tabfile_location,'rb'))
        showtree = json.load(file(showtreefile_location,'rb'))
except OSError:
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    update_index()
except IOError:
    os.unlink(showtreefile_location)
    os.unlink(tabfile_location)
    update_index()




if __name__ == '__main__':
    #showtree = []; update_index()
    #print showtree[0]['categories']

    #get_tabs()
    #os.unlink(showtreefile_location)
    #os.unlink(tabfile_location)
    #update_index()
    #print showtree
    
    for stod in showtree:
        #print stod
        print stod['name'].encode('utf-8')

    #for flokkur in showtree[0]['categories']:
    #    print flokkur

    #for show in showtree[0]['categories'][0][u'shows']:
    #    print show[0].encode('utf-8')

    #print get_episodes("http://dagskra.ruv.is/opus")
    
    #print get_stream_info("http://www.ruv.is/ruv")
    #print get_stream_info("http://www.ruv.is/ras1")
    #print get_stream_info("http://www.ruv.is/sarpurinn/regina-osk/19012012")
    #print get_latest_episodes("http://www.ruv.is/sarpurinn/ras1")
    
    #get_tabs()
    #print tabs


