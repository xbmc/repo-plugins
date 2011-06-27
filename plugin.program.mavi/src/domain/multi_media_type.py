'''
Created on 4 jun. 2011

@author: Nick
'''
from os.path import splitext

class MultiMediaType:

    def __call__(self):
        return self
    
    UNKNOWN    = 0
    IMAGE_TYPE = 1;    
    VIDEO_TYPE = 2;
    
    imageTypes = (".jpg", ".bmp", ".gif", ".png", ".tif")
    videoTypes = (".3g2", ".3gp", ".asf", "asx", "avi", ".flv", ".mov", ".mp4", ".mpg", ".rm", ".swf", ".vob", ".wmv")

    def getTypeFromUrl(self, url):
        ext = splitext(url)
        if ext[1] in self.imageTypes:
            return self.IMAGE_TYPE
        elif ext[1] in self.videoTypes or "http://www.youtube.com" in url:
            return self.VIDEO_TYPE
        else:
            return self.UNKNOWN