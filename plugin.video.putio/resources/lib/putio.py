#!/usr/bin/env python
# encoding: utf-8

# Created by Put.io.
# Copyright (c) 2010 Put.io.

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
    Basic Tutorial:
        
        from putio import *
        
        # connecting your put.io with your api key and api secret
        api = Api("123456","abcdef")
        
        # getting your items
        items = api.get_items()
        for it in items:
            print "%5s  %s" % (it.id, it.name)
        
        # creating a folder
        newitem = api.create_folder(name="blabla")
        
        # getting one item
        item = api.get_items(id=newitem.id)[0]
        #item = api.get_items()[0]
        
        # getting an item info
        item = item.update_info()
        print item.name, item.id, item.is_dir, item.__dict__
        
        # renaming an item
        print "old name: %s" % item.name
        newitem = item.rename_item("renamed by api")
        print "new name: %s" % newitem.name
        
        # moving an item to a target folder
        # 0 being root of your files
        newitem.move_item(target=0)
        
        # deleting an item
        newitem.delete_item()
        
        # searching items
        sresults = api.search_items("avi from:me type:video")
    
    See the site for more info.
    
    
    Todos:
    * oAuth support
    * Creating and getting MP4 Files
    * File Uploading
    * User Methods
    
"""


import sys
import socket
import urllib
import urllib2

try:
    import json
except ImportError:
    import simplejson as json


# setup
RPC_URL = "http://api.put.io/v1"

# constants
UNITS = ['B', 'K', 'M', 'G', 'T', 'P', 'E']
TIMEOUT = 60 #seconds
VERSION = "0.91"

# 0.92  transfers/add change
# 0.91  tidying up for the release; unicode human_size, user_idi user info
#       bugs; some user, friend and item methods        
# 0.90  updated auth, "v1"
# 0.85  reformated input and output. big changes on the api server.
# 0.84b typos
# 0.84  item_search to search_items, get_items orderby, get_friends
# 0.83  new stream url


def human_size(size):
    """
    Converts bytes to human readable strings
    
    Takes  : An Integer
    Returns: A String
    
    Example:
    >>> print human_size(12.66)            # 12.7B
    >>> print human_size(12345)            # 12.1K
    >>> print human_size(12345678)         # 11.8M
    >>> print human_size(12345678910)      # 11.5G
    >>> print human_size(12345678910111)   # 11.2T
    
    """
    
    if isinstance(size, unicode): size = int(size)
    
    s = float(size * 1.0)
    i = 0
    
    while size >= 1024.00 and i < len(UNITS):
        i += 1
        size /= 1024.00
    return "%.1f%s" % (size, UNITS[i])



def _send(obj, path, post=None, **args):
    """
    Chats with API Server.
    
    Takes  : A dict.
    Returns: JSON
    
    To format the output, call _result() method.
    
    Request Format:
    
    {
        "user_id"    : INTEGER,
        "api_key"    : STRING,
        "api_secret" : STRING,
        "params"     : DICTIONARY
    }
    
    Response Format:
    
    {
        "user_id"       : INTEGER,
        "response"      : {
                              "results"   : [{
                                                 .... data ....
                                            }]
                          },
        "error"         :null,
        "error_message" :null
    }
    
    """
    post_request = dict()
    
 
    if not obj:
        raise PutioError("You need to login first")
    else:
        post_request['api_key'] = obj.api_key
        post_request['api_secret'] = obj.api_secret

    
    url = RPC_URL + path
    if args: url += "?" + urllib.urlencode(args)

    # print url
    # print "0. REQUEST: %s: %s" % (type(post), post)

    post_request['params'] = dict()
    
    for k in post.keys():
        #if k not in ("user_id", "api_key", "api_secret"):         
        if k not in ("api_key", "api_secret"):         
            post_request['params'][k] = post[k]
        else:
            post_request[k] = post[k]
    
    # print "POSTREQUEST: %s" % post_request
    
    pre_post = {}
    pre_post['request'] = json.dumps(post_request)
    
    error_data = ""
    
    try:
        # print "1. POST: %s: %s" % (type(pre_post), pre_post)
        request = urllib2.Request(url, urllib.urlencode(pre_post))
        
        # default timeout time is 60 seconds.
        socket.setdefaulttimeout(TIMEOUT)
        
        if (sys.version_info[0] == 2 and sys.version_info[1] > 5) \
        or sys.version_info[0] > 2:
            u = urllib2.urlopen(request, timeout=TIMEOUT)
        else:
            u = urllib2.urlopen(request)
        
        data = u.read()

        # print "2. RECEIVED DATA: %s" % data
        
        return _result(obj, data)

    except urllib2.HTTPError, e:
        error_data = e.read()
        if e.code == 500:
            raise PutioError("An error occured. This may be a bug. Please \
report to the application provider.", e)
        elif e.code == 404:
            raise PutioError("Unknown method, service or parameters.", e)
        else:
            raise PutioError("Service unavailable. Please try again.", e)
    
    except urllib2.URLError, e:
        raise PutioError("Request failed. (%s)" % str(e), e)

    except UnboundLocalError, e:
        raise PutioError("Service unavailable. This may be a bug on the api \
server side. Please report following info: (%s)" % str(e), e)



def _result(obj, data):
    """
    Takes  : JSON
    Returns: A Dict
    
    Checks if the api server returned an error or not.
    Returns the error message or the success message.
    
    JSON Format that API Server returns:
    
    {
        "error": false,
        "error_message": null,
        "user_id": some_integer,
        "user_name": "username"
        "response": {
            "results": [ ...Always an array of things... ]
        }
    }
    
    
    """

    try:
        result = json.loads(data)
        # print "3. RESULT DATA: %s" % result
        
    except ValueError, e:
        #logger.error('Error: %s'  % e)
        #logger.error('Data: %s'   % data)
        #logger.error('Result: %s' % result)
        raise PutioError("Json error.", e)
    
    # It's now a python dictionary. Json.loads() makes necessary
    # conversions like "false" to "False", "null" to "None", etc.
    # print "3. JSON TO DICT: ", result
    
    if result['error'] is False: 
        obj.user_name = result['user_name']
        obj.user_id = result['id']
        
        return result['response']['results']
    
    else:
        #raise PutioError(result['error_message'])
        return None



def strip_tags(value):
    """
    Return the given HTML with all tags stripped.
    
    You may use this to strip the html tags from
    Put.io Dashboard Messages. (Optional)
    
    Usage:
        print strip_tags(MessageInstance.title)
    
    """
    
    import re
    return re.sub(r'<[^>]*?>', '', value)



class BaseObj(object):
    
    # Creates an object with given dictionary.
    def __init__(self, dictionary=None, **args):
        if dictionary:
            self.__dict__ = dictionary
        
        if len(args) > 0:
            for k,v in args.iteritems():
                self.__dict__[k] = v
    

    # def __getattr__(self, k):
    #     return self.__dict__[k]
    
    
    def _convert_to_string(self):
        if self.__dict__.has_key('file_type'):
            self.file_type = Item._int_to_filetype(self.file_type)
        if self.__dict__.has_key('dl_handler'):
            self.dl_handler = UrlBucket.dl_handler[str(self.dl_handler)]
        if self.__dict__.has_key('dltype'):
            self.dltype = UrlBucket.dltype[str(self.dltype)]



class PutioError(Exception):
    """
    PutioError Exception Class
    """
    
    def __init__(self, message='', original=None):
        self.message = message
        self.original = original
    
    def __str__(self):
        if self.original:
            original_name = type(self.original).__name__
            return '%s (Original Exception: %s, "%s")' % (self.message, 
                                                          original_name, 
                                                          self.original.args)
        else:
            return self.message



class User(BaseObj):
    """
    Sample user:
    
        u.name                  : 'aft'
        u.friends_count         : 497 
        u.bw_avail_last_month   : '0'
        u.bw_quota              : '161061273600' 
        u.shared_items          : 3
        u.bw_quota_available    : '35157040261' 
        u.disk_quota            : '206115891200' 
        u.disk_quota_available  : '158153510402' 
        u.shared_space          : 0
    
    """
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api



class Friend(BaseObj):
    """
    Sample friend
    
        f.dir_id    : '1407'
        f.id        : '2'
        f.name      : 'hasan'
    
    """
    
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api

    def get_items(self, **args):
        """
        Takes  : A friend instance
        Returns: A List of item objects.
        
        Shortcut for listing a friends shared items.
        """
        
        return self.api.get_items(parent_id = self.dir_id, **args)



class Message(BaseObj):
    """
    Dashboard message objects.
    
    Message Methods:
        
        message.delete()
    
    
    Message Attributes:
        
        message.id              (Integer)
        message.user_id         (Integer)
        message.title           (String)
        message.description     (None)
        message.importance      (Integer)
        message.file_name       (String)
        message.file_type       (String)
        message.user_file_id    (Integer)
        message.from_user_id    (Integer. If None, message is from Put.io)
        message.channel         (Integer)
        message.hidden          (Integer, 1 or 0)
    
    Sample:
        
        user_file_id            = 4
        user_id                 = 17
        description             = None
        title                   = '<a rel="userfile" href="/file/4">abcd.mp4 
                                  </a> <span class="dash-gray">(89.86K) 
                                  downloaded</span>'
        importance              = 0
        file_name               = 'abcd.mp4'
        id                      = 3773
        file_type               = 'audio'
        hidden                  = 0
        from_user_id            = None
        channel                 = 2
    
    """
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, *args)
        self.file_type = Item._int_to_filetype(self.file_type)
        self.api = api
    
    def delete(self):
        """
        Deletes messages. Returns none if unsuccessful.
        """
        
        args = {"id":self.id}
        
        result = _send(self.api, path="/messages", post=args, method="delete")
        
        if not result: return None



class Api(object):
    """
    A python interface into the Put.io API
    
    Example usage:
    
    To create an instance of the putio.Api class, with authentication:
        
        >>> from putio import *
        >>> api = api(YOUR_API_KEY, YOUR_API_SECRET)
    
    
    To get the list of your files:
        
        >>> items = api.get_items()
        >>> for i in items: print i.id, i.name
    
    
    To get the item list in a specified folder:
        
        >>> items = api.get_items(id=123)
        >>> for i in items: print i.id, i.name
    
    
    Api Methods:
        
        api.get_items()
        api.get_transfers()
        api.get_user()
        api.is_ready()
        api.create_folder()
        api.search_items()
        api.get_messages()
        api.create_subscription()
        api.get_subscription()
        api.get_folder_list()
        api.update_user_token()
        api.get_user_info()
        api.create_bucket()
        
    """
    

    
    def __init__(self, api_key, api_secret):
        self.user_id = None
        self.user_name = None
        self.access_token = None
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Token is required only for streaming links
        self.access_token = self._get_user_token()
        
        self.api = self

        
    def update_user_token(self):
        """
        Before streaming a video/audio file, its best to update the token.
        This method doesn't return anything. It just updates the Api instance.
        
        """
        self.access_token = self._get_user_token()
    
    
    def get_user_name(self):
        """
        Takes  : Nothing
        Returns: A String
        
        Returns the name of the authenticated user. You can use this to 
        welcome your user.
        
        """
        return self.user_name
    
    
    def is_ready(self):
        """
        Takes  : Nothing.
        Returns: True or False
        
        Checks if the authentication is successful. Returns False if it isn't.
        Probably, you won't be using this much.
        
        Example:
        >>> api = Api("key", "secret")
        >>> if api.is_ready(): print "Vuhuu!"
        
        """
        try:
            return self.user_name
        except: 
            return None


    def get_items(self, limit=20, offset=0, parent_id=0, **arguments):
        """
        Takes  : Item attributes [Optional]
        Returns: An Array of Item objects
        
        Example:
        >>> import putio
        >>> api = putio.Api(YOUR_API_KEY, YOUR_API_SECRET)
        >>> items = api.get_items()                     #without an argument
        >>> items = api.get_items(type="video")    #with an argument
        >>> for i in items: print i.name, i.id, i.type
        
        You can use these optional parameters while selecting item(s):
        
            id          = STRING or INTEGER
            parent_id   = STRING or INTEGER
            offset      = INTEGER (Default:0)
            limit       = INTEGER (Default: 20)
            type        = STRING  (See Item class for available types)
            orderby     = STRING  (Default: createdat_desc)
        
        Orderby parameters:
        
            id_asc
            id_desc
            type_asc
            type_desc
            name_asc
            name_desc
            extention_asc
            extention_desc
            createdat_asc
            createdat_desc (Default)
        
        See Item Class doc for the available attributes.
        
        """
        
        items = []
        args = {"limit":limit, "offset":offset, "parent_id":parent_id}
        
        for k,v in arguments.iteritems(): args[k] = v
        
        if "type" in arguments:
            args['type'] = Item._filetype_to_int(arguments["type"])
        
        result = _send(self.api, path="/files", post=args, method="list")
        
        if result:
            self.update_user_token()
            
            for r in result: 
                items.append(Item(self.api, r))
            
            return items
        else:
            raise PutioError("You have no items to show.")
    
    
    def get_transfers(self):
        """
        Takes  : Nothing
        Returns: An Array of Transfer objects
        
        Example:
        >>> trans = api.get_transfers()
        >>> if newtransfers:
        >>>    for t in newtransfers:
        >>>        print t.name, t.status, t.percent_done
        >>> else: print "you have no active transfers"
        
        See Transfer Class doc for the available attributes.
        
        """
        transfers = []
        
        args = {}
        transferlist = _send(self, path="/transfers", post=args, method="list")
        
        if len(transferlist) > 0:
            for k in transferlist:
                transfers.append(Transfer(self.api, k))
            return transfers
        else:
            return None
            raise PutioError('You have no active transfers at the moment.')
    
    
    def create_folder(self, name="New Folder", parent_id=0):
        """
        Takes  : A String   [Optional], and
                 An Integer [Optional]
        Returns: A Single Item object if successful.
        
        Example:
        >>> newfolder = api.create_folder(name="Created by Api")
        >>> if newfolder: print "%s is created." % newfolder.name
        
        """
        
        args = {"name":name, "parent_id":parent_id}
        newfolder = _send(self.api, 
                            path="/files", 
                            post=args, 
                            method="create_dir")
                            
        
        if newfolder and isinstance(newfolder, list):
            newfolder = newfolder[0]
            newfolder['id'] = int(newfolder['id'])
            return Item(self.api, newfolder)
        else: 
            #raise PutioError('Folder could not be created.')
            return None
    
    
    def search_items(self, query):
        """
        Takes  : A String
        Returns: An Array of Item objects
        
        Returns search results. You may add search parameters to the string
        such as:
            
            "from:'me'"      (from:shares|jack|all|etc.)
            "type:'video'"   (audio|image|iphone|all|etc.)
            "ext:'mp3'"      (avi|jpg|mp4|all|etc.)
            "time:'today'"   (yesterday|thismonth|thisweek|all|etc.)
        
        
        Example:
        >>> searchresults = api.search_items("'jazz' from:'me' type:'audio'")
        >>> if searchresults:
        >>>     for sr in searchresults: print sr.name
        
        """
        
        search_results = []
        
        args = {"query":query}
        result = _send(self, path="/files", post=args, method="search")
        
        if result:
            self.update_user_token()
            for r in result: search_results.append(Item(self.api, r))
            return search_results
        else:
            return None
    
    
    def get_messages(self):
        """
        Takes  : Nothing
        Returns: An Array of Message objects
        
        Returns your dashboard messages.
        
        Example:
        >>> msgs = api.get_messages()
        >>> if msgs:
        >>>     for m in msgs: print m.title
        
        """
        messages = []
        
        args = {}
        result = _send(self, path="/messages", post=args, method="list")
        
        if result:
            for r in result: messages.append(Message(self.api, r))
            return messages
        else:
            return None
    
    
    def create_subscription(self, name="My LegalTorrents Subscription",
                            url="http://www.legaltorrents.com/rss.xml",
                            **arguments):
        """
        Takes  : A String for name, a string for URL, and optional args.
        Returns: A Single Subscription object
        
        Creates a new subscription and returns it.
        
        Example:
        >>> newsub = api.create_subscription(name="Mininova",
                     url="http://www.mininova.org/rss.xml")
        >>> if newsub: print "%s created." % newsub.name
        
        See Subscription Class for available attributes
        
        """
        
        args = {"title":name, "url":url}
        for k in arguments.keys(): args[k] = arguments[k]
        result = _send(self, path="/subscriptions", post=args, method="create")
        
        if result:
            return Subscription(self.api, result[0])
        else:
            return None
    
    
    def get_subscriptions(self, **arguments):
        """
        Takes: Nothing
        Returns: An Array of Subscription objects
        
        Returns a list of your subscriptions.
        
        Example:
        >>> subs = api.get_subscriptions()
        >>> if newsub:
        >>>     for s in subs: print subs.name
        
        See Subscription Class for available attributes
        
        """
        
        subscriptions = []
        
        args = {}
        result = _send(self, path="/subscriptions", post=args, method="list")
        
        if len(result) > 0:
            for r in result:
                if len(arguments) > 0:
                    for k,v in arguments.iteritems():
                        if r[k] == v: 
                            subscriptions.append(Subscription(self.api, r))
                else:
                    subscriptions.append(Subscription(self.api, r))
            return subscriptions
        else:
            return None
    
    
    def get_folder_list(self):
        """
        Takes  : Nothing
        Returns: An Array of item objects.
        
        Notice that this method returns a flat list of your folders. Create
        your own method if you need a tree like list.
        
        Parent_id is id of the container folder
        
        Example:
        >>> folderlist = api.get_folder_list()
        >>> if folderlist:
        >>>     for f in folderlist: print f.name
        
        
        Here is the returned item before being processed:
            
            {
                u'dirs': [...{sub folder 1}, {sub folder 2}...],  # or []
                u'shared': None,
                u'id': u'4220',
                u'name': u'renamed (4)',
                u'default_shared': None
            }
        
        See Folder Class for available attributes
        
        """
        
        folders = []
        
        args = {}
        result = _send(self, path="/files", post=args, method="dirmap")
        
        # flattens the folder list
        def recursive(folderarray):
            if len(folderarray['dirs']) > 0:
                for fa in folderarray['dirs']:
                    folders.append(Folder(self.api, fa))
                    recursive(fa)
            else: folders.append(Folder(self.api, folderarray))
        
        if result:
            for r in result['dirs']:
                if len(r['dirs']) > 0:
                    recursive(r)
                else: folders.append(Folder(self.api, r))
            return folders
        else:
            return None
    
    
    def get_user_info(self):
        """
        Takes  : Nothing
        Returns: A Single User object if successful.
        
        Gives information about the authenticated user. Use this to inform
        user about its quotas, sharing size, current available space, etc.
        
        All sizes are in bytes. Use human_size(byte) to convert if necessary.

        Returned Attributes:
            
            info.bw_quota
            info.disk_quota
            info.bw_quota_available
            info.disk_quota_available
            info.name
            info.shared_space
            info.friends_count
            info.shared_items
        
        """
        
        args = {}
        result = _send(self, path="/user", post=args, method="info")[0]

        if result:
            return User(self.api, result)
        else:
            return None
    
    
    def _get_user_token(self):
        """
        Internal method for getting the user token.
        """
        
        args = {}
        result = _send(self, path="/user", post=args, method="acctoken")
         
        if result: 
            return result['token']


    def get_friends(self):
        """
        Takes  : Nothing
        Returns: An Array of Friend objects

        Returns friends of the authenticated user.

        Friend attributes:
        
            friend.id
            friend.name
            friend.dir_id

        Example:
        >>> friends = api.get_friends()
        >>> if friends:
        >>>     for f in friends: print f.name

        To get a friend's files, use dir_id as a parent_id with get_items()
        
        Option 1:
        >>> for f in friends:
        >>>     items[f] = api.get_items(parent_id=f.dir_id)

        >>> for i in items['jack']: print i.name
        
        Option 2:
        >>> for f in friends:
        >>>     f_items = f.get_items(limit=1)
        >>>         for fi in f_items: print fi.name
        
        Returns None if the friend has no items.
        """

        friends = []

        args = {}
        result = _send(self, path="/user", post=args, method="friends")

        if result:
            for r in result: friends.append(Friend(self.api, r))
            return friends
        else:
            return None

    def create_bucket(self):
        """
        Takes  : Nothing
        Returns: An empty bucket object.
        
        You'll need buckets to analyze and fetch URLs. Bucket is basicly a
        container of one or more URLs, which then you can analyze and make
        Put.io fetch the successfully analyzed URLs.
        
        To fetch some URLs, you'll need to:
        
          * Create a bucket (or use already existing one)
          * Use Add method to add some URLs to the bucket
          * Make Put.io analyze the bucket
          * Add more or delete some of them
          * And make Put.io fetch the URLs in the bucket.
          
        
        After the analyzation, you can get a report about the bucket content
        and the user quotas. For this, use get_report() method of UrlBucket 
        class.
          
        
        """
        return UrlBucket(self.api)


class Item(BaseObj):
    """
    An item can be a file or a folder.
    
    Avaiable Item methods are:
        
        item.rename_item()
        item.move_item()
        item.delete_item()
        item.update_info()
        item.get_download_url()
        item.get_zip_url()
        item.get_stream_url()
    
    Available Item attributes:
    Sizes are in bytes. Use human_size(byte) to convert if necessary.
        
        item.id
        item.name
        item.type
        item.size
        item.is_dir
        item.parent_id
        item.screenshot_url
        item.thumb_url
        item.file_icon_url
        item.download_url
    
    Example Folder Item:
        
        "id":"4394",
        "name":"Billie Ray Martin The Crackdown Project - Vol 1",
        "type":"folder",
        "size":"23472048",
        "is_dir":true,
        "parent_id":"0",
        "screenshot_url":"http://put.io/screenshot/b/dgRraFxlXmNl.jpg",
        "thumb_url":"http://put.io/screenshot/dgRraFxlXmNl.jpg",
        "file_icon_url":"http://put.io/images/file_types/folder.png",
        "folder_icon_url":"",
        "download_url":"http://node2.endlessdisk.com/download-file/17/4394",
        "zip_url":"/stream-basket/17/4394"}
    
    
    at the moment, type can be a:
        
        folder
        file
        audio
        movie
        image
        compressed
        pdf
        ms_doc
        text
        swf
        unknown
    
    """
    
    
    filetypes = {
        "folder"     : 0,
        "file"       : 1,
        "audio"      : 2,
        "movie"      : 3,
        "image"      : 4,
        "compressed" : 5,
        "pdf"        : 6,
        "ms_doc"     : 7,
        "text"       : 8,
        "swf"        : 9
    }
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api
        
    
    @staticmethod
    def _filetype_to_int(filetype):
        if Item.filetypes.has_key(str(filetype.lower())):
            return Item.filetypes[filetype]
        else: raise PutioError("Unknown type. Please use one of these: " \
                               "folder, file, audio, movie, image," \
                               "compressed, pdf, ms_doc, text, swf")
    
    
    @staticmethod
    def _int_to_filetype(filetypeint):
        """
        This method is not used because Api Server gives file types as string
        """
        
        newfiletypes = dict()
        # changes {"key":intvalue} to {"strvalue":"key"} first
        for k,v in Item.filetypes.iteritems(): newfiletypes[str(v)] = k
        
        # then finds value in keys
        if newfiletypes.has_key(str(filetypeint)): 
            return newfiletypes[str(filetypeint)]
        else: 
            return "unknown"
    
        
    def rename_item(self, name):
        """
        Takes  : A String [Required]
        Returns: A Single Item object
        
        Example:
        >>> print "Old Name: %s" % item.name
        >>> item = item.rename_item("New Item Name")
        >>> print "New Name: %s" % item.name
        
        Renames the item.
        
        """
        
        args = {"name":name, "id":self.id}

        result = _send(self.api, path="/files", post=args, method="rename")
        
        if result: return Item(self.api, result[0])
        else: return None
    
    
    def move_item(self, target=0):
        """
        Takes  : An Integer of target folder id. [Optional]
        Returns: A Single Item object
        
        Example:
        >>> item = item.move_item(target=1221)
        >>> if item:
        >>>     print "New Location: %s" % api.get_items(id=item.id).name
        
        Moves the item to another folder. Parent_id = 0 is the root folder
        of your disk space.
        
        """
        
        args = {"id":self.id, "parent_id":target}
        
        result = _send(self.api, path="/files", post=args, method="move")
        
        if result: return Item(self.api, result[0])
        else: return None
    
    
    def delete_item(self):
        """
        Takes  : Nothing
        Returns: Nothing if successful.
        
        Example:
        >>> item.delete_item()
        
        Destroys the item permanently.
        
        """
        
        args = {"id":self.id}
        
        result = _send(self.api, path="/files", post=args, method="delete")
        # fixme, check and return the result
        return result
    
    
    def update_info(self):
        """
        Takes  : Nothing
        Returns: A Single Item object
        
        Example:
        >>> item = item.update_info()
        >>> print item.__dict__
        
        Refreshes the items attributes. Useful for folders, because folders
        can be updated via subscriptions in the background.
        
        Raises an exception if unsuccessful.
        
        """
        
        args = {"id":self.id}

        result = _send(self.api, path="/files", post=args, method="info")
        
        if result:
            return Item(self.api, result[0])
        else:
            raise PutioError("Update failed. Item may be unavailable.")
    
    
    def get_download_url(self):
        """
        Returns: A String
        
        Example:
        >>> item = item.update_info()  #if necessary
        >>> print item.get_download_url()
        
        """
        if self.is_dir == False:
            return self.download_url
        else: 
            return None
    
        
    
    def get_stream_url(self):
        """
        Takes  : Nothing
        Returns: A String
        
        Returns the stream url of files. If item is a folder, then download
        url will be returned.
        
        """
        
        result = self.update_info()
        
        if result:
            if self.is_dir == False:
                sturl = str(self.stream_url) + "/atk/" \
                        + self.api.access_token
                return sturl
            else:
                return self.get_download_url()
        else: raise PutioError("Error: Item not found.")
    
    
    def create_mp4(self):
        """TODO"""
        pass

    
    def create_folder(self, name="New Folder", **args):
        """
        Takes  : Nothing
        Returns: An Item object
        
        Creates and returns a folder in another folder.
        
        """
        
        return self.api.create_folder(name = name, parent_id = self.id,**args)



class Folder(Item):
    """
    Folders are an Item object. Check Item class documentation for more info.
    
    Sample:
        
        folder.id               =  4394
        folder.name             =  "Billie Ray Martin The Crackdown Project"
        folder.type             =  "folder"
        folder.size             =  23472048
        folder.is_dir           =  True
        folder.parent_id        =  0
        folder.screenshot_url   =  "/images/file_types/file.png"
        folder.thumb_url        =  "/images/file_types/file.png"
        folder.file_icon_url    =  "/images/file_types/folder.png"
        folder.folder_icon_url  =  ""
        folder.download_url     =  "http://XX.put.io/download-file/17/4394"
        folder.zip_url          =  "http://XX.put.io/stream-basket/17/4394"
    
    """
    
    
    def __init__(self, api, dictionary=None, **args):
        Item.__init__(self, dictionary, **args)
        self.api = api

    def create_folder(self, name="New Folder", **args):
        """
        Creates a folder in another folder. This method is not being used
        at the moment.
        
        """
        
        return self.api.create_folder(name = name, parent_id = self.id,**args)



class Subscription(BaseObj):
    """
    Subscription Methods:
        
        edit()
        delete()
        toggle_status()
        undate_info()
        add_do_filters()
        add_dont_filters()
    
    
    Subscription Attributes:
        
        subsitem.id                  (integer)
        subsitem.url                 (string)
        subsitem.name                (string)
        subsitem.do_filters          (strings, seperated by commas)
        subsitem.dont_filters        (strings, seperated by commas)
        subsitem.parent_folder_id    (integer)
        subsitem.last_update_time    (string)
        subsitem.next_update_time    (string)
        subsitem.paused              (boolean)
    
    Example:
    >>> subsitem = api.get_subscriptions()[0]
    >>> if subsitem: print subsitem.name
    
    Sample Values:
        
        subsitem.id                =  860
        subsitem.url               =  "http://legaltorrents.com/music/rss.xml"
        subsitem.name              =  "Jazz Radio"
        subsitem.do_filters        =  "jazz, mp3"
        subsitem.dont_filters      =  "smooth, wav"
        subsitem.parent_folder_id  =  234
        subsitem.last_update_time  =  "2010-01-01 00:00"
        subsitem.next_update_time  =  "2010-01-01 00:00"
        subsitem.paused            =  False
    
    """
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api
    
    def edit(self, **arguments):
        """
        Takes  : A Dictionary of attributes to change
        Returns: A Single Subscription object
        
        Example:
        >>> newsub = subsitem.edit(name="newname", url="http://newurl", ...)
        >>> if newsubs: print "Subscription updated."
        
        Changes values of any given subscription attribute.
        
        """
        
        args = {"id":self.id, "title":self.name, "url":self.url}
        
        for k in arguments.keys(): args[k] = arguments[k]
        
        result = _send(self.api, 
                        path="/subscriptions", 
                        post=args, 
                        method="edit")
        
        if result: return Subscription(self.api, result[0])
        else: return None
    
    
    def delete(self):
        """
        Deletes the subscription item permanently.
        
        Example:
        >>> subsitem.delete()
        >>> if newsubs: print "Subscription updated."
        
        """
        
        args = {"id":self.id}
        result = _send(self.api, path="/subscriptions", post=args, method="delete")
        
        # fixme, better solution?
        if not result: return None
    
    
    def toggle_status(self):
        """
        Toggles the activity status of a subscription item. You may also
        change this value by editing the subscription item. This is just a
        shortcut we use.
        
        Example:
        >>> print subsitem.paused      # print True
        >>> subsitem.toggle_status()
        >>> print subsitem.paused      # print False
        
        """
        
        args = {"id":self.id}
        result = _send(self.api, path="/subscriptions", post=args, method="pause")
        
        if result:
            self.paused = result[0]['paused']
            return Subscription(self.api, result[0])
        else:
            return None
    
    
    def update_info(self):
        """
        Refreshes the subscription info. Use this to get the latest info
        about the subscriptions.
        
        Example:
        >>> subs.update_info()
        or
        >>> subs = subs.update_info
        """
        
        args = {"id":self.id}
        result = _send(self.api, path="/subscriptions", post=args, method="info")
        
        if result:
            return Subscription(self.api, result[0])
        else:
            raise PutioError("Subscription update failed.")
    
    
    def add_do_filters(self, *arguments):
        """
        Takes  : An Array of strings
        Returns: Updated Subscription object
        
        Adds keyword(s) to "do fetch" filter
        
        """
        args = self._modify_filter("add", *arguments)
        result = _send(self.api, path="/subscriptions", post=args, method="edit")
        
        if result:
            return Subscription(self.api, result[0])
        else:
            return False
    
    
    def add_dont_filters(self, *arguments):
        """
        Takes  : An Array of strings
        Returns: Updated Subscription object
        
        Adds keyword(s) to "don't fetch" filter
        
        """
        
        args = self._modify_filter("add", *arguments)
        result = _send(self.api, path="/subscriptions", post=args, method="edit")
        
        if result:
            return Subscription(self.api, result[0])
        else:
            return False
    
    
    def del_do_filters(self, *arguments):
        """
        Takes  : An Array of strings
        Returns: Updated Subscription object
        
        Deletes keyword(s) from "do fetch" filter
        
        """
        
        args = self._modify_filter("remove", *arguments)
        result = _send(self.api, path="/subscriptions", post=args, method="edit")
        
        if result:
            return Subscription(self.api, result[0])
        else:
            return False
    
    
    def del_dont_filters(self, *arguments):
        """
        Takes  : An Array of strings
        Returns: Updated Subscription object
        
        Deletes keyword(s) from "dont fetch" filter
        
        """
        
        args = self._modify_filter("remove", *arguments)
        result = _send(self.api, path="/subscriptions", post=args, method="edit")
        
        if result:
            return Subscription(self.api, result[0])
        else:
            return False
    
    
    def _modify_filter(self, task, *arguments):
        
        if self.do_filters is None: self.do_filters = ""
        if self.dont_filters is None: self.dont_filters = ""
        
        if task == "remove":
            self.do_filters = self._remove_filter(self.do_filters, *arguments)
            self.dont_filters = self._remove_filter(self.dont_filters, *arguments)
        else:
            self.do_filters = self._add_filter(self.do_filters, *arguments)
            self.dont_filters = self._add_filter(self.dont_filters, *arguments)
        
        args = {
            "id":self.id,
            "title":self.name,
            "url":self.url,
            "do_filters":self.do_filters,
            "dont_filters":self.dont_filters
        }
        
        return args
    
    
    @staticmethod
    def _add_filter(filt, *arguments):
        filters = list(filt.split(','))
        for a in arguments:filters.append(a)
        for n in range(len(filters)): filters[n] = str(filters[n]).strip()
        filters_str = ",".join(filters)
        return filters_str
    
    
    @staticmethod
    def _remove_filter(filt, *arguments):
        filters = list(filt.split(','))
        for a in arguments:filters.append(a)
        for n in range(len(filters)): filters[n] = str(filters[n]).strip()
        filters_str = ",".join(filters)
        return filters_str



class Transfer(BaseObj):
    """
    Transfer Methods:
        
        instance.destroy_transfer()
    
    
    Transfer Attributes:
        
        instance.id
        instance.name
        instance.status
        instance.percent_done
    
    
        human_size  : 200.0M 
        name        : The.Messenger.DVDRip.XviD-AMIABLE.part1.rar 
        url         : http://rapidshare.com/files/3232/abc.part1.rar' 
        needs_pass  : 0, 
        source      : rapidshare.com', 
        paid_bw     : 209715200', 
        error       : None, 
        type        : file', 
        size        : 209715200'
    
    Samples:
        
        instance.status       = 'Completed'
        instance.percent_done = '100'
        instance.id           = '45'
        instance.name         = 'A video file.avi'
        
        
        instance.status       : 'Waiting'
        instance.percent_done : '0'
        instance.id           : '47'
        instance.name         : 'abcde.mp4'
    
    """
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api
    
    def destroy_transfer(self):
        """
        Destroys an active transfer irreversibly.
        
        Example:
        >>> instance.destroy_transfer()
        
        """
        
        args = {"id":self.id}
        result = _send(self.api, path="/transfers", post=args, method="cancel")
        
        if result: return True
        else: return None
    
    def send_password(self):
        """TODO"""
        pass



class UrlBucket(object):
    """
    Url bucket is a completion of urls ready to fetch.
    
    UrlBucket Methods:
        
        bucket.add()
        bucket.analyze_and_add_urls()
        bucket.get_report()
        bucket.fetch()
    
    Static Methods:
        
        extract_urls()
        crawl_webpage()
    
    Abilities:
        
        * Add urls to the bucket
        * Get report of the bucket if you need to.
        * Fetch the urls
        
        You can also:
        * Analyze urls and add
        * Crawl a web page and extract URLs
        * Extract URLs from a text block
    
    
    """
    
    def __init__(self, api, singleurl=[], torrenturl=[], multiparturl=[], **info):
        
        self.api = api
        
        self.report = {}
                
        self.last_analyzed_bw_avail   = None
        self.last_analyzed_disk_avail = None
        self.req_space                = None
        self.paid_bw                  = None
        
        self.links = {"multiparturl":[], "torrenturl":[], "singleurl":[], "error":[]}
        
        self._add(singleurl=singleurl, torrenturl=torrenturl, multiparturl=multiparturl)

    
    
    def _add(self, singleurl=[], torrenturl=[], multiparturl=[], error=[], **info):
        """
        
        Internal method. Use add() instead, or better yet use analyze().
        
        """
        
        for v in [singleurl, torrenturl, multiparturl, error]:
            if not isinstance(v, list):
                raise PutioError("Add method takes only arrays.")
        
        if len(multiparturl) > 0:
            for m in multiparturl:
                self.links['multiparturl'].append(m)
        if len(torrenturl) > 0:
            for i in torrenturl:
                self.links['torrenturl'].append(i)
        if len(singleurl) > 0:
            for i in singleurl:
                self.links['singleurl'].append(i)
        if len(error) > 0:
            for i in error:
                self.links['error'].append(i)
        if len(info.keys()) > 0:
            self.last_analyzed_bw_avail   = info["last_analyzed_bw_avail"]
            self.last_analyzed_disk_avail = info["last_analyzed_disk_avail"]
            self.req_space                = info["req_space"]
            self.paid_bw                  = info["paid_bw"]
        return self
    
    
    def add(self, url):
        """
        Takes: String or array
        Returns: Dictionary of bucket items
        
        Adds url(s) to the bucket to analyze or fetch. We recommend using
        analyze_and_add_urls() method.
        
        """
        
        if url and isinstance(url, str):
            arg = {"url":url}
            self.links['singleurl'].append(Url(self.api, arg))
        elif url and isinstance(url, list):
            for u in url: 
                arg = {"url":url}
                self.links['singleurl'].append(Url(self.api, arg))
        else:
            raise PutioError("Add method takes a string or a list")
        
        return self.links
            
    
    def get_report(self):
        """
        Returns the report of your bucket's last analyzation. Each UrlBucket
        has its own report. After updating a bucket, remember to check its
        new report.
        
        Analyzed urls return like this one:
        
        {
            'dl_handler': 1,
            'name': 'Itemname.ext',
            'file_type': 1,
            'error': None,
            'url': 'http://torrent.a.b/file.torrent',
            'paid_bw': 0,
            'file_size': 244091464,
            'type_name': 'file',
            'dltype': 2,             #fixme whats this?
            'human_size': '232.78M'
        }
        
        """
        return {"Current Available Disk Space": self.last_analyzed_disk_avail,
                "Current Available Bandwidth": self.last_analyzed_bw_avail,
                "Required Space": self.req_space,
                "Bandwidth to be deducted from quota": self.paid_bw,
                "Urls":self.links}
    
    
    def fetch(self):
        """
        Takes  : A bucket instance
        Returns: Array of transfers. (All the active transfers, to be exact.)
        
        Initiates fetching all the links of the given URL Bucket instance.
        
        Returns newly added transfers. Erroneous transfers will have the word
        "Error" in "status".
        
        Also you may edit below to raise exceptions, if result.error is not
        false.
        
        """
        
        go_fetch = []
        
        for k in self.links.keys():
            for i in self.links[k]: 
                if k != "error": go_fetch.append(i.url)
                
        self.links = {}
        
        args = {"links":go_fetch}
        result = _send(self.api, path="/transfers", post=args, method="add")
        
        transfers = []

        if result:
            for r in result:
                transfers.append(Transfer(self.api, r))
            return transfers
        else:
            return None
            
    
    def analyze(self, links=None):
        """
        Takes  : An Array of URLs.
        Returns: An Array of Link objects.
        
        Example:
        Link objects can be fetched one by one by iterating the array.
        >>> links = bucket.analyze(array)
        >>> for l in links: l.fetch()
            
            or
        
        The whole bucket can be fetched with a single request.
        >>> bucket.analyze(array)
        >>> mytransfers = bucket.fetch()
        
        """
        multipart_urls  = []
        single_urls     = []
        torrent_urls    = []
        error_urls      = []
        
        paid_bw = 0
        req_space = 0
        
        #args = {"links":urllib.quote(text)}
        if links and isinstance(links, list): 
            args = {"links":links}
        elif links and isinstance(links, str):
            raise PutioError("Analyze method takes a list. Use " + \
                    "extract_urls() to convert string of urls to a list.")
        else: 
            go_analyze = []

            for k in self.links.keys():
                for i in self.links[k]: 
                    if k != "error": go_analyze.append(i.url)
                    
            args = {"links":go_analyze}
        
        result = _send(self.api, path="/urls", post=args, method="analyze")
        
        if result:
                        
            if len(result['items']['multiparturl']) > 0:
                for r in result['items']['multiparturl']:
                    # unicode to int
                    paid_bw += int(r['paid_bw'])
                    req_space += int(r['size'])
                    
                    for p in r["parts"]:
                        multipart_urls.append(Multipart(self.api, p))
            
            if len(result['items']['torrent']) > 0:
                for r in result['items']['torrent']:
                    torrent_urls.append(Torrent(self.api, r))
                    
                    paid_bw += int(r['paid_bw'])
                    req_space += int(r['size'])
            
            if len(result['items']['singleurl']) > 0:
                for r in result['items']['singleurl']:
                    single_urls.append(Url(self.api, r))
                    
                    paid_bw += int(r['paid_bw'])
                    req_space += int(r['size'])
                    
            if len(result['items']['error']) > 0:
                for r in result['items']['error']:
                    error_urls.append(Url(self.api, r))
            
            self.links = {"multiparturl":[], "torrenturl":[], 
                          "singleurl":[], "error":[]}
            
            self._add(multiparturl=multipart_urls,
                     singleurl=single_urls,
                     torrenturl=torrent_urls,
                     error=error_urls,
                     last_analyzed_disk_avail=result['disk_avail'],
                     last_analyzed_bw_avail=result['bw_avail'],
                     paid_bw=paid_bw,
                     req_space=req_space
                     )

            return self.get_report()
        else:
            return None
    
    
    def crawl_webpage(self, url):
        """
        Takes  : A String of a web page URL
        Returns: A String of cleaned url list
        
        Example:
        >>> newbucket = api.create_bucket()
        >>> cleaned_urls = newbucket.crawl_webpage("http://a.b.c/downloads")
        """
        return self.extract_urls(url)
    
    
    def extract_urls(self, text):
        """
        Takes  : A String
        Returns: A list of cleaned urls
        
        Example:
        >>> txt = "Check these out: http://a.b/c.torrent and ftp://a.b/c.rar"
        >>> urls = bucket.extract_urls(txt)
        >>> print urls
        ["http://a.b/c.torrent", "ftp://a.b/c.rar"]
        
        Extracts URLs from a block of text.
        
        
        * Links in the text are recognized by the protocol names such as http,
          ftp, etc.
        * Torrent file links do have to have .torrent extention.
        
        """
        
        extracted_urls = []
        
        args = {"txt":text}
        result = _send(self.api, path="/urls", post=args, method="extracturls")
        
        if result:
            for r in result: extracted_urls.append(r['url'])
            #return " \n".join(extracted_urls)
            return extracted_urls
        else: 
            return []
        


class Url(BaseObj):
    """
    For us, Url is a downloadable file link. These files can be any type.
    Sources can be ftp, http, etc.
    
    Url Attributes:
        
        instance.dl_handler  = 'Single Url'
        instance.name        = 'name_of_the_file.mp4'
        instance.file_type   = 'file'
        instance.error       = None
        instance.url         = 'ftp://a.b.c/name_of_the_file.mp4'
        instance.paid_bw     = 0
        instance.file_size   = '92014'
        instance.type_name   = 'file'
        instance.dltype      = 3
        instance.human_size  = '89.86K'
    
    """
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api




class Error(BaseObj):
    """
    SingleRapid is a Rapidshare url, which is generally an archive file. If
    the downloaded file have a multiple volume, it's a Multipart object.
    
    Url Attributes:
        
        instance.dl_handler = 'Rapid'
        instance.name       = 'ABCDE.rar'
        instance.file_type  = 'file'
        instance.error      = None
        instance.url        = 'http://rapidshare.com/files/abcde.rar'
        instance.paid_bw    = '104961263'
        instance.file_size  = '104961263'
        instance.type_name  = 'file'
        instance.dltype     = 1
        instance.human_size = '100.10M'
    
    """
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api


class Torrent(BaseObj):
    """
    Torrent objects are fetched via our Torrent clients. It can contain
    single, multi part archive files, or any other file type. Send the
    torrent URL, we figure out the rest.
    
    Torrent Attributes:
        
        instance.dl_handler  = 'Torrent'
        instance.name        = 'ABCDE.avi'
        instance.file_type   = 'file'
        instance.file_size   = 244091464
        instance.url         = 'http://a.b/c.torrent'
        instance.paid_bw     = 0
        instance.error       = None
        instance.type_name   = 'file'
        instance.dltype      = 2
        instance.human_size  = '232.78M'
    
    """
    
    def __init__(self, api, dictionary=None, url=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api
        

class Multipart(BaseObj):
    """
    Multipart objects are files, which contains patterns like "part1",
    "001", etc. These files are automatically extracted and saved to your
    space.
    
    Multipart Attributes:
        
        instance.name       = 'ABCDE'
        instance.size       = 366500388
        instance.human_size = 350.0M
        instance.paid_bw    = 366500388
        instance.parts      = [
        
                     {
                       "url":"http:\/\/rapidshare.com\/files\/1\/M.part3.rar",
                       "size":"47711664",
                       "paid_bw":"47711664",
                       "source":"rapidshare.com",
                       "name":"Mdb35.part3.rar",
                       "human_size":"45.5M",
                       "type":"file",
                       "needs_pass":0,
                       "error":null
                    },
                    {
                       "url":"http:\/\/rapidshare.com\/files\/2\/M.part1.rar",
                       "size":"55000000",
                       "paid_bw":"55000000",
                       "source":"rapidshare.com",
                       "name":"Mdb35.part1.rar",
                       "human_size":"52.5M",
                       "type":"file",
                       "needs_pass":0,
                       "error":null
                    }

                              ]
        instance.error      = None
    
    """
    
    def __init__(self, api, dictionary=None, **args):
        BaseObj.__init__(self, dictionary, **args)
        self.api = api
        

if __name__ == '__main__':
    
    print "This file should not be executed."
    