import resources.lib.utils as utils
from resources.lib.requestapi import RequestAPI
from resources.lib.listitem import ListItem
_genreids = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80, "Documentary": 99, "Drama": 18,
    "Family": 10751, "Fantasy": 14, "History": 36, "Horror": 27, "Kids": 10762, "Music": 10402, "Mystery": 9648,
    "News": 10763, "Reality": 10764, "Romance": 10749, "Science Fiction": 878, "Sci-Fi & Fantasy": 10765, "Soap": 10766,
    "Talk": 10767, "TV Movie": 10770, "Thriller": 53, "War": 10752, "War & Politics": 10768, "Western": 37}


class TMDb(RequestAPI):
    def __init__(self, api_key=None, language=None, cache_long=None, cache_short=None, append_to_response=None, mpaa_prefix=None, filter_key=None, filter_value=None, exclude_key=None, exclude_value=None):
        super(TMDb, self).__init__(
            cache_short=cache_short, cache_long=cache_long,
            req_api_name='TMDb', req_api_url='https://api.themoviedb.org/3', req_wait_time=0.25,
            req_api_key='?api_key=a07324c669cac4d96789197134ce272b')
        api_key = api_key if api_key else 'a07324c669cac4d96789197134ce272b'
        language = language if language else 'en-US'
        self.iso_language = language[:2]
        self.iso_country = language[-2:]
        self.req_language = '{0}-{1}&include_image_language={0},null'.format(self.iso_language, self.iso_country)
        self.req_api_key = '?api_key={0}'.format(api_key)
        self.req_append = append_to_response if append_to_response else None
        self.imagepath_original = 'https://image.tmdb.org/t/p/original'
        self.imagepath_poster = 'https://image.tmdb.org/t/p/w500'
        self.mpaa_prefix = '{0} '.format(mpaa_prefix) if mpaa_prefix else ''
        self.filter_key = filter_key if filter_key else None
        self.filter_value = filter_value if filter_value else None
        self.exclude_key = exclude_key if exclude_key else None
        self.exclude_value = exclude_value if exclude_value else None
        self.library = 'video'

    def get_title(self, item):
        if item.get('title'):
            return item.get('title')
        elif item.get('name'):
            return item.get('name')
        elif item.get('author'):
            return item.get('author')
        elif item.get('width') and item.get('height'):
            return u'{0}x{1}'.format(item.get('width'), item.get('height'))

    def get_imagepath(self, path_affix, poster=False):
        if poster:
            return '{0}{1}'.format(self.imagepath_poster, path_affix)
        return '{0}{1}'.format(self.imagepath_original, path_affix)

    def get_icon(self, item):
        if item.get('poster_path'):
            return self.get_imagepath(item.get('poster_path'), poster=True)
        elif item.get('profile_path'):
            return self.get_imagepath(item.get('profile_path'), poster=True)
        elif item.get('file_path'):
            return self.get_imagepath(item.get('file_path'))

    def get_season_poster(self, item):
        if item.get('season_number') and item.get('seasons'):
            for i in item.get('seasons'):
                if i.get('season_number') == item.get('season_number'):
                    if i.get('poster_path'):
                        return self.get_imagepath(i.get('poster_path'), poster=True)
                    break

    def get_season_thumb(self, item):
        if item.get('still_path'):
            return self.get_imagepath(item.get('still_path'))

    def get_fanart(self, item):
        if item.get('backdrop_path'):
            return self.get_imagepath(item.get('backdrop_path'))

    def get_infolabels(self, item):
        infolabels = {}
        infolabels['title'] = self.get_title(item)
        infolabels['originaltitle'] = item.get('original_title')
        infolabels['tvshowtitle'] = item.get('tvshowtitle')
        infolabels['plot'] = item.get('overview') or item.get('biography') or item.get('content')
        infolabels['rating'] = item.get('vote_average')
        infolabels['votes'] = '{:0,.0f}'.format(item.get('vote_count')) if item.get('vote_count') else None
        infolabels['premiered'] = item.get('air_date') or item.get('release_date') or item.get('first_air_date') or ''
        infolabels['year'] = infolabels.get('premiered')[:4]
        infolabels['imdbnumber'] = item.get('imdb_id')
        infolabels['tagline'] = item.get('tagline')
        infolabels['status'] = item.get('status')
        infolabels['episode'] = item.get('episode_number') if item.get('episode_number') or item.get('episode_number') == 0 else item.get('number_of_episodes')
        infolabels['season'] = item.get('season_number') if item.get('season_number') or item.get('season_number') == 0 else item.get('number_of_seasons')
        infolabels['genre'] = utils.dict_to_list(item.get('genres', []), 'name')
        if item.get('runtime'):
            infolabels['duration'] = item.get('runtime', 0) * 60
        if item.get('belongs_to_collection'):
            infolabels['set'] = item.get('belongs_to_collection').get('name')
        if item.get('networks'):
            infolabels['studio'] = infolabels.setdefault('studio', []) + utils.dict_to_list(item.get('networks'), 'name')
        if item.get('production_companies'):
            infolabels['studio'] = infolabels.setdefault('studio', []) + utils.dict_to_list(item.get('production_companies'), 'name')
        if item.get('production_countries'):
            infolabels['country'] = infolabels.setdefault('country', []) + utils.dict_to_list(item.get('production_countries'), 'name')
        if item.get('origin_country'):
            infolabels['country'] = infolabels.setdefault('country', []) + item.get('origin_country')
        if item.get('release_dates') and item.get('release_dates').get('results'):
            for i in item.get('release_dates').get('results'):
                if i.get('iso_3166_1') and i.get('iso_3166_1') == self.iso_country:
                    if i.get('release_dates') and i.get('release_dates')[0].get('certification'):
                        infolabels['MPAA'] = '{0}{1}'.format(self.mpaa_prefix, i.get('release_dates')[0].get('certification'))
        if item.get('content_ratings') and item.get('content_ratings').get('results'):
            for i in item.get('content_ratings').get('results'):
                if i.get('iso_3166_1') and i.get('iso_3166_1') == self.iso_country and i.get('rating'):
                    infolabels['MPAA'] = '{0}{1}'.format(self.mpaa_prefix, i.get('rating'))
        return infolabels

    def get_infoproperties(self, item):
        infoproperties = {}
        infoproperties['tmdb_id'] = item.get('id')
        infoproperties['imdb_id'] = item.get('imdb_id') or item.get('external_ids', {}).get('imdb_id')
        infoproperties['tvdb_id'] = item.get('external_ids', {}).get('tvdb_id')
        infoproperties['biography'] = item.get('biography')
        infoproperties['birthday'] = item.get('birthday')
        infoproperties['age'] = utils.age_difference(item.get('birthday'), item.get('deathday'))
        infoproperties['deathday'] = item.get('deathday')
        infoproperties['character'] = item.get('character')
        infoproperties['department'] = item.get('department')
        infoproperties['job'] = item.get('job')
        infoproperties['known_for'] = item.get('known_for_department')
        infoproperties['role'] = item.get('character') or item.get('job') or item.get('department') or item.get('known_for_department')
        infoproperties['born'] = item.get('place_of_birth')
        if item.get('last_episode_to_air'):
            i = item.get('last_episode_to_air', {})
            infoproperties['last_aired'] = i.get('air_date')
            infoproperties['last_aired.episode'] = i.get('episode_number')
            infoproperties['last_aired.name'] = i.get('name')
            infoproperties['last_aired.tmdb_id'] = i.get('id')
            infoproperties['last_aired.plot'] = i.get('overview')
            infoproperties['last_aired.season'] = i.get('season_number')
            infoproperties['last_aired.rating'] = i.get('vote_average')
            infoproperties['last_aired.votes'] = i.get('vote_count')
            infoproperties['last_aired.thumb'] = self.get_season_thumb(i)
        if item.get('next_episode_to_air'):
            i = item.get('next_episode_to_air', {})
            infoproperties['next_aired'] = i.get('air_date')
            infoproperties['next_aired.episode'] = i.get('episode_number')
            infoproperties['next_aired.name'] = i.get('name')
            infoproperties['next_aired.tmdb_id'] = i.get('id')
            infoproperties['next_aired.plot'] = i.get('overview')
            infoproperties['next_aired.season'] = i.get('season_number')
            infoproperties['next_aired.thumb'] = self.get_season_thumb(i)
        if item.get('created_by'):
            infoproperties = utils.iter_props(item.get('created_by'), 'Creator', infoproperties, name='name', tmdb_id='id')
            infoproperties['creator'] = utils.concatinate_names(item.get('created_by'), 'name', '/')
        if item.get('genres'):
            infoproperties = utils.iter_props(item.get('genres'), 'Genre', infoproperties, name='name', tmdb_id='id')
        if item.get('networks'):
            infoproperties = utils.iter_props(item.get('networks'), 'Studio', infoproperties, name='name', tmdb_id='id')
            infoproperties = utils.iter_props(item.get('networks'), 'Studio', infoproperties, icon='logo_path', func=self.get_imagepath)
        if item.get('production_companies'):
            infoproperties = utils.iter_props(item.get('production_companies'), 'Studio', infoproperties, name='name', tmdb_id='id')
            infoproperties = utils.iter_props(item.get('production_companies'), 'Studio', infoproperties, icon='logo_path', func=self.get_imagepath)
        if item.get('production_countries'):
            infoproperties = utils.iter_props(item.get('production_countries'), 'Country', infoproperties, name='name', tmdb_id='id')
        if item.get('spoken_languages'):
            infoproperties = utils.iter_props(item.get('spoken_languages'), 'Language', infoproperties, name='name', iso='iso_639_1')
        if item.get('also_known_as'):
            infoproperties['aliases'] = ' / '.join(item.get('also_known_as'))
        if item.get('known_for'):
            infoproperties['known_for'] = utils.concatinate_names(item.get('known_for'), 'title', '/')
            infoproperties = utils.iter_props(item.get('known_for'), 'known_for', infoproperties, title='title', tmdb_id='id', rating='vote_average', tmdb_type='media_type')
        if item.get('budget'):
            infoproperties['budget'] = '${:0,.0f}'.format(item.get('budget'))
        if item.get('revenue'):
            infoproperties['revenue'] = '${:0,.0f}'.format(item.get('revenue'))
        if item.get('belongs_to_collection'):
            infoproperties['set.tmdb_id'] = item.get('belongs_to_collection').get('id')
            infoproperties['set.name'] = item.get('belongs_to_collection').get('name')
            infoproperties['set.poster'] = self.get_imagepath(item.get('belongs_to_collection').get('poster_path'))
            infoproperties['set.fanart'] = self.get_imagepath(item.get('belongs_to_collection').get('backdrop_path'))
        return infoproperties

    def get_trailer(self, item):
        infolabels = {}
        if not isinstance(item, dict):
            return infolabels
        videos = item.get('videos') or {}
        videos = videos.get('results') or []
        for i in videos:
            if i.get('type', '') != 'Trailer' or i.get('site', '') != 'YouTube' or not i.get('key'):
                continue
            infolabels['trailer'] = 'plugin://plugin.video.youtube/play/?video_id={0}'.format(i.get('key'))
            break
        return infolabels

    def get_cast(self, item):
        cast = []
        if item.get('credits') or item.get('guest_stars'):
            cast_list = []
            if item.get('guest_stars'):
                cast_list = cast_list + item.get('guest_stars')
            if item.get('credits') and item.get('credits').get('cast'):
                cast_list = cast_list + item.get('credits').get('cast')
            if cast_list:
                added_names = []
                for i in sorted(cast_list, key=lambda k: k.get('order', 0)):
                    if i.get('name') and not i.get('name') in added_names:
                        added_names.append(i.get('name'))  # Add name to temp list to prevent dupes
                        cast_member = {}
                        cast_member['name'] = i.get('name')
                        cast_member['role'] = i.get('character')
                        cast_member['order'] = i.get('order')
                        cast_member['thumbnail'] = self.get_imagepath(i.get('profile_path'), poster=True) if i.get('profile_path') else ''
                        cast.append(cast_member)
        return cast

    def get_cast_properties(self, cast):
        x = 1
        infoproperties = {}
        for cast_member in cast:
            p = 'Cast.{0}.'.format(x)
            infoproperties['{0}name'.format(p)] = cast_member.get('name')
            infoproperties['{0}role'.format(p)] = cast_member.get('role')
            infoproperties['{0}thumb'.format(p)] = cast_member.get('thumbnail')
            x = x + 1
        return infoproperties

    def get_crew_properties(self, item):
        infoproperties = {}
        if item.get('credits'):
            crew_list = item.get('credits', {}).get('crew', [])
            x = 1
            for i in crew_list:
                if i.get('name'):
                    p = 'Crew.{0}.'.format(x)
                    infoproperties['{0}name'.format(p)] = i.get('name')
                    infoproperties['{0}job'.format(p)] = i.get('job')
                    infoproperties['{0}department'.format(p)] = i.get('department')
                    infoproperties['{0}thumb'.format(p)] = self.get_imagepath(i.get('profile_path'), poster=True) if i.get('profile_path') else ''
                    x = x + 1
        return infoproperties

    def get_director_writer(self, item):
        infolabels = {}
        if item.get('credits'):
            crew_list = item.get('credits', {}).get('crew', [])
            for i in crew_list:
                if i.get('name'):
                    if i.get('job') == 'Director':
                        infolabels.setdefault('director', []).append(i.get('name'))
                    if i.get('department') == 'Writing':
                        infolabels.setdefault('writer', []).append(i.get('name'))
        return infolabels

    def get_niceitem(self, item):
        label = self.get_title(item)
        icon = self.get_icon(item)
        poster = self.get_season_poster(item) or icon
        thumb = self.get_season_thumb(item) or ''
        fanart = self.get_fanart(item)
        cast = self.get_cast(item)
        infolabels = self.get_infolabels(item)
        infolabels = utils.merge_two_dicts(infolabels, self.get_trailer(item))
        infolabels = utils.merge_two_dicts(infolabels, self.get_director_writer(item))
        infoproperties = self.get_infoproperties(item)
        infoproperties = utils.merge_two_dicts(infoproperties, self.get_cast_properties(cast))
        infoproperties = utils.merge_two_dicts(infoproperties, self.get_crew_properties(item))
        return {
            'label': label, 'icon': icon, 'poster': poster, 'thumb': thumb, 'fanart': fanart,
            'cast': cast, 'infolabels': infolabels, 'infoproperties': infoproperties,
            'tmdb_id': infoproperties.get('tmdb_id'), 'imdb_id': infoproperties.get('imdb_id'),
            'tvdb_id': infoproperties.get('tvdb_id')}

    def get_nicelist(self, items):
        return [
            ListItem(library=self.library, **self.get_niceitem(i)) for i in items if
            not utils.filtered_item(i, self.filter_key, self.filter_value) and
            not utils.filtered_item(i, self.exclude_key, self.exclude_value, True)]

    def get_translated_list(self, items, itemtype=None, separator=None):
        """
        If itemtype specified will look-up IDs using search function otherwise assumes item ID is passed
        """
        separator = self.get_url_separator(separator)
        temp_list = ''
        for item in items:
            item_id = self.get_tmdb_id(itemtype=itemtype, query=item, longcache=True) if itemtype else item
            if item_id:
                if separator:  # If we've got a url separator then concatinate the list with it
                    temp_list = '{0}{1}{2}'.format(temp_list, separator, item_id) if temp_list else item_id
                else:  # If no separator, assume that we just want to use the first found ID
                    temp_list = str(item_id)
                    break  # Stop once we have a item
        temp_list = temp_list if temp_list else 'null'
        return temp_list

    def get_url_separator(self, separator=None):
        if separator == 'AND':
            return '%2C'
        elif separator == 'OR':
            return '%7C'
        elif not separator:
            return '%2C'
        else:
            return False

    def get_detailed_item(self, itemtype, tmdb_id, season=None, episode=None, cache_only=False, cache_refresh=False):
        extra_request = None
        cache_name = '{0}.TMDb.{1}.{2}'.format(self.cache_name, itemtype, tmdb_id)
        cache_name = '{0}.Season{1}'.format(cache_name, season) if season else cache_name
        cache_name = '{0}.Episode{1}'.format(cache_name, episode) if season and episode else cache_name
        itemdict = self.get_cache(cache_name) if not cache_refresh else None
        if not itemdict and not cache_only:
            request = self.get_request_lc(itemtype, tmdb_id, language=self.req_language, append_to_response=self.req_append, cache_refresh=cache_refresh)
            if itemtype == 'tv':
                request['tvshowtitle'] = self.get_title(request)
            if season and episode:
                extra_request = self.get_request_lc('tv', tmdb_id, 'season', season, 'episode', episode, language=self.req_language, append_to_response=self.req_append, cache_refresh=cache_refresh)
            elif season:
                extra_request = self.get_request_lc('tv', tmdb_id, 'season', season, language=self.req_language, append_to_response=self.req_append, cache_refresh=cache_refresh)
            if season and episode and not extra_request:
                extra_request = {'episode_number': episode, 'season_number': season}
            if extra_request:
                request = utils.merge_two_dicts(request, extra_request)
            itemdict = self.set_cache(self.get_niceitem(request), cache_name, self.cache_long) if request else {}
        return itemdict

    def get_externalid_item(self, itemtype, external_id, external_source):
        """
        Lookup an item using an external id such as IMDb or TVDb
        """
        cache_name = '{0}.find.{1}.{2}'.format(self.cache_name, external_source, external_id)
        itemdict = self.get_cache(cache_name)
        if not itemdict:
            request = self.get_request_lc('find', external_id, language=self.req_language, append_to_response=self.req_append, external_source=external_source)
            request = request.get('{0}_results'.format(itemtype), [])
            itemdict = self.set_cache(self.get_niceitem(request[0]), cache_name, self.cache_long) if request else {}
        if itemdict.get('tmdb_id'):
            itemdict = self.get_detailed_item(itemtype, itemdict.get('tmdb_id'), cache_only=True) or itemdict
        return itemdict

    def get_item_externalid(self, itemtype, tmdb_id, external_id=None):
        """
        Lookup external ids for an item using tmdb_id
        """
        request = self.get_request_lc(itemtype, tmdb_id, 'external_ids') or {}
        return request.get(external_id) if external_id else request

    def get_tmdb_id(self, itemtype=None, imdb_id=None, query=None, year=None, selectdialog=False, longcache=False):
        func = self.get_request_lc if longcache else self.get_request_sc
        if not itemtype:
            return
        request = None
        if itemtype == 'genre' and query:
            return _genreids.get(query, '')
        elif imdb_id:
            request = func('find', imdb_id, language=self.req_language, external_source='imdb_id')
            request = request.get('{0}_results'.format(itemtype), [])
        elif query:
            request = func('search', itemtype, language=self.req_language, query=query, year=year)
            request = request.get('results', [])
        if not request:
            return
        itemindex = 0
        if selectdialog:
            item = utils.dialog_select_item(items=request, details=self)
            return item.get('id') if item else None
        return request[itemindex].get('id')

    def get_credits_list(self, itemtype, tmdb_id, key):
        return self.get_list(itemtype, tmdb_id, 'credits', key=key, longcache=True)

    def get_list(self, *args, **kwargs):
        key = kwargs.pop('key', 'results')
        pagination = kwargs.pop('pagination', True)
        longcache = kwargs.pop('longcache', False)
        func = self.get_request_lc if longcache else self.get_request_sc
        request = func(*args, language=self.req_language, **kwargs)
        items = self.get_nicelist(request.get(key, []))
        if pagination and utils.try_parse_int(request.get('page', 0)) < utils.try_parse_int(request.get('total_pages', 0)):
            items.append(ListItem(library=self.library, label='Next Page', nextpage=utils.try_parse_int(request.get('page', 0)) + 1))
        return items
