import requests

from xbmcswift2 import xbmc

from BeautifulSoup import BeautifulSoup


BASE_URL = 'http://codigofacilito.com'
T_ERROR_TITLE = 30001
T_ERROR_SERVER = 30002
T_ERROR_COURSES = 30003
T_ERROR_VIDEOS = 30004

def log(message):
    xbmc.log(message)

def alert(title, message):
    xbmc.executebuiltin("Notification(" + title + "," + message + ")")

def get_courses():
    url = BASE_URL + '/cursos'
    page = requests.get(url , verify=False)
    soup = BeautifulSoup(page.content)
    output = []

    for article in soup.find('section').findAll('article'):
        anchor = article.find('h3').find('a', {'class': 'blue'})
        text = anchor.text.encode('utf8')
        link = anchor.get('href')
        img  = article.find('img').get('src')
        videos = article.find('i', {'class': 'mdi-av-play-arrow'})
        if videos is not None:
            videos = ' (' + videos.parent.text.encode('utf8') + ')'
            output.append({'title': text + videos,
             'url': link,
             'thumbnail': img,
             })

    return output

def get_course(url):
    url = BASE_URL + url
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content)
    output = []

    aitems = soup.find(id='recordline').find('ul').findAll('a')
    liitems = soup.find(id='recordline').find('ul').findAll('li')

    for idx, val in enumerate(aitems):
        link = val.get('href')
        title = liitems[idx].get('data-original-title')
        if title is not None:
            output.append({
                'title': title.encode('utf8'),
                'url': link})

    return output


def get_video(url):
    url = BASE_URL + url
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content)

    return soup.find(id='video_id_h').get('value')
