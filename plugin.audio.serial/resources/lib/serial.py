import requests
import re
import urllib2
from bs4 import BeautifulSoup as bs


def get_soup(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')

    return soup


def get_podcast_s1(url):
    soup = get_soup(url)
    content = soup.find_all('div', {'class': 'node node-episode node-promoted node-teaser view-teaser season-1 live clearfix'})
    
    output = []
    for i in content:
        label = i.get_text().strip() 

        path = i.find('a', {'class': 'play'})['data-audio']
    
        item = {
            'label': label,
            'path': path,
        }

        output.append(item)

    return output


def get_podcast_s2(url):
    soup = get_soup(url)
    content = soup.find_all('div', {'class': 'wrapper'})
    
    output = []
    content = content [:-1]
    for i in content:
        label = i.find('div', {'class': 'episode'}).get_text()

        path = i.find('a', {'class': 'play'})['data-audio']
      
        item = {
            'label': label,
            'path': path,
        }

        output.append(item)
    return output
