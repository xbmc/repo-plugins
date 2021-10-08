import xbmc
from resources.lib.addon.plugin import get_mpaa_prefix, get_language, convert_type, ADDON
from resources.lib.addon.parser import try_int, try_float
from resources.lib.addon.setutils import iter_props, dict_to_list, get_params
from resources.lib.addon.timedate import format_date, age_difference
from resources.lib.addon.constants import IMAGEPATH_ORIGINAL, IMAGEPATH_POSTER, TMDB_GENRE_IDS
from resources.lib.api.mapping import UPDATE_BASEKEY, _ItemMapper, get_empty_item


def get_imagepath_poster(v):
    return u'{}{}'.format(IMAGEPATH_POSTER, v)


def get_imagepath_fanart(v):
    return u'{}{}'.format(IMAGEPATH_ORIGINAL, v)


def get_runtime(v, *args, **kwargs):
    if isinstance(v, list):
        v = v[0]
    return try_int(v) * 60


def get_credits(v):
    infolabels = {}
    infolabels['director'] = [
        i['name'] for i in v.get('crew', []) if i.get('name') and i.get('job') == 'Director']
    infolabels['writer'] = [
        i['name'] for i in v.get('crew', []) if i.get('name') and i.get('department') == 'Writing']
    return infolabels


def get_collection(v):
    infoproperties = {}
    infoproperties['set.tmdb_id'] = v.get('id')
    infoproperties['set.name'] = v.get('name')
    infoproperties['set.poster'] = get_imagepath_poster(v.get('poster_path'))
    infoproperties['set.fanart'] = get_imagepath_fanart(v.get('backdrop_path'))
    return infoproperties


def get_collection_properties(v):
    ratings = []
    infoproperties = {}
    year_l, year_h, votes = 9999, 0, 0
    for p, i in enumerate(v):
        infoproperties[u'set.{}.title'.format(p)] = i.get('title', '')
        infoproperties[u'set.{}.tmdb_id'.format(p)] = i.get('id', '')
        infoproperties[u'set.{}.originaltitle'.format(p)] = i.get('original_title', '')
        infoproperties[u'set.{}.plot'.format(p)] = i.get('overview', '')
        infoproperties[u'set.{}.premiered'.format(p)] = i.get('release_date', '')
        infoproperties[u'set.{}.year'.format(p)] = i.get('release_date', '')[:4]
        infoproperties[u'set.{}.rating'.format(p)] = u'{:0,.1f}'.format(try_float(i.get('vote_average')))
        infoproperties[u'set.{}.votes'.format(p)] = i.get('vote_count', '')
        infoproperties[u'set.{}.poster'.format(p)] = get_imagepath_poster(i.get('poster_path', ''))
        infoproperties[u'set.{}.fanart'.format(p)] = get_imagepath_fanart(i.get('backdrop_path', ''))
        year_l = min(try_int(i.get('release_date', '')[:4]), year_l)
        year_h = max(try_int(i.get('release_date', '')[:4]), year_h)
        if i.get('vote_average'):
            ratings.append(i['vote_average'])
        votes += try_int(i.get('vote_count', 0))
    if year_l == 9999:
        year_l = None
    if year_l:
        infoproperties['set.year.first'] = year_l
    if year_h:
        infoproperties['set.year.last'] = year_h
    if year_l and year_h:
        infoproperties['set.years'] = u'{0} - {1}'.format(year_l, year_h)
    if len(ratings):
        infoproperties['set.rating'] = infoproperties['tmdb_rating'] = u'{:0,.1f}'.format(sum(ratings) / len(ratings))
    if votes:
        infoproperties['set.votes'] = infoproperties['tmdb_votes'] = u'{:0,.0f}'.format(votes)
    infoproperties['set.numitems'] = p
    return infoproperties


def get_mpaa_rating(v, mpaa_prefix, iso_country, certification=True):
    for i in v or []:
        if not i.get('iso_3166_1') or i.get('iso_3166_1') != iso_country:
            continue
        if not certification:
            if i.get('rating'):
                return u'{}{}'.format(mpaa_prefix, i['rating'])
            continue
        for i in sorted(i.get('release_dates', []), key=lambda k: k.get('type')):
            if i.get('certification'):
                return u'{}{}'.format(mpaa_prefix, i['certification'])


