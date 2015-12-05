import re
import urllib2

from xbmcswift2 import xbmc

from BeautifulSoup import BeautifulSoup


BASE_URL = 'http://codigofacilito.com'
T_ERROR_TITLE = 30001
T_ERROR_SERVER = 30002
T_ERROR_COURSES = 30003
T_ERROR_VIDEOS = 30004

agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0'

def log(message):
    xbmc.log(message)

def alert(title, message):
    xbmc.executebuiltin("Notification(" + title + "," + message + ")")

def get_soup_url(url):
    req = urllib2.Request(url)
    req.add_header('User-agent', agent)
    return BeautifulSoup(urllib2.urlopen(req).read(), convertEntities=BeautifulSoup.HTML_ENTITIES)

def get_courses():
    url = BASE_URL + '/courses'
    soup = get_soup_url(url)
    output = []

    for index, div in enumerate(soup.findAll('div', {'class': ' col-xs-12 col-md-4 col-lg-4'})):
        if index is 0:
            divparent = soup.find('section', {'class': 'row'})
            premium = divparent.find('div', {'class': 'small-padding yellow darken-3 be-small white-text'})
            videos = divparent.find('i', {'class': 'mdi-av-queue-music'}).parent
            videosc = filter(str.isdigit, videos.text.encode('utf8'))
            if premium is not None:
                continue
        else:
            premium = div.find('div', {'class': 'small-padding yellow darken-3 be-small white-text'})
            videos = div.find('i', {'class': 'mdi-av-queue-music'}).parent
            videosc = filter(str.isdigit, videos.text.encode('utf8'))
            if premium is not None:
                continue
        anchor = div.find('a')
        text = div.find('h2').text.encode('utf8')
        link = anchor.get('href').encode('utf8')
        img  = div.find('img').get('src')
        if videos is not None:
            videos = ' (' + videosc + ')'
            output.append({'title': text + videos,
                'url': link,
                'thumbnail': BASE_URL + img,
            })

    return output

def get_course(url):
    url = BASE_URL + url
    soup = get_soup_url(url)
    output = []

    for index, li in enumerate(soup.findAll('li', {'class': 'be-normal no-margin grey-text large-padding uppercase big-line-height'})):
        link = li.find('a').get('href')
        title = li.find('div', {'class': 'col-xs-10 col-lg-11'})
        if title is not None:
            output.append({
                'title': title.text.encode('utf8'),
                'url': link})

    return output


def get_video(url):
    url = BASE_URL + url
    soup = get_soup_url(url)

    return soup.find(id='youtube_video_id').get('value')
