from datetime import datetime

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile

teaserPattern = getTagPattern('article', 'b-content-teaser-item')
sourcePattern = compile('<source\s*class="m-16-9"[^>]*data-srcset="([^"]*)"')
labelPattern = getTagPattern('div', 'teaser-label')
iconPattern = compile('<span\s*class="icon-[0-9]*_([^ ]*) icon">')
catPattern = compile('<span class="teaser-cat"[^>]*>([^<]*)</span>')
aPattern = compile('<a href="([^"]*)"[^>]*>')
titleIconPattern = compile('<span\s*class="title-icon icon-[0-9]*_([^"]*)">')
textPattern = compile('<p class="teaser-text"[^>]*>([^<]*)</p>')
datePattern = compile('<dd class="video-airing"[^>]*>([^<]*)</dd>')

    
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
    
    def __init__(self):
        pass
               
    def init(self, title, text, image, url, date, genre, category, label, type, playable):
        self.title = stripHtml(title)
        self.text = stripHtml(text)
        self.image = image
        self.url = url
        self.date = date
        self.genre = stripHtml(genre)
        self.category = stripHtml(category)
        self.label = stripHtml(label)
        self.type = type
        self.playable = playable
        self.contentName = None
        if url is not None:
            i = url.rfind('.')
            if i != -1:
                j = url.rfind('/')
                if j != -1:
                    self.contentName = url[j+1:i]
                    
    def valid(self):
        return self.title is not None and self.url is not None and self.url[0:1] == '/' 
     
    def __str__(self):
        return "<Teaser '%s' url='%s'>" % (self.title, self.url)
        

    def parse(self, string, pos=0, teaserMatch=None):
        if teaserMatch is None:
            teaserMatch = teaserPattern.search(string, pos)
        if teaserMatch is None:
            return -1
        class_ = teaserMatch.group(1)
        
        article = getTag('article', string, teaserMatch)
        endPos = teaserMatch.start(0) + len(article)
        if class_.find('m-hidden') != -1:
            return endPos
        
        sourceMatch = sourcePattern.search(article)
        src = None
        if sourceMatch is not None:
            srcset = sourceMatch.group(1)
            src = srcset.split(' ')[0]
            pos = sourceMatch.end(0)
        
        labelMatch = labelPattern.search(article, pos)
        label = None
        type = None
        if labelMatch is not None:        
            labelTags = getTag('div', article, labelMatch)
            iconMatch = iconPattern.search(labelTags)
            if iconMatch is not None:    
                type = iconMatch.group(1)
            i = labelTags.find('</span>') + len('</span>')
            j = labelTags.rfind('</div>')
            pos = j + len('</div>') 
            label = labelTags[i:j]
            label = label.replace('<strong>', '')
            label = label.replace('</strong>', '')
            label = label.strip()
            
        catMatch = catPattern.search(article, pos)
        genre = None
        category = None

        if catMatch is not None:
            parts = catMatch.group(1).strip().split('|')
            if len(parts) > 0:
                genre = parts[0].strip()
            if len(parts) > 1:
                category = parts[1].strip()
            pos = catMatch.end(0)
            
        aMatch = aPattern.search(article, pos)
        title = None
        url = None
        playable = False
        if aMatch is not None:
            url = aMatch.group(1).strip()        
            pos = aMatch.end(0)
            i = pos
            j = article.find('</a>', i)
            iconMatch = titleIconPattern.search(article, pos)
            if iconMatch is not None:    
                playable =  iconMatch.group(1) == 'play'
                i = article.find('</span>', pos) + len('</span>')
            title = article[i:j]
            title = title.replace('<strong>', '')
            title = title.replace('</strong>', '')
            title = title.strip()
            pos = j + len('</a>') 
    
        textMatch = textPattern.search(article, pos)
        text = None
        if textMatch is not None:
            text = textMatch.group(1).strip()
            pos = textMatch.end(0)
            
        dateMatch = datePattern.search(article, pos)
        date = None
        if dateMatch is not None:
            date = dateMatch.group(1).strip()
            pos = dateMatch.end(0)
    
        self.init(title, text, src, url, date, genre, category, label, type, playable)
        return endPos
