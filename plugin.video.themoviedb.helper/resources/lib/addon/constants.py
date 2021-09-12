ALPHANUM_CHARS = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
INVALID_FILECHARS = "\\/\"\'<>:|?*"

ACCEPTED_MEDIATYPES = [
    'video', 'movie', 'tvshow', 'season', 'episode', 'musicvideo', 'music', 'song', 'album', 'artist']

LANGUAGES = [
    'ar-AE', 'ar-SA', 'be-BY', 'bg-BG', 'bn-BD', 'ca-ES', 'ch-GU', 'cs-CZ', 'da-DK', 'de-AT', 'de-CH',
    'de-DE', 'el-GR', 'en-AU', 'en-CA', 'en-GB', 'en-IE', 'en-NZ', 'en-US', 'eo-EO', 'es-ES', 'es-MX',
    'et-EE', 'eu-ES', 'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR', 'gl-ES', 'he-IL', 'hi-IN', 'hu-HU', 'id-ID',
    'it-IT', 'ja-JP', 'ka-GE', 'kk-KZ', 'kn-IN', 'ko-KR', 'lt-LT', 'lv-LV', 'ml-IN', 'ms-MY', 'ms-SG',
    'nb-NO', 'nl-NL', 'no-NO', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK', 'sl-SI',
    'sr-RS', 'sv-SE', 'ta-IN', 'te-IN', 'th-TH', 'tl-PH', 'tr-TR', 'uk-UA', 'vi-VN', 'zh-CN', 'zh-HK',
    'zh-TW', 'zu-ZA']

TMDB_PARAMS_SEASONS = {
    'info': 'details',
    'tmdb_type': 'tv',
    'tmdb_id': '{tmdb_id}',
    'season': '{season_number}'}

TMDB_PARAMS_EPISODES = {
    'info': 'details',
    'tmdb_type': 'tv',
    'tmdb_id': '{tmdb_id}',
    'season': '{season_number}',
    'episode': '{episode_number}'}

IMAGEPATH_ORIGINAL = 'https://image.tmdb.org/t/p/original'

IMAGEPATH_POSTER = 'https://image.tmdb.org/t/p/w500'

TMDB_GENRE_IDS = {
    "Action": 28, "Adventure": 12, "Action & Adventure": 10759, "Animation": 16, "Comedy": 35, "Crime": 80, "Documentary": 99, "Drama": 18,
    "Family": 10751, "Fantasy": 14, "History": 36, "Horror": 27, "Kids": 10762, "Music": 10402, "Mystery": 9648,
    "News": 10763, "Reality": 10764, "Romance": 10749, "Science Fiction": 878, "Sci-Fi & Fantasy": 10765, "Soap": 10766,
    "Talk": 10767, "TV Movie": 10770, "Thriller": 53, "War": 10752, "War & Politics": 10768, "Western": 37}

PLAYERS_URLENCODE = [
    'name', 'showname', 'clearname', 'tvshowtitle', 'title', 'thumbnail', 'poster', 'fanart',
    'originaltitle', 'plot', 'cast', 'actors']

PLAYERS_BASEDIR_USER = 'special://profile/addon_data/plugin.video.themoviedb.helper/players/'
PLAYERS_BASEDIR_SAVE = 'special://profile/addon_data/plugin.video.themoviedb.helper/reconfigured_players/'
PLAYERS_BASEDIR_BUNDLED = 'special://home/addons/plugin.video.themoviedb.helper/resources/players/'
PLAYERS_PRIORITY = 1000

NO_LABEL_FORMATTING = ['details', 'upcoming', 'trakt_calendar', 'trakt_myairing', 'trakt_anticipated', 'library_nextaired', 'videos']

