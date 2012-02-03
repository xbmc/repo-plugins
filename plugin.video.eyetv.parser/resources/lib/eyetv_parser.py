# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Benjamin Bertrand
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# http://www.gnu.org/copyleft/gpl.html

import os
import base64
import datetime
import re
import xml.etree.ElementTree as ET
from xbmcswift import xbmc
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

    def __init__(self, archivePath, sortMethod):
        """Initialize the list of EyeTV recordings"""
        self.archivePath = archivePath
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
