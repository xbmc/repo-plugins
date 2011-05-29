# -*- coding: utf-8 -*-
"""EyeTV parser

Inspired by XBMCEyetvParser plugin from prophead and Nic Wolfe (midgetspy)
http://xbmc-addons.googlecode.com/svn/trunk/plugins/video/XBMCEyetvParser

Re-written for Dharma by beenje
"""
import sys
import os
import base64
import datetime
import re
import xml.etree.ElementTree as ET
import xbmcplugin
import xbmcgui
import xbmcaddon
try:
    import xbmcvfs
except ImportError:
    import shutil
    copyfile =  shutil.copyfile
else:
    copyfile = xbmcvfs.copy


# constants
SORTKEYS = ('Date Recorded', 'Date Recorded', 'Display Title')
# 0 : recorded date
# 1 : reverse recorded date
# 2 : title

__url__ = "http://github.com/beenje/plugin.video.eyetv.parser"
__addon__ = xbmcaddon.Addon(id='plugin.video.eyetv.parser')
__plugin__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')

getLS = __addon__.getLocalizedString


class Plist:
    """Simple class to read Apple's plist format

    code from http://effbot.org/zone/element-iterparse.htm
    """
    _unmarshallers = {
        # collections
        "array": lambda x: [v.text for v in x],
        "dict": lambda x:
            dict((x[i].text, x[i+1].text) for i in range(0, len(x), 2)),
        "key": lambda x: x.text or "",

        # simple types
        "string": lambda x: x.text or "",
        "data": lambda x: base64.decodestring(x.text or ""),
        "date": lambda x: datetime.datetime(*map(int, re.findall("\d+", x.text))),
        "true": lambda x: True,
        "false": lambda x: False,
        "real": lambda x: float(x.text),
        "integer": lambda x: int(x.text),
    }

    def load(self, filename):
        parser = ET.iterparse(filename)
        for action, elem in parser:
            unmarshal = self._unmarshallers.get(elem.tag)
            if unmarshal:
                data = unmarshal(elem)
                elem.clear()
                elem.text = data
            elif elem.tag != "plist":
                raise IOError("unknown plist type: %r" % elem.tag)
        return parser.root[0].text


class Eyetv:
    """Class to retrieve EyeTV recordings"""

    def __init__(self):
        """Initialize the list of EyeTV recordings"""
        # Get settings
        self.archivePath = __addon__.getSetting('archivePath')
        sortMethod = int(__addon__.getSetting('sortMethod'))
        # Parse the 'EyeTV Archive.xml' plist - copy it locally first
        # (needed for external python when the file is on a smb share for example)
        archiveXml = os.path.join(self.archivePath, u'EyeTV Archive.xml')
        localXml = xbmc.translatePath('special://temp/EyeTVArchive.xml')
        copyfile(archiveXml, localXml)
        plist = Plist().load(localXml)
        # Remove temporary file
        os.remove(localXml)
        # Get all recordings from the plist
        self.recordings = plist["Recordings"].values()
        # Sort the list of recordings
        self.recordings.sort(key=lambda recording: recording[SORTKEYS[sortMethod]])
        if sortMethod == 1:
            # reverse recorded date
            self.recordings.reverse()

    def _recordingPath(self, recording):
        """Return the full path of a recording file without suffix"""
        relativePath = recording['Relative Path']
        # 'Relative Path' might contains '/' for episode number (ex: 1/6)
        # that shall be replaced with ':' to get the real path
        dirname = os.path.dirname(relativePath).replace('/', ':')
        # Remove '.eyetvr' suffix
        filename = os.path.basename(relativePath)[:-7]
        return os.path.join(self.archivePath, dirname, filename)

    def recordingsInfo(self):
        """Generator that returns all recordings as a tuple (url, icon, thumbnail, infoLabels)"""
        for recording in self.recordings:
            filename = self._recordingPath(recording)
            url = filename + u'.mpg'
            icon = filename + u'.tiff'
            thumbnail = filename + u'.thumbnail.tiff'
            infoLabels = {'title': recording['Display Title'], 'plot': recording['Description']}
            yield (url, icon, thumbnail, infoLabels)

    def nbRecordings(self):
        """Return the number of recordings available"""
        return len(self.recordings)


def main():
    """Entry point"""

    print '%s version %s' % (__plugin__, __version__)

    # Open settings if EyeTV Archive path is not set
    if not __addon__.getSetting('archivePath'):
        __addon__.openSettings()

    try:
        eyetv = Eyetv()
    except IOError:
        xbmcgui.Dialog().ok(getLS(30100), getLS(30101))
    else:
        nbItems = eyetv.nbRecordings()
        for (url, icon, thumbnail, info) in eyetv.recordingsInfo():
            li = xbmcgui.ListItem(label=info['title'], iconImage=icon, thumbnailImage=thumbnail)
            li.setInfo(type='Video', infoLabels=info)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, totalItems=nbItems)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))


if __name__ == "__main__":
    main()
