#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc

class WdrShow:
    def getEpisodes(self, context, index, page):
        context['episodes'] = list()
        episode = None

        if not self.findArticles(context, page):
            return context['episodes']
        
        article = self.getArticle(context, page)
        while article != None and not xbmc.Monitor().abortRequested():
            if self.hasVideo(article):
                episode = dict()
            
                episode['image'] = self.getImage(article)
                episode['link'] = self.getDetailLink(article)
                episode['title'] = self.getTitle(article)
                episode['date'] = self.getDate(article)
                episode['teaser'] = self.getTeaser(article)
                if episode['teaser'] != None:
                    episode['title'] += ' - ' + episode['teaser']
                
                if episode != None:
                    context['episodes'].append(episode)
            article = self.getArticle(context, page)
        return context['episodes']
    
    def findArticles(self, context, page):
        ret = False
        ix = page.find('Rückschau')
        if ix != -1:
            context['charIndex'] = ix
            ret = True
        return ret
    
    def getArticle(self, context, page):
        article = None
        ix = page.find('<a href', context['charIndex'])
        if ix != -1:
            ex = page.find('hideTeasertext', ix)
            if ex != -1:
                article = page[ix:ex].replace("\n", '')
                context['charIndex'] = ex + 9
                if self.isCluster(article):
                    article = None
        else:
            context['charIndex'] = 0
        return article
    
    def getImage(self, article):
        ret = ''
        s = article.find('src=')
        if s != -1:
            s = article.find(chr(34), s) + 1
            e = article.find(chr(34), s)
            ret = 'https://www1.wdr.de/' + article[s:e]
        return ret

    def getTeaser(self, line):
        ret = None
        s = line.find('text__underline')
        if s != -1:
            s = line.find('>', s) + 1
            e = line.find('<', s)
            ret = line[s:e]
        return ret

    def getDetailLink(self, article):
        ret = ''
        s = article.find('<a href="/media')
        if s != -1:
            s = article.find(chr(34), s) + 1
            e = article.find(chr(34), s)
            ret = 'https://www1.wdr.de/' + article[s:e]
        return ret

    def getTitle(self, article):
        ret = ''
        s = article.find('headline')
        if s != -1:
            s = article.find('>', s) + 1
            e = article.find('<', s)
            if s != -1 and e != -1:
                ret = article[s:e]
        return ret
    
    def getDate(self, article):
        ret = ''
        s = article.find('datetime')
        if s != -1:
            s = article.find('>', s)
            if s != -1:
                e = article.find('<', s)
                if e != -1:
                    ret = article[s+1:e]
        return ret
    
    def hasVideo(self, article):    
        return article.find('mediathek') != -1
   
    def isCluster(self, article):
        return article.find('clusterTeaser') != -1
 
