# Copyright 2010 Jonathan Beluch.
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
# This file incorporates work covered by the following copyright and
# permission notice:
#
#   Copyright 2007 Doug Hellmann.
#
#   All Rights Reserved
#
#   Permission to use, copy, modify, and distribute this software and its
#   documentation for any purpose and without fee is hereby granted,
#   provided that the above copyright notice appear in all copies and that
#   both that copyright notice and this permission notice appear in
#   supporting documentation, and that the name of Doug Hellmann not be
#   used in advertising or publicity pertaining to distribution of the
#   software without specific, written prior permission.
#
#   DOUG HELLMANN DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
#   INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
#   EVENT SHALL DOUG HELLMANN BE LIABLE FOR ANY SPECIAL, INDIRECT OR
#   CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
#   USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
#   OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
#   PERFORMANCE OF THIS SOFTWARE.
#   OCW class
from urllib import quote_plus
from cStringIO import StringIO
import urllib2
import urlparse
import asyncore, socket
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

class XBMCVideoPlugin(object):
    """This is a class to help handle routine tasks for a video plugin
    such as adding directories and/or movies to the UI.""" 
    argv0 = None
    argv1 = None
    
    def __init__(self, argv0, argv1):
        """Takes argv[0] and argv[1] arguments to the application"""
        self.xbmc = xbmc
        self.xbmcgui = xbmcgui
        self.xbmcplugin = xbmcplugin
        self.xbmcaddon = xbmcaddon
        self.addon = self.xbmcaddon.Addon(id=os.path.basename(os.getcwd()))
        self.argv0 = argv0
        self.argv1 = int(argv1)
        self.dp = None

    def getString(self, id):
        return self.addon.getLocalizedString(id)
        
    def add_videos(self, lis, end=True):
        """Takes a list of directory items which will be added as
        videos in the XBMC UI.  Each directory item is a dictionary
        containing the following key/value pairs:
            name = title of the video
            url = url of the video
            info = a dict object with key/val pairs. Info can be found
                in the xbmc documentation (optional)
            icon = url to an icon (optional)
            tn = url to a thumbnail (optional)
        The second parameter the function takes is 'end'.  This
        simply defines whether or not to call 
        xbmcplugin.endOfDirectory()
        """
        _lis = [self._make_directory_item(li, False) for li in lis]
        self.xbmcplugin.addDirectoryItems(self.argv1, _lis, len(_lis))
        if end == True: 
            self.xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)   
    
    def add_dirs(self, dirs, end=True):
        """Takes a list of directory items which will be added as
        folders in the XBMC UI.  Each directory item is a dictionary
        containing the following key/value pairs:
            name = title of the list item 
            url = url of the folder contents (usu a link back to the plugin)
            info = a dict object with key/val pairs. Info can be found
                in the xbmc documentation (optional)
            icon = url to an icon (optional)
            tn = url to a thumbnail (optional)
        The second parameter the function takes is 'end'.  This
        simply defines whether or not to call 
        xbmcplugin.endOfDirectory()
        """
        _dirs = [self._make_directory_item(d, True) for d in dirs]
        self.xbmcplugin.addDirectoryItems(self.argv1, _dirs, len(_dirs))
        if end == True: 
            self.xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)

    def _make_directory_item(self, diritem, isFolder=True):
        """An internally used function to build the actual lis items
        using xbmcgui.ListItem()"""
        if isFolder:
            url = '%s?url=%s&mode=%s' % (self.argv0, 
                                         quote_plus(diritem.get('url', '')), 
                                         diritem.get('mode'))
        else:
            url = diritem.get('url')
        li = self.xbmcgui.ListItem(diritem.get('name'))
        if 'info' in diritem.keys(): li.setInfo('video', diritem.get('info'))
        if 'icon' in diritem.keys(): li.setIconImage(diritem.get('icon'))
        if 'tn' in diritem.keys(): li.setThumbnailImage(diritem.get('tn'))
        return (url, li, isFolder)
               
    def _urljoin(self, url):
        return urlparse.urljoin(self.base_url, url)

class DialogProgress(xbmcgui.DialogProgress):
    """This class is meant to extend functionality for the 
    xbmcgui.DialogProgress class. It adds an increment() method, which 
    updates the percentage of progress for one event, the step size is 
    calculated by dividing 100 by the number of events to complete.  By
    including the increment method which takes only optional parameters,
    other classes/functions can handle updating the dialog progress bar
    without knowing all the details such as step size, current state, 
    etc. """

    def __init__(self, heading, line1='', line2='', line3='', num_steps=None):
        xbmcgui.DialogProgress.__init__(self)
        self.lines = [line1, line2, line3]
        self.create(heading, *self.lines)
        self.update(0)
        self.num_steps = num_steps
        self.step = 0
        self.progress = 0
        if self.num_steps != None:
            self.step = int(100 / self.num_steps)
    
    def increment(self, num_incr_steps=1, line1=None, line2=None, line3=None):
        if line1 != None: self.lines[0] = line1
        if line2 != None: self.lines[1] = line2
        if line3 != None: self.lines[2] = line3
        self.progress += (num_incr_steps * self.step)
        self.update(self.progress, *self.lines)


class HTTPClient(asyncore.dispatcher):
    """
    Originally based on HttpClient by Doug Hellmann from 
    http://www.doughellmann.com/PyMOTW/asyncore/

    The asyncore.dispatcher is used to create lots of asynchronous
    connections.  When crawling web pages to parse video information this
    class can significantly improve loading time.
    """

    def __init__(self, url, dp=None):
        self.url = url
        self.parsed_url = urlparse.urlparse(url)
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        #xbmc's current version of the python interpreter doesn't include named
        #tuple attributes, so use index instead of attribute 'netloc'
        self.connect((self.parsed_url[1], 80))
        self.write_buffer = 'GET %s HTTP/1.0\r\n\r\n' % self.url
        self.read_buffer = StringIO() 
        self.dp = dp

    def handle_read(self):
        data = self.recv(8192)
        self.read_buffer.write(data)

    def handle_write(self):
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]

    def handle_close(self):
        if self.dp:
            self.dp.increment(line2=self.parsed_url[2])
        self.close()

    def writable(self):
        return (len(self.write_buffer) > 0)


def async_urlread(url_list, dp=None):   
    """Takes a list of urls and returns a list of responses once all of
    the requests have finished"""
    #create an HTTPClient for each url
    http_clients = [HTTPClient(url, dp) for url in url_list]
    #run the syncore loop, it will downloda all of the registered HTTPClients
    asyncore.loop()
    #return a list of the responses
    return [c.read_buffer.getvalue() for c in http_clients]

def urlread(url):
    """Helper function to reduce code needed for a simple urlopen()"""
    f = urllib2.urlopen(url)
    page_contents = f.read()
    f.close()
    return page_contents

def parse_qs(qs):
    """takes a query string argument and returns a dict of key/val pairs"""
    if len(qs) < 1: return {}
    return dict([p.split('=') for p in qs.strip('?').split('&')])    
