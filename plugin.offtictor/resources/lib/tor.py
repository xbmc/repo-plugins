'''
The MIT License (MIT)

Copyright (c) 2015 Kurochkin Vasiliy

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software 
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial 
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT 
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''
__author__ = 'Qra'
__version__ = "0.1.0a0"

import requests
import logging

logger = logging.getLogger(__name__)

url_api = 'https://theoldreader.com/reader/api/0/'
url_login = 'https://theoldreader.com/accounts/ClientLogin'


class Connection(object):
    """ Connection to TheOldReader API  """

    def __init__(self, email, password, client="TORPythonAPI"):
        self._logger = logging.getLogger(__name__ + ".TheOldReaderConnection")
        self.client = client
        self.email = email
        self.password = password
        self.header = {'user-agent': "TORPythonAPI/" + __version__}
        self.auth_code = None

    def make_request(self, url, var, use_get=True):
        """
        Make request to url (if not loggedin -> tries to)

        :param url: Url to load
        :type url: str
        :param var: Additional information for request (get or post data)
        :type var: dict
        :param use_get: Use http GET (default: True) (alternative: POST)
        :type use_get: bool
        :return: Response from server
        :rtype: None | int | float | str | list | dict
        """
        if self.auth_code is None:
            self.login()

        header = {}
        if self.auth_code:
            header['Authorization'] = "GoogleLogin auth=" + self.auth_code
        header.update(self.header)

        var_json = {'output': 'json'}
        var_json.update(var)
        '''
        for param in var:
            self._logger.debug(param + ":" + str(var[param]))
        '''
        if use_get:
            response = requests.get(url, params=var_json, headers=header)
        else:
            response = requests.post(url, data=var_json, headers=header)

        response.raise_for_status()
        try:
            result = response.json()
        except ValueError:
            result = None
        return result

    def login(self, username=None, password=None):
        """
        Login in and retrieve api token

        :param username: Username or email (default: None)
            if not set, use internal
        :type username: str
        :param password: Password (default: None)
            if not set, use internal
        :type password: str
        :rtype: None
        """
        if not username:
            username = self.email
        if not password:
            password = self.password
        var = {
            'client': self.client,
            'accountType': 'HOSTED_OR_GOOGLE',
            'service': 'reader',
            'Email': username,
            'Passwd': password
        }
        # do login
        self.auth_code = ""
        resp1 = self.make_request(url_login, var, use_get=False)
        self.auth_code = resp1['Auth']
        self._logger.info(u"Logged in as {}".format(username))


class Item(object):

    def __init__(self, connection, item_id):
        """
        Initialize object
        :param connection: The corresponding connection
        :type connection: TheOldReaderConnection
        :param item_id: Id of item
        :type item_id: str
        :rtype: None
        """
        self.item_id = item_id
        self.connection = connection
        self.title = None
        self.content = None
        self.href = None
        self.mediaUrl = None
        self.published = None
        self.enctype = None

    # TODO: No use_get
    def _make_api_request(self, url_end, var, use_get=True):
        return self.connection.make_request(url_api + url_end, var, use_get)

    def _make_edit_request(self, state, undo=False, additional_var=None):
        """
        Make request to api for this item
        :param state: Which attribute to change (read, starred, like, ..)
        :type state: str
        :param undo: If true, undos the state (Unread, remove starred, ..)
            (default: False)
        :type undo: bool
        :param additional_var: Add aditional fields to url params
        :type additional_var: None | dict
        :return: Response of urlopen
        :rtype: None | int | float | str | list | dict
        """
        var = {
            'i': self.item_id
        }

        if undo:
            var['r'] = 'user/-/state/com.google/' + state
        else:
            var['a'] = 'user/-/state/com.google/' + state
        if additional_var:
            var.update(additional_var)
        return self._make_api_request('edit-tag', var, False)

    # Mark as read
    def mark_as_read(self):
        return self._make_edit_request('read')

    # Mark as unread
    def mark_as_unread(self):
        return self._make_edit_request('read', True)

    # Mark as starred
    def mark_as_starred(self):
        return self._make_edit_request('starred')

    # remove_starred_mark
    def remove_starred_mark(self):
        return self._make_edit_request('starred', True)

    # Mark as liked
    def mark_as_liked(self):
        return self._make_edit_request('like')

    # remove_liked_mark
    def remove_liked_mark(self):
        return self._make_edit_request('like', True)

    # Mark as shared
    def mark_as_shared(self):
        return self._make_edit_request('broadcast')

    # Mark as shared (with_note)
    def mark_as_shared_with_note(self, note):
        return self._make_edit_request(
            'broadcast',
            additional_var={'annotation': note}
        )

    # remove_shared_mark
    def remove_shared_mark(self):
        return self._make_edit_request('broadcast', True)

    # get more information(title, description, link)
    def get_details(self):
        resp3 = self._make_api_request(
            'stream/items/contents',
            {'i': self.item_id}
        )
        item_det = resp3['items'][0]
        self.title = item_det['title']
        self.content = item_det['summary']['content']
        self.published = item_det['published']
        self.href = item_det['alternate'][0]['href']
        if 'enclosure' in item_det:
            self.mediaUrl = item_det['enclosure'][0]['href']
            self.enctype = item_det['enclosure'][0]['type']
        self.source = resp3['title']
        self.source_id = resp3['id']

class ItemsSearch(object):
    def __init__(self, connection):
        """
        Initialize object
        :param connection: The corresponding connection
        :type connection: TheOldReaderConnection
        :rtype: None
        """
        self.connection = connection
        self.next_pointer = None

    def _make_search_request(self, var, limit_items=1000):
        var['n'] = limit_items
        return self.connection.make_request(
            url_api + 'stream/items/ids',
            var,
            use_get=True
        )

    def _load_rest(self, continuation, var, limit_items=1000, items_list=None, stop=False):
        if items_list is None:
            items_list = []
        while continuation is not None:
            var['c'] = continuation
            resp = self._make_search_request(var, limit_items)
            continuation = resp.get('continuation')
            self.next_pointer = continuation
            items_list.extend(resp['itemRefs'])
            if stop:
                break
        return [
            Item(self.connection, item.get('id'))
            for item in items_list
        ]
        
    def _pre_load_rest(self, continuation, var, limit_items=1000, stop=False):
        ''' 
        private function to prevent repeating same code for diferent request modes
        :param continuation: id for the next bloc (limit_items-sized) of feeds
        :param var: parameters in the TOR request
        :param limit_items: size of the feeds bloc
        :param stop: stops asking for further blocs
        '''
        if continuation!=None and stop==True:
            # asking for a new page
            items_list = None
        else:
            #asking for the first page or all of them
            resp = self._make_search_request(var, limit_items)
            continuation = resp.get('continuation')
            self.next_pointer = continuation
            items_list = resp.get('itemRefs', [])
            if (stop):
                #just the first one, this will prevent loop inside _load_rest
                continuation = None
        return self._load_rest(continuation, var, limit_items, items_list, stop)

    def get_unread_only(self, limit_items=1000, feed=None, stop=False, continuation=None):
        ''' 
        Gets just unread posts
        :param limit_items: size of the feeds bloc
        :param feed: gets only posts from this feed (all if none)
        :param stop: stops asking for further blocs
        :param continuation: id for the next bloc (limit_items-sized) of feeds
        '''
        
        var = {
            's': 'user/-/state/com.google/reading-list',
            'xt': 'user/-/state/com.google/read'
        }
        if (feed!=None):
            var['s'] = feed
        return self._pre_load_rest(continuation, var, limit_items, stop)

    def get_starred_only(self, limit_items=1000, feed=None, stop=False, continuation=None):
        ''' 
        Gets just starred posts
        :param limit_items: size of the feeds bloc
        :param feed: gets only posts from this feed (all if none)
        :param stop: stops asking for further blocs
        :param continuation: id for the next bloc (limit_items-sized) of feeds
        '''
        var = {
            's': 'user/-/state/com.google/starred'
        }
        if (feed!=None):
            var['s'] = feed
        return self._pre_load_rest(continuation, var, limit_items, stop)

    def get_liked_only(self, limit_items=1000, feed=None, stop=False, continuation=None):
        ''' 
        Gets just liked posts
        :param limit_items: size of the feeds bloc
        :param feed: gets only posts from this feed (all if none)
        :param stop: stops asking for further blocs
        :param continuation: id for the next bloc (limit_items-sized) of feeds
        '''
        var = {
            's': 'user/-/state/com.google/like'
        }
        if (feed!=None):
            var['s'] = feed
        return self._pre_load_rest(continuation, var, limit_items, stop)

    def get_shared_only(self, limit_items=1000, feed=None, stop=False, continuation=None):
        ''' 
        Gets just shared posts
        :param limit_items: size of the feeds bloc
        :param feed: gets only posts from this feed (all if none)
        :param stop: stops asking for further blocs
        :param continuation: id for the next bloc (limit_items-sized) of feeds
        '''
        var = {
            's': 'user/-/state/com.google/broadcast'
        }
        if (feed!=None):
            var['s'] = feed
        return self._pre_load_rest(continuation, var, limit_items, stop)

class Subscriptions (object):
    def __init__(self, connection, mode = None):
        """
        Initialize object
        :param connection: The corresponding connection
        :type connection: TheOldReaderConnection
        :rtype: None
        
        :param mode: search the beginning of the post enctype (i.e. 'audio')
        """
        self.connection = connection
        self.id = None
        self.title = None
        self.iconUrl = None
        self.firstitemmsec = None
        self.unread_count = 0
        
        self.unread_response = None
        self.mode = mode
        self.matches = False
        
    def get_all(self, limit_items=1000):
        return self.get_items(False, limit_items)
    
    def get_unread(self, limit_items=1000):
        return self.get_items(True, limit_items)
    
    def get_all_cursor(self, limit_items=1000):
        return SubscriptionsCursor(self.get_items(False, limit_items), self.mode)
    
    def get_unread_cursor(self, limit_items=1000):
        return SubscriptionsCursor(self.get_items(True, limit_items), self.mode)
        
    def get_items(self, just_unread = False, limit_items=1000):
        var = {
            
        }
        var['n'] = limit_items
        response = self.connection.make_request(
            url_api + 'subscription/list',
            var,
            use_get=True
        )
        
        if just_unread:
            self.unread_response = self.connection.make_request(
                url_api + 'unread-count',
                var,
                use_get=True
            )
        
        s_list = []
        for feed in response['subscriptions']:
            s = Subscriptions(self.connection)
            s.id =  feed['id']
            s.title = feed['title']
            s.iconUrl = 'http:' + feed['iconUrl']
            s.firstitemmsec = feed['firstitemmsec']
            s.unread_count = self.count_unread(feed['id'])
            s.mode = self.mode
            
            if (just_unread==False or s.unread_count>0):
                s_list.append(s)
            
        return s_list
    
    def count_unread(self, feedId):
        '''
        Once list is gotten, helps to find the feed unread counts
        '''
        for counter in self.unread_response['unreadcounts']:
            if counter['id']==feedId:
                return counter['count']
            
        return 0
    
    def matches_mode (self, feedId):
        '''
        Checks if the first post of the feed matches with the mode
        Better use it with a SubscriptionsCursor and informing about the progress, cause it's a quite expensive process
        '''
        if self.mode != None:
            search = ItemsSearch(self.connection)
            unread = search.get_unread_only(1, feedId, True)
            item = unread[0]
            if item != None:
                item.get_details()
                if item.enctype != None and item.enctype.startswith(self.mode):
                    return True
                else:
                    return False
        else:
            return True


class SubscriptionsCursor(object):
    '''
    maintains an array and provides deferred, expensive queries to be done one by one
    '''
    def __init__(self, subscriptions, mode):
        self.subscriptions = subscriptions
        self.mode = mode
        self.current = 0
        
    def next(self):
        if self.current>=len(self.subscriptions):
            return False
        s = self.subscriptions[self.current]
        self.current = self.current + 1
        if s.matches_mode(s.id):
            s.matches = True
        return s
    
    def reset(self):
        self.current = 0
    
        
        
        
        