import resources.lib.utils as utils
from resources.lib.requestapi import RequestAPI


class OMDb(RequestAPI):
    def __init__(self, api_key=None, cache_short=None, cache_long=None, addon_name=None):
        self.req_api_key = '?apikey={0}'.format(api_key)
        self.req_api_name = 'OMDb'
        self.req_api_url = 'http://www.omdbapi.com/'
        self.req_wait_time = 1
        self.cache_long = 14 if not cache_long or cache_long < 14 else cache_long
        self.cache_short = 1 if not cache_short or cache_short < 1 else cache_short
        self.addon_name = addon_name if addon_name else 'plugin.video.themoviedb.helper'

    def get_request_item(self, imdb_id=None, title=None, year=None, tomatoes=True, fullplot=True, cache_only=False):
        kwparams = {}
        kwparams['i'] = imdb_id
        kwparams['t'] = title
        kwparams['y'] = year
        kwparams['plot'] = 'full' if fullplot else 'short'
        kwparams['tomatoes'] = 'True' if tomatoes else None
        kwparams = utils.del_empty_keys(kwparams)
        request = self.get_request_lc(is_json=False, cache_only=cache_only, r='xml', **kwparams)
        if request and request.get('root') and not request.get('root').get('response') == 'False':
            request = request.get('root').get('movie')[0]
        else:
            request = {}
        return request

    def get_infolabels(self, item):
        infolabels = {}
        infolabels['title'] = item.get('title', None)
        infolabels['year'] = item.get('year', None)
        infolabels['mpaa'] = item.get('rated', None)
        infolabels['rating'] = item.get('imdbRating', None)
        infolabels['votes'] = item.get('imdbVotes', None)
        infolabels['duration'] = int(item.get('runtime', '00000')[:-4]) * 60
        infolabels['genre'] = item.get('genre', '').split(', ')
        infolabels['director'] = item.get('director', None)
        infolabels['writer'] = item.get('writer', '').split(', ')
        infolabels['cast'] = item.get('cast', '').split(', ')
        infolabels['plot'] = item.get('plot', None)
        infolabels['country'] = item.get('country', '').split(', ')
        infolabels['mediatype'] = item.get('type', None)
        infolabels['imdbnumber'] = item.get('imdbID', None)
        infolabels['studio'] = item.get('Production', None)
        return infolabels

    def get_infoproperties(self, item):
        infoproperties = {}
        infoproperties['awards'] = item.get('awards', None)
        infoproperties['metacritic_rating'] = item.get('metascore', None)
        infoproperties['imdb_rating'] = item.get('imdbRating', None)
        infoproperties['imdb_votes'] = item.get('imdbVotes', None)
        infoproperties['rottentomatoes_rating'] = item.get('tomatoMeter', None)
        infoproperties['rottentomatoes_image'] = item.get('tomatoImage', None)
        infoproperties['rottentomatoes_reviewtotal'] = item.get('tomatoReviews', None)
        infoproperties['rottentomatoes_reviewsfresh'] = item.get('tomatoFresh', None)
        infoproperties['rottentomatoes_reviewsrotten'] = item.get('tomatoRotten', None)
        infoproperties['rottentomatoes_consensus'] = item.get('tomatoConsensus', None)
        infoproperties['rottentomatoes_usermeter'] = item.get('tomatoUserMeter', None)
        infoproperties['rottentomatoes_userreviews'] = item.get('tomatoUserReviews', None)
        return infoproperties

    def get_ratings_awards(self, imdb_id=None, title=None, year=None, cache_only=False):
        request = self.get_request_item(imdb_id=imdb_id, title=title, year=year, cache_only=cache_only)
        return self.get_infoproperties(request)

    def get_details(self, imdb_id=None, title=None, year=None, cache_only=False):
        request = self.get_request_item(imdb_id=imdb_id, title=title, year=year, cache_only=cache_only)
        return self.get_infolabels(request)
