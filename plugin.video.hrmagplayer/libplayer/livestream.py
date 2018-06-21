#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from libplayer.http import HttpRetriever

class Livestream:
    def getEpisodes(self, context, index, page):
        context['episodes'] = list()
        episode = dict()
        
        episode['link'] = self.getLiveLink(page)
        episode['title'] = 'Hessicher Rundfunk Livestream'
        
        context['episodes'].append(episode)

        return context['episodes']
    
    def getLiveLink(self, page):
        link = None
        s = page.find('video" content="')
        if s != -1:
            e = page.find('"', s + 16)
            if e != -1:
                link = page[s + 16 : e]
        return link

    def getChannelGuide(self, context):
        http = HttpRetriever()
        page = http.get('https://www.hr-fernsehen.de/tv-programm/index.html')
        
        epg = list()
        
        context['charIndex'] = 0
        item = self.getItem(context, page)
        while item != None and not xbmc.Monitor().abortRequested():
            epgItem = dict()
            epgItem['time'] = self.getTime(item)
            epgItem['head'] = self.getHeadline(item)
            epgItem['sub'] = self.getSubline(item)
            epg.append(epgItem)
            item = self.getItem(context, page)
        context['charIndex'] = 0
        
    def getLiveAndNext(self, context):
        http = HttpRetriever()
        page = http.get('https://www.hr-fernsehen.de/tv-programm/index.html')
        
        live = list()
        
        context['charIndex'] = 0
        item = self.getItem(context, page)
        nextFlag = False
        while item != None and not xmbc.Monitor().abortRequested():
            liveFlag = self.getLiveFlag(item)
            if liveFlag or nextFlag:
                liveItem = dict()
                liveItem['time'] = self.getTime(item)
                liveItem['head'] = self.getHeadline(item)
                liveItem['sub'] = self.getSubline(item)
                live.append(liveItem)
                if not nextFlag:
                    nextFlag = True
                else:
                    nextFlag = False
            item = self.getItem(context, page)
        context['charIndex'] = 0
        return live
    
    def getItem(self, context, page):
        item = None
        ix = context['charIndex']
        ix = page.find('c-epgBroadcast__startTime', ix)
        if ix != -1:
            ex = page.find('</li>', ix)
            if ex != -1:
                item = page[ix:ex].replace("\n", '')
                context['charIndex'] = ex + 4
        return item
    
    def getTime(self, item):
        time = None
        ix = item.find('>')
        if ix != -1:
            ex = item.find('<', ix)
            if ex != -1:
                time = item[ix+1:ex]
        return time
    
    def getHeadline(self, item):
        headline = None
        ix = item.find('text__headline">')
        if ix != -1:
            ix += 16
            ex = item.find('<', ix)
            if ex != -1:
                headline = item[ix:ex]
        return headline
    
    def getSubline(self, item):
        subline = None
        ix = item.find('text__subline">')
        if ix != -1:
            ix += 15
            ex = item.find('<', ix)
            if ex != -1:
                subline = item[ix:ex]
        return subline
    
    def getLiveFlag(self, item):
        return item.find('liveFlag') != -1
    
        
        