#!/usr/bin/python
# coding: utf-8

########################

import sys
import xbmc
import xbmcgui

from resources.lib.helper import *
from resources.lib.tmdb import *

########################

FILTER_MOVIES = ADDON.getSettingBool('filter_movies')
FILTER_SHOWS = ADDON.getSettingBool('filter_shows')
FILTER_SHOWS_BLACKLIST = [10763, 10764, 10767]
FILTER_UPCOMING = ADDON.getSettingBool('filter_upcoming')
FILTER_DAYDELTA = int(ADDON.getSetting('filter_daydelta'))

########################

class TMDBPersons(object):
    def __init__(self,call_request):
        self.tmdb_id = call_request['tmdb_id']
        self.local_movies = call_request['local_movies']
        self.local_shows = call_request['local_shows']
        self.result = {}

        if self.tmdb_id:
            cache_key = 'person' + str(self.tmdb_id)
            self.details = get_cache(cache_key)

            if not self.details:
                self.details = tmdb_query(action='person',
                                          call=self.tmdb_id,
                                          params={'append_to_response': 'translations,movie_credits,tv_credits,images'},
                                          show_error=True
                                          )

                write_cache(cache_key, self.details)

            if not self.details:
                return

            self.local_movie_count = 0
            self.local_tv_count = 0
            self.all_credits = list()

            self.result['movies'] = self.get_movie_list()
            self.result['tvshows'] = self.get_tvshow_list()
            self.result['combined'] = self.get_combined_list()
            self.result['person'] = self.get_person_details()
            self.result['images'] = self.get_person_images()

    def __getitem__(self,key):
        return self.result.get(key, '')

    def get_person_details(self):
        li = list()

        list_item = tmdb_handle_person(self.details)
        list_item.setProperty('LocalMovies', str(self.local_movie_count))
        list_item.setProperty('LocalTVShows', str(self.local_tv_count))
        list_item.setProperty('LocalMedia', str(self.local_movie_count + self.local_tv_count))
        li.append(list_item)

        return li

    def get_combined_list(self):
        combined = sort_dict(self.all_credits, 'release_date', True)
        li = list()

        for item in combined:
            if item['type'] == 'movie':
                list_item, is_local = tmdb_handle_movie(item, self.local_movies)

            elif item['type'] =='tvshow':
                list_item, is_local = tmdb_handle_tvshow(item, self.local_shows)

            li.append(list_item)

        return li

    def get_movie_list(self):
        movies = self.details['movie_credits']['cast']
        movies = sort_dict(movies, 'release_date', True)
        li = list()
        duplicate_handler = list()

        for item in movies:
            skip_movie = False

            ''' Filter to only show real movies and to skip documentaries / behind the scenes / etc
            '''
            if FILTER_MOVIES:
                character = item.get('character')
                if character:
                    for genre in item['genre_ids']:
                        if genre == 99 and ('himself' in character.lower() or 'herself' in character.lower()):
                            skip_movie = True
                            break

            ''' Filter to hide in production or rumored future movies
            '''
            if FILTER_UPCOMING:
                diff = date_delta(item.get('release_date', '2900-01-01'))
                if diff.days > FILTER_DAYDELTA:
                    skip_movie = True

            if not skip_movie and item['id'] not in duplicate_handler:
                list_item, is_local = tmdb_handle_movie(item, self.local_movies)
                li.append(list_item)
                duplicate_handler.append(item['id'])
                item['type'] = 'movie'

                if is_local:
                    self.local_movie_count += 1

                self.all_credits.append(item)

        return li

    def get_tvshow_list(self):
        tvshows = self.details['tv_credits']['cast']
        tvshows = sort_dict(tvshows, 'first_air_date', True)
        li = list()
        duplicate_handler = list()

        for item in tvshows:
            skip_show = False

            ''' Filter to only show real TV series and to skip talk, reality or news shows
            '''
            if FILTER_SHOWS:
                if not item['genre_ids']:
                    skip_show = True
                else:
                    for genre in item['genre_ids']:
                        if genre in FILTER_SHOWS_BLACKLIST:
                            skip_show = True
                            break

            ''' Filter to hide in production or rumored future shows
            '''
            if FILTER_UPCOMING:
                diff = date_delta(item.get('first_air_date', '2900-01-01'))
                if diff.days > FILTER_DAYDELTA:
                    skip_show = True

            if not skip_show and item['id'] not in duplicate_handler:
                list_item, is_local = tmdb_handle_tvshow(item, self.local_shows)
                li.append(list_item)
                duplicate_handler.append(item['id'])
                item['type'] = 'tvshow'
                item['release_date'] = item['first_air_date']

                if is_local:
                    self.local_tv_count += 1

                self.all_credits.append(item)

        return li

    def get_person_images(self):
        li = list()

        for item in self.details['images']['profiles']:
            list_item = tmdb_handle_images(item)
            li.append(list_item)

        return li