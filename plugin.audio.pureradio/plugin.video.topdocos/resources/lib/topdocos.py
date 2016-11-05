from bs4 import BeautifulSoup as bs
import requests
import re


def get_soup(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')
    
    return soup


def get_categorys(url):
    soup = get_soup(url)
    content = soup.find('nav', {'class': 'module clear'})
    content = content.find_all('a')
    
    output = []

    for i in content:
        label = i.get_text()

        path = i.get('href')

        items = {
            'label': label,
            'path': path,
        }

        output.append(items)

    return output


def get_categorys_content(url):
    soup = get_soup(url)
    content = soup.find_all('article', {'class': 'module'})

    output = []

    for i in content:
        label = i.find('h2')
        label = label.find('a').get('title')

        path = i.find('h2')
        path = path.find('a').get('href')
        
        thumb = i.find('img').get('src')

        items = {
                'label': label,
                'path': path,
                'thumbnail': thumb,
        }

        output.append(items)

    return output


def play_categorys(url):
    soup = get_soup(url)

    try:
        content = soup.find('meta', {'itemprop': 'embedUrl'})
    
        output = []
    
        path = content.get('content').split('embed/')[1]
        
        label = soup.find('meta', {'itemprop': 'name'})
        label = label.get('content')
    
        items = {
                'label': label,
                'path': path,
        }

    except AttributeError:
        items = {
                'label': 'Sorry content not avaliable.',
                'path': ' ',
        }
        
    output.append(items)
    
    return output   


def get_section(url, section):
    soup = get_soup(url)
    content = soup.find_all('section', {'class': 'module'})
   
    output = []

    for i in content:
        current_section = i.find('h3').get_text().lower()
        
        if section in current_section:  
            content = i.find_all('li')
            
            for i in content:
                try:
                    label_path = i.find('a')
                    label = label_path.get('title')
                    print label
                    path = label_path.get('href')
                
                    thumbnail = i.find('img').get('src')

                    items = {
                        'label': label,
                        'path': path,
                        'thumbnail': thumbnail,
                    }
                
                except AttributeError:
                    continue

                output.append(items)
    
    return output

get_section('http://topdocumentaryfilms.com/', 'highest rated')
