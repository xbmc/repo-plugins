from bs4 import BeautifulSoup as bs
import requests
import re


def get_soup(url):
    page = requests.get(url)
    soup = bs(page.text, 'html.parser')

    return soup


def get_latest(url):
    soup = get_soup(url)
    content = soup.find_all('div', {'class': 'yt-lockup-dismissable'})
    output = []
    
    for i in content:
        label_path = i.find('a', {'class': 'yt-uix-sessionlink yt-uix-tile-link  spf-link  yt-ui-ellipsis yt-ui-ellipsis-2'})
        label = label_path.get_text()
        
        path = label_path.get('href')
        path = re.search(r'\=(.*)', path).group(0)
       
        img = i.find('img')['src']
        img = 'http:' + img
        
        item = {
            'label': label,
            'path': path,
            'thumbnail': img,
        }

        output.append(item)

    return output
