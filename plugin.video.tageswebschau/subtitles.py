# -*- coding: utf-8 -*-
# Copyright 2011 Jörn Schumacher, Henning Saul 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os, urllib2, codecs, logging, xml.sax

# https://vimeosrtplayer.googlecode.com/svn-history/r5/VimeoSrtPlayer/bin/srt/example.srt

class SubtitlesContentHandler(xml.sax.ContentHandler):
    """ContentHandler than parses TTML XML into SRT."""

    def __init__(self):
        """Inits SubtitlesContentHandler."""
        xml.sax.ContentHandler.__init__(self)
        self._result = ""
        self._count = 0
        self._line = False
 
    def startElement(self, name, attrs):
        if name == "tt:p":
            self._startEntry(attrs.get("begin"), attrs.get("end"))
        elif name == "tt:span":
            self._startLine()

    def endElement(self, name):
        if name == "tt:p":
            self._endEntry()
        elif name == "tt:span":
            self._endLine()    
        elif name == "tt:br":
            self._newLine()    
             
    def characters(self, content):
        if(self._line):
            self._result += content

    def _startEntry(self, begin, end):
        """Start a new entry in SRT format.
        
        Args:
            begin: timestamp in format hh:mm:ss.mmm
            end: timestamp in format hh:mm:ss.mmm            
        """
        self._count = self._count + 1
        self._result += str(self._count)
        self._result += "\n"
        self._result += begin.replace('.', ',')
        self._result += " --> "
        self._result += end.replace('.', ',')
        self._result += "\n"
    
    def _endEntry(self):
        """Ends the current SRT entry."""
        self._result += "\n\n"        
    
    def _startLine(self):
        """Starts a line for current SRT entry."""
        self._line = True
        
    def _endLine(self):
        """Ends line for current SRT entry."""
        self._line = False
   
    def _newLine(self):
        """Appends new line for current SRT entry."""
        self._result += "\n"
                 
    def result(self):
        """Returns the parsed result in SRT format.

        Returns:
            A single String for the parsed result in SRT format.
        """
        return self._result 

def download_subtitles(url, subtitles_dir):
    """Downloads and parses TTML subtitles from the given URL and saves it as tagesschau.de.srt in the given subtitles directory.
    
    If downloading or parsing fails, returns None.
    
    Args:
        url: URL of TTML subtiles
        subtitles_dir: Directory to save parsed SRT file to

    Returns:
        File handle of the parsed SRT, or None
    """    
    if not os.path.exists(subtitles_dir):
        os.makedirs(subtitles_dir)

    path = os.path.join(subtitles_dir, 'tagesschau.de.srt')

    if (os.path.exists(path)):
        os.remove(path)

    if not url:
        return None
    
    logger = logging.getLogger("plugin.video.tagesschau.subtitles")
    try:
        source = urllib2.urlopen(url)
        handler = SubtitlesContentHandler()
        xml.sax.parse(source, handler)
        outfile = codecs.open(path, "w", "utf-8-sig")
        outfile.write(handler.result())
        outfile.close()
        return path
    except xml.sax.SAXException:
        logger.error("Failed to parse TTML from " + url)
        return None
    except urllib2.HTTPError:
        # the only way to find out if we have subtitles is to try to retrieve them
        logger.debug("Received HTTP error for " + url)
        return None        