def get_iter_props(v, base_name, *args, **kwargs):
    infoproperties = {}
    if kwargs.get('basic_keys'):
        infoproperties = iter_props(
            v, base_name, infoproperties, **kwargs['basic_keys'])
    if kwargs.get('image_keys'):
        infoproperties = iter_props(
            v, base_name, infoproperties, func=get_imagepath_poster, **kwargs['image_keys'])
    return infoproperties


def get_providers(v):
    infoproperties = {}
    infoproperties['provider.link'] = v.pop('link', None)
    newlist = (
        dict(i, **{'key': key}) for key, value in v.items() if isinstance(value, list)
        for i in value if isinstance(i, dict))
    added = []
    added_append = added.append
    for i in sorted(newlist, key=lambda k: k.get('display_priority', 1000)):
        if not i.get('provider_name'):
            continue
        # If provider already added just update type
        if i['provider_name'] in added:
            idx = u'provider.{}.type'.format(added.index(i['provider_name']) + 1)
            infoproperties[idx] = u'{} / {}'.format(infoproperties.get(idx), i.get('key'))
            continue
        # Add item provider
        x = len(added) + 1
        infoproperties.update({
            u'provider.{}.id'.format(x): i.get('provider_id'),
            u'provider.{}.type'.format(x): i.get('key'),
            u'provider.{}.name'.format(x): i['provider_name'],
            u'provider.{}.icon'.format(x): get_imagepath_poster(i.get('logo_path'))})
        added_append(i['provider_name'])
    return infoproperties


def get_trailer(v):
    if not isinstance(v, dict):
        return
    for i in v.get('results') or []:
        if i.get('type', '') != 'Trailer' or i.get('site', '') != 'YouTube' or not i.get('key'):
            continue
        return u'plugin://plugin.video.youtube/play/?video_id={0}'.format(i.get('key'))


def _get_genre_by_id(genre_id):
    for k, v in TMDB_GENRE_IDS.items():
        if v == try_int(genre_id):
            return k


def get_genres_by_id(v):
    genre_ids = v or []
    return [_get_genre_by_id(genre_id) for genre_id in genre_ids if _get_genre_by_id(genre_id)]


def get_external_ids(v):
    unique_ids = {}
    if v.get('imdb_id'):
        unique_ids['imdb'] = v['imdb_id']
    if v.get('tvdb_id'):
        unique_ids['tvdb'] = v['tvdb_id']
    if v.get('id'):
        unique_ids['tmdb'] = v['id']
    return unique_ids


def get_episode_to_air(v, name):
    i = v or {}
    infoproperties = {}
    infoproperties[u'{}'.format(name)] = format_date(i.get('air_date'), xbmc.getRegion('dateshort'))
    infoproperties[u'{}.long'.format(name)] = format_date(i.get('air_date'), xbmc.getRegion('datelong'))
    infoproperties[u'{}.day'.format(name)] = format_date(i.get('air_date'), "%A")
    infoproperties[u'{}.year'.format(name)] = format_date(i.get('air_date'), "%Y")
    infoproperties[u'{}.episode'.format(name)] = i.get('episode_number')
    infoproperties[u'{}.name'.format(name)] = i.get('name')
    infoproperties[u'{}.tmdb_id'.format(name)] = i.get('id')
    infoproperties[u'{}.plot'.format(name)] = i.get('overview')
    infoproperties[u'{}.season'.format(name)] = i.get('season_number')
    infoproperties[u'{}.rating'.format(name)] = u'{:0,.1f}'.format(try_float(i.get('vote_average')))
    infoproperties[u'{}.votes'.format(name)] = i.get('vote_count')
    infoproperties[u'{}.thumb'.format(name)] = get_imagepath_poster(i.get('still_path'))
    return infoproperties


def _get_cast_thumb(i):
    if i.get('thumbnail'):
        return i['thumbnail']
    if i.get('profile_path'):
        return get_imagepath_poster(i['profile_path'])


