#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin,xbmcaddon, xbmc
import urlfetch
from BeautifulSoup import BeautifulSoup
import json
import re
import fptplay
import zingtv

plugin = Plugin()
__settings__ = xbmcaddon.Addon(id='plugin.video.fptplay')
crawurl = 'https://fptplay.net/livetv'

def getAllChannels():
    cns = []
    cns.extend(getChannels(crawurl))
    return cns

def startChannel():
    channelid = __settings__.getSetting('start_channelid')
    link =     link = fptplay.getLinkById(channelid,__settings__.getSetting('quality'))
    xbmc.Player().play(link)

@plugin.route('/')
def index():
    cns = getAllChannels()
    return cns

@plugin.route('/plays/<id>')
def plays(id):
    link = fptplay.getLinkById(id,__settings__.getSetting('quality'))
    plugin.log.info("Playing : " + link)
    plugin.set_resolved_url(link)

@plugin.route('/resolve/<uri>')
def resolve(uri):
    plugin.log.info("Resolve : " + uri)
    s_link = resolve_url(uri)
    plugin.log.info("Return url : " + s_link)
    if s_link == None :
        return None 
    plugin.set_resolved_url(s_link)

def resolve_url(uri):
    if uri.startswith('http://tv.zing.vn'):
        return zingtv.getLink(uri)
    if uri.startswith('https://fptplay.net'):
        return fptplay.getLink(uri,__settings__.getSetting('quality'))
    return None

def getChannels(url):
    cns = []
    result = None
    result = urlfetch.fetch(
        url,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })
    if result.status_code != 200 :
        plugin.log.error('Something wrong when get list fpt play channel !')
        return None
    soup = BeautifulSoup(result.content, convertEntities=BeautifulSoup.HTML_ENTITIES)

    items = soup.findAll('div', {'class' : 'hover01'})
    for item in items:

        ac = item.find('a', {'class' : 'tv_channel '})

        if ac == None :
            ac = item.find('a', {'class' : 'tv_channel active'})
            if ac == None :
                continue

        lock = item.find('img', {'class' : 'lock'})

        if lock != None :
            continue

        dataref = ac.get('data-href')

        if dataref == None :
            continue

        img = ac.find('img', {'class' : 'img-responsive'})

        imgthumbnail = ''

        if img != None :
            imgthumbnail = img.get('data-original')

        if not dataref.startswith(crawurl) :
            continue

        channelid = dataref[27:]

        if not channelid :
            continue

        title = channelid
        cn = {
                'label': title,
                'path': plugin.url_for('plays', id = channelid),
                'thumbnail':imgthumbnail,
                'is_playable': True
            }
        cns.append(cn)
    return cns

if __name__ == '__main__':
    plugin.run()
