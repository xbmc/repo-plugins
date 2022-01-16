from resources.lib.api.mapping import UPDATE_BASEKEY, _ItemMapper, get_empty_item
from resources.lib.addon.plugin import get_mpaa_prefix, get_language, convert_type, get_setting, get_localized
from resources.lib.addon.parser import try_int, try_float, iter_props, dict_to_list, get_params
from resources.lib.addon.tmdate import format_date, age_difference
from resources.lib.addon.consts import (
    IMAGEPATH_ORIGINAL,
    IMAGEPATH_QUALITY_POSTER,
    IMAGEPATH_QUALITY_FANART,
    IMAGEPATH_QUALITY_THUMBS,
    IMAGEPATH_QUALITY_CLOGOS,
    TMDB_GENRE_IDS,
    ITER_PROPS_MAX
)

ARTWORK_QUALITY = get_setting('artwork_quality', 'int')
ARTWORK_QUALITY_POSTER = IMAGEPATH_QUALITY_POSTER[ARTWORK_QUALITY]
ARTWORK_QUALITY_FANART = IMAGEPATH_QUALITY_FANART[ARTWORK_QUALITY]
ARTWORK_QUALITY_THUMBS = IMAGEPATH_QUALITY_THUMBS[ARTWORK_QUALITY]
ARTWORK_QUALITY_CLOGOS = IMAGEPATH_QUALITY_CLOGOS[ARTWORK_QUALITY]


def get_imagepath_poster(v):
    return f'{ARTWORK_QUALITY_POSTER}{v}' if v else ''


def get_imagepath_fanart(v):
    return f'{ARTWORK_QUALITY_FANART}{v}' if v else ''


def get_imagepath_thumb(v):
    return f'{ARTWORK_QUALITY_THUMBS}{v}' if v else ''


def get_imagepath_logo(v):
    return f'{ARTWORK_QUALITY_CLOGOS}{v}' if v else ''


def get_imagepath_quality(v, quality=IMAGEPATH_ORIGINAL):
    return f'{quality}{v}' if v else ''


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
    for p, i in enumerate(v, start=1):
        infoproperties[f'set.{p}.title'] = i.get('title', '')
        infoproperties[f'set.{p}.tmdb_id'] = i.get('id', '')
        infoproperties[f'set.{p}.originaltitle'] = i.get('original_title', '')
        infoproperties[f'set.{p}.plot'] = i.get('overview', '')
        infoproperties[f'set.{p}.premiered'] = i.get('release_date', '')
        infoproperties[f'set.{p}.year'] = i.get('release_date', '')[:4]
        infoproperties[f'set.{p}.rating'] = f'{try_float(i.get("vote_average")):0,.1f}'
        infoproperties[f'set.{p}.votes'] = i.get('vote_count', '')
        infoproperties[f'set.{p}.poster'] = get_imagepath_poster(i.get('poster_path', ''))
        infoproperties[f'set.{p}.fanart'] = get_imagepath_fanart(i.get('backdrop_path', ''))
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
        infoproperties['set.years'] = f'{year_l} - {year_h}'
    if len(ratings):
        infoproperties['set.rating'] = infoproperties['tmdb_rating'] = f'{sum(ratings) / len(ratings):0,.1f}'
    if votes:
        infoproperties['set.votes'] = infoproperties['tmdb_votes'] = f'{votes:0,.0f}'
    infoproperties['set.numitems'] = p
    return infoproperties


def get_mpaa_rating(v, mpaa_prefix, iso_country, certification=True):
    for i in v or []:
        if not i.get('iso_3166_1') or i.get('iso_3166_1') != iso_country:
            continue
        if not certification:
            if i.get('rating'):
                return f'{mpaa_prefix}{i["rating"]}'
            continue
        for i in sorted(i.get('release_dates', []), key=lambda k: k.get('type')):
            if i.get('certification'):
                return f'{mpaa_prefix}{i["certification"]}'


