# Copyright 2011 Jonathan Beluch. 
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
from urllib import unquote_plus, quote_plus
from urlparse import urlparse
from cStringIO import StringIO
import urllib2
import xbmc
import xbmcgui
import xbmcplugin
import asyncore, socket
from urlparse import urlparse
import pickle

def parse_url_qs(url, pickled_fragment=False):
    '''Returns a dict of key/vals parsed from a query string.  If
    pickled_fragment=True, the method unpickles python objects stored in the
    fragment portion of the url and adds them to the returned dictionary.
    '''
    parts = urlparse(url)
    qs = parts[4]
    fragment = parts[5]

    #parse qs
    params = parse_qs(qs)

    #unpickle the fragment and update params with the pickled dict
    if pickled_fragment and len(fragment) > 0:
        params.update(pickle.loads(unquote_plus(fragment)))
    return params

    
def parse_qs(qs):
    '''Takes a query string and returns a {} with key/vals.  If more than
    one instance of a key is specified, the last value will be returned.'''
    if qs is None or len(qs) == 0:
        return {}

    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r ={} 

    for pair in pairs:
        parts = pair.split('=', 1)
        if len(parts) != 2:
            raise ValueError, 'bad query field: %r' % (pair)
        r[unquote_plus(parts[0])] = unquote_plus(parts[1])
    return r

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
        #xbmcgui.DialogProgress.__init__(self)
        super(DialogProgress, self).__init__()
        self.lines = [line1, line2, line3]
        self.create(heading, *self.lines)
        self.update(0)
        self.num_steps = num_steps
        self.step = 0
        self.progress = 0
        if self.num_steps != None:
            print 'NUMSTEPS: %d' % self.num_steps
            self.step = 100. / self.num_steps

    def set_num_items(self, num_items):
        self.num_steps = num_items
        self.step = 100. / self.num_steps
    
    def increment(self, num_incr_steps=1, line1=None, line2=None, line3=None):
        if line1 != None: self.lines[0] = line1
        if line2 != None: self.lines[1] = line2
        if line3 != None: self.lines[2] = line3
        self.progress += (num_incr_steps * self.step)
        #convert self.progress to int here,
        self.update(int(self.progress), *self.lines)


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
        self.parsed_url = urlparse(url)
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

    def handle_connect(self):
        '''A warning is printing if this method isn't overridden'''
        #check if dialog is cancelled.  Since we can't set a callback method
        #the best we can do is check the dialog status for every connect
        #and close event, hopefully it is a fast call otherwise this will impact
        #performance.
        if self.dp and self.dp.iscanceled():
            raise XBMCDialogCancelled
            

    def handle_close(self):
        if self.dp:
            self.dp.increment()
        if self.dp and self.dp.iscanceled():
            raise XBMCDialogCancelled
        self.close()

    def writable(self):
        return (len(self.write_buffer) > 0)

class XBMCVideoPluginException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class XBMCDialogCancelled(Exception):
    pass

def async_urlread(url_list, dp=None):   
    """Takes a list of urls and returns a list of responses once all of
    the requests have finished"""
    #create an HTTPClient for each url
    http_clients = [HTTPClient(url, dp) for url in url_list]
    #run the syncore loop, it will downloda all of the registered HTTPClients
    asyncore.loop()

    #if the dialog progress was cancelled we must re-raise the exception here
    #since the asyncore.loop seems to eat the exception
    if dp and dp.iscanceled():
        raise XBMCDialogCancelled

    #finished successfully, return a list of the responses
    return [c.read_buffer.getvalue() for c in http_clients]

def urlread(url, data=None):
    """Helper function to reduce code needed for a simple urlopen()"""
    f = urllib2.urlopen(url, data)
    page_contents = f.read()
    f.close()
    return page_contents

#Code modeled after python's urllib.unquote
_hextochr = dict(('%02x' % i, chr(i)) for i in range(256))
_hextochr.update(('%02X' % i, chr(i)) for i in range(256))

def unhex(s):
    '''unquote(r'abc\x20def') -> 'abc def'.'''
    res = s.split(r'\x')
    for i in xrange(1, len(res)):
        item = res[i]
        try:
            res[i] = _hextochr[item[:2]] + item[2:]
        except KeyError:
            res[i] = '%' + item
        except UnicodeDecodeError:
            res[i] = unichr(int(item[:2], 16)) + item[2:]
    return ''.join(res)

    





















