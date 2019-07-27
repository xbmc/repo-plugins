import requests
import re
from bs4 import BeautifulSoup

def get_soup(url):
    """
    @param: url of site to be scraped
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    print "type: ", type(soup)
    return soup

get_soup("http://feeds.thisiscriminal.com/CriminalShow")


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

            title = content.find('title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()
            
            thumbnail = content.find('itunes:image')
            thumbnail = thumbnail.get('href')

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail
        }
        
        #needto check that item is not null here
        subjects.append(item) 
    
    return subjects


def get_podcast_heading(soup):
    """
    @para: parsed html page
    """
    subjects = []
    
    for content in soup.find_all('item'):    
        
        link = content.find('enclosure')
        link = link.get('url')
        print "\n\nLink: ", link

        title = content.find('title')
	title = title.get_text()

        desc = content.find('itunes:subtitle')
        desc = desc.get_text()

        thumbnail = content.find('itunes:image')
        thumbnail = thumbnail.get('href')
        
        item = { 
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail
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


def get_new_to_criminal(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail
        }
        
    subjects.append(item) 
    
    return subjects

def compile_new_to_criminal(compile_ntc):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = [{
		    'label': 'Episode 85: The Manual',
        	    'thumbnail': '/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/85.png',
        	    'path': 'https://dts.podtrac.com/redirect.mp3/dovetail.prxu.org/criminal/51289384-3c02-410d-8a40-5ec7a0ac42a6/Episode_85_The_Manual_Part_1.mp3',
        	    'info': 'Description TEXT HERE',
        	    'is_playable': True},
           	    {'label': 'Episode 59: In Plain Sight',
        	    'thumbnail': '/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/59.png',
        	    'path': 'https://dts.podtrac.com/redirect.mp3/dovetail.prxu.org/criminal/cfea1c64-4cda-47f7-b0c1-f7c945d71714/Episode_59__In_Plain_Sight.mp3',
        	    'info': 'Description TEXT HERE',
        	    'is_playable': True},
		    {'label': 'Episode 51: Money Tree',
        	    'thumbnail': '/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/51.png',
        	    'path': 'https://dts.podtrac.com/redirect.mp3/dovetail.prxu.org/criminal/058d60c0-b85e-497a-8e8c-46ec039a2483/01_Episode_51__Money_Tree.mp3',
        	    'info': 'Description TEXT HERE',
        	    'is_playable': True},
		    {'label': 'Episode 1: Animal Instincts',
        	    'thumbnail': '/home/osmc/.kodi/addons/plugin.audio.criminalpodcast/resources/media/1.png',
        	    'path': 'https://dts.podtrac.com/redirect.mp3/dovetail.prxu.org/criminal/a3e66eb8-6268-4435-a411-3f158ec9106a/Ep._1__Animal_Instincts.mp3',
        	    'info': 'Description TEXT HERE',
        	    'is_playable': True},
]

    return items


def get_latest_episode(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup.find('item'):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()
            
            thumbnail = content.find('itunes:image')
            thumbnail = thumbnail.get('href')

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail
        }
        
        subjects.append(item) 
    
    return subjects


def compile_latest_episode(compile_latest):
    """
    @para: list containing dict of key/values pairs for playable podcasts
    """
    items = []

    for podcast in compile_latest:
     	items({
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

    for content in soup.find_all('item', limit=1):
        
        try:        
            link = content.find('enclosure')
            link = link.get('url')
            print "\n\nLink: ", link

            title = content.find('title')
            title = title.get_text()

            desc = content.find('itunes:subtitle')
            desc = desc.get_text()
            
            thumbnail = content.find('itunes:image')
            thumbnail = thumbnail.get('href')

        except AttributeError:
            continue
              
        item = {
                'url': link,
                'title': title,
                'desc': desc,
                'thumbnail': thumbnail
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