def get_iter_props(v, base_name, *args, **kwargs):
    infoproperties = {}
    if kwargs.get('basic_keys'):
        infoproperties = iter_props(
            v, base_name, infoproperties, **kwargs['basic_keys'])
    if kwargs.get('image_keys'):
        infoproperties = iter_props(
            v, base_name, infoproperties, func=get_imagepath_poster, **kwargs['image_keys'])
    return infoproperties


def get_providers(v, allowlist=None):
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
        if allowlist and i['provider_name'] not in allowlist:
            continue
        # If provider already added just update type
        if i['provider_name'] in added:
            idx = f'provider.{added.index(i["provider_name"]) + 1}.type'
            infoproperties[idx] = f'{infoproperties.get(idx)} / {i.get("key")}'
            continue
        # Add item provider
        x = len(added) + 1
        infoproperties.update({
            f'provider.{x}.id': i.get('provider_id'),
            f'provider.{x}.type': i.get('key'),
            f'provider.{x}.name': i['provider_name'],
            f'provider.{x}.icon': get_imagepath_logo(i.get('logo_path'))})
        added_append(i['provider_name'])
    infoproperties['providers'] = ' / '.join(added)
    return infoproperties


def get_trailer(v, iso_639_1=None):
    if not isinstance(v, dict):
        return
    url = None
    for i in v.get('results') or []:
        if i.get('type', '') != 'Trailer' or i.get('site', '') != 'YouTube' or not i.get('key'):
            continue
        if i.get('iso_639_1') == iso_639_1:
            return f'plugin://plugin.video.youtube/play/?video_id={i["key"]}'
        url = url or f'plugin://plugin.video.youtube/play/?video_id={i["key"]}'
    return url


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


def get_roles(v, key='character'):
    infoproperties = {}
    for x, i in enumerate(sorted(v, key=lambda d: d.get('episode_count', 0)), start=1):
        infoproperties[f'{key}.{x}.name'] = i.get(key)
        infoproperties[f'{key}.{x}.episodes'] = i.get('episode_count')
        infoproperties[f'{key}.{x}.id'] = i.get('credit_id')
    else:
        name = infoproperties[f'{key}.1.name']
        episodes = infoproperties[f'{key}.1.episodes']
        infoproperties[key] = infoproperties['role'] = f"{name} ({episodes})"
    return infoproperties


def get_extra_art(v):
    """ Get additional artwork types from artwork list
    Fanart with language is treated as landscape because it will have text
    """
    artwork = {}

    landscape = [i for i in v.get('backdrops', []) if i.get('iso_639_1') and i.get('aspect_ratio') == 1.778]
    if landscape:
        landscape = sorted(landscape, key=lambda i: i.get('vote_average', 0), reverse=True)
        artwork['landscape'] = get_imagepath_thumb(landscape[0].get('file_path'))

    clearlogo = [i for i in v.get('logos', []) if i.get('file_path', '')[-4:] != '.svg']
    if clearlogo:
        clearlogo = sorted(clearlogo, key=lambda i: i.get('vote_average', 0), reverse=True)
        artwork['clearlogo'] = get_imagepath_logo(clearlogo[0].get('file_path'))

    fanart = [i for i in v.get('backdrops', []) if not i.get('iso_639_1') and i.get('aspect_ratio') == 1.778]
    if fanart:
        fanart = sorted(fanart, key=lambda i: i.get('vote_average', 0), reverse=True)
        artwork['fanart'] = get_imagepath_fanart(fanart[0].get('file_path'))

    return artwork


