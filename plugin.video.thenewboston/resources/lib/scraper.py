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

def get_categories(html):
    '''
    Return an array of dictionaries of tops
    '''
    output = []
    soup = BeautifulSoup(str(html))
    categories = soup.findAll('hgroup')
    for category in categories:
        # Clean titles
        title = category.h1.string
        output.append({'title': title})

    return output

def get_topics(html, title):
    """
    Return a list of topics from an show page
    """
    output = []
    soup = BeautifulSoup(str(html))
    categories = soup.findAll('hgroup')
    for category in categories:
        if category.h1.string == urllib.unquote(title):
            topics = category.findNext('ul').findAll('li')
            break

    for topic in topics:
        title_info = topic.a.string
        title = title_info.split('(')[0].strip()  
        count = title_info.split('(')[-1].split(" ")[0]

        url = 'http://thenewboston.org/' + topic.a['href']
        output.append({'title' : title,
                       'url'   : url,
                       'count' : count})

    return output

def get_lessons(html):
    """
    Return a list of lessons from a topic page
    """
    output = []
    soup = BeautifulSoup(str(html))
    lessons = soup.findAll('li', 'contentList')
    for lesson in lessons:
        title = lesson.a.string
        url = 'http://thenewboston.org/' + lesson.a['href']
        output.append({'title' : title,
                       'url'   : url})

    return output

def get_youtube(html):
    """
    Return a Youtube url and id tuple from an episode page
    """
    soup = BeautifulSoup(str(html))
    youtube_url = soup.find('iframe')['src']
    youtube_id = youtube_url.split('/')[-1]

    return youtube_url, youtube_id

if __name__ == '__main__':
    contents = open_page('http://thenewboston.org/tutorials.php')
    categories =  get_categories(contents)
    print categories
    contents = open_page('http://thenewboston.org/tutorials.php')
    for category in categories:
        print get_topics(contents, category['title'])
    html = open_page('http://thenewboston.org/list.php?cat=6')
    print get_lessons(html)
    html = open_page('http://thenewboston.org/watch.php?cat=6&number=1')
    print get_youtube(html)
