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
import sys;
import re;
import json;
import urllib;
import urlparse;
import base64;
import datetime;
import logging;

from resources.lib.modules import utils;
from resources.lib.modules import control;
from resources.lib.modules import client;
from resources.lib.modules import cache;


class animeshows:

    def __init__(self):

        self.logger = logging.getLogger('funimationnow');

        self.list = [];

        self.ut = utils.setting('fn.ut') if not None else 'FunimationUser';

        self.uid = utils.setting('fn.uid');

        self.flatten_seasons = json.loads(utils.setting('fn.flatten_seasons')) if not None else False;
        self.display_extras = json.loads(utils.setting('fn.display_extras')) if not None else True;
        self.display_simular = json.loads(utils.setting('fn.display_simular')) if not None else True;
        self.display_movies = json.loads(utils.setting('fn.display_movies')) if not None else True;

        self.video_quality = int(utils.setting('fn.video_quality')) if not None else 2;
        self.image_quality = int(utils.setting('fn.image_quality')) if not None else 2;
        
        self.poster_type = int(utils.setting('fn.poster_type')) if not None else 0;

        self.result_count = self.convertValue('result_count');
        self.content_type = self.convertValue('content_type');
        self.user_role = self.convertValue('user_role');

        self.offset = None;
        self.posterart = None;
        self.season = None;
        self.trigger = None;
        self.currentid = None;
        self.searchstring = None;
        self.actiontype = None;

        self.allMenu = control.lang(32124).encode('utf-8');
        self.extraMenu = control.lang(32125).encode('utf-8');
        self.simMenu = control.lang(32126).encode('utf-8');
        self.movieMenu = control.lang(32128).encode('utf-8');
        self.nextMenu = control.lang(32127).encode('utf-8');


        self.funimation_url = 'http://www.funimation.com/feeds/ps/';

        self.tvdb_key = base64.urlsafe_b64decode('VWxSSk5VMUVhelJPYWxWNlRrVldSRkpWU1RGUmR6MDk=');
        self.tvdb_api_url = 'https://api.thetvdb.com/%s';
        self.tvdb_search = 'https://api.thetvdb.com/search/';
        self.tvdb_series = 'https://api.thetvdb.com/series/';
        self.tvdb_episodes = 'https://api.thetvdb.com/series/312878/episodes';
        self.tvdb_episode = 'https://api.thetvdb.com/episodes/312878';
        self.tvdb_artwork = 'http://thetvdb.com/banners/%s'; #(seriesid, imageid)

        self.tvdb_token = utils.gettvdbToken(self.tvdb_key, self.tvdb_api_url);

        self.favorites = utils.favorites();

        

    def getsubs(self, action, rkey=None, params=None, filtertype=None):

        try:

            cookie = None;
            posterart = None;
            season = None;
            offset = 0;

            self.funimation_url += action;

            if not params is None:
                from resources.lib.modules import cookiecache;

                if 'action' in params:
                    self.actiontype = params['action'];
                    params.pop('action');

                #Why? For some reason Kodi appears to strip off the attribute named filter
                if 'filterx' in params:
                    params['filter'] = params['filterx'];
                    params.pop('filterx');
                
                if filtertype:
                    params.pop('filtertype');

                if 'posterart' in params:
                    self.posterart = params['posterart'];
                    params.pop('posterart');

                if 'season' in params:
                    self.season = str(params['season']);
                    params.pop('season');

                if 'offset' in params:
                    self.offset = int(params['offset']);
                    params.pop('offset');

                if 'first-letter' in params:
                    self.trigger = params['first-letter'];

                if 'genre' in params:
                    self.trigger = params['genre'];

                if 'rating' in params:
                    self.trigger = params['rating'];

                if 'show_id' in params:
                    self.currentid = params['show_id'];

                if 'search' in params:
                    self.searchstring = params['search'];


                #if 'limit' in params:
                    #params.pop('limit');

                params = urllib.urlencode(params);

                self.funimation_url += ('?' + params);

                uid = utils.setting('fn.uid');

                if uid is not None:
                    cookie = cookiecache.fetch(uid.lower(), 1);


            agent = utils.setting(control.lang(32215).encode('utf-8'));

            if agent is None:
                agent = 'Sony-PS3';

            headers = {'User-Agent': agent};

            result = client.request(self.funimation_url, headers=headers, redirect=False, cookie=cookie);

            result = json.loads(result);

            try: 
                
                if rkey is not None:
                    filtertype = rkey.encode("utf-8");
                    result = list(result[rkey]);

                entries = getattr(self, filtertype)(result, action, filtertype);

                if entries is None:
                    utils.sendNotification(32501, 10000);

                elif len(entries) <= 0:
                    utils.sendNotification(32500, 10000);

            except Exception as inst:
                self.logger.error(inst)
                pass;

            
            #result = result.decode('iso-8859-1').encode('utf-8')
            #items = client.parseDOM(result, 'tr', attrs = {'class': '.+? detailed'})
        except Exception as inst:

            try:
                
                emesage = re.search(r'<h2[^>]*>(?P<message>.*)</h2>', result, re.I);
                emesage = emesage.group('message');
                emesage = re.sub('<[^>]*>', '', emesage);

            except:
                emesage = 32502;
                pass;

            utils.sendNotification(emesage, 15000);

            self.logger.error(inst);

            pass;


    def convertValue(self, prop):

        if prop == 'content_type':
            return 'Subbed' if (int(utils.setting('fn.%s' % prop)) if not None else 0) == 0 else 'Dubbed';

        if prop == 'result_count':
            result_count = int(utils.setting('fn.%s' % prop)) if not None else 0;

            return 3000 if (result_count == 0) else result_count;

        if prop == 'user_role':
            return bool(re.compile(r'(All-Access|Sub)Pass').match(utils.setting('fn.%s' % prop)));


        return;


    def episodeinfo(self, episode):

        return {
                'mpaa':episode['rating'],
                'plot':episode['description'],
                'aired':episode['pubDate'],
                'episode':episode['sequence'],
                'year':'2013',
            };


    def posterArt(self, itm):

        if self.poster_type < 1:
            imgs = ['thumbnail_large', 'thumbnail_medium', 'thumbnail_small'];

            if self.image_quality == 2:
                imgs = [imgs[0], imgs[1], imgs[2]];

            elif self.image_quality == 1:
                imgs = [imgs[1], imgs[0], imgs[2]];

            else:
                imgs = [imgs[2], imgs[1], imgs[0]];

        else:
            imgs = ['poster_art_large', 'poster_art'];

            if self.image_quality >= 1:
                imgs = [imgs[0], imgs[1]];

            else:
                imgs = [imgs[1], imgs[0]];


        for art in imgs:

            if art in itm and itm[art] is not None:
                return itm[art];

        return;


    def episodeArt(self, itm):

        #imgs = ['thumbnail_url', 'thumbnail_large', 'thumbnail_medium'];
        imgs = ['thumbnail_url', 'thumbnail_medium', 'thumbnail_small'];

        if self.image_quality == 2:
            imgs = [imgs[0], imgs[1], imgs[2]];

        elif self.image_quality == 1:
            imgs = [imgs[1], imgs[0], imgs[2]];

        else:
            imgs = [imgs[2], imgs[1], imgs[0]];


        for art in imgs:

            if art in itm and itm[art] is not None:
                return itm[art];

        return;


    def browseAll(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'],
                    'series_name': show['series_name'], 
                    'asset_id': show['asset_id'], 
                    'url': lurl, 'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': 'shows&filtertype=browseAll&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s' % (self.content_type, maxidx, self.ut), 
                'image': '', 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def categories(self, genres, action, filtertype):

        for genre in sorted(genres): 
            
            lurl = str('filtertype=genre&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&genre=%s' % (self.content_type, self.ut, genre));
            
            self.list.append({'name': genre, 'url': lurl, 'image': 'genres.png', 'action': 'shows', 'isFolder': True, 'checkqueue': False});
        
        self.addDirectory(self.list);
        
        return self.list;


    def featured(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'],
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True,
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('featured&filtertype=featured&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s' % (self.content_type, maxidx, self.ut)), 
                'image': '', 
                'action': 'featured', 
                'isFolder': True,
                'checkqueue': False
            });

       
        self.addDirectory(self.list);
        
        return self.list;


    def firstletter(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            #if idx <= maxidx and idx > self.offset: #(idx > self.offset or self.offset == 0)
            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'],
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': 'shows&filtertype=firstletter&limit=3000&first-letter=%s&offset=%s&ut=%s' %(self.trigger, maxidx, self.ut), 
                'image': '', 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def genre(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'],
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('filtertype=genre&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&genre=%s' % (self.content_type, maxidx, self.ut, self.trigger)), 
                'image': '', 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def rating(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'],
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'],
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('filtertype=rating&sort=SortOptionFromBeginning&offset=%s&limit=3000&ut=%s&rating=%s' % (maxidx, self.ut, self.trigger)), 
                'image': '', 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def getVideoHistory(self, historyresults, action, filtertype):

        lcount = 0;

        movies = [];
        extras = [];
        episodes = [];

        if historyresults is not None:
            movies = [d for d in historyresults if d['video_type'].lower() == 'movie'.encode('utf-8')];
            episodes = [d for d in historyresults if d['video_type'].lower() == 'episode'.encode('utf-8')];
            extras = [d for d in historyresults if (d['video_type'].lower() != 'episode'.encode('utf-8') and d['video_type'].lower() != 'movie'.encode('utf-8'))];


        lcount = sum(len(i) > 0 for i in [movies, extras, episodes]);

        if lcount < 1:
            #'send notification of no results'

            return self.list;

        else:

            if self.season is None:

                if len(extras) > 0:

                    extra_types = [];

                    for extra in extras:
                        extra_types.append(extra['video_type']);

                    for extra in sorted(list(set(extra_types)), key=lambda s: s.lower()):

                        #'getVideoHistory&filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=0&limit=3000&username=%s' % (self.content_type, self.uid), 'movies.png', 'DefaultMovies.png');

                        lurl = str('filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=0&limit=3000&username=%s&season=%s' % (self.content_type, self.uid, self.searchstring, extra));

                        self.list.append({
                            'name': extra.title(), 
                            'series_name': '(Funimation History) ',
                            'asset_id': 0, 
                            'url': lurl, 
                            'image': '', 
                            'action': 'getVideoHistory', 
                            'isFolder': True, 
                            'checkqueue': False
                        });


                if len(movies) > 0:

                    lurl = str('filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=0&limit=3000&username=%s&season=Movie' % (self.content_type, self.uid));

                    self.list.append({
                        'name': 'Movies', 
                        'series_name': '(Funimation History) ',
                        'asset_id': 0, 
                        'url': lurl, 
                        'image': '', 
                        'action': 'getVideoHistory', 
                        'isFolder': True, 
                        'checkqueue': False
                    });


                if len(episodes) > 0:

                    lurl = str('filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=0&limit=3000&username=%s&season=Episode' % (self.content_type, self.uid));

                    self.list.append({
                        'name': 'Episodes', 
                        'series_name': '(Funimation History) ',
                        'asset_id': 0, 
                        'url': lurl, 
                        'image': '', 
                        'action': 'getVideoHistory', 
                        'isFolder': True, 
                        'checkqueue': False
                    });


                self.addDirectory(self.list);

                return self.list;


            elif self.season == 'Movie':

                tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', None, movies, True) if self.tvdb_token else None;

                return self.episodes([], movies, 'search', tvdbmeta, appendtitle=False, historyresults=True);


            elif self.season == 'Episode':

                tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', None, episodes, True) if self.tvdb_token else None;

                return self.episodes(episodes, [], 'search', tvdbmeta, appendtitle=True, historyresults=True);

            else:

                extras = [d for d in extras if d['video_type'] == self.season.encode('utf-8')];

                tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', None, extras, True) if self.tvdb_token else None;

                return self.episodes(extras, [], 'search', tvdbmeta, appendtitle=True, historyresults=True);


    def latestNavigator(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'release_date'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'], 
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('shows&sort=SortOptionLatestSubscription&filtertype=latestNavigator&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s' % (self.content_type, maxidx, self.ut)), 
                'image': '', 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def getQueue(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        utils.syncqueue(series, 1);

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'], 
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('getQueue&filtertype=getQueue&filterx=FilterOption%sOnly&offset=%s&limit=3000&username=%s&v=2' % (self.content_type, maxidx, self.uid)), 
                'image': '', 
                'action': 'getQueue', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def similarSeries(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;
        show_id = None;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'], 
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('filtertype=similarSeries&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&show_id=%s' % (self.content_type, maxidx, self.ut, self.currentid)), 
                'image': '', 
                'action': 'similarSeries', 
                'isFolder': True, 
                'checkqueue': False
            });
            
        
        self.addDirectory(self.list);
        
        return self.list;


    def ratings(self, ratings, action, filtertype):

        for rating in ratings:

            #lurl = str('filtertype=rating&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&rating=%s' % (self.content_type, self.ut, rating)); # DB column error
            '''
                Error Number: 1054

                Unknown column 'active_svod_sub' in 'where clause'

                SELECT * FROM (`default_tv_ratings`) WHERE `active_svod_sub` = 1

                Filename: /var/www/funimation.com/releases/9decc133b28ba65d25e10bdd45dda1fee71828d5/models/feeds/feeds_m.php

                Line Number: 1580

            '''

            lurl = str('filtertype=rating&sort=SortOptionFromBeginning&offset=0&limit=3000&ut=%s&rating=%s' % (self.ut, rating));
            lthumb = '%s.png' % rating;

            self.list.append({
                'name': rating, 
                'url': lurl, 
                'image': lthumb, 
                'icon': lthumb, 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list, imgPath='ratings');
        
        return self.list;


    def videos(self, extras, action, filtertype):

        if self.season is None:

            extra_types = [];

            for extra in extras:
                extra_types.append(extra['video_type']);

            for extra in sorted(list(set(extra_types)), key=lambda s: s.lower()):

                lurl = str('filtertype=videos&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&season=%s' % (self.content_type, self.ut, self.currentid, extra));

                self.list.append({
                    'name': extra, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'extras', 
                    'isFolder': True, 
                    'checkqueue': False
                });

            
            self.addDirectory(self.list);

            return self.list;

        else:

            extras = [d for d in extras if d['video_type'].lower() == self.season.lower().encode('utf-8')];

            return self.episodes(extras, [], filtertype, None);

    
    def search(self, searchresults, action, filtertype):

        lcount = 0;

        movies = [];
        extras = [];
        episodes = [];

        series = searchresults['episodes']['videos'] if ('episodes' in searchresults and 'videos' in searchresults['episodes']) else [];
        shows = searchresults['shows'] if 'shows' in searchresults else [];

        if series is not None:
            movies = [d for d in series if d['video_type'].lower() == 'movie'.encode('utf-8')];
            episodes = [d for d in series if d['video_type'].lower() == 'episode'.encode('utf-8')];
            extras = [d for d in series if (d['video_type'].lower() != 'episode'.encode('utf-8') and d['video_type'].lower() != 'movie'.encode('utf-8'))];


        lcount = sum(len(i) > 0 for i in [movies, extras, episodes, shows]);

        if lcount < 1:
            #'send notification of no results'

            return self.list;

        else:

            if self.season is None:

                #if lcount > 1:

                if len(extras) > 0:

                    extra_types = [];

                    for extra in extras:
                        extra_types.append(extra['video_type']);

                    for extra in sorted(list(set(extra_types)), key=lambda s: s.lower()):

                        lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&search=%s&season=%s' % (self.content_type, self.ut, self.searchstring, extra));

                        self.list.append({
                            'name': extra.title(), 
                            'series_name': extra.title(),
                            'asset_id': 0, 
                            'url': lurl, 
                            'image': '', 
                            'action': 'search', 
                            'isFolder': True, 
                            'checkqueue': False
                        });


                if len(movies) > 0:

                    lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&search=%s&season=Movie' % (self.content_type, self.ut, self.searchstring));

                    self.list.append({
                        'name': 'Movies', 
                        'series_name': 'Movies',
                        'asset_id': 0, 
                        'url': lurl, 
                        'image': '', 
                        'action': 'search', 
                        'isFolder': True, 
                        'checkqueue': False
                    });


                if len(shows) > 0:

                    lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&search=%s&season=shows' % (self.content_type, self.ut, self.searchstring));

                    self.list.append({
                        'name': 'Shows', 
                        'series_name': 'Shows',
                        'asset_id': 0, 
                        'url': lurl, 
                        'image': '', 
                        'action': 'search', 
                        'isFolder': True, 
                        'checkqueue': False
                    });


                if len(episodes) > 0:

                    lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&search=%s&season=Episode' % (self.content_type, self.ut, self.searchstring));

                    self.list.append({
                        'name': 'Episodes', 
                        'series_name': 'Episodes',
                        'asset_id': 0, 
                        'url': lurl, 
                        'image': '', 
                        'action': 'search', 
                        'isFolder': True, 
                        'checkqueue': False
                    });


                self.addDirectory(self.list);

                return self.list;


            elif self.season == 'Movie':

                tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', None, movies, True) if self.tvdb_token else None;

                return self.episodes([], movies, 'search', tvdbmeta, appendtitle=False, searchresult=True);


            elif self.season == 'Episode':

                tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', None, episodes, True) if self.tvdb_token else None;

                return self.episodes(episodes, [], 'search', tvdbmeta, appendtitle=True, searchresult=True);


            elif self.season == 'shows':

                maxidx = (self.result_count + self.offset);
                paging = False;

                for idx, show in enumerate(self.sortedList(shows, 'series_name'), 1):

                    if idx <= maxidx and idx > self.offset:
                        
                        lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                        self.list.append({
                            'name': show['series_name'],
                            'series_name': show['series_name'], 
                            'asset_id': show['asset_id'], 
                            'url': lurl,
                            'image': self.posterArt(show), 
                            'action': 'videos', 
                            'isFolder': True, 
                            'checkqueue': True
                        });

                    elif (idx + 1) > maxidx:
                        paging = True;


                if paging:

                    lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&search=%s&season=shows' % (self.content_type, maxidx, self.ut, self.searchstring));

                    self.list.append({
                        'name': self.nextMenu, 
                        'url': lurl, 
                        'image': '', 
                        'action': 'search', 
                        'isFolder': True, 
                        'checkqueue': False
                    });
                
                self.addDirectory(self.list);
                
                return self.list;


            else:

                extras = [d for d in extras if d['video_type'] == self.season.encode('utf-8')];

                tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', None, extras, True) if self.tvdb_token else None;

                return self.episodes(extras, [], 'search', tvdbmeta, appendtitle=True, searchresult=True);


    def series(self, series, action, filtertype):

        series = series[action];

        movies = [d for d in series if d['video_type'].lower() == 'movie'.encode('utf-8')];
        series = [d for d in series if d['video_type'].lower() == 'episode'.encode('utf-8')];

        if len(series) > 0:
            tvdbmeta = utils.checktvdbMeta(self.tvdb_key, self.tvdb_token, self.tvdb_api_url, 'series', series[0]['show_name'], series) if self.tvdb_token else None;

        else:
            tvdbmeta = None;

        
        if self.flatten_seasons:
            return self.episodes(series, movies, filtertype, tvdbmeta);

        elif self.season is None:
            return self.seasons(series, movies, filtertype, tvdbmeta);

        else:
            return self.episodes(series, movies, filtertype, tvdbmeta);


    def seasons(self, series, movies, filtertype, tvdbmeta):

        season_set = [];
        movie_set = [];

        for ep in series:

            season_set.append({
                'season': ep['season_number'],
                'series_name': ep['show_name'],
                'show_id': ep['show_id'],
                'poster': self.posterart
            });

        for mov in movies:

            movie_set.append({
                'season': mov['season_number'],
                'series_name': mov['show_name'],
                'show_id': mov['show_id'],
                'poster': self.posterart
            });

        season_set = [dict(t) for t in set([tuple(d.items()) for d in season_set])];

        if len(season_set) == 1:
            return self.episodes(series, movies, filtertype, tvdbmeta);

        elif len(season_set) == 0 and len(movie_set) > 0:
            #self.season = 'movies';
            return self.episodes(series, movies, filtertype, tvdbmeta);

        else:

            for season in self.sortedList(season_set, 'season'):

                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&season=%s' % (self.content_type, self.ut, season['show_id'], season['season']));
                
                self.list.append({
                    'name': 'Season %s' % season['season'], 
                    'series_name': season['series_name'],
                    'asset_id': season['show_id'], 
                    'url': lurl, 
                    'image': season['poster'], 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': True
                });


            ec = len(self.list);

            if self.display_movies and len(movie_set) > 0:

                movies = movie_set[0];

                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&season=movies' % (self.content_type, self.ut, movies['show_id']));

                self.list.insert(0, {
                    'name': self.movieMenu, 
                    'url': lurl, 
                    'image': movies['poster'], 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            if ec >= self.result_count and self.result_count > 0:

                self.list.append({
                    'name': self.nextMenu, 
                    'url': 'http://ffff', 
                    'image': 'http://ffff', 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            if len(season_set) > 0:
                self.specialfolders(self.list, season_set[0]['show_id'], True);


            self.addDirectory(self.list);

            return self.list;


    def episodes(self, series, movies, filtertype, tvdbmeta, appendtitle=False, searchresult=False, historyresults=False):

        maxidx = (self.result_count + self.offset);
        paging = False;
        show_id = None;
        video_type = None;
        sort_type = 'number';
        isExtra = False;
        isMovieOnly = False;
        banner = None;
        fanart = None;
        poster = None;
        showstatus = utils.getshowstatus(self.currentid);
        

        if len(movies) > 0 and len(series) == 0:
            self.season = 'movies';
            isMovieOnly = True;

        if self.season == 'movies':
            video_type = 0;
            series = movies;
            sort_type = 'extended_title' if (searchresult or historyresults) else 'title';

        elif self.season and self.season.isdigit():
            video_type = 1;
            series = [i for i in series if i['season_number'] == self.season];

        elif self.season and self.season == 'Episode' and (searchresult or historyresults):
            video_type = 1;
            sort_type = 'releaseDate' if (searchresult or historyresults) else 'created_date';

        elif self.season and self.season != 'all':
            isExtra = True;
            video_type = 1;
            sort_type = 'releaseDate' if (searchresult or historyresults) else 'created_date';

        else:
            video_type = 1;


        artwork = utils.getartwork(self.currentid);

        if artwork:
            
            try:
                from random import randint

                artwork = json.loads(artwork)['data'];

                banners = [d for d in artwork if d['keyType'].lower() == 'series'.encode('utf-8')];
                fanarts = [d for d in artwork if d['keyType'].lower() == 'fanart'.encode('utf-8')];
                posters = [d for d in artwork if d['keyType'].lower() == 'poster'.encode('utf-8')];

                if banners and len(banners) > 0:
                    banner = self.tvdb_artwork % banners[randint(0, (len(banners) - 1))]['fileName'];

                if fanarts and len(fanarts) > 0:
                    fanart = self.tvdb_artwork % fanarts[randint(0, (len(fanarts) - 1))]['fileName'];

                if posters and len(posters) > 0:
                    poster = self.tvdb_artwork % posters[randint(0, (len(posters) - 1))]['fileName'];

            except Exception as inst:
                self.logger.error(inst);
            
                pass;

        series = self.sortedList(series, sort_type);

        for idx, episode in enumerate(series, 1):

            progress = 0;
            playcount = 0;
            studio = None;

            genre = " / ".join(sorted(list(set(episode.get('genre', '').split(','))))) if episode['genre'] is not None else 'aaaa';

            try:

                if idx <= maxidx and idx > self.offset:

                    year = None;
                    show_id = episode['show_id'];
                    plot = episode['description'] if 'description' in episode else None;

                    try:
                        
                        aired = episode['releaseDate'] if 'releaseDate' in episode else None;

                        if aired is None:
                            aired = episode['pubDate'] if 'pubDate' in episode else None;

                    except:
                        aired = None;

                        pass;


                    if tvdbmeta is not None:

                        try:

                            meta = tvdbmeta[episode['asset_id'].encode('utf-8')];

                            if meta is not None:

                                aired = meta['firstAired'];
                                overview = meta['overview'];
                                genre = meta['genre'];
                                studio = meta['network'];

                                if overview is not None:
                                    if re.sub(r'[^a-zA-Z0-9]+', '', overview).lower() != 'na':
                                        plot = overview;


                        except Exception as inst:
                            self.logger.error(inst);
                            
                            pass;


                    if aired is not None:
                        
                        from datetime import datetime;
                        from dateutil import parser;
                        
                        try:

                            aired = parser.parse(aired, dayfirst=False);

                            year = aired.strftime('%Y');
                            aired = aired.strftime('%d/%m/%Y');

                        except Exception as inst:
                            self.logger.error(inst);
                        
                            pass;

                    videoInfo = {
                        'duration': episode['duration'], 
                        'codec': 'h264',
                    };

                    audioInfo = {
                        'codec': 'aac',
                        'channels': 2,
                    };

                    info = {
                        'mpaa': episode['rating'],
                        'plot': plot,
                        'aired': aired,
                        'year': year,
                        'studio': studio,
                        'genre': genre,
                        'title': '',
                        'votes': '',
                        'rating': '',

                        #'sorttitle': episode['title']
                    };

                    if showstatus is not None and episode['asset_id'] in showstatus:

                        try:

                            status = showstatus[episode['asset_id']];
                            playcount = status['watched'];
                            progress = str(status['progress']);
                            
                            info.update({'playcount': playcount, 'overlay': 6 if int(playcount) <= 0 else 7});


                        except Exception as inst:
                            self.logger.error(inst);
                        
                            pass;


                    lurl = str('filtertype=episodes&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s' % (self.content_type, self.ut, episode['asset_id']));


                    if self.season != 'movies' and not isExtra:

                        if self.flatten_seasons:
                            epnum = episode['number'];

                        elif int(series[0]['number']) == 0:
                            epnum = (idx - 1);

                        else:
                            epnum = idx;

                        epnum = epnum if len(str(epnum)) > 1 else '0%s' % epnum;

                        info['episode'] = epnum;


                    if self.season == 'movies' or isExtra:

                        name = episode['title'];

                        if name == 'The Movie' and not searchresult:
                            
                            try:
                                name = re.sub('(?i)[ ]+\((Sub|Dub)\)', '', episode['extended_title']);

                            except:
                                name = episode['extended_title'];

                        elif (searchresult or historyresults):

                            try:
                                name = re.sub('(?i)[ ]+\((Sub|Dub)\)', '', episode['extended_title']);

                            except:
                                name = episode['extended_title'];


                    elif appendtitle:
                        name = '(%s) %sx%s: %s' % (episode['show_name'], episode['season_number'], epnum, episode['title']);

                    else:
                        name = '%sx%s: %s' % (episode['season_number'], epnum, episode['title']);


                    try:

                        rawurl = episode['hd_video_url'] if ('hd_video_url' in episode and episode['hd_video_url'] is not None and len(episode['hd_video_url']) > 0) else (episode['xbox_one_video_url'] if ('xbox_one_video_url' in episode and episode['xbox_one_video_url'] is not None and len(episode['xbox_one_video_url']) > 0) else episode['video_url']);                       
                        
                        infos = self.formurl(rawurl, videoInfo);

                        url = infos[0];
                        videoInfo = infos[1];

                    except Exception as inst:
                        
                        url = None;

                        self.logger.error(inst)
                        pass;


                    asset_id = episode['show_id'] if 'show_id' in episode else episode['asset_id'];
                    season_num = episode['season_number'] if ('season_number' in episode and episode['season_number'] is not None) else 0;
                    episode_num = episode['number'] if ('number' in episode and episode['number'] is not None) else 0;


                    self.list.append({
                        'name': name,
                        'asset_id': asset_id,
                        'show_id': episode['show_id'],
                        'episode_id': episode['asset_id'],
                        'series_name': episode['show_name'],
                        'season_number': season_num,
                        'number': episode_num,
                        'duration': episode['duration'],
                        'progress': progress,
                        'playcount': playcount,
                        'url': url, 
                        'image': self.episodeArt(episode), 
                        'banner': banner,
                        'fanart': fanart,
                        'poster': poster,
                        'action': 'player',
                        'video': episode['video_type'],
                        'infoLabel': info,
                        #'sorttitle': episode['title'],
                        'videoInfo': videoInfo,
                        'audioInfo': audioInfo,
                        'isFolder': False,
                        'videoType': video_type,
                        'checkqueue': True
                    });


                elif (idx + 1) > maxidx:
                    paging = True;


            except Exception as inst:
                self.logger.error(inst);

                pass;


        if (self.flatten_seasons or self.season is None) and self.offset == 0 and self.season != 'movies' and not isExtra and not searchresult and not historyresults:

            if self.display_movies and len(movies) > 0:

                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&season=movies' % (self.content_type, self.ut, show_id));

                self.list.insert(0, {
                    'name': self.movieMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': False
                });

            self.specialfolders(self.list, show_id, False);


        elif isMovieOnly and self.offset == 0 and not searchresult and not historyresults:
            self.specialfolders(self.list, show_id, False);


        if paging:

            if isExtra and not searchresult and not historyresults:

                self.list.append({
                    'name': self.nextMenu, 
                    'url': str('filtertype=videos&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&show_id=%s&season=%s' % (self.content_type, maxidx, self.ut, show_id, self.season)), 
                    'image': '', 
                    'action': 'extras', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            elif isExtra and searchresult:

                lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&search=%s&season=%s' % (self.content_type, maxidx, self.ut, self.searchstring, self.season));

                self.list.append({
                    'name': self.nextMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'search', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            elif isExtra and historyresults:

                lurl = str('filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=%s&limit=3000&username=%s&season=%s' % (self.content_type, maxidx, self.uid, self.season));

                self.list.append({
                    'name': self.nextMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'getVideoHistory', 
                    'isFolder': True, 
                    'checkqueue': False
                });

            
            elif (self.flatten_seasons or self.season is None) and self.season != 'movies' and not searchresult and not historyresults:

                self.list.append({
                    'name': self.nextMenu, 
                    'url': str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&show_id=%s' % (self.content_type, maxidx, self.ut, show_id)), 
                    'image': '', 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            elif searchresult and self.season == 'movies':

                lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&search=%s&season=Movie' % (self.content_type, maxidx, self.ut, self.searchstring));

                self.list.append({
                    'name': self.nextMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'search', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            elif historyresults and self.season == 'movies':

                lurl = str('filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=%s&limit=3000&username=%s&season=Movie' % (self.content_type, maxidx, self.uid));

                self.list.append({
                    'name': self.nextMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'getVideoHistory', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            elif searchresult and self.season == 'Episode':

                lurl = str('filtertype=search&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&search=%s&season=Episode' % (self.content_type, maxidx, self.ut, self.searchstring));

                self.list.append({
                    'name': self.nextMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'search', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            elif historyresults and self.season == 'Episode':

                lurl = str('filtertype=getVideoHistory&filterx=FilterOption%sOnly&offset=%s&limit=3000&username=%s&season=Episode' % (self.content_type, maxidx, self.uid));

                self.list.append({
                    'name': self.nextMenu, 
                    'url': lurl, 
                    'image': '', 
                    'action': 'getVideoHistory', 
                    'isFolder': True, 
                    'checkqueue': False
                });


            else:

                self.list.append({
                    'name': self.nextMenu, 
                    'url': str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=%s&limit=3000&ut=%s&show_id=%s&season=%s' % (self.content_type, maxidx, self.ut, show_id, self.season)), 
                    'image': '', 
                    'action': 'videos', 
                    'isFolder': True, 
                    'checkqueue': False
                });


        self.addDirectory(self.list, isFolder=False);
        
        return self.list;

    
    def specialfolders(self, list, show_id, season_set):

        if self.display_simular:

            lurl = str('filtertype=similarSeries&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s' % (self.content_type, self.ut, show_id));

            self.list.insert(0, {'name': self.simMenu, 'url': lurl, 'image': 'http://ffff', 'action': 'similarSeries', 'isFolder': True, 'checkqueue': False});

        
        if self.display_extras:

            lurl = str('filtertype=videos&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s' % (self.content_type, self.ut, show_id));

            self.list.insert(0, {'name': self.extraMenu, 'url': lurl, 'image': 'http://ffff', 'action': 'extras', 'isFolder': True, 'checkqueue': False});


        if not self.flatten_seasons and season_set:
            self.list.insert(0, {'name': self.allMenu, 'url': str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&season=all' % (self.content_type, self.ut, show_id)), 'image': 'http://ffff', 'action': 'videos', 'isFolder': True, 'checkqueue': False});


    def sortedList(self, itms, name):

        if name == 'release_date':

            rts = ['latest_video_subscription_release_date', 'latest_video_free_release_date'];
            
            if not self.user_role:
                rts.reverse();

            #needs some work still to get longs, i believe this is comparing strings
            return list(reversed(sorted(itms, key=lambda k: (k[rts[0]] if not None else k[rts[1]] if not None else 0))));

        elif name == 'created_date':
            return sorted(itms, key=lambda k: long(k[name]));

        elif name == 'number' or name == 'season':
            return sorted(itms, key=lambda k: int(k[name]));

        elif name == 'releaseDate':
            from operator import itemgetter;

            itms = sorted(itms, key=itemgetter('show_name', 'releaseDate'))
            return sorted(itms, key=lambda k: (k['show_name'].lower(), k['releaseDate']))

        else:
            return sorted(itms, key=lambda k: k[name].lower());


    def formurl(self, url, info):

        url = urlparse.urlparse(url);

        segments = url.path.split(',');

        rates = sorted([int(r) for r in segments if r.isdigit()], reverse=True);

        rsize = len(rates);

        qdict = {
            0:1500, 
            1:2500, 
            2:4000
        };

        hedict = {
            750:[640, 480],
            #1500:[768, 576], # aert by year
            1500:[960, 540],
            2000:[1280, 720],
            2500:[1280, 720],
            4000:[1920, 1080],
        };

        for r in rates:

            if r <= qdict[self.video_quality]:

                rate = r;

                break;


        path = '%s%s%s' % (segments[0], str(rate), segments[-1]);

        if rate not in hedict:
            rate = min(hedict, key=lambda x:abs(x - rate));

        finalurl = '%s://%s%s?%s' % (url.scheme, url.netloc, path, url.query);

        w = hedict[rate][0];
        h = hedict[rate][1];

        info['width'] = w;
        info['height'] = h;
        info['aspect'] = (w / float(h));

        return (finalurl, info);


    def simulcastsNavigator(self, series, action, filtertype):

        maxidx = (self.result_count + self.offset);
        paging = False;

        for idx, show in enumerate(self.sortedList(series, 'series_name'), 1):

            if idx <= maxidx and idx > self.offset:
                
                lurl = str('filtertype=series&sort=SortOptionFromBeginning&filterx=FilterOption%sOnly&offset=0&limit=3000&ut=%s&show_id=%s&posterart=%s' % (self.content_type, self.ut, show['asset_id'], self.posterArt(show)));

                self.list.append({
                    'name': show['series_name'], 
                    'series_name': show['series_name'],
                    'asset_id': show['asset_id'], 
                    'url': lurl, 
                    'image': self.posterArt(show), 
                    'action': 'videos',
                    'isFolder': True, 
                    'checkqueue': True
                });

            elif (idx + 1) > maxidx:
                paging = True;


        if paging:

            self.list.append({
                'name': self.nextMenu, 
                'url': str('shows&sort=SortOptionFromBeginning&filtertype=simulcastsNavigator&filterx=FilterOptionSimulcast&offset=%s&limit=3000&ut=%s' % (maxidx, self.ut)), 
                'image': '', 
                'action': 'shows', 
                'isFolder': True, 
                'checkqueue': False
            });
        
        self.addDirectory(self.list);
        
        return self.list;


    def addDirectory(self, items, queue=False, isFolder=True, imgPath=None):
        import xbmcplugin;

        if items == None or len(items) == 0: 

            control.idle(); 
            sys.exit();

        sysaddon = sys.argv[0];
        syshandle = int(sys.argv[1]);

        addonFanart = control.addonFanart();
        addonThumb = control.addonThumb();
        artPath = control.artPath(imgPath);

        queueMenu = control.lang(32065).encode('utf-8');

        for i in items:

            if 'isFolder' in i:
                isFolder = i['isFolder'];

            try:

                name = i['name'];

                if i['image'].startswith('http://'): 
                    thumb = i['image'];

                else:

                    thumb = os.path.join(artPath, i['image']) if not artPath == None else addonThumb;


                '''
                if isFolder:

                    url = '%s?action=%s' % (sysaddon, i['action']);

                    try: 
                        #url += '&url=%s' % urllib.quote_plus(i['url']);
                        url += '&%s' % i['url'];

                    except: 
                        pass;

                else:
                    url = i['url'];
                '''

                if isFolder:

                    url = '%s?action=%s' % (sysaddon, i['action']);

                    try: 
                        #url += '&url=%s' % urllib.quote_plus(i['url']);
                        url += '&%s' % i['url'];

                    except: 
                        pass;

                else:

                    url = '%s?action=%s' % (sysaddon, i['action']);

                    try: 
                        #url += '&url=%s&show_id=%s&asset_id=%s' % (urllib.quote(i['url']), i['show_id'], i['episode_id']);
                        url += '&video=%s&barcode=%s-%s-%s-%s-%s-%s' % (i['video'], i['season_number'], i['show_id'], i['episode_id'], i['duration'], i['progress'], i['number']);

                    except Exception as inst:
                        self.logger.error(inst);

                        pass;
                    #url = i['url'];


                cm = [];
                #http://forum.kodi.tv/showthread.php?tid=46364
                #http://kodi.wiki/view/Favourites.xml
                #http://kodi.wiki/view/Media_flags
                #https://forums.tvaddons.ag/general-python-development/17948-invoking-video-playback-addon-isplayable-isfolder-setresolvedurl-explained.html

                if queue == True:
                    cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon));

                cm.append((control.lang2(19033).encode('utf-8'), 'Action(Info)'));
                cm.append((control.lang2(10140).encode('utf-8'), 'Addon.OpenSettings(%s)' % control.addonInfo('id')));
                


                if i['checkqueue']:
                    cm.append(self.queuecontext(i['asset_id'], i['series_name'], sysaddon));

                if isFolder:
                    item = control.item(label=name, label2="**");
                else:
                    item = control.item(label=name);

                item.setArt({'icon': thumb, 'thumb': thumb});


                if isFolder is False:

                    try:
                        
                        if i['videoType'] == 1:
                            xbmcplugin.setContent(syshandle, 'episodes');
                            #xbmcplugin.setContent(syshandle, 'tvshows');

                        else:
                            xbmcplugin.setContent(syshandle, 'movies');

                        #item.setProperty('IsPlayable', 'true');
                        item.addStreamInfo('video', i['videoInfo']);
                        item.addStreamInfo('audio', i['audioInfo']);

                        try:

                            cduration = i['duration'];
                            cprogress = utils.calcprogress(i['progress'], cduration);

                            if cprogress > 0:
                                if (int(cduration) * .92) > cprogress:
                                    item.setProperty("resumetime", str(int(cprogress)));


                            cm.append(self.watchedcontext(i['show_id'], i['episode_id'], i['playcount'], int(cprogress), i['duration'], i['video'], sysaddon));
                        
                        except Exception as inst:

                            cm.append(self.watchedcontext(i['show_id'], i['episode_id'], i['playcount'], 0, i['duration'], i['video'], sysaddon));
                    
                            self.logger.error(inst)
                            pass;

                        #item.setProperty("resumetime", str(1000))
                        #item.setProperty("totaltime",str(2000))
                        #"overlay": 7
                        #"watched": True
                        #studio
                        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': i['poster'], 'tvshow.poster': i['poster'], 'season.poster': i['poster'], 'banner': i['banner'], 'tvshow.banner': i['banner'], 'season.banner': i['banner'], 'fanart': i['fanart']});

                        #http://nullege.com/codes/search/xbmcplugin.SORT_METHOD_EPISODE
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_EPISODE)
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE) # broken
                        #No sorting until we figure out how to pin an item at it's location
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_DATE)
                        xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_UNSORTED)
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_LABEL) #name
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
                        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_EPISODE) # Breaks shit
                        
                        item.setInfo(type='video', infoLabels=i['infoLabel'])


                    except Exception as inst:
                        self.logger.error(inst)
                        pass;

                    cm.append(self.favoritescontext(url, name, isFolder, sysaddon, thumb));
                
                else:
                    cm.append(self.favoritescontext(url, name, isFolder, sysaddon));
                #item.setInfo(type='Video', infoLabels = meta)

                #Note: content: files, songs, artists, albums, movies, tvshows, episodes, musicvideos'''

                #if not addonFanart == None: 
                    #item.setProperty('Fanart_Image', addonFanart);

                item.addContextMenuItems(cm, replaceItems=True);
                #item.addContextMenuItems(cm, replaceItems=True);

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder);

            except Exception as inst:
                self.logger.error(inst)
                pass;

        #control.do_block_check(False)
        control.directory(syshandle);
        #http://mirrors.xbmc.org/docs/python-docs/stable/xbmcplugin.html#-endOfDirectory


    def queuecontext(self, asset_id, series_name, sysaddon):

        try:

            inqueue = utils.getqueuestatus(asset_id);

            if inqueue:
                return ('Remove from My Queue', 'RunPlugin(%s?action=updatemyqueue&asset_id=%s&series_name=%s&state=0)' % (sysaddon, asset_id, series_name));

            else:
                return ('Add to My Queue', 'RunPlugin(%s?action=updatemyqueue&asset_id=%s&series_name=%s&state=1)' % (sysaddon, asset_id, series_name));

        except Exception as inst:
            self.logger.error(inst);
            pass;


    def watchedcontext(self, show_id, asset_id, watched, progress, duration, content, sysaddon):

        try:

            if int(watched) < 1:
                return ('Mark Watched', 'RunPlugin(%s?action=updatewatched&show_id=%s&asset_id=%s&progress=%s&watched=1&duration=%s&content=%s)' % (sysaddon, show_id, asset_id, progress, duration, content));

            else:
                return ('Mark Unwatched', 'RunPlugin(%s?action=updatewatched&show_id=%s&asset_id=%s&progress=0&watched=0&duration=%s&content=%s)' % (sysaddon, show_id, asset_id, duration, content));

            #params['content'],  params['duration']

        except Exception as inst:
            self.logger.error(inst);
            pass;


    def librarycontext(self, url, image, isFolder):

        try:

            if isFolder:
                return ('Add to Library', 'RunPlugin(%s?action=updatewatched&show_id=%s&asset_id=%s&progress=%s&watched=1&duration=%s&content=%s)' % (sysaddon, show_id, asset_id, progress, duration, content));

            else:
                return ('Add to Library', 'RunPlugin(%s?action=updatewatched&show_id=%s&asset_id=%s&progress=0&watched=0&duration=%s&content=%s)' % (sysaddon, show_id, asset_id, duration, content));


        except Exception as inst:
            self.logger.error(inst);
            pass;


    def favoritescontext(self, url, name, isFolder, sysaddon, thumb=None):

        compurl = url.split('?');
        params = dict(urlparse.parse_qsl(compurl[1]));

        if thumb:
            url = ('%s&posterart=%s' % (url, thumb));

        if 'action' in params:
            compurl = ('%s?action=%s&' % (compurl[0], params['action']));
            params.pop('action');

        if 'posterart' in params:
            params.pop('posterart');

        if isFolder:

            if self.actiontype is None:
                name = ('[COLOR purple]F[/COLOR]unimation [B]%s[/B]' % name);

            elif 'filtertype' in params and params['filtertype'] == 'getVideoHistory':
                name = ('[COLOR purple]F[/COLOR]unimation [B]%s[/B] [COLOR purple]H[/COLOR]istory' % name);

            elif 'filtertype' in params and params['filtertype'] == 'search':
                name = ('[COLOR purple]F[/COLOR]unimation [B]%s[/B] [COLOR purple]S[/COLOR]earch [COLOR purple]R[/COLOR]esults - (%s)' % (name, urllib.unquote(self.searchstring)));

            elif 'show_id' in params:
                show_name = utils.getshowname(params['show_id']);

                if show_name:
                    name = ('%s - %s' % (show_name, name));

            if not thumb:
                url = ('%s&posterart=%s' % (url, self.posterart));


        compurl += urllib.urlencode(params);

        if compurl in self.favorites:
            return (control.lang2(14077).encode('utf-8'), 'RunPlugin(%s?action=updatefavorites&name=%s&url=%s&isFolder=%s)' % (sysaddon, name, url, isFolder));

        else:
            return (control.lang2(14076).encode('utf-8'), 'RunPlugin(%s?action=updatefavorites&name=%s&url=%s&isFolder=%s)' % (sysaddon, name, url, isFolder));
