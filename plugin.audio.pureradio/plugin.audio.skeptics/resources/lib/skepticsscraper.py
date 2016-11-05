import requests
import re
from bs4 import BeautifulSoup as bs

BASE_URL = 'http://www.theskepticsguide.org'

def get_soup(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')

    return soup

def get_latest_podcast(url):
    # get html
    soup = get_soup(url)

    # parse html for useful links 
    content = soup.find('div', {'class': 'podcasts-detail'})
    content = content.find_all('li')
    
    output = []

    for i in content:
        try:
            path = i.find_all('a')[2].get('href')
            path = BASE_URL + path
            
            if not path:
                break 

            label = i.find('a')
            label = i.get_text()
            label = re.search('Episode(.*)$', label).group(0)
            
            img = i.find('img').get('src')

        except IndexError:
            continue
        
        items = {
                'label': label,
                'path': path,
                'thumbnail': img,
        }

        output.append(items)

    return output

def get_podcast_content(url):
    soup = get_soup(url)
    content = soup.find('div', {'class': 'podcast-detail'})

    title = content.find('h1').get_text()
    
    img = content.find('div', {'class': 'podcast-image'})
    img = img.find('img').get('src')

    path = content.find('div', {'class': 'podcast-actions noPrint'})
    path = path.find('a').get('href')

    specific_content = soup.find_all('div', {'class': 'podcast-segment'})

    output = []
    word = ''
    for i in specific_content:
        find_word = i.find('h3').get_text()

        if """What's the Word""" in find_word:
            word = i.find('span', {'class': 'podcast-item-value'}).get_text()
        if "Skeptical Quote of the Week" in find_word:
            quote = i.find('span', {'class': 'podcast-item-value'}).get_text()
    
    items = {
        'title': title,
        'path': path,
        'img': img,
        'word': word,
        'quote': quote,
    }

    output.append(items)

    return output

def get_news_items(url):
    soup = get_soup(url)
    content = soup.find_all('div', {'class': 'podcast-segment'})
    
    news_items = []
    for i in content:
        find_word = i.find('h3').get_text()

        if "News Items" in find_word:
            items = i.find_all('li')
            for k in items:
                news_label = k.find('span', {'class': 'podcast-item-label'}).get_text()
                news_link = k.find('span', {'class': 'podcast-item-value'}).get_text()
                
                items = {
                    'news_label': news_label,
                    'news_link': news_link,
                }

                news_items.append(items)

    return news_items

def get_podcast_archive(url):
    soup = get_soup(url)
    content = soup.find_all('li', {'class': 'alt'})
    
    output = []
    for i in content:
        archive = i.find('a')['href']
        if 'http' in archive:
            label = i.find('div', {'class': 'podcasts-number'})
            label = label.get_text()
         
            path = i.find('a')['href']

            items = {
                'label': label,
                'path': path,
            }

            output.append(items)

    return output
