import requests
from BeautifulSoup import BeautifulSoup
import re

ABC_URL = "http://abc.net.au/radionational/rntv"


def get_videos():
    """Return videos from Radio National's RNTV website"""
    url = ABC_URL
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    output = []

    content = soup.find('div', {'id': 'content'})
    section_items = content.find('div', 'section').findAll('li')

    for i in section_items:
        try:
            title = i.find('h3', 'title').a.text
        except AttributeError:
            continue

        title = re.sub('&#039;', "'", title)

        thumbnail = i.find('div', 'figure').find('img')['src']
        url = i.find('div', 'summary').find('a')['href']
        youtube_id = url.split('/')[-1]
        description = i.find('div', 'summary').findAll('p')[1].text

        item = {
            'title': title,
            'thumbnail': thumbnail,
            'youtube_id': youtube_id,
            'description': description
        }

        output.append(item)

    return output
