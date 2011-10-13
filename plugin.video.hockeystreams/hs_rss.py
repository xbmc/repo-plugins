from xml.dom import minidom
import re
import time
import datetime

__author__ = 'longman'


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


def get_archive_rss_streams(rssBody, _debug_):
    return get_rss_streams(rssBody, False, _debug_)

def get_rss_streams(rssBody, live = True, _debug_ = False):
    print "get_rss_streams: debug = " + str(_debug_)
    gameDom = minidom.parse(rssBody)
    games = []
    for game in gameDom.getElementsByTagName('item'):
        title = getText(game.getElementsByTagName('title')[0].childNodes)
        description = getText(game.getElementsByTagName('description')[0].childNodes)
        if _debug_:
            print "title " + title + " description " + description
        if live:
            date, rest = description.strip().split('<a', 1)
            date = date.strip()
            if date.endswith('-'): #ongoing
                date = date[:-2]
            if date.endswith(','): #final
                date = date[:-1]
        else:
            date, rest = description.strip().split(' ', 1)
        date = date.strip()
        if _debug_:
            print "date " + date + " rest " + rest
        links = game.getElementsByTagName('link')
        if len(links) > 0 and len(links[0].childNodes) > 0:
            url = getText(links[0].childNodes)
        else:
            if live:
                url = re.search('href="(http://.*?[0-9]+/)[a-z_]+"', rest).group(1)
            else:
                url = re.search('href="(/.*?/[0-9]+/)[a-z_]+"', rest).group(1)
        if _debug_:
            print "url " + url

        if "Final" in date:
            real_date = time.strptime(date, "%m/%d/%Y - Final")
        else:
            try:
                real_date = time.strptime(date, "%m/%d/%Y - %I:%M %p")
            except:
                try:
                    real_date = time.strptime(date, "%m/%d/%Y")
                except:
                    real_date = datetime.date.today()
        games.append(
            (title, url, date, real_date )
        )
    return games


