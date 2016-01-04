import requests
import re
from bs4 import BeautifulSoup as bs

BASE_URL = "http://www.abc.net.au"


def get_audio(url):

    page = requests.get(url)
    soup = bs(page.text, 'html.parser')

    output = []

    for content in soup.find_all('div', class_="cs-teaser"):
        try: 
            link = content.find('a', {'class': 'ico ico-download'})
            link = link.get('href')
            
            title = content.find('h3', {'class': 'title'})
            title = title.get_text()
            
            desc = content.find('div', {'class': 'summary'})
            desc = desc.get_text()
            desc = desc.split('\n')[1]
            
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
        
        output.append({
            'label': item['title'],
            'thumbnail': item['thumbnail'],
            'path': item['url'],
            'info': item['desc'],
            'is_playable': True,
        })
    
    return output


def get_subjects(url):
    
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')
    
    output = []
    content = soup.find('ol', {'class':'article-index'})
    content = content.find_all('a')
        
    for i in content:
        try:
            title = i.get_text()
            
            url = i.get('href')
            url = BASE_URL + url
        
        except AttributeError:
            continue

        item = {
                'title': title,
                'url': url
        }

        output.append(item)

    return output


def get_subjects_contents(url):

    page = requests.get(url)
    soup = bs(page.text, 'html.parser')

    output = []

    content = soup.find_all('div', {'class': 'cs-teaser'})
    
    for i in content:
        try:
            title = i.find('h3', {'class': 'title'})
            title = title.get_text()
            
            url = i.find('a')
            url = url.get('href')
            url = BASE_URL + url

            img = i.find('img')
            img = img.get('src')

        except AttributeError:
            continue
        
        item = {
                'title': title,
                'url': url,
                'img': img
        }
        
        output.append(item)

    return output


def get_playable_subjects(url):

    page = requests.get(url)
    soup = bs(page.text, 'html.parser')

    output = []

    content = soup.find('div', {'class': 'article'})
    
    url = content.find('ul', {'class': 'cs-has-media'})
    url = url.find('a')
    url = url.get('href')
    
    img = content.find('img')
    img = img.get('src')

    title = content.find('h1')
    title = title.get_text()
    
    item = {'title': title,
            'url': url,
            'img': img
    }
    
    output.append({
        'label': item['title'],
        'path': item['url'],
        'thumbnail': item['img'],
        'is_playable': True,
    })
    
    return output
