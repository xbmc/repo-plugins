import urllib
import os.path
import sys
import xbmc
import xbmcgui

#enable localization
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.ted.talks')
getLS = __settings__.getLocalizedString
pluginName = sys.modules['__main__'].__plugin__


class Download:

    def __init__(self, title, videoURL, downloadPath):
        self.pDialog = xbmcgui.DialogProgress()
        self.pDialog.create(getLS(30000))

        downloadPath = xbmc.translatePath(downloadPath)
        self.url = videoURL
        self.title = title
        #unicode causes problems here, convert to standard str
        self.filename = self.getLegalFilename(self.title.title().replace(' ', '') + '.mp4')
        self.fullDownloadPath = os.path.join(downloadPath, self.filename)
        print '[%s] %s : Attempting to download\n%s --> %s' % (pluginName, __name__, self.url, self.fullDownloadPath)

        if self.checkPath(downloadPath, self.filename):
            try:
                re = urllib.urlretrieve(self.url, self.fullDownloadPath, reporthook = self.showdlProgress)
                print '[%s] Download Success!' % (pluginName)
            except IOError, e:
                print e
                self.pDialog.close()
                dialog = xbmcgui.Dialog()
                dialog.ok('Error', str(i)+' of '+str(len(photos))+'\n'+self.url, e.__str__())
        if self.pDialog.iscanceled():
                self.pDialog.close()
        #close the progress dialog
        self.pDialog.close()

    def showdlProgress(self, count, blockSize, totalSize):
        percent = int(count*blockSize*100/totalSize)
        self.pDialog.update(percent, '%s %s' % (getLS(32023), self.url), '%s %s' % (getLS(32024), self.fullDownloadPath))
        print percent, '% ',
        if self.pDialog.iscanceled():
            self.pDialog.close()

    def checkPath(self, path, filename):
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path, filename)):
                if not os.path.getsize(os.path.join(path, filename))>0:
                    return True #overwrite empty files, #skip others.
            else:
                return True

    def getLegalFilename(self, filename, illegalChars = '=?:;\'"*+,/|\\'):
        for c in illegalChars:
            filename = filename.replace(c, '')
        #xbox needs file name trunicated to 42 characters including extension.
        if os.environ.get("OS", "xbox") == 'xbox':
            #at some point in writing the file xbmc+windows pukes on unicode, so convert to retular string.
            return str(os.path.splitext(filename)[:-1][0][:38] + os.path.splitext(filename)[-1])
        else:
            #at some point in writing the file xbmc+windows pukes on unicode, so convert to retular string.
            return str(filename)
