import requests
import re
from bs4 import BeautifulSoup

def get_soup0(url0):
    """
    @param: url of site to be scraped
    """
    page = requests.get(url0)
    soup0 = BeautifulSoup(page.text, 'html.parser')
    
    print "type: ", type(soup0)
    return soup0

get_soup0("http://api.spokenlayer.com/feed/channel/v1-intercept-news2-ext/3c9929b72538c12bd92ac6762f8d798b9d4e8cdca7692ea74f466061d01816cb")

def get_soup(url):
    """
    @param: url of site to be scraped
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    
    print "type: ", type(soup)
    return soup

get_soup("http://feeds.megaphone.fm/deconstructed")

def get_soup2(url2):
    """
    @param: url of site to be scraped
    """
    page = requests.get(url2)
    soup2 = BeautifulSoup(page.text, 'html.parser')
    
    print "type: ", type(soup2)
    return soup2

get_soup2("http://feeds.megaphone.fm/intercepted")

def get_soup3(url3):
    """
    @param: url of site to be scraped
    """
    page = requests.get(url3)
    soup3 = BeautifulSoup(page.text, 'html.parser')
    
    print "type: ", type(soup3)
    return soup3

get_soup3("https://rss.prod.firstlook.media/murderville/podcast.rss")


def get_playable_podcast0(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup.find_all('item'):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

            desc = content.find('description')
            desc = desc.get_text()

            thumbnail = content.find('itunes:image')
            thumbnail = thumbnail.get('href')

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail,
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_podcast0(playable_podcast0):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_podcast0:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items


def get_playable_podcast01(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup.find_all('item', limit=3):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

            thumbnail = content.find('itunes:image')
            thumbnail = thumbnail.get('href')

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail,
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_podcast01(playable_podcast01):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_podcast01:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'is_playable': True,
    })

    return items


def get_playable_podcast(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup.find_all('item'):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('itunes:title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': "https://static.megaphone.fm/podcasts/fcf98d00-1c11-11e8-bf47-4b460462a564/image/uploads_2F1544117246770-vb6r1xfm1ib-4762e5a8199166b03554b9b67a5d7bb2_2FDeconstructed_COVER-with-logo.png"
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_podcast(playable_podcast):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_podcast:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items


def get_playable_podcast1(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup.find_all('item', limit=3):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('itunes:title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': "https://static.megaphone.fm/podcasts/fcf98d00-1c11-11e8-bf47-4b460462a564/image/uploads_2F1544117246770-vb6r1xfm1ib-4762e5a8199166b03554b9b67a5d7bb2_2FDeconstructed_COVER-with-logo.png"
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_podcast1(playable_podcast1):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_podcast1:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items

def get_playable_intercepted(soup2):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup2.find_all('item'):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('itunes:title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': "https://static.megaphone.fm/podcasts/d5735a50-d904-11e6-8532-73c7de466ea6/image/uploads_2F1544117316918-ix7o6i7vnto-6a6e5ad7be02dd89be56d2081ae5e859_2FIntercepted_COVER-with-logo.png"
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_intercepted(playable_intercepted):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_intercepted:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items


def get_playable_intercepted1(soup2):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup2.find_all('item', limit=3):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('itunes:title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': "https://static.megaphone.fm/podcasts/d5735a50-d904-11e6-8532-73c7de466ea6/image/uploads_2F1544117316918-ix7o6i7vnto-6a6e5ad7be02dd89be56d2081ae5e859_2FIntercepted_COVER-with-logo.png"
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_intercepted1(playable_intercepted1):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_intercepted1:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items


def get_playable_murderGA(soup3):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup3.find_all('item'):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

            desc = content.find('itunes:summary')
            desc = desc.get_text()

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': "https://theintercept-static.imgix.net/usq/490edc26-8485-4094-a20c-dc4ce70207b1/1dcfad38-a2d0-4e29-a86b-4420b3980e4b.jpeg?auto=compress,format&cs=srgb&dpr=2&h=440&w=440&fit=crop&crop=faces%2Cedges&_=7f3dc1b866c965bc3eee2890e79e85c3"
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_murderGA(playable_murderGA):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_murderGA:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items


def get_playable_murderGA1(soup3):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup3.find_all('item', limit=3):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

            desc = content.find('itunes:summary')
            desc = desc.get_text()

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': "https://theintercept-static.imgix.net/usq/490edc26-8485-4094-a20c-dc4ce70207b1/1dcfad38-a2d0-4e29-a86b-4420b3980e4b.jpeg?auto=compress,format&cs=srgb&dpr=2&h=440&w=440&fit=crop&crop=faces%2Cedges&_=7f3dc1b866c965bc3eee2890e79e85c3"
        }
        
        subjects.append(item) 
    
    return subjects


def compile_playable_murderGA1(playable_murderGA1):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in playable_murderGA1:
        items.append({
            'label': podcast['title'],
            'thumbnail': podcast['thumbnail'],
            'path': podcast['url'],
            'info': podcast['desc'],
            'is_playable': True,
    })

    return items

