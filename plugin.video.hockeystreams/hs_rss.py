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


def get_archive_rss_streams(rssBody, __debug__):
    return get_rss_streams(rssBody, False, __debug__)

def get_rss_streams(rssBody, live = True, __debug__ = False):
    gameDom = minidom.parse(rssBody)
    games = []
    for game in gameDom.getElementsByTagName('item'):
        title = getText(game.getElementsByTagName('title')[0].childNodes)
        description = getText(game.getElementsByTagName('description')[0].childNodes)
        if __debug__:
            print "title " + title + " description " + description
        date, rest = description.split('<', 1)
        date = date.strip()
        if __debug__:
            print "date " + date + "rest " + rest
        if live:
            url = re.search( 'href="(http://.*?[0-9]+/)[a-z_]+"', rest).group(1)
            if "Final" in date:
                real_date = time.strptime(date, "%m/%d/%Y - Final")
            else:
                try:
                    real_date = time.strptime(date, "%m/%d/%Y - %I:%M %p")
                except:
                    real_date = datetime.date.today()
        else:
            url = re.search( 'href="(/.*?/[0-9]+/)[a-z_]+"', rest).group(1)
            real_date = time.strptime(date, "%m/%d/%Y")

        if __debug__:
            print "url " + url
        games.append(
            (title, url, date, real_date )
        )
        
    return games


