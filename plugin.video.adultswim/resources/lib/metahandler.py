# -*- coding: utf-8 -*-
"""
Credit to script.module.metahndler
"""
import os
import re
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
from thetvdbapi import TheTVDB
from sqlite3 import dbapi2 as database

addon_id = xbmcaddon.Addon().getAddonInfo("id")
data_path = xbmc.translatePath('special://profile/addon_data/%s' % addon_id)


class MetaData:
    def __init__(self):
        if not xbmcvfs.exists(data_path):
            xbmcvfs.mkdir(data_path)
        self.videocache = os.path.join(data_path, 'video_cache.db')
        self.dbcon = database.connect(self.videocache)
        self.dbcon.row_factory = database.Row  # return results indexed by field names and not numbers so we can
        # convert to dict
        self.dbcur = self.dbcon.cursor()
        
        # initialize cache db
        self._cache_create_db()

    def remove_database(self):
        xbmc.log("Metahandler - deleting database...")
        self.__del__()
        try:
            if xbmcvfs.exists(self.videocache):
                xbmcvfs.delete(self.videocache)
        except:
            if os.path.exists(self.videocache):
                os.remove(self.videocache)
        xbmcgui.Dialog().ok("Metahandler", "Database deleted")
        xbmc.log("Metahandler - Clearing database cache. Done!")

    def __del__(self):
        """ Cleanup db when object destroyed """
        try:
            self.dbcur.close()
            self.dbcon.close()
        except:
            pass

    def _remove_none_values(self, meta):
        """ Ensure we are not sending back any None values, XBMC doesn't like them """
        for item in meta:
            if meta[item] is None:
                meta[item] = ''
                
        return meta

    def __insert_from_dict(self, table, size):
        """ Create a SQL Insert statement with dictionary values """
        sql = 'INSERT INTO %s ' % table
        _format = ', '.join('?' * size)
        sql_insert = sql + 'Values (%s)' % _format
        
        return sql_insert

    def _valid_imdb_id(self, imdb_id):
        """
        Check and return a valid IMDB ID

        Args:
            imdb_id (str): IMDB ID
        Returns:
            imdb_id (str) if valid with leading tt, else None
        """
        # add the tt if not found. integer aware.
        if imdb_id:
            if not imdb_id.startswith('tt'):
                imdb_id = 'tt%s' % imdb_id
            if re.search('tt[0-9]{7}', imdb_id):
                return imdb_id
            else:
                return None

    def _clean_string(self, string):
        """ 
            Method that takes a string and returns it cleaned of any special characters
            in order to do proper string comparisons
        """        
        try:
            return ''.join(e for e in string if e.isalnum())
        except:
            return string

    def _string_compare(self, s1, s2):
        """ Method that takes two strings and returns True or False, based
            on if they are equal, regardless of case.
        """
        try:
            return s1.lower() == s2.lower()
        except AttributeError:
            xbmc.log("Please only pass strings into this method.", 4)
            xbmc.log("You passed a %s and %s" % (s1.__class__, s2.__class__), 4)

    def _cache_create_db(self):
        """ Creates the cache tables if they do not exist.  """
        
        # Create TV Show table
        sql_create = "CREATE TABLE IF NOT EXISTS tvshow_meta ("\
                           "imdb_id TEXT, "\
                           "tvdb_id TEXT, "\
                           "title TEXT, "\
                           "year INTEGER,"\
                           "cast TEXT,"\
                           "rating FLOAT, "\
                           "duration TEXT, "\
                           "plot TEXT,"\
                           "mpaa TEXT, "\
                           "premiered TEXT, "\
                           "genre TEXT, "\
                           "studio TEXT,"\
                           "status TEXT,"\
                           "banner_url TEXT, "\
                           "cover_url TEXT,"\
                           "trailer_url TEXT, "\
                           "backdrop_url TEXT,"\
                           "overlay INTEGER,"\
                           "UNIQUE(imdb_id, tvdb_id, title)"\
                           ");"
        
        self.dbcur.execute(sql_create)
        self.dbcur.execute('CREATE INDEX IF NOT EXISTS nameindex on tvshow_meta (title);')
        
    def _init_tvshow_meta(self, imdb_id, tvdb_id, name, year):
        """
        Initializes a tvshow_meta dictionary with default values, to ensure we always
        have all fields

        Args:
            imdb_id (str): IMDB ID
            tvdb_id (str): TVDB ID
            name (str): full name of movie you are searching
            year (int): 4 digit year

        Returns:
            DICT in the structure of what is required to write to the DB
        """
        
        if year:
            year = int(year)
        else:
            year = 0
            
        meta = {'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'title': name, 'TVShowTitle': name, 'rating': 0, 'duration': '',
                'plot': '', 'mpaa': '', 'premiered': '', 'year': year, 'trailer_url': '', 'genre': '', 'studio': '',
                'status': '', 'cast': [], 'banner_url': '', 'cover_url': '', 'backdrop_url': '', 'overlay': 6,
                'episode': 0, 'playcount': 0}

        return meta
        
    def _cache_lookup_by_name(self, name, year=''):
        """
        Lookup in SQL DB for video meta data by name and year

        Args:
            name (str): full name of tvshow you are searching
        Kwargs:
            year (str): 4 digit year of video, recommended to include the year whenever possible
                        to maximize correct search results.

        Returns:
            DICT of matched meta data or None if no match.
        """

        name = self._clean_string(name.lower())
        sql_select = "SELECT * FROM tvshow_meta WHERE title = '%s'" % name

        xbmc.log('Looking up in local cache by name for: %s %s' % (name, year), 0)
        
        if year:
            sql_select = sql_select + " AND year = %s" % year
            
        xbmc.log('SQL Select: %s' % sql_select, 0)
        
        try:
            self.dbcur.execute(sql_select)
            matchedrow = self.dbcur.fetchone()
        except Exception as e:
            xbmc.log('************* Error selecting from cache db: %s' % e, 4)
            return None
            
        if matchedrow:
            xbmc.log('Found meta information by name in cache table: %s' % dict(matchedrow), 0)
            return dict(matchedrow)
        else:
            xbmc.log('No match in local DB', 0)
            return None

    def get_meta(self, name, imdb_id='', tmdb_id='', year='', overlay=6):
        """
        Main method to get meta data for tvshow. Will lookup by name/year
        if no IMDB ID supplied.

        Args:
            name (str): full name of tvshow you are searching
        Kwargs:
            imdb_id (str): IMDB ID
            tmdb_id (str): TMDB ID
            year (str): 4 digit year of video, recommended to include the year whenever possible
                        to maximize correct search results.
            overlay (int): To set the default watched status (6=unwatched, 7=watched) on new videos

        Returns:
            DICT of meta data or None if cannot be found.
            :param overlay:
            :param year:
            :param tmdb_id:
            :param name:
            :param imdb_id:
        """
       
        xbmc.log('---------------------------------------------------------------------------------------', 0)
        xbmc.log('Attempting to retrieve meta data for %s %s %s %s' % (name, year, imdb_id, tmdb_id), 0)
 
        if imdb_id:
            imdb_id = self._valid_imdb_id(imdb_id)
            meta = self._cache_lookup_by_id(imdb_id=imdb_id)  # for future use
        elif tmdb_id:
            meta = self._cache_lookup_by_id(tmdb_id=tmdb_id)  # for future use
        else:
            meta = self._cache_lookup_by_name(name, year)

        if not meta:
            meta = self._get_tvdb_meta(imdb_id, name, year)
            self._cache_save_video_meta(meta, name, overlay)
            
        meta = self.__format_meta(meta, name)
        
        return meta

    def __format_meta(self, meta, name):
        """
        Format and massage tv show data to prepare for return to addon

        Args:
            meta (dict): tv show meta data dictionary returned from cache or online
            name (str): full name of tvshow you are searching
        Returns:
            DICT. Data formatted and corrected for proper return to xbmc addon
        """

        try:
            # We want to send back the name that was passed in
            meta['title'] = name
            
            # Change cast back into a tuple
            if meta['cast']:
                meta['cast'] = eval(str(meta['cast']))
                
            # Return a trailer link that will play via youtube addon
            try:
                meta['trailer'] = ''
                trailer_id = ''
                if meta['trailer_url']:
                    r = re.match('^[^v]+v=(.{3,11}).*', meta['trailer_url'])
                    if r:
                        trailer_id = r.group(1)
                    else:
                        trailer_id = meta['trailer_url']
                 
                if trailer_id:
                    meta['trailer'] = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % trailer_id
                    
            except Exception as e:
                meta['trailer'] = ''
                xbmc.log('Failed to set trailer: %s' % e, 3)
                
            # Ensure we are not sending back any None values, XBMC doesn't like them
            meta = self._remove_none_values(meta)
            
            # Add TVShowTitle infolabel
            meta['TVShowTitle'] = meta['title']
            
            xbmc.log('Returned Meta: %s' % meta, 0)
            return meta
        except Exception as e:
            xbmc.log('************* Error formatting meta: %s' % e, 4)
            return meta

    def _cache_save_video_meta(self, meta_group, name, overlay=6):
        """
        Saves meta data to SQL table given type

        Args:
            meta_group (dict/list): meta data of video to be added to database
                                    can be a list of dicts (batch insert)or a single dict
        Kwargs:
            overlay (int): To set the default watched status (6=unwatched, 7=watched) on new videos
        """
        table = 'tvshow_meta'
        
        try:
            for meta in meta_group:
                # If a list of dicts (batch insert) has been passed in, ensure individual list item is converted to a
                #  dict
                if type(meta_group) is list:
                    meta = dict(meta)
                    name = meta['title']
                
                # Else ensure we use the dict passed in
                else:
                    meta = meta_group
                    
                # strip title
                meta['title'] = self._clean_string(name.lower())

                if 'cast' in meta:
                    meta['cast'] = str(meta['cast'])
                
                # set default overlay - watched status
                meta['overlay'] = overlay
                
                xbmc.log('Saving cache information: %s' % meta, 0)
                
                sql_insert = self.__insert_from_dict(table, 18)
                xbmc.log('SQL INSERT: %s' % sql_insert, 0)
                
                self.dbcur.execute(sql_insert, (meta['imdb_id'], meta['tvdb_id'], meta['title'], meta['year'],
                                                meta['cast'], meta['rating'], meta['duration'], meta['plot'],
                                                meta['mpaa'], meta['premiered'], meta['genre'], meta['studio'],
                                                meta['status'], meta['banner_url'], meta['cover_url'],
                                                meta['trailer_url'], meta['backdrop_url'], meta['overlay']))
                    
                # Break loop if we are dealing with just 1 record
                if type(meta_group) is dict:
                    break
                
            # Commit all transactions
            self.dbcon.commit()
            xbmc.log('SQL INSERT Successfully Commited', 0)
        except Exception as e:
            xbmc.log('************* Error attempting to insert into %s cache table: %s ' % (table, e), 4)

    def _get_tvdb_meta(self, imdb_id, name, year=''):
        """
        Requests meta data from TVDB and creates proper dict to send back

        Args:
            imdb_id (str): IMDB ID
            name (str): full name of tvshow you are searching
        Kwargs:
            year (str): 4 digit year of tvshow, when imdb_id is not available it is recommended
                        to include the year whenever possible to maximize correct search results.

        Returns:
            DICT. It must also return an empty dict when
            no movie meta info was found from tvdb because we should cache
            these "None found" entries otherwise we hit tvdb alot.
        """
        xbmc.log('Starting TVDB Lookup', 0)
        tvdb = TheTVDB()
        tvdb_id = ''
        
        try:
            if imdb_id:
                tvdb_id = tvdb.get_show_by_imdb(imdb_id)
        except Exception as e:
            xbmc.log('************* Error retreiving from thetvdb.com1: %s ' % e, 4)
            tvdb_id = ''
            
        # Intialize tvshow meta dictionary
        meta = self._init_tvshow_meta(imdb_id, tvdb_id, name, year)

        # if not found by imdb, try by name
        if tvdb_id == '':
            try:
                # If year is passed in, add it to the name for better TVDB search results
                # if year:
                #    name = name + ' ' + year
                show_list = tvdb.get_matching_shows(name)
            except Exception as e:
                xbmc.log('************* Error retreiving from thetvdb.com2: %s ' % e, 4)
                show_list = []

            xbmc.log('Found TV Show List: %s' % show_list, 0)
            tvdb_id = ''
            for show in show_list:
                (junk1, junk2, junk3) = show
                try:
                    # if we match imdb_id or full name (with year) then we know for sure it is the right show
                    if (imdb_id and junk3 == imdb_id) or (year and self._string_compare(self._clean_string(junk2), self._clean_string(name + year))):
                        tvdb_id = self._clean_string(junk1)
                        if not imdb_id:
                            imdb_id = self._clean_string(junk3)
                        name = junk2
                        break
                    # if we match just the cleaned name (without year) keep the tvdb_id
                    elif self._string_compare(self._clean_string(junk2), self._clean_string(name)):
                        tvdb_id = self._clean_string(junk1)
                        if not imdb_id:
                            imdb_id = self._clean_string(junk3)
                        break
                        
                except Exception as e:
                    xbmc.log('************* Error retreiving from thetvdb.com3: %s ' % e, 4)

        if tvdb_id:
            xbmc.log('Show *** ' + name + ' *** found in TVdb. Getting details...', 0)

            try:
                show = tvdb.get_show(tvdb_id)
            except Exception as e:
                xbmc.log('************* Error retreiving from thetvdb.com: %s ' % e, 4)
                show = None
            
            if show is not None:
                meta['imdb_id'] = imdb_id
                meta['tvdb_id'] = tvdb_id
                meta['title'] = name
                if str(show.rating) != '' and show.rating is not None:
                    meta['rating'] = float(show.rating)
                meta['duration'] = int(show.runtime) * 60
                meta['plot'] = show.overview
                meta['mpaa'] = show.content_rating
                meta['premiered'] = str(show.first_aired)

                # Do whatever we can to set a year, if we don't have one lets try to strip it from
                # show.first_aired/premiered
                if not year and show.first_aired:
                        # meta['year'] = int(self._convert_date(meta['premiered'], '%Y-%m-%d', '%Y'))
                        meta['year'] = int(meta['premiered'][:4])

                if show.genre != '':
                    temp = show.genre.replace("|", ",")
                    temp = temp[1:(len(temp)-1)]
                    meta['genre'] = temp
                meta['studio'] = show.network
                meta['status'] = show.status
                if show.actors:
                    for actor in show.actors:
                        meta['cast'].append(actor)
                meta['banner_url'] = show.banner_url
                meta['cover_url'] = show.poster_url
                meta['backdrop_url'] = show.fanart_url
                meta['overlay'] = 6
                
                return meta
        else:
            return meta

    def _cache_lookup_by_id(self, imdb_id='', tmdb_id=''):
        return {}
