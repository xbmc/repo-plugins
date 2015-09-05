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

get_soup("http://abc.net.au/radionational/podcasts")

def get_playable_podcast(soup):
    """
    @param: parsed html page            
    """
    subjects = []

    for content in soup.find_all('div', class_= "cs-teaser"):
        
        try:        
            link = content.find('a', {'class': 'ico ico-download'})
            link = link.get('href')
            print "\n\nLink: ", link

            title = content.find('h3', {'class': 'title'})
            title = title.get_text()

            desc = content.find('div', {'class': 'summary'})
            desc = desc.get_text()
            
     
            thumbnail = content.find('img')
            thumbnail = thumbnail.get('src')
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
    
    for content in soup.find_all('div', class_= 'header'):    
        
        link = content.find('a')
        link = link.get('href')
        link = "http://abc.net.au" + link 

        title = content.find('h3')
        title = title.get_text()
        
        item = { 
                'url': link,
                'title': title
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
