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

import re
import urllib2
import sys
from urlparse import urlparse, urlunsplit
from urllib import quote_plus, unquote_plus, urlencode
from common import parse_qs
try:
    from collections import namedtuple
except ImportError:
    from extra import namedtuple

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

URLRule = namedtuple('URLRule', 'endpoint, url_format, pattern, view_func, keywords, name, options')

def make_url_rule(rule, endpoint, view_func, name=None, **options):
    # Get keywords first. These are the positional vars in <> in the URL
    keywords = re.findall(r'\<(.+?)\>', rule)

    #change <> to {} for use with str.format()
    url_format = rule.replace('<', '{').replace('>', '}')

    # Make a regex pattern for matching incoming URLs
    p = rule.replace('<', '(?P<').replace('>', '>[^/]+?)')
    # Match the entire path
    pattern = re.compile('^' + p + '$')

    rule = URLRule(endpoint, url_format, pattern, view_func, keywords, name, options)
    return rule

def make_listitems(iterable):
    ''' Takes either a list of tuples, or a list of dicts and retunrs a list of 
    xbmcgui.ListItems'''
    #if tuple
    lis = None
    if iterable[0] == tuple:
        lis = [self.make_listitem(*item) for item in iterable]
    else: # if iterable is a list of dicts
        lis = [self.make_listitem(**item) for item in iterable]
    return lis

def clean_info(info_dict):
    '''Verifies none of the values are None, otherwise XBMC wll break'''
    if not info_dict:
        return None
    # Filter out bad items?
    ret = filter(lambda pair: pair[1] is not None, info_dict.items())

    # Make sure we have at least one item left
    if len(ret) == 0:
        return None
    
    # We have at least one item, return a dict
    return dict(ret)

def make_listitem(label, label2=None, iconImage=None, thumbnail=None, path=None, info=None):
    # XBMC doesn't like None values, so convert all None's to empty strings
    if label is None: label = 'PARSE ERROR'
    if label2 is None: label2 = ''
    if iconImage is None: iconImage = ''
    if thumbnail is None: thumbnail = ''
    if path is None: path = ''

    li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage, thumbnailImage=thumbnail, path=path)

    # Clean info dict and remove and values with None, XBMC will break
    cleaned_info = clean_info(info)
    if cleaned_info:
        li.setInfo('video', cleaned_info)
    return li

class C(object):
    '''class to hold colors'''
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    magenta = '\033[35m'
    cyan = '\033[36m'
    end = '\033[0m'

