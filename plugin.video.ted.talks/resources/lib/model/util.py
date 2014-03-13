import urllib2
import re


def getUrllib2ResponseObject(url):
    return urllib2.urlopen(url)


def resizeImage(imagePath):
    '''
    Turn paths for small thumbnails into higher resolution versions.
    '''
    return re.sub('_\d+x\d+.jpg', '_389x292.jpg', imagePath)
