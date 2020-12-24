from datetime import datetime

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import stripTag
from de.generia.kodi.plugin.backend.zdf.Regex import cleanTags
from de.generia.kodi.plugin.backend.zdf.Regex import compile

teaserPattern = getTagPattern('article', 'b-content-teaser-item')
sourcePattern = compile('class="m-16-9"[^>]*data-srcset="([^"]*)"')
labelPattern = getTagPattern('div', 'teaser-label')
iconPattern = compile('class="icon-[0-9]*_([^ ]*) icon">')
catPattern = compile('class="teaser-cat\s*[^"]*"[^>]*>')
catCategoryPattern = compile('class="teaser-cat-category\s*[^"]*"[^>]*>([^<]*)</[^>]*>')
catBrandPattern = compile('class="teaser-cat-brand\s*[^"]*"[^>]*>([^<]*)</[^>]*>')
aPattern = compile('href="([^"]*)"[^>]*>')
textPattern = compile('class="teaser-text"[^>]*>([^<]*)</[^>]*>')
footPattern = compile('class="teaser-foot"[^>]*>')
footIconPattern = compile('class="[^"]*icon-[0-9]*_(play)[^"]*">')
datePattern = compile('class="teaser-info[^"]*"[^>]*>([^<]*)</[^>]*>')
apiTokenPattern = compile('"apiToken"\s*:\s*"([^"]*)"')

    
def compareTeasers(t1, t2):
    if t1 is None and t2 is None:
        return 0
    if t1 is None and t2 is not None:
        return 1
    if t1 is not None and t2 is None:
        return -1
    
    '''
    if t1.date is not None and t2.date is not None:
        d1 = datetime.strptime(t1.date, "%d.%m.%Y")
        d2 = datetime.strptime(t2.date, "%d.%m.%Y")
        return d1.toordinal() - d2.toordinal()
    '''
    if t1.date is not None and t2.date is None:
        return 1
        
    if t1.date is None and t2.date is not None:
        return -1
    
    if t1.title < t2.title:
        return -1
    
    if t1.title > t2.title:
        return 1
    
    return 0

class Teaser(object):
    title = None
    text = None
    image = None
    url = None
    date = None
    genre = None
    category = None
    label = None
    type = None
    playable = False
    contentName = None
    apiToken = None
    duration = None
    
    def __init__(self):
        pass
                    
    def valid(self):
        return self.title is not None and self.url is not None and self.url[0:1] == '/' 
     
    def __str__(self):
        return "<Teaser '%s' playable='%s' url='%s' apiToken='%s' label='%s'>" % (self.title, self.playable, self.url, self.apiToken, self.label)
        

    def parse(self, string, pos=0, baseUrl=None, teaserMatch=None):
        if teaserMatch is None:
            teaserMatch = teaserPattern.search(string, pos)
        if teaserMatch is None:
            return -1
        class_ = teaserMatch.group(1)
        
        article = getTag('article', string, teaserMatch)
        endPos = teaserMatch.start(0) + len(article)
        if class_.find('m-hidden') != -1:
            return endPos
                
        pos = self.parseImage(article, pos)
        pos = self.parseCategory(article, pos)
        pos = self.parseTitle(article, pos, baseUrl)
        pos = self.parseText(article, pos)
        pos = self.parseLabel(article, pos)
        pos = self.parseFoot(article, pos)

        return endPos

    def parseImage(self, article, pos, pattern=sourcePattern):
        sourceMatch = pattern.search(article)
        src = None
        if sourceMatch is not None:
            srcset = sourceMatch.group(1)
            src = srcset.split(' ')[0]
            pos = sourceMatch.end(0)
        self.image = src
        return pos
    
    def parseLabel(self, article, pos):
        labelMatch = labelPattern.search(article, pos)
        label = None
        type = None
        if labelMatch is not None:        
            labelTags = getTag('div', article, labelMatch)
            iconMatch = iconPattern.search(labelTags)
            if iconMatch is not None:    
                type = iconMatch.group(1)
            i = labelTags.find('>') + len('>')
            j = labelTags.rfind('</div>')
            pos = j + len('</div>') 
            label = labelTags[i:j]
            label = stripTag('abbr', label)
            label = cleanTags(label)
            label = label.strip()

        self.label = stripHtml(label)
        self.type = type
        return pos
    
    def parseCategory(self, article, pos):
        catMatch = catPattern.search(article, pos)
        genre = None
        category = None

        if catMatch is not None:
            pos = catMatch.end(0)

            catCategoryMatch = catCategoryPattern.search(article, pos)
            if catCategoryMatch is not None:
                genre = catCategoryMatch.group(1).strip()
                pos = catCategoryMatch.end(0)

            catBrandMatch = catBrandPattern.search(article, pos)
            if catBrandMatch is not None:
                category = catBrandMatch.group(1).strip()
                pos = catBrandMatch.end(0)
                            
            
        self.genre = stripHtml(genre)
        self.category = stripHtml(category)
        return pos
        
    def parseTitle(self, article, pos, baseUrl):
        aMatch = aPattern.search(article, pos)
        title = None
        url = None
        if aMatch is not None:
            url = aMatch.group(1).strip()        
            pos = aMatch.end(0)
            i = pos
            j = article.find('</a>', i)
            # check for '<span class="arrowhover ...'
            k = article.find('<span class="arrowhover', i)
            if k != -1 and k < j:
                j = k
            title = article[i:j]
            title = cleanTags(title)
            title = title.strip()
            pos = j + len('</a>') 
    
        self.title = stripHtml(title)
        self.url = url
        self.contentName = None
        if url is not None:
            if baseUrl is not None and url[0:len(baseUrl)] == baseUrl:
                self.url = url[len(baseUrl):]
            i = url.rfind('.')
            if i != -1:
                self.contentName = '/zdf' + url[0:i]
        return pos
    
    def parseText(self, article, pos, pattern=textPattern):
        textMatch = pattern.search(article, pos)
        text = None
        if textMatch is not None:
            text = textMatch.group(1).strip()
            pos = textMatch.end(0)

        self.text = stripHtml(text)
        return pos

    def parseFoot(self, article, pos, pattern=footPattern):
        playable = False
        footMatch = pattern.search(article, pos)
        foot = None
        if footMatch is not None:
            pos = footMatch.end(0)

            iconMatch = footIconPattern.search(article, pos)
            if iconMatch is not None:    
                playable =  iconMatch.group(1) == 'play'
                pos = article.find('</span>', pos) + len('</span>')

        self.playable = playable
        pos = self.parseDuration(article, pos)
        return pos
        
    def parseDuration(self, article, pos, pattern=datePattern):
        durationMatch = pattern.search(article, pos)
        playable = False
        duration = None
        if durationMatch is not None:
            duration = durationMatch.group(1).strip()
            duration = duration.replace(' min', '')
            if duration.isdigit():
                duration = int(duration) * 60
                playable = True
            else:
                duration = None
            pos = durationMatch.end(0)
    
        if not self.playable and playable:
            self.playable = playable
        self.duration = duration
        return pos


    def parseApiToken(self, article, pos, pattern=apiTokenPattern):
        apiTokenMatch = pattern.search(article, pos)
        
        apiToken = None
        if apiTokenMatch is not None:
            apiToken = apiTokenMatch.group(1)
            pos = apiTokenMatch.end(0) 

        self.apiToken = apiToken
        return pos
        