def get_episode_to_air(v, name):
    i = v or {}
    air_date = i.get('air_date')
    infoproperties = {}
    infoproperties[f'{name}'] = format_date(air_date, region_fmt='dateshort')
    infoproperties[f'{name}.long'] = format_date(air_date, region_fmt='datelong')
    infoproperties[f'{name}.short'] = format_date(air_date, "%d %b")
    infoproperties[f'{name}.day'] = format_date(air_date, "%A")
    infoproperties[f'{name}.day_short'] = format_date(air_date, "%a")
    infoproperties[f'{name}.year'] = format_date(air_date, "%Y")
    infoproperties[f'{name}.episode'] = i.get('episode_number')
    infoproperties[f'{name}.name'] = i.get('name')
    infoproperties[f'{name}.tmdb_id'] = i.get('id')
    infoproperties[f'{name}.plot'] = i.get('overview')
    infoproperties[f'{name}.season'] = i.get('season_number')
    infoproperties[f'{name}.rating'] = f'{try_float(i.get("vote_average")):0,.1f}'
    infoproperties[f'{name}.votes'] = i.get('vote_count')
    infoproperties[f'{name}.thumb'] = get_imagepath_thumb(i.get('still_path'))
    infoproperties[f'{name}.original'] = air_date
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
        item['role'] = f'{item["role"]} / {role}'
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
    p = f'{prefix}.{x}.'
    if i.get('name'):
        infoproperties[f'{p}name'] = i['name']
    if i.get('job'):
        infoproperties[f'{p}role'] = infoproperties[f'{p}job'] = i['job']
    if i.get('character'):
        infoproperties[f'{p}role'] = infoproperties[f'{p}character'] = i['character']
    if i.get('department'):
        infoproperties[f'{p}department'] = i['department']
    if i.get('profile_path'):
        infoproperties[f'{p}thumb'] = get_imagepath_poster(i['profile_path'])
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
        if x <= ITER_PROPS_MAX:
            infoproperties.update(set_crew_properties(i, x, 'Crew'))
        if i.get('department') not in department_map:
            continue
        dm = department_map[i['department']]
        dm['x'] += 1
        if dm['x'] <= ITER_PROPS_MAX:
            infoproperties.update(set_crew_properties(i, dm['x'], dm['name']))
    return infoproperties


