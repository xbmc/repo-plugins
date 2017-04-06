# -*- coding: utf-8 -*-

'''
    Funimation|Now Add-on
    Copyright (C) 2016 Funimation|Now

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os;
import re;
import string;
import sys;
import urlparse;
import logging;

from resources.lib.modules import control;
from resources.lib.modules import utils;


sysaddon = sys.argv[0];
syshandle = int(sys.argv[1]);
#artPath = control.artPath();
addonFanart = control.addonFanart();
queueMenu = control.lang(32001).encode('utf-8');


class navigator:

    def __init__(self):

        self.logger = logging.getLogger('funimationnow');

        self.uid = utils.setting('fn.uid');
        self.ut = utils.setting('fn.ut') if not None else 'FunimationUser';
        self.result_count = self.convertValue('result_count');
        self.content_type = self.convertValue('content_type');

        self.role = self.checkrole();

        if self.result_count == 0:
            self.result_count = 3000;


    def convertValue(self, prop):

        if prop == 'content_type':
            return 'Subbed' if (int(utils.setting('fn.%s' % prop)) if not None else 0) == 0 else 'Dubbed';

        if prop == 'result_count':
            result_count = int(utils.setting('fn.%s' % prop)) if not None else 0;

            return 3000 if (result_count == 0) else result_count;

        return;


    def root(self):

        self.addDirectoryItem(32100, 'featured&filtertype=featured&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s' % (self.content_type, self.ut), 'movies.png', 'DefaultRecentlyAddedEpisodes.png');
        self.addDirectoryItem(32101, 'shows&sort=SortOptionLatestSubscription&filtertype=latestNavigator&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s' % (self.content_type, self.ut), 'movies.png', 'DefaultMovies.png');
        self.addDirectoryItem(32102, 'shows&sort=SortOptionFromBeginning&filtertype=simulcastsNavigator&filterx=FilterOptionSimulcast&offset=0&limit=3000&ut=%s' % self.ut, 'movies.png', 'DefaultMovies.png');
        self.addDirectoryItem(32103, 'browseNavigator', 'movies.png', 'DefaultMovies.png');


        if self.role is not None and bool(re.compile(r'(All-Access|Sub)Pass').match(self.role)):
            self.addDirectoryItem(32104, 'getVideoHistory&filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=0&limit=3000&username=%s' % (self.content_type, self.uid), 'movies.png', 'DefaultMovies.png');
            self.addDirectoryItem(32105, 'getQueue&filtertype=getQueue&filterx=FilterOption%sOnly&offset=0&limit=3000&username=%s&v=2' % (self.content_type, self.uid), 'movies.png', 'DefaultMovies.png');

        elif self.role is not None and self.role == 'Registered User':
            self.addDirectoryItem(32106, 'upgradeNavigator', 'movies.png', 'DefaultMovies.png');
            #http://cwal.me/xbmc/repository.vc.net.cwal.v1/plugin.video.vctv/plugin.video.vctv-1.0.0/Default.py
            #Reference this for duplicating the registration form

        else: 
            self.addDirectoryItem(32107, 'loginNavigator', 'movies.png', 'DefaultMovies.png');
            self.addDirectoryItem(32108, 'registerNavigator', 'movies.png', 'DefaultMovies.png');


        self.addDirectoryItem(32109, 'searchNavigator', 'movies.png', 'DefaultMovies.png');

        self.endDirectory();

        #from resources.lib.modules import cache
        #from resources.lib.modules import changelog
        #cache.get(changelog.get, 600000000, control.addonInfo('version'), table='changelog')

    
    def browse(self):

        self.addDirectoryItem(32120, 'shows&filtertype=browseAll&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s' % (self.content_type, self.ut), 'genres.png', 'DefaultTVShows.png')
        self.addDirectoryItem(32121, 'alphaNavigator', 'certificates.png', 'DefaultTVShows.png')
        self.addDirectoryItem(32122, 'genres', 'networks.png', 'DefaultTVShows.png')
        self.addDirectoryItem(32123, 'getAllRatings', 'people-watching.png', 'DefaultRecentlyAddedEpisodes.png')

        self.endDirectory();

    
    def ratings(self, action):
        import animeshows;

        animeshows.animeshows().getsubs(action, 'ratings');


    def genres(self, action):
        import animeshows;

        animeshows.animeshows().getsubs(action, 'categories');


    def search(self, action, params):
        import animeshows;

        if 'ut' not in params:
            params.update({'ut': (utils.setting('fn.ut') if not None else 'FunimationUser')});

        if 'filterx' not in params:
            params.update({'filterx': 'FilterOption%sOnly' % ('Subbed' if (int(utils.setting('fn.content_type')) if not None else 0) == 0 else 'Dubbed')});

        if 'offset' not in params:
            params.update({'offset': 0});

        if 'limit' not in params:
            params.update({'limit': 3000});

        if 'filtertype' not in params:
            params.update({'filtertype': 'search'});

        self.filtered(action=action, params=params, filtertype='search');
            
            
    def filtered(self, action, filtertype, params, rkey=None):
        import animeshows;

        animeshows.animeshows().getsubs(action, rkey, params, filtertype);


    def browsealpha(self):

        self.addDirectoryItem('#!', str('shows&filtertype=firstletter&offset=0&limit=3000&first-letter=non-alpha&ut=%s' % self.ut), 'people-watching.png', 'DefaultRecentlyAddedEpisodes.png');

        for char in list(string.ascii_uppercase):
            self.addDirectoryItem(char, str('shows&filtertype=firstletter&offset=0&limit=3000&first-letter=%s&ut=%s' %(char, self.ut)), 'people-watching.png', 'DefaultRecentlyAddedEpisodes.png');

        self.endDirectory();


    def checkrole(self):

        utils.checkcookie();
        role = utils.setting('fn.user_role');

        return role;

    
    def addDirectoryItem(self, name, query, thumb, icon, queue=False, isAction=True, isFolder=True, imgPath = None):

        self.logger = logging.getLogger('funimationnow');

        try: 

            name = control.lang(name).encode('utf-8') if isinstance(name, (int, long)) else name;

        except: 
            pass;

        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query;

        artPath = control.artPath(imgPath);
        thumb = os.path.join(artPath, thumb) if not artPath == None else icon;

        cm = [];

        if queue == True: 
            cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon));

        item = control.item(label=name);

        item.addContextMenuItems(cm);
        item.setArt({'icon': thumb, 'thumb': thumb});

        if not addonFanart == None: 
            item.setProperty('Fanart_Image', addonFanart);

        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder);

    
    def endDirectory(self):
        control.directory(syshandle, cacheToDisc=True)