TMDB_ALL_ITEMS_LISTS = {
    'movie': {
        'type': 'movie',
        'sort': False,
        'limit': 20
    },
    'tv': {
        'type': 'tv_series',
        'sort': False,
        'limit': 20
    },
    'person': {
        'type': 'person',
        'sort': False,
        'limit': 20
    },
    'collection': {
        'type': 'collection',
        'sort': False,
        'limit': 20
    },
    'network': {
        'type': 'tv_network',
        'sort': True,
        'limit': 2500,
        'params': {
            'info': 'discover', 'tmdb_type': 'tv',
            'with_networks': '{tmdb_id}', 'with_id': 'True'}
    },
    'keyword': {
        'type': 'keyword',
        'sort': True,
        'limit': 2500,
        'params': {
            'info': 'discover', 'tmdb_type': 'movie',
            'with_keywords': '{tmdb_id}', 'with_id': 'True'}
    },
    'studio': {
        'type': 'production_company',
        'sort': True,
        'limit': 2500,
        'params': {
            'info': 'discover', 'tmdb_type': 'movie',
            'with_companies': '{tmdb_id}', 'with_id': 'True'}
    }
}

RANDOMISED_LISTS_ROUTE = {
    'lambda': lambda func, **kwargs: func(**kwargs),
    'getattr': 'list_randomised'}
RANDOMISED_LISTS = {
    'random_genres': {
        'params': {'info': 'genres'},
        'route': RANDOMISED_LISTS_ROUTE},
    'random_keyword': {
        'params': {'info': 'all_items', 'tmdb_type': 'keyword'},
        'route': RANDOMISED_LISTS_ROUTE},
    'random_trendinglists': {
        'params': {'info': 'trakt_trendinglists'},
        'route': RANDOMISED_LISTS_ROUTE},
    'random_popularlists': {
        'params': {'info': 'trakt_popularlists'},
        'route': RANDOMISED_LISTS_ROUTE},
    'random_likedlists': {
        'params': {'info': 'trakt_likedlists'},
        'route': RANDOMISED_LISTS_ROUTE},
    'random_mylists': {
        'params': {'info': 'trakt_mylists'},
        'route': RANDOMISED_LISTS_ROUTE}}

RANDOMISED_TRAKT_ROUTE = {
    'lambda': lambda func, **kwargs: func(**kwargs),
    'getattr': 'list_randomised_trakt'}
RANDOMISED_TRAKT = {
    'random_trending': {
        'info': 'trakt_trending',
        'route': RANDOMISED_TRAKT_ROUTE},
    'random_popular': {
        'info': 'trakt_popular',
        'route': RANDOMISED_TRAKT_ROUTE},
    'random_mostplayed': {
        'info': 'trakt_mostplayed',
        'route': RANDOMISED_TRAKT_ROUTE},
    'random_anticipated': {
        'info': 'trakt_anticipated',
        'route': RANDOMISED_TRAKT_ROUTE}}

TMDB_BASIC_LISTS_ROUTE = {
    'lambda': lambda func, **kwargs: func(**kwargs),
    'getattr': 'list_tmdb'}