class ItemMapper(_ItemMapper):
    def __init__(self, language=None, mpaa_prefix=None):
        self.language = language or get_language()
        self.mpaa_prefix = mpaa_prefix or get_mpaa_prefix()
        self.iso_language = language[:2]
        self.iso_country = language[-2:]
        self.imagepath_quality = 'IMAGEPATH_ORIGINAL'
        self.provider_allowlist = get_setting('provider_allowlist', 'str')
        self.provider_allowlist = self.provider_allowlist.split(' | ') if self.provider_allowlist else []
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
            'episodes': [{
                'keys': [('infolabels', 'episode')],
                'func': lambda v: f'{len(v)}'
            }],
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
                'func': self.get_imagepath_quality
            }],
            'still_path': [{
                'keys': [('art', 'thumb')],
                'func': get_imagepath_thumb
            }],
            'logo_path': [{
                'keys': [('art', 'thumb')],
                'func': get_imagepath_quality
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
                'func': get_trailer,
                'args': [self.iso_language]
            }],
            'popularity': [{
                'keys': [('infoproperties', 'popularity')],
                'type': str
            }],
            'vote_count': [{
                'keys': [('infolabels', 'votes'), ('infoproperties', 'tmdb_votes')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'
            }],
            'vote_average': [{
                'keys': [('infolabels', 'rating'), ('infoproperties', 'tmdb_rating')],
                'type': float,
                'func': lambda v: f'{v:.1f}'
            }],
            'budget': [{
                'keys': [('infoproperties', 'budget')],
                'type': float,
                'func': lambda v: f'${v:0,.0f}'
            }],
            'revenue': [{
                'keys': [('infoproperties', 'revenue')],
                'type': float,
                'func': lambda v: f'${v:0,.0f}'
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
            'roles': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_roles,
                'kwargs': {'key': 'character'}
            }],
            'jobs': [{
                'keys': [('infoproperties', UPDATE_BASEKEY)],
                'func': get_roles,
                'kwargs': {'key': 'job'}
            }],
            'external_ids': [{
                'keys': [('unique_ids', UPDATE_BASEKEY)],
                'func': get_external_ids
            }],
            'images': [{
                'keys': [('art', UPDATE_BASEKEY)],
                'func': get_extra_art
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
                'kwargs': {'allowlist': self.provider_allowlist},
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
                    1: get_localized(32071),
                    2: get_localized(32070)}]
            }]
        }
        self.standard_map = {
            'overview': ('infolabels', 'plot'),
            'content': ('infolabels', 'plot'),
            'tagline': ('infolabels', 'tagline'),
            'id': ('unique_ids', 'tmdb'),
            'provider_id': ('unique_ids', 'tmdb'),
            'original_title': ('infolabels', 'originaltitle'),
            'original_name': ('infolabels', 'originaltitle'),
            'title': ('infolabels', 'title'),
            'name': ('infolabels', 'title'),
            'author': ('infolabels', 'title'),
            'provider_name': ('infolabels', 'title'),
            'origin_country': ('infolabels', 'country'),
            'status': ('infolabels', 'status'),
            'season_number': ('infolabels', 'season'),
            'episode_number': ('infolabels', 'episode'),
            'season_count': ('infolabels', 'season'),
            'episode_count': ('infolabels', 'episode'),
            'number_of_seasons': ('infolabels', 'season'),
            'number_of_episodes': ('infolabels', 'episode'),
            'department': ('infoproperties', 'department'),
            'known_for_department': ('infoproperties', 'department'),
            'place_of_birth': ('infoproperties', 'born'),
            'birthday': ('infoproperties', 'birthday'),
            'deathday': ('infoproperties', 'deathday'),
            'width': ('infoproperties', 'width'),
            'height': ('infoproperties', 'height'),
            'aspect_ratio': ('infoproperties', 'aspect_ratio')
        }

    def get_imagepath_quality(self, v):
        try:
            quality = globals()[self.imagepath_quality]
        except KeyError:
            quality = IMAGEPATH_ORIGINAL
        return get_imagepath_quality(v, quality)

    def finalise(self, item, tmdb_type):

        def _finalise_image():
            item['infolabels']['title'] = f'{item["infoproperties"].get("width")}x{item["infoproperties"].get("height")}'
            item['params'] = -1
            item['infolabels']['picturepath'] = item['path'] = item['art'].get('thumb') or item['art'].get('poster') or item['art'].get('fanart')
            item['is_folder'] = False
            item['library'] = 'pictures'

        def _finalise_person():
            if item['infoproperties'].get('birthday'):
                item['infoproperties']['age'] = age_difference(
                    item['infoproperties']['birthday'],
                    item['infoproperties'].get('deathday'))

        def _finalise_tv():
            item['infolabels']['tvshowtitle'] = item['infolabels'].get('title')

        def _finalise_video():
            item['params'] = -1

        finalise_route = {
            'image': _finalise_image,
            'person': _finalise_person,
            'tv': _finalise_tv,
            'video': _finalise_video}

        if tmdb_type in finalise_route:
            finalise_route[tmdb_type]()

        item['label'] = item['infolabels'].get('title')
        item['infoproperties']['tmdb_type'] = tmdb_type
        item['infolabels']['mediatype'] = item['infoproperties']['dbtype'] = convert_type(tmdb_type, 'dbtype')
        for k, v in item['unique_ids'].items():
            item['infoproperties'][f'{k}_id'] = v

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
            if x <= ITER_PROPS_MAX:
                p = f'Cast.{x}.'
                for j in [('name', 'Name'), ('role', 'Role'), ('thumbnail', 'Thumb')]:
                    item['infoproperties'][f'{p}{j[1]}'] = i.get(j[0], '')
            cast_prop.append(i['name'])
            cast_list.append(i)
        item['infoproperties']['cast'] = " / ".join(cast_prop)
        item['cast'] = cast_list
        return item

    def get_info(self, info_item, tmdb_type, base_item=None, base_is_season=False, **kwargs):
        item = get_empty_item()
        item = self.map_item(item, info_item)
        item = self.add_base(item, base_item, tmdb_type, key_blacklist=['year', 'premiered', 'season', 'episode'], is_season=base_is_season)
        item = self.add_cast(item, info_item, base_item)
        item = self.finalise(item, tmdb_type)
        item['params'] = get_params(info_item, tmdb_type, params=item.get('params', {}), **kwargs)
        return item