def _get_cast_item(i, cast_dict):
    name = i.get('name')
    role = i.get('character') or i.get('role')
    if name not in cast_dict:
        return {'name': name, 'role': role, 'order': i.get('order', 9999)}
    item = cast_dict[name]
    if role and item.get('role') and role not in item['role']:
        item['role'] = u'{} / {}'.format(item['role'], role)
    item['order'] = min(item.get('order', 9999), i.get('order', 9999))
    return item


def _get_cast_dict(item, base_item=None):
    cast_list = []
    cast_dict = {}
    if base_item and base_item.get('cast'):
        cast_list += base_item['cast']
    if item.get('credits', {}).get('cast'):
        cast_list += item['credits']['cast']
    if item.get('guest_stars'):
        cast_list += item['guest_stars']
    if not cast_list:
        return cast_dict

    # Build a dictionary of cast members to avoid duplicates by combining roles
    for i in cast_list:
        name = i.get('name')
        cast_dict[name] = _get_cast_item(i, cast_dict)
        if not cast_dict[name].get('thumbnail'):
            cast_dict[name]['thumbnail'] = _get_cast_thumb(i)

    return cast_dict


def set_crew_properties(i, x, prefix):
    infoproperties = {}
    p = u'{}.{}.'.format(prefix, x)
    if i.get('name'):
        infoproperties[u'{}name'.format(p)] = i['name']
    if i.get('job'):
        infoproperties[u'{}role'.format(p)] = infoproperties[u'{}job'.format(p)] = i['job']
    if i.get('character'):
        infoproperties[u'{}role'.format(p)] = infoproperties[u'{}character'.format(p)] = i['character']
    if i.get('department'):
        infoproperties[u'{}department'.format(p)] = i['department']
    if i.get('profile_path'):
        infoproperties[u'{}thumb'.format(p)] = get_imagepath_poster(i['profile_path'])
    return infoproperties


def get_crew_properties(v):
    infoproperties = {}
    department_map = {
        u'Directing': {'name': 'director', 'x': 0},
        u'Writing': {'name': 'writer', 'x': 0},
        u'Production': {'name': 'producer', 'x': 0},
        u'Sound': {'name': 'sound_department', 'x': 0},
        u'Art': {'name': 'art_department', 'x': 0},
        u'Camera': {'name': 'photography', 'x': 0},
        u'Editing': {'name': 'editor', 'x': 0}}
    x = 0
    for i in v:
        if not i.get('name'):
            continue
        x += 1
        infoproperties.update(set_crew_properties(i, x, 'Crew'))
        if i.get('department') not in department_map:
            continue
        dm = department_map[i['department']]
        dm['x'] += 1
        infoproperties.update(set_crew_properties(i, dm['x'], dm['name']))
    return infoproperties


