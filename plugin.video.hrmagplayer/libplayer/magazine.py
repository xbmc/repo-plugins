#!/usr/bin/python
# -*- coding: utf-8 -*-

class Show:
    def getEpisodes(self, context, index, page):
        context['episodes'] = list()
        episode = None

        article = self.getArticle(context, page)
        while article != None:
            if self.hasVideo(article):
                episode = dict()
            
                episode['image'] = self.getImage(article)
                episode['link'] = self.getDetailLink(article)
                episode['title'] = self.getTitle(article)
                episode['date'] = self.getDate(article)
                episode['teaser'] = self.getTeaser(article)
                if episode['date'] != None:
                    episode['title'] += ' - ' + episode['date']
                
                if episode != None:
                    context['episodes'].append(episode)
            article = self.getArticle(context, page)
            
        # Check for cluster items
        clusterItem = self.getClusterItem(context, page)

        while clusterItem != None:
            episode = dict()
            episode['image'] = ''
            episode['date'] = self.getClusterDate(clusterItem)
            episode['title'] = self.getClusterTitle(clusterItem)
            if episode['date'] != None:
                episode['title'] += ' - ' + episode['date']
            episode['link'] = self.getClusterLink(clusterItem)
            context['episodes'].append(episode)
            
            clusterItem = self.getClusterItem(context, page)
        return context['episodes']
    
    def getArticle(self, context, page):
        article = None
        ix = page.find('<article', context['charIndex'])
        #print ix
        if ix != -1:
            ex = page.find('</article', ix)
            #print ex
            if ex != -1:
                article = page[ix:ex].replace("\n", '')
                context['charIndex'] = ex + 9
                if self.isCluster(article):
                    article = None
                    context['charIndex'] = ix
        #else:
        #    context['charIndex'] = 0
        return article
    
    def getImage(self, article):
        #print("getImage: " + line)
        ret = ''
        s = article.find("data-srcset=")
        if s != -1:
            #print "Image line: " + line
            s = article.find(chr(34), s) + 1
            e = article.find(' ', s)
            #print "Image: " + line[s:e]
            ret = article[s:e]
        return ret

    def getTeaser(self, line):
        ret = ''
        s = line.find("text__underline")
        if s != -1:
            s = line.find('>', s) + 1
            e = line.find('<', s)
            #print "Teaser: " + line[s:e]
            ret = line[s:e]
        return ret

    def getDetailLink(self, article):
        ret = ''
        s = article.find("<a href")
        if s != -1:
            s = article.find(chr(34), s) + 1
            e = article.find(chr(34), s)
            ret = article[s:e]
            #print("DetailLink: " + ret)
        return ret

    def getTitle(self, article):
        ret = ''
        s = article.find("text__headline")
        if s != -1:
            s = article.find('>', s) + 1
            e = article.find('<', s)
            if s != -1 and e != -1:
                ret = article[s:e]
                #print("Title: " + ret)
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
    
    def getClusterItem(self, context, page):
        item = None
        ix = page.find('clusterTeaser__item', context['charIndex'])
        #print ix
        if ix != -1:
            ex = page.find('</a>', ix)
            #print ex
            if ex != -1:
                context['charIndex'] = ex + 5
                item = page[ix:ex].replace("\n", '')
        else:
            context['charIndex'] = 0
        return item
    
    def getClusterTitle(self, item):
        title = None
        ix = item.find('decorated')
        if ix != -1:
            ix += 11
            ex = item.find('<', ix)
            if ex != -1:
                title = item[ix:ex]
        return title
    
    def getClusterDate(self, item):
        date = None
        ix = item.find('datetime')
        if ix != -1:
            ix = item.find('>', ix)
            if ix != -1:
                ex = item.find('<', ix)
                if ex != -1:
                    date = item[ix+1:ex]
        return date
    
    def getClusterLink(self, item):
        link = None
        ix = item.find('href')
        if ix != -1:
            ix += 6
            ex = item.find(chr(34), ix)
            if ex != -1:
                link = item[ix:ex]
        return link
    
    def hasVideo(self, article):    
        return article.find('zum Video') != -1
   
    def isCluster(self, article):
        return article.find('clusterTeaser') != -1
 
