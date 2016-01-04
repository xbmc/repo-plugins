from bs4 import BeautifulSoup as bs
import re
import requests


URL = "http://www.youtube.com"
CHANNEL_URL = "http://www.youtube.com/user/vice/channels"


def get_shows(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser') 
    soup = soup.find('li', {'class': 'feed-item-container yt-section-hover-container browse-list-item-container branded-page-box vve-check '}) 
    content = soup.find_all('div', {'class': 'yt-lockup clearfix  yt-lockup-channel yt-lockup-grid'})
    
    output = [] 
    
    for i in content:
        try:
            label = i.find('title')
            label = i.get_text()
            label = re.search(r'.+?(?=(- C))', label)
            label = label.group(0)

            path = i.find('a')
            path = path.get('href')
            path = URL + path

            thumbnail = i.img['data-thumb']

            items = {
                'label': label,
                'path': path,
                'thumbnail': thumbnail,
            }

            output.append(items)

        except AtrributeError:
            continue

    return output
    

def get_show_content(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')
    content = soup.find_all('div', {'class': 'yt-lockup-dismissable'})
    
    output = []
     
    for i in content:
        
        label = i.find('h3', {'class': 'yt-lockup-title '})
        label = label.find('a').get('title')
        
        path_thumb = i.find('a')

        path = path_thumb.get('href')
        path = re.search(r'\=(.*)', path).group(0)
        
        thumb = path_thumb.find('img').get('data-thumb')
        thumb = 'https:' + thumb

        items = {
                'label': label,
                'path': path,
                'thumbnail': thumb,
            }

        output.append(items)

    return output


def get_hbo_content(url):
    content = get_latest_content(url)
    
    match = 'HBO'
    
    output = []

    for i in content:
        if match in i['label']:     
         
            output.append(i)
    
    output = output[1:100]

    return output


def get_latest_content(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')
    content = soup.find_all('div', {'class': 'yt-lockup-dismissable'})
    
    output = []
     
    for i in content:
        
        label = i.find('h3', {'class': 'yt-lockup-title '})
        label = label.find('a').get('title')
        path_thumb = i.find('a')

        path = path_thumb.get('href')
        path = re.search(r'\=(.*)', path).group(0)

        thumb = i.find('img').get('src')
        thumb = 'https:' + thumb

        items = {
                'label': label,
                'path': path,
                'thumbnail': thumb,
            }

        output.append(items)

    return output
