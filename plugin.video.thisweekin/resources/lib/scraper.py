import urllib
import urllib2
import re
import os
from BeautifulSoup import BeautifulSoup

def open_page(url):
    '''
    Return the contents of a page as a string
    '''
    user_agent='Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
    req = urllib2.Request(url)
    req.add_header('User_Agent', user_agent)
    response = urllib2.urlopen(req)
    output = response.read()
    response.close()

    return output.decode('ascii', 'ignore')

def get_shows(contents):
    '''
    Return an array of dictionaries of different shows
    '''
    output = []
    soup = BeautifulSoup(str(contents))
    categories = soup.find(id='menu-item-13682').findAll('li')
    for category in categories:
        if category is None:
            continue
        # Clean titles
        title = category.a.string
        title = re.sub('&#8217;', '\'', title)
        # Get URLs
        url = category.a['href']
        # Get the thumbnail images
        thumb = url.split("/")[-2]
        thumb = "http://thisweekin.com/show_heads/" + thumb + ".jpg"
        output.append({'title': title,
                       'url'  : url,
                       'thumb': thumb})

    return output

def get_episode_list(contents):
    """
    Return a list of episodes from an show page
    """
    output = []
    soup = BeautifulSoup(str(contents))
    episodes = soup.findAll('li', 'videoitem')
    for episode in episodes:
        url = episode.find('div', 'thumbnail')
        url = url.a['href']
        title = episode.find('h2').string
        title = re.sub('&#8217;', '\'', title)
        title = title + "..."
        thumb = episode.find('img', 'attachment-episode_thumbnail')['src']
        output.append({'title' : title,
                       'url'   : url,
                       'thumb' : thumb})
    return output

def get_youtube_url(contents):
    """
    Return a Youtube url from an episode page
    """
    soup = BeautifulSoup(str(contents))
    youtube_url = soup.find('div', id='show_player').find('a')['href']

    return youtube_url

if __name__ == '__main__':
    contents = open_page('http://thisweekin.com/')
    print get_shows(contents)
    contents = open_page('http://thisweekin.com/thisweekin-startups/')
    print get_episode_list(contents)
    contents = open_page('http://thisweekin.com/thisweekin-techstars/this-week-in-techstars-36-brad-feld-of-foundry-group/')
    print get_youtube_url(contents)
