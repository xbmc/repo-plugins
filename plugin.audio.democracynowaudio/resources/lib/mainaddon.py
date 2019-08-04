import requests
import re
from bs4 import BeautifulSoup

def get_soup1(URL1):
    """
    @param: URL of site to be scraped
    """
    page = requests.get(URL1)
    soup1 = BeautifulSoup(page.text, 'html.parser')
    print "type: ", type(soup1)
    return soup1
get_soup1("https://www.democracynow.org/podcast.xml")


def get_playable_podcast(soup1):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup1.find_all('item'):
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

#            desc = content.find('description')
#            desc = desc.get_text()

#            thumbnail = content.find('itunes:image')
#            thumbnail = thumbnail.get('href')

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
#                'desc': desc,
                'thumbnail': "/home/osmc/.kodi/addons/plugin.audio.democracynowaudio/resources/media/icon.jpg"
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
#            'info': podcast['desc'],
            'is_playable': True,
    })
    return items


def get_playable_podcast1(soup1):
    """
    @param: parsed html page            
    """
    subjects = []
    for content in soup1.find_all('item', limit=6):
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

#            desc = content.find('description')
#            desc = desc.get_text()

#            thumbnail = content.find('itunes:image')
#            thumbnail = thumbnail.get('href')
        except AttributeError:
            continue
             
        item = {
                'url': link,
                'title': title,
#                'desc': desc,
                'thumbnail': "/home/osmc/.kodi/addons/plugin.audio.democracynowaudio/resources/media/icon.jpg"
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
#            'info': podcast['desc'],
            'is_playable': True,
    })

    return items