class XBMCSwiftPlugin(object):
    routes = []
    default_route = None

    def __init__(self, name, plugin_id, debug=False):
        '''need to get id here'''
        self._plugin = xbmcaddon.Addon(id=plugin_id)
        self.name = name
        
        # Check if we are being run from the command line.
        # Can set it manually
        self.debug = debug

        # If we are running from command line, there will be 4 args instead of 3
        if len(sys.argv) == 4:
            self.debug = True
            self.mode = 'debug'
        else:
            self.mode = 'xbmc'

        # If we're in debug mode, shift argv to the left 1,
        # This removes the python executable name from the args
        if self.debug:
            sys.argv = sys.argv[1:]
        self._init_args(sys.argv)

    def _init_args(self, argv):
        self.argv0 = argv[0]
        self.argv1 = argv[1]
        self.handle = int(self.argv1)
        self.argv2 = argv[2]
        self.args = parse_qs(self.argv2)

        # Doesn't work correctly in pyton 2.4
        #url = urlparse(self.argv0)
        def urlparse(url):
            protocol, remainder = url.split('://', 1)
            netloc, path = remainder.split('/', 1)
            return (protocol, netloc, '/' + path)

        url = urlparse(self.argv0)
        self.protocol = url[0]
        self.netloc = url[1]
        self.path = url[2]

    def get_setting(self, key, pickled_value=True):
        if pickled_value:
            return pickle.loads(self._plugin.getSetting(key))
        return self._plugin.getSetting(key)

    def set_setting(self, key, val, pickled_value=True):
        if pickled_value:
            return self._plugin.setSetting(key, pickle.dumps(val))
        return self._plugin.setSetting(key, val)

    def add_url_rule(self, rule, endpoint=None, view_func=None, name=None, default=False, **options):
        if endpoint is None:
            endpoint = view_func.__name__

        rule = make_url_rule(rule, endpoint, view_func, name, **options)
        
        if default:
            self.default_route = rule
        self.routes.append(rule)

    def route(self, rule, default=False, name=None, **options):
        #return a decorator
        def decorator(f):
            self.add_url_rule(rule, None, f, name=name, default=default, **options)
            return f
        return decorator
        
    def url_for(self, endpoint, **values):
        '''Add the ability to pass a name argument instead of just an endpoint.
        Currently will match endpoint to an actual endpoint and also to a give name argument'''
        #URLRule = namedtuple('URLRule', 'endpoint, format, pattern, view_func, keywords, name, options')

        # Loop through our list of URL rules and break when we find a rule for the specified endpoint
        url_format = None
        selected_rule = None

        for rule in self.routes:
            if rule.endpoint == endpoint or rule.name == endpoint:
                selected_rule = rule
                #url_format = rule[0]
                break
                #path = route[0].format(**encoded_values)

        # Could't find endpoint
        if selected_rule is None:
            print 'Couldn\'t find a rule for the specified endpoint, "%s".' % endpoint
            return
        
        # Now we need to separate the given values dictionary into two dicts. One dict will
        # contain the key/val pairs to be substituted into the URL path. The other dict will
        # contain all remaining values and will be encoded into the query string of the URL.
        # URL keywords
        url_keys = filter(lambda k: k in selected_rule.keywords, values.keys())
        qs_keys = filter(lambda k: k not in url_keys, values.keys())
        qs_params = [(k, values[k]) for k in qs_keys]


        # Encode the values going into the URL path and create the new URL
        url_params = dict((k, quote_plus(values[k])) for k in url_keys)

        try:
            path = selected_rule.url_format.format(**url_params)
        except AttributeError:
            path = selected_rule.url_format
            # Old version of python, doesn't have format method on a string, hack our own with re for now?
            for k, v in url_params.items():
                p = re.compile('{%s}' % k)
                path = re.sub(p, v, path)
                

        # Create querystring from remaining key/vals
        qs = urlencode(qs_params)

        url = urlunsplit((self.protocol, self.netloc, path, qs, None))
        return url
        #return urlunsplit((self.protocol, self.netloc, path, qs, None))

    def set_resolved_url(self, url):
        if self.debug:
            print 'ListItem resolved to %s' % url
        li = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(self.handle, True, li)
        if self.mode in ['interactive', 'crawl']:
            return []

    def route_url(self, url):
        '''Need to update and pass in extra options from plugin.route as well'''
        '''Also need to check endpong names as well'''

        # Need to implement own cache now!!!!
        # Check cache before checking any url rules!
        # Cache will be pickeled items list passed to add_items, so simply load and call add_items
        selected_rule = None
        values = {}

        for rule in self.routes:
            m = rule.pattern.search(url)
            if m:
                selected_rule = rule
                values = dict(((key, unquote_plus(val)) for key, val in m.groupdict().items()))
                break
        else:
            #fallback to default rule, could be = to None
            selected_rule = self.default_route
        
        if selected_rule is None:
            print 'Didn\'t match any rules, set the default route for now perhpas'
        # Add any default optinos to the dict if keky doesn't exist
        # If we are calling a default rule, we do not match any values in the URL, however we can still
        # supply values provided in the @route decorator
        [values.update({k: v}) for k, v in selected_rule.options.items() if k not in values.keys()]

        # Now call the route with our args
        return selected_rule.view_func(**values)

    def add_item(self, label=None, label2=None, icon=None, thumbnail=None, path=None, info=None,
                  url=None, is_folder=None):
        li = make_listitem(label, label2, icon, thumbnail, path, info)
        if not xbmcplugin.addDirectoryItem(self.handle, url, li, is_folder):
            raise
    
    def add_items(self, iterable):
        ''' Takes a list of dicts keyed with the keyword args in add_item()'''
        items = []
        if self.debug:
                #print '[0] ..'
            pass

        for i, item in enumerate(iterable):
            if self.debug:
                print '[%d] %s%s%s (%s)' % (i + 1, C.blue, item.get('label'), C.end, item.get('url'))


            li = make_listitem(*[item.get(key) for key in ['label', 'label2', 'icon', 'thumbnail', 'path', 'info']])

            if item.get('is_playable') is True:
                li.setProperty('IsPlayable', 'true')
            items.append((item['url'], li, item.get('is_folder', True)))
        
        if self.mode not in ['interactive', 'crawl']:
            print '*****************************************'
            print self.handle
            print len(items)
            print items
            if not xbmcplugin.addDirectoryItems(self.handle, items, len(items)):
                raise Exception, 'problem?'
        else:
            # If crawl or interactive, return a list of urls
            #urls = [self.lastpath]
            urls = []
            urls.extend(map(lambda item: item[0], items))
            return urls
        xbmcplugin.endOfDirectory(self.handle)

    #def add_directory_item(self, url, listitem, is_folder=True):
        #if not xbmcplugin.addDirectoryItem(self.handle, url, listitem, is_folder):
            #raise Exception, 'poop'

    #def add_directory_items(self, 
        #handle, url, listItem, isFolder, totalItems
        #handle, items, totall itmes where items is list of tuples (url, li) or (url, li, isFolder)


    def crawl(self):
        ''' Call the default handler, override plugin_additems, get URLS and other details, print them to screen
        Add all urls to a  set.'''
        self.mode = 'crawl'
        argv = sys.argv

        # Call default rule
        print 'Resolving %s ...' % self.path

        # urls_tovisit = []
        # urls_visited = set()

        urls_tovisit = self.default_route.view_func()
        urls_visited = set()

        while len(urls_tovisit) > 0:
            # Get first url in the list and add it to a visited list
            url = urls_tovisit.pop(0)
            if url in urls_visited:
                continue
            urls_visited.add(url)
            print '--\n'
            print 'Next url to resolve: %s' % url
            raw_input('> go on?')
            parts = urlparse(url)
            url_noqs = urlunsplit((parts[0], parts[1], parts[2], None, None))
            argv[0] = url_noqs
            argv[2] = parts[3]
            self._init_args(argv)
            urls = self.route_url(self.path)

            # Filter new urls by checking against urls_visited set
            urls = filter(lambda u: u not in urls_visited and u not in urls_tovisit, urls)
            # also need to check against urls currently in the queu
            #print urls

            urls_tovisit.extend(urls)
            #print len(urls_tovisit)
            print ''

    def interactive(self):
        ''' Interactive session, choose next link or 'q' to quit.'''
        self.lastpath = None
        self.mode = 'interactive'
        print 'Starting with self.path'
        argv = sys.argv[:]
        #self.add_items = self._crawl_add_items
        urls = self.route_url(self.path)
        #print urls

        inp = raw_input('Choose an item or "q" to quit: ')
        print '--\n' 
        while inp != 'q':
            self.lastpath = self.path
            parts = urlparse(urls[int(inp) - 1])
            url_noqs = urlunsplit((parts[0], parts[1], parts[2], None, None))
            argv[0] = url_noqs
            argv[2] = parts[3]
            self._init_args(argv)
            urls = self.route_url(self.path)
            inp = raw_input('Choose an item or "q" to quit: ')
            print '--\n' 
            
    def run(self):
        '''The main entry point for a plugin. Will route to the proper view based on the path
        parsed from the command line arguments.'''
        self.route_url(self.path)

   
