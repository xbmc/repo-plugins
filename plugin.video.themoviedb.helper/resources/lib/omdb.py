import resources.lib.utils as utils
from resources.lib.requestapi import RequestAPI


class OMDb(RequestAPI):
    def __init__(self, api_key=None, cache_short=None, cache_long=None):
        super(OMDb, self).__init__(
            cache_short=cache_short, cache_long=cache_long,
            req_api_key='apikey={0}'.format(api_key), req_api_name='OMDb',
            req_api_url='http://www.omdbapi.com/', req_wait_time=1)

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
        infolabels = utils.del_empty_keys(infolabels, ['N/A', '0.0', '0'])
        return infolabels

    def get_infoproperties(self, item):
        infoproperties = {}
        infoproperties['awards'] = item.get('awards', None)
        infoproperties['oscar_wins'] = utils.get_between_strings(item.get('awards', ''), 'Won ', ' Oscar')
        infoproperties['oscar_nominations'] = utils.get_between_strings(item.get('awards', ''), 'Nominated for ', ' Oscar')
        infoproperties['award_wins'] = utils.get_between_strings(item.get('awards', ''), '. Another ', ' wins') or utils.get_between_strings(item.get('awards', ''), '', ' wins')
        infoproperties['award_nominations'] = utils.get_between_strings(item.get('awards', ''), 'wins & ', ' nominations') or utils.get_between_strings(item.get('awards', ''), '', ' nominations')
        infoproperties['metacritic_rating'] = item.get('metascore', None)
        infoproperties['imdb_rating'] = item.get('imdbRating', None)
        infoproperties['imdb_votes'] = item.get('imdbVotes', None)
        infoproperties['rottentomatoes_rating'] = item.get('tomatoMeter', None)
        infoproperties['rottentomatoes_image'] = item.get('tomatoImage', None)
        infoproperties['rottentomatoes_reviewstotal'] = '{:0,.0f}'.format(utils.try_parse_int(item.get('tomatoReviews'))) if item.get('tomatoReviews') else None
        infoproperties['rottentomatoes_reviewsfresh'] = '{:0,.0f}'.format(utils.try_parse_int(item.get('tomatoFresh'))) if item.get('tomatoFresh') else None
        infoproperties['rottentomatoes_reviewsrotten'] = '{:0,.0f}'.format(utils.try_parse_int(item.get('tomatoRotten'))) if item.get('tomatoRotten') else None
        infoproperties['rottentomatoes_consensus'] = item.get('tomatoConsensus', None)
        infoproperties['rottentomatoes_usermeter'] = item.get('tomatoUserMeter', None)
        infoproperties['rottentomatoes_userreviews'] = '{:0,.0f}'.format(utils.try_parse_int(item.get('tomatoUserReviews'))) if item.get('tomatoUserReviews') else None
        infoproperties = utils.del_empty_keys(infoproperties, ['N/A', '0.0', '0'])
        return infoproperties

    def get_ratings_awards(self, imdb_id=None, title=None, year=None, cache_only=False):
        request = self.get_request_item(imdb_id=imdb_id, title=title, year=year, cache_only=cache_only)
        return self.get_infoproperties(request)

    def get_details(self, imdb_id=None, title=None, year=None, cache_only=False):
        request = self.get_request_item(imdb_id=imdb_id, title=title, year=year, cache_only=cache_only)
        return self.get_infolabels(request)