TMDB_BASIC_LISTS = {
    'popular': {
        'path': '{tmdb_type}/popular',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'top_rated': {
        'path': '{tmdb_type}/top_rated',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'upcoming': {
        'path': '{tmdb_type}/upcoming',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'trending_day': {
        'path': 'trending/{tmdb_type}/day',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'trending_week': {
        'path': 'trending/{tmdb_type}/week',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'now_playing': {
        'path': '{tmdb_type}/now_playing',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'airing_today': {
        'path': '{tmdb_type}/airing_today',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'on_the_air': {
        'path': '{tmdb_type}/on_the_air',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'recommendations': {
        'path': '{tmdb_type}/{tmdb_id}/recommendations',
        'key': 'results',
        'dbid_sorting': True,
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'similar': {
        'path': '{tmdb_type}/{tmdb_id}/similar',
        'key': 'results',
        'dbid_sorting': True,
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'stars_in_movies': {
        'path': 'person/{tmdb_id}/movie_credits',
        'key': 'cast',
        'tmdb_type': 'movie',
        'dbid_sorting': True,
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'stars_in_tvshows': {
        'path': 'person/{tmdb_id}/tv_credits',
        'key': 'cast',
        'dbid_sorting': True,
        'tmdb_type': 'tv',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'crew_in_movies': {
        'path': 'person/{tmdb_id}/movie_credits',
        'key': 'crew',
        'dbid_sorting': True,
        'tmdb_type': 'movie',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'crew_in_tvshows': {
        'path': 'person/{tmdb_id}/tv_credits',
        'key': 'crew',
        'dbid_sorting': True,
        'tmdb_type': 'tv',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'images': {
        'path': 'person/{tmdb_id}/images',
        'key': 'profiles',
        'tmdb_type': 'image',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'posters': {
        'path': '{tmdb_type}/{tmdb_id}/images',
        'key': 'posters',
        'tmdb_type': 'image',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'fanart': {
        'path': '{tmdb_type}/{tmdb_id}/images',
        'key': 'backdrops',
        'tmdb_type': 'image',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'reviews': {
        'path': '{tmdb_type}/{tmdb_id}/reviews',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'revenue_movies': {
        'path': 'discover/{tmdb_type}?sort_by=revenue.desc',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'most_voted': {
        'path': 'discover/{tmdb_type}?sort_by=vote_count.desc',
        'key': 'results',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'collection': {
        'path': 'collection/{tmdb_id}',
        'key': 'parts',
        'tmdb_type': 'movie',
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'movie_keywords': {
        'path': 'movie/{tmdb_id}/keywords',
        'key': 'keywords',
        'tmdb_type': 'keyword',
        'params': {
            'info': 'discover',
            'tmdb_type': 'movie',
            'with_keywords': '{tmdb_id}',
            'with_id': 'True'
        },
        'route': TMDB_BASIC_LISTS_ROUTE
    },
    'genres': {
        'path': 'genre/{tmdb_type}/list',
        'key': 'genres',
        'tmdb_type': 'genre',
        'params': {
            'info': 'discover',
            'tmdb_type': '{base_tmdb_type}',
            'with_genres': '{tmdb_id}',
            'with_id': 'True'
        },
        'route': TMDB_BASIC_LISTS_ROUTE
    }
}


TRAKT_BASIC_LISTS_ROUTE = {
    'lambda': lambda func, **kwargs: func(**kwargs),
    'getattr': 'list_trakt'}
TRAKT_BASIC_LISTS = {
    'trakt_trending': {
        'path': '{trakt_type}s/trending',
        'route': TRAKT_BASIC_LISTS_ROUTE
    },
    'trakt_popular': {
        'path': '{trakt_type}s/popular',
        'route': TRAKT_BASIC_LISTS_ROUTE
    },
    'trakt_mostplayed': {
        'path': '{trakt_type}s/played/weekly',
        'route': TRAKT_BASIC_LISTS_ROUTE
    },
    'trakt_anticipated': {
        'path': '{trakt_type}s/anticipated',
        'route': TRAKT_BASIC_LISTS_ROUTE
    },
    'trakt_boxoffice': {
        'path': '{trakt_type}s/boxoffice',
        'route': TRAKT_BASIC_LISTS_ROUTE
    },
    'trakt_recommendations': {
        'path': 'recommendations/{trakt_type}s?ignore_collected=true',
        'authorize': True,
        'route': TRAKT_BASIC_LISTS_ROUTE
    },
    'trakt_myairing': {
        'path': 'calendars/my/{trakt_type}s',
        'authorize': True,
        'route': TRAKT_BASIC_LISTS_ROUTE
    }
}


TRAKT_SYNC_LISTS_ROUTE = {
    'lambda': lambda func, **kwargs: func(**kwargs),
    'getattr': 'list_sync'}
TRAKT_SYNC_LISTS = {
    'trakt_collection': {
        'sync_type': 'collection',
        'sort_by': 'title',
        'sort_how': 'asc',
        'route': TRAKT_SYNC_LISTS_ROUTE
    },
    'trakt_watchlist': {
        'sync_type': 'watchlist',
        'use_show_activity': True,
        'sort_by': 'unsorted',
        'route': TRAKT_SYNC_LISTS_ROUTE
    },
    'trakt_history': {
        'sync_type': 'watched',
        'sort_by': 'watched',
        'sort_how': 'desc',
        'route': TRAKT_SYNC_LISTS_ROUTE
    },
    'trakt_mostwatched': {
        'sync_type': 'watched',
        'sort_by': 'plays',
        'sort_how': 'desc',
        'route': TRAKT_SYNC_LISTS_ROUTE
    },
    'trakt_inprogress': {
        'sync_type': 'playback',
        'sort_by': 'paused',
        'sort_how': 'desc',
        'route': TRAKT_SYNC_LISTS_ROUTE
    }
}


TRAKT_LIST_OF_LISTS_ROUTE = {
    'lambda': lambda func, **kwargs: func(**kwargs),
    'getattr': 'list_lists'}
TRAKT_LIST_OF_LISTS = {
    'trakt_trendinglists': {
        'path': 'lists/trending',
        'route': TRAKT_LIST_OF_LISTS_ROUTE},
    'trakt_popularlists': {
        'path': 'lists/popular',
        'route': TRAKT_LIST_OF_LISTS_ROUTE},
    'trakt_likedlists': {
        'path': 'users/likes/lists',
        'authorize': True,
        'route': TRAKT_LIST_OF_LISTS_ROUTE},
    'trakt_mylists': {
        'path': 'users/me/lists',
        'authorize': True,
        'route': TRAKT_LIST_OF_LISTS_ROUTE}
}

CONTEXT_MENU_ITEMS = {
    'tmdbhelper.context.artwork': {
        'movie': {'ftv_type': 'movies', 'ftv_id': '{ftv_id}'},
        'tvshow': {'ftv_type': 'tv', 'ftv_id': '{ftv_id}'}
    },
    'tmdbhelper.context.refresh': {
        'episode': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}', 'episode': '{episode}'},
        'season': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}'},
        'other': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    },
    'tmdbhelper.context.related': {
        'episode': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}', 'episode': '{episode}'},
        'other': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    },
    'tmdbhelper.context.addlibrary': {
        'movie': {'info': '{tmdb_type}', 'tmdb_id': '{tmdb_id}', 'force': True},
        'tvshow': {'info': '{tmdb_type}', 'tmdb_id': '{tmdb_id}', 'force': True},
        'season': {'info': '{tmdb_type}', 'tmdb_id': '{tmdb_id}', 'force': True},
        'episode': {'info': '{tmdb_type}', 'tmdb_id': '{tmdb_id}', 'force': True}
    },
    'tmdbhelper.context.trakt': {
        'episode': {'trakt_type': '{trakt_type}', 'unique_id': '{tmdb_id}', 'id_type': 'tmdb', 'season': '{season}', 'episode': '{episode}'},
        'other': {'trakt_type': '{trakt_type}', 'unique_id': '{tmdb_id}', 'id_type': 'tmdb'}
    }
}

ROUTE_NO_ID = {
    'pass': {'route': {
        'lambda': lambda func, **kwargs: None,
        'getattr': '_noop'}},
    'dir_search': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_searchdir_router'}},
    'dir_multisearch': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_multisearchdir_router'}},
    'search': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_search'}},
    'user_discover': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_userdiscover'}},
    'dir_discover': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_discoverdir_router'}},
    'discover': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_discover'}},
    'all_items': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_all_items'}},
    'trakt_userlist': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_userlist'}},
    'trakt_becauseyouwatched': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_becauseyouwatched'}},
    'trakt_becausemostwatched': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_becauseyouwatched'}},
    'trakt_inprogress': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_inprogress'}},
    'trakt_nextepisodes': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_nextepisodes'}},
    'trakt_calendar': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_trakt_calendar'}},
    'library_nextaired': {'route': {
        'lambda': lambda func, **kwargs: func(library=True, **kwargs),
        'getattr': 'list_trakt_calendar'}},
    'trakt_sortby': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_trakt_sortby'}},
    'trakt_searchlists': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_lists_search'}},
}


ROUTE_TMDB_ID = {
    'details': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_details'}},
    'seasons': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_seasons'}},
    'flatseasons': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_flatseasons'}},
    'episodes': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_episodes'}},
    'episode_groups': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_episode_groups'}},
    'episode_group_seasons': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_episode_group_seasons'}},
    'episode_group_episodes': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_episode_group_episodes'}},
    'cast': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_cast'}},
    'crew': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_crew'}},
    'trakt_upnext': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_upnext'}},
    'videos': {'route': {
        'lambda': lambda func, **kwargs: func(**kwargs),
        'getattr': 'list_videos'}},
}
