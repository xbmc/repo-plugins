# -*- coding: utf-8 -*-
import urllib
import os.path
import sys
import xbmc

__addon__ = sys.modules['__main__'].__addon__
pluginName = sys.modules['__main__'].__plugin__

def getLS(i):
    return __addon__.getLocalizedString(i).encode('utf-8')

class Download:

    def __init__(self, title, videoURL, downloadPath):
        if title is None or videoURL is None:
            print '[%s] No file to download!' % (pluginName)
            self.showNotification(getLS(30202), getLS(30205))
        else:
            downloadPath = xbmc.translatePath(downloadPath)
            self.url = videoURL
            self.title = title
            #unicode causes problems here, convert to standard str
            self.filename = self.getLegalFilename(self.title.title().replace(' ', ''))
            self.fullDownloadPath = os.path.join(downloadPath, self.filename)
            print '[%s] %s : Attempting to download\n%s --> %s' % (pluginName, __name__, self.url, self.fullDownloadPath)
            if self.checkPath(downloadPath, self.filename):
                self.showNotification(getLS(30200), self.filename)
                try:
                    urllib.urlretrieve(self.url, self.fullDownloadPath)
                except IOError, e:
                    print e
                    self.showNotification(getLS(30202), e.__str__())
                else:
                    print '[%s] Download complete!' % (pluginName)
                    self.showNotification(getLS(30201), self.filename)

    def showNotification(self, header, message):
        xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % (header, message))

    def checkPath(self, path, filename):
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path, filename)):
                if os.path.getsize(os.path.join(path, filename))>0:
                    self.showNotification(getLS(30203), '%s %s' % (filename, getLS(30204)))
                else:
                    return True #overwrite empty files, #skip others.
            else:
                return True
        return False

    def getLegalFilename(self, filename, illegalChars = '=?:;\'"*+,/|\\'):
        for c in illegalChars:
            filename = filename.replace(c, '')
        #xbox needs file name trunicated to 42 characters including extension.
        if os.environ.get("OS", "xbox") == 'xbox':
            #at some point in writing the file xbmc+windows pukes on unicode, so convert to regular string.
            return str(os.path.splitext(filename)[:-1][0][:38] + os.path.splitext(filename)[-1])
        else:
            #at some point in writing the file xbmc+windows pukes on unicode, so convert to regular string.
            return str(filename)
