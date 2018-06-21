#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc

class Hessenschau:
    def getEpisodes(self, context, index, page):
        context['episodes'] = list()
        episode = None

        article = self.getArticle(context, page)
        ix = 0
        while article != None and not xbmc.Monitor().abortRequested():
            if episode != None:
                if episode['date'] != None:
                    context['episodes'].append(episode)
            episode = dict()
            
            episode['link'] = self.getLink(article)
            episode['date'] = self.getDate(article)
            episode['title'] = 'Hessenschau ' + str(episode['date'])
            episode['image'] = 'https://www.hessenschau.de/tv-sendung/banner-hessenschau-100~_t-1508156576948_v-16to9__small.jpg'
 
            article = self.getArticle(context, page)
            ix += 1
        return context['episodes']
    
    def getArticle(self, context, page):
        article = None
        ix = page.find('li class="c-clusterTeaser__item', context['charIndex'])
        if ix != -1:
            ex = page.find('</li', ix + 26)
            if ex != -1:
                article = page[ix:ex]
                context['charIndex'] = ex
        else:
            context['charIndex'] = 0
        return article
    
    def getLink(self, article):
        link = None
        ix = article.find('<a href=')
        if ix != -1:
            ex = article.find('"', ix + 9)
            link = article[ix + 9:ex]
        return link
    
    def getTitle(self, article):
        title = None
        ix = article.find('')
        
    def getDate(self, article):
        date = None
        ix = article.find('datetime')
        if ix != -1:
            ix = article.find('>', ix)
            if ix != -1:
                ex = article.find('<', ix)
                if ex != -1:
                    date = article[ix + 1:ex]
        return date
            
            
