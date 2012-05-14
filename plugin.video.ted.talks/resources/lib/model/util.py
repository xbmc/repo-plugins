import urllib2
import re


def getUrllib2ResponseObject(url):
    return urllib2.urlopen(url)


def cleanHTML(s, noBS=False):
    """(string[, noBS=False])
    The 2nd half of this removes HTML tags.
    The 1st half deals with the fact that BeautifulSoup sometimes spits
    out a list of NavigableString objects instead of a regular string.
    This only happens when there are HTML elements, so it made sense to
    fix both problems in the same function.
    Passing noBS=True bypasses the BeautifulSoup stuff."""
    if not noBS:
        tmp = list()
        for ns in s:
            tmp.append(unicode(ns))
        s = u''.join(tmp)
    s = re.sub('\s+', ' ', s) #remove extra spaces
    s = re.sub('<.+?>|Image:.+?\r|\r', '', s) #remove htmltags, image captions, & newlines
    s = s.replace('&#39;', '\'') #replace html-encoded single-quotes
    s = s.replace('&quot;', '"') #replace html-encoded double-quotes
    s = s.replace('&nbsp;', ' ') #replace html-encoded nonbreaking space
    s = s.strip()
    return s


def resizeImage(imagePath):
    '''
    Turn paths for small thumbnails into higher resolution versions.
    '''
    return re.sub('_\d+x\d+.jpg', '_389x292.jpg', imagePath)