class ItemMapper(_ItemMapper):
    def __init__(self, language=None, mpaa_prefix=None):
        self.language = language or get_language()
        self.mpaa_prefix = mpaa_prefix or get_mpaa_prefix()
        self.iso_language = language[:2]
        self.iso_country = language[-2:]
        self.blacklist = []
        """ Mapping dictionary
        keys:       list of tuples containing parent and child key to add value. [('parent', 'child')]
                    parent keys: art, unique_ids, infolabels, infoproperties, params
                    use UPDATE_BASEKEY for child key to update parent with a dict
        func:       function to call to manipulate values (omit to skip and pass value directly)
        (kw)args:   list/dict of args/kwargs to pass to func.
                    func is also always passed v as first argument
        type:       int, float, str - convert v to type using try_type(v, type)
        extend:     set True to add to existing list - leave blank to overwrite exiting list
        subkeys:    list of sub keys to get for v - i.e. v.get(subkeys[0], {}).get(subkeys[1]) etc.
                    note that getting subkeys sticks for entire loop so do other ops on base first if needed

        use standard_map for direct one-to-one mapping of v onto single property tuple
        """
        self.advanced_map = {
            'poster_path': [{
                'keys': [('art', 'poster')],
                'func': get_imagepath_poster
            }],
            'profile_path': [{
                'keys': [('art', 'poster')],
                'func': get_imagepath_poster
            }],
            'file_path': [{
                'keys': [('art', 'poster')],
                'func': get_imagepath_fanart
            }],
            'still_path': [{
                'keys': [('art', 'thumb')],
                'func': get_imagepath_fanart
            }],
            'backdrop_path': [{
                'keys': [('art', 'fanart')],
                'func': get_imagepath_fanart
            }],
            'content_ratings': [{
                'keys': [('infolabels', 'mpaa')],
                'subkeys': ['results'],
                'func': get_mpaa_rating,
                'args': [self.mpaa_prefix, self.iso_country, False]
            }],
            'release_dates': [{
                'keys': [('infolabels', 'mpaa')],
                'subkeys': ['results'],
                'func': get_mpaa_rating,
                'args': [self.mpaa_prefix, self.iso_country, True]
            }],
            'release_date': [{
                'keys': [('infolabels', 'premiered')]}, {
                'keys': [('infolabels', 'year')],
                'func': lambda v: v[0:4]
            }],
            'first_air_date': [{
                'keys': [('infolabels', 'premiered')]}, {
                'keys': [('infolabels', 'year')],
                'func': lambda v: v[0:4]
            }],
            'air_date': [{
                'keys': [('infolabels', 'premiered')]}, {
                'keys': [('infolabels', 'year')],
                'func': lambda v: v[0:4]
            }],
            'genre_ids': [{
                'keys': [('infolabels', 'genre')],
                'func': get_genres_by_id
            }],
            'videos': [{
                'keys': [('infolabels', 'trailer')],
                'func': get_trailer
            }],
            'popularity': [{
                'keys': [('infoproperties', 'popularity')],
                'type': str
            }],
            'vote_count': [{
                'keys': [('infolabels', 'votes'), ('infoproperties', 'tmdb_votes')],
                'type': float,
                'func': lambda v: u'{:0,.0f}'.format(v)
            }],
            'vote_average': [{
                'keys': [('infolabels', 'rating'), ('infoproperties', 'tmdb_rating')],
                'type': float,
                'func': lambda v: u'{:.1f}'.format(v)
            }],
            'budget': [{
                'keys': [('infoproperties', 'budget')],
                'type': float,
                'func': lambda v: u'${:0,.0f}'.format(v)
            }],
            'revenue': [{
                'keys': [('infoproperties', 'revenue')],
                'type': float,
                'func': lambda v: u'${:0,.0f}'.format(v)
            }],
            'spoken_languages': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': iter_props,
                'args': ['language'],
                'kwargs': {'name': 'name', 'iso': 'iso_639_1'}
            }],
            'keywords': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'subkeys': ['keywords'],
                'func': iter_props,
                'args': ['keyword'],
                'kwargs': {'name': 'name', 'tmdb_id': 'id'}
            }],
            'reviews': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'subkeys': ['results'],
                'func': iter_props,
                'args': ['review'],
                'kwargs': {'content': 'content', 'author': 'author', 'tmdb_id': 'id'}
            }],
            'created_by': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_iter_props,
                'args': ['creator'],
                'kwargs': {
                    'basic_keys': {'name': 'name', 'tmdb_id': 'id'},
                    'image_keys': {'thumb': 'profile_path'}}}, {
                # ---
                'keys': [('infoproperties', 'creator')],
                'func': lambda v: ' / '.join([x['name'] for x in v or [] if x.get('name')])
            }],
            'also_known_as': [{
                'keys': [('infoproperties', 'aliases')],
                'func': lambda v: ' / '.join([x for x in v or [] if x])
            }],
            'known_for': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': iter_props,
                'args': ['known_for'],
                'kwargs': {'title': 'title', 'tmdb_id': 'id', 'rating': 'vote_average', 'tmdb_type': 'media_type'}}, {
                # ---
                'keys': [('infoproperties', 'known_for')],
                'func': lambda v: ' / '.join([x['title'] for x in v or [] if x.get('title')])
            }],
            'external_ids': [{
                'keys': [('unique_ids', UPDATE_BASEKEY)],
                'func': get_external_ids
            }],
            'credits': [{
                'keys': [('infolabels', UPDATE_BASEKEY)],
                'func': get_credits}, {
                # ---
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'subkeys': ['crew'],
                'func': get_crew_properties
            }],
            'parts': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_collection_properties
            }],
            'movie_credits': [{
                'keys': [('infoproperties', 'numitems.tmdb.movies.cast')],
                'func': lambda v: len(v.get('cast') or [])}, {
                # ---
                'keys': [('infoproperties', 'numitems.tmdb.movies.crew')],
                'func': lambda v: len(v.get('crew') or [])}, {
                # ---
                'keys': [('infoproperties', 'numitems.tmdb.movies.total')],
                'func': lambda v: len(v.get('cast') or []) + len(v.get('crew') or [])

            }],
            'tv_credits': [{
                'keys': [('infoproperties', 'numitems.tmdb.tvshows.cast')],
                'func': lambda v: len(v.get('cast') or [])}, {
                # ---
                'keys': [('infoproperties', 'numitems.tmdb.tvshows.crew')],
                'func': lambda v: len(v.get('crew') or [])}, {
                # ---
                'keys': [('infoproperties', 'numitems.tmdb.tvshows.total')],
                'func': lambda v: len(v.get('cast') or []) + len(v.get('crew') or [])

            }],
            'belongs_to_collection': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_collection}, {
                # ---
                'keys': [('infolabels', 'set')],
                'subkeys': ['name']
            }],
            'episode_run_time': [{
                'keys': [('infolabels', 'duration')],
                'func': get_runtime
            }],
            'runtime': [{
                'keys': [('infolabels', 'duration')],
                'func': get_runtime
            }],
            'genres': [{
                'keys': [('infolabels', 'genre')],
                'func': dict_to_list,
                'args': ['name']}, {
                # ---
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': iter_props,
                'args': ['genre'],
                'kwargs': {'name': 'name', 'tmdb_id': 'id'}
            }],
            'production_countries': [{
                'keys': [('infolabels', 'country')],
                'extend': True,
                'func': dict_to_list,
                'args': ['name']}, {
                # ---
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': iter_props,
                'args': ['country'],
                'kwargs': {'name': 'name', 'tmdb_id': 'id'}
            }],
            'networks': [{
                'keys': [('infolabels', 'studio')],
                'extend': True,
                'func': dict_to_list,
                'args': ['name']}, {
                # ---
                'keys': [('infoproperties', 'network')],
                'func': lambda v: ' / '.join([x['name'] for x in v or [] if x.get('name')])}, {
                # ---
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_iter_props,
                'args': ['network'],
                'kwargs': {
                    'basic_keys': {'name': 'name', 'tmdb_id': 'id'},
                    'image_keys': {'icon': 'logo_path'}}
            }],
            'production_companies': [{
                'keys': [('infolabels', 'studio')],
                'extend': True,
                'func': dict_to_list,
                'args': ['name']}, {
                # ---
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_iter_props,
                'args': ['studio'],
                'kwargs': {
                    'basic_keys': {'name': 'name', 'tmdb_id': 'id'},
                    'image_keys': {'icon': 'logo_path'}}
            }],
            'watch/providers': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'subkeys': ['results', self.iso_country],
                'func': get_providers
            }],
            'last_episode_to_air': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_episode_to_air,
                'args': ['last_aired']
            }],
            'next_episode_to_air': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_episode_to_air,
                'args': ['next_aired']
            }],
            'imdb_id': [{
                'keys': [('infolabels', 'imdbnumber'), ('unique_ids', 'imdb')]
            }],
            'character': [{
                'keys': [('infoproperties', 'role'), ('infoproperties', 'character'), ('label2', None)]
            }],
            'job': [{
                'keys': [('infoproperties', 'role'), ('infoproperties', 'job'), ('label2', None)]
            }],
            'biography': [{
                'keys': [('infoproperties', 'biography'), ('infolabels', 'plot')]
            }],
            'gender': [{
                'keys': [('infoproperties', 'gender')],
                'func': lambda v, d: d.get(v),
                'args': [{
                    1: ADDON.getLocalizedString(32071),
                    2: ADDON.getLocalizedString(32070)}]
            }]
        }
        self.standard_map = {
            'overview': ('infolabels', 'plot'),
            'content': ('infolabels', 'plot'),
            'tagline': ('infolabels', 'tagline'),
            'id': ('unique_ids', 'tmdb'),
            'original_title': ('infolabels', 'originaltitle'),
            'original_name': ('infolabels', 'originaltitle'),
            'title': ('infolabels', 'title'),
            'name': ('infolabels', 'title'),
            'author': ('infolabels', 'title'),
            'origin_country': ('infolabels', 'country'),
            'status': ('infolabels', 'status'),
            'season_number': ('infolabels', 'season'),
            'episode_number': ('infolabels', 'episode'),
            'season_count': ('infolabels', 'season'),
            'episode_count': ('infolabels', 'episode'),
            'number_of_seasons': ('infolabels', 'season'),
            'number_of_episodes': ('infolabels', 'episode'),
            'department': ('infoproperties', 'department'),
            'place_of_birth': ('infoproperties', 'born'),
            'birthday': ('infoproperties', 'birthday'),
            'deathday': ('infoproperties', 'deathday'),
            'width': ('infoproperties', 'width'),
            'height': ('infoproperties', 'height'),
            'aspect_ratio': ('infoproperties', 'aspect_ratio')
        }

    def finalise_image(self, item):
        item['infolabels']['title'] = u'{}x{}'.format(
            item['infoproperties'].get('width'),
            item['infoproperties'].get('height'))
        item['params'] = -1
        item['path'] = item['art'].get('thumb') or item['art'].get('poster') or item['art'].get('fanart')
        item['is_folder'] = False
        item['library'] = 'pictures'
        return item

    def finalise_person(self, item):
        if item['infoproperties'].get('birthday'):
            item['infoproperties']['age'] = age_difference(
                item['infoproperties']['birthday'],
                item['infoproperties'].get('deathday'))
        return item

    def finalise(self, item, tmdb_type):
        if tmdb_type == 'image':
            item = self.finalise_image(item)
        elif tmdb_type == 'person':
            item = self.finalise_person(item)
        elif tmdb_type == 'tv' and not item['infolabels'].get('tvshowtitle'):
            item['infolabels']['tvshowtitle'] = item['infolabels'].get('title')
        item['label'] = item['infolabels'].get('title')
        item['infoproperties']['tmdb_type'] = tmdb_type
        item['infolabels']['mediatype'] = item['infoproperties']['dbtype'] = convert_type(tmdb_type, 'dbtype')
        item['art']['thumb'] = item['art'].get('thumb') or item['art'].get('poster')
        for k, v in item['unique_ids'].items():
            item['infoproperties'][u'{}_id'.format(k)] = v
        return item

    def add_cast(self, item, info_item, base_item=None):
        cast_dict = _get_cast_dict(info_item, base_item)
        if not cast_dict:
            return item
        cast_list, cast_prop = [], []
        for x, i in enumerate(sorted(cast_dict, key=lambda k: cast_dict[k].get('order', 9999)), start=1):
            i = cast_dict[i]
            if not i or not i['name']:
                continue
            p = u'{}.{}.'.format('Cast', x)
            for j in [('name', 'Name'), ('role', 'Role'), ('thumbnail', 'Thumb')]:
                item['infoproperties'][u'{}{}'.format(p, j[1])] = i.get(j[0], '')
            cast_prop.append(i['name'])
            cast_list.append(i)
        item['infoproperties']['cast'] = " / ".join(cast_prop)
        item['cast'] = cast_list
        return item

    def get_info(self, info_item, tmdb_type, base_item=None, **kwargs):
        item = get_empty_item()
        item = self.map_item(item, info_item)
        item = self.add_base(item, base_item, tmdb_type, key_blacklist=['year', 'premiered'])
        item = self.add_cast(item, info_item, base_item)
        item = self.finalise(item, tmdb_type)
        item['params'] = get_params(info_item, tmdb_type, params=item.get('params', {}), **kwargs)
        return item
