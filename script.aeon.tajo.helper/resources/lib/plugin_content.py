#!/usr/bin/python
# coding: utf-8

########################

import random
import xbmcvfs

from resources.lib.helper import *
from resources.lib.library import *

########################

class PluginContent(object):
    def __init__(self,params,li):
        self.params = params
        self.dbtitle = remove_quotes(params.get('title'))
        self.dblabel = remove_quotes(params.get('label'))
        self.dbtype = remove_quotes(params.get('type'))
        self.exclude = remove_quotes(params.get('exclude'))
        self.dbcontent = remove_quotes(params.get('content'))
        self.dbid = remove_quotes(params.get('dbid'))
        self.idtype = remove_quotes(params.get('idtype'))
        self.season = remove_quotes(params.get('season'))
        self.limit = remove_quotes(params.get('limit'))
        self.retry_count = 1
        self.li = li

        if self.limit:
            self.limit = int(self.limit)

        if self.dbtype:
            if self.dbtype in ['movie', 'tvshow', 'season', 'episode', 'musicvideo']:
                library = 'Video'
            else:
                library = 'Audio'

            self.method_details = '%sLibrary.Get%sDetails' % (library, self.dbtype)
            self.method_item = '%sLibrary.Get%ss' % (library, self.dbtype)
            self.param = '%sid' % self.dbtype
            self.key_details = '%sdetails' % self.dbtype
            self.key_items = '%ss' % self.dbtype
            self.properties = JSON_MAP.get('%s_properties' % self.dbtype)

        self.sort_random = {'method': 'random'}
        self.filter_title = {'operator': 'is', 'field': 'title', 'value': self.dbtitle}


    ''' by dbid to get all available listitems
    '''
    def getbydbid(self):
        try:
            if self.dbtype == 'tvshow' and self.idtype in ['season', 'episode']:
                self.dbid = self._gettvshowid()

            json_query = json_call(self.method_details,
                                properties=self.properties,
                                params={self.param: int(self.dbid)}
                                )

            result = json_query['result'][self.key_details]

            if self.dbtype == 'episode':
                try:
                    season_query = json_call('VideoLibrary.GetSeasons',
                                             properties=JSON_MAP['season_properties'],
                                             sort={'order': 'ascending', 'method': 'season'},
                                             params={'tvshowid': int(result.get('tvshowid'))}
                                             )

                    season_query = season_query['result']['seasons']

                    for season in season_query:
                        if season.get('season') == result.get('season'):
                            result['season_label'] = season.get('label')
                            break

                except Exception:
                    pass

        except Exception as error:
            log('Get by DBID: No result found: %s' % error)
            return

        add_items(self.li,[result],type=self.dbtype)
        plugin_category = 'DBID #' + str(self.dbid) + ' (' + self.dbtype + ')'
        set_plugincontent(content=self.key_items, category=plugin_category)


    ''' resource helper to create a list with all existing and matching resource images
    '''
    def getresourceimages(self):
        resource_addon = self.params.get('addon')
        resource_dir = xbmcvfs.translatePath('resource://%s/' % resource_addon)

        string = remove_quotes(self.params.get('string'))
        separator = remove_quotes(self.params.get('separator'))

        if separator:
            values = string.split(separator)
        else:
            values = string.splitlines()

        for item in values:
            for filename in ['%s.jpg' % item, '%s.png' % item]:
                filepath = resource_dir + filename
                if xbmcvfs.exists(filepath):
                    list_item = xbmcgui.ListItem(label=item, offscreen=True)
                    list_item.setArt({'icon': filepath})
                    self.li.append(('', list_item, False))
                    break

            set_plugincontent(content='files', category=resource_addon)


    ''' get items by actor
    '''
    def getitemsbyactor(self):
        ''' Pick random actor of provided DBID item
        '''
        if self.dbid:
            json_query = json_call(self.method_details,
                                   properties=['title', 'cast'],
                                   params={self.param: int(self.dbid)}
                                   )

            try:
                cast = json_query['result'][self.key_details]['cast']
                exclude = json_query['result'][self.key_details]['label']

                if not cast:
                    raise Exception

            except Exception:
                log('Items by actor: No cast found')
                return

            cast_range=[]
            i = 0
            for actor in cast:
                if i > 3:
                    break
                cast_range.append(actor['name'])
                i += 1

            actor = ''.join(random.choice(cast_range))

        else:
            actor = self.dblabel
            exclude = self.exclude

        if actor:
            filters = [{'operator': 'is', 'field': 'actor', 'value': actor}]
            if exclude:
                filters.append({'operator': 'isnot', 'field': 'title', 'value': exclude})

            if self.dbcontent != 'tvshow':
                movie_query = json_call('VideoLibrary.GetMovies',
                                        properties=JSON_MAP['movie_properties'],
                                        sort=self.sort_random,
                                        query_filter={'and': filters}
                                        )

                try:
                    movie_query = movie_query['result']['movies']
                except Exception:
                    log('Items by actor %s: No movies found' % actor)
                else:
                    add_items(self.li, movie_query, type='movie', searchstring=actor)

            if self.dbcontent != 'movie':
                tvshow_query = json_call('VideoLibrary.GetTVShows',
                                         properties=JSON_MAP['tvshow_properties'],
                                         sort=self.sort_random,
                                         query_filter={'and': filters}
                                         )

                try:
                    tvshow_query = tvshow_query['result']['tvshows']
                except Exception:
                    log('Items by actor %s: No shows found' % actor)
                else:
                    add_items(self.li, tvshow_query, type='tvshow', searchstring=actor)

            ''' Retry if query is based on dbid and a random actor
            '''
            if self.dbid and not self.li:
                self._retry('getitemsbyactor')

            plugin_category = ADDON.getLocalizedString(32030) + ' ' + actor
            set_plugincontent(content='videos', category=plugin_category)

            random.shuffle(self.li)


    ''' get cast of item
    '''
    def getcast(self):
        try:
            if self.dbtitle:
                json_query = json_call(self.method_item,
                                       properties=['cast'],
                                       limit=1,
                                       query_filter=self.filter_title
                                       )

            elif self.dbid:
                if self.dbtype == 'tvshow' and self.idtype in ['season', 'episode']:
                    self.dbid = self._gettvshowid()

                json_query = json_call(self.method_details,
                                       properties=['cast'],
                                       params={self.param: int(self.dbid)}
                                       )

            if self.key_details in json_query['result']:
                cast = json_query['result'][self.key_details]['cast']

                ''' Fallback to TV show cast if episode has no cast stored
                '''
                if not cast and self.dbtype == 'episode':
                    tvshow_id = self._gettvshowid(idtype='episode', dbid=self.dbid)

                    json_query = json_call('VideoLibrary.GetTVShowDetails',
                                           properties=['cast'],
                                           params={'tvshowid': int(tvshow_id)}
                                           )

                    cast = json_query['result']['tvshowdetails']['cast']

            else:
                cast = json_query['result'][self.key_items][0]['cast']

            if not cast:
                raise Exception

        except Exception:
            log('Get cast: No cast found.')
            return

        add_items(self.li, cast, type='cast')


    ''' function to return the TV show id based on a season or episode id
    '''
    def _gettvshowid(self,dbid=None,idtype=None):
        try:
            if not dbid:
                dbid = self.dbid

            if not idtype:
                idtype = self.idtype

            if idtype == 'season':
                method_details = 'VideoLibrary.GetSeasonDetails'
                param = 'seasonid'
                key_details = 'seasondetails'
            elif idtype == 'episode':
                method_details = 'VideoLibrary.GetEpisodeDetails'
                param = 'episodeid'
                key_details = 'episodedetails'
            else:
                raise Exception

            json_query = json_call(method_details,
                                   properties=['tvshowid'],
                                   params={param: int(dbid)}
                                   )

            result = json_query['result'][key_details]
            dbid = result.get('tvshowid')

            return dbid

        except Exception:
            return ''


    ''' retry loop for random based widgets if previous run has not returned any single item
    '''
    def _retry(self,type):
        log('Retry to get content (%s)' % str(self.retry_count))

        if self.retry_count < 5:
            self.retry_count += 1
            getattr(self, type)()

        else:
            log('No content found. Stop retrying.')
            self.retry_count = 1
