#!/usr/bin/python
# -*- coding: utf-8 -*-

class Livestream:
    def getEpisodes(self, context, index, page):
        print('Get livestream episode')
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
