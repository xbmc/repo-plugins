BASEDIR = ['search', 'popular', 'top_rated', 'upcoming', 'airing_today', 'now_playing', 'on_the_air']

TYPE_CONVERSION = {'movie':
                   {'plural': 'Movies',
                    'container': 'movies',
                    'dbtype': 'movie'},
                   'tv':
                   {'plural': 'TV Shows',
                    'container': 'tvshows',
                    'dbtype': 'tvshow'},
                   'person':
                   {'plural': 'People',
                    'container': 'actors',
                    'dbtype': ''},
                   'review':
                   {'plural': 'Reviews',
                    'container': '',
                    'dbtype': ''},
                   'image':
                   {'plural': 'Images',
                    'container': 'images',
                    'dbtype': 'image'},
                   'season':
                   {'plural': 'Seasons',
                    'container': 'seasons',
                    'dbtype': 'season'},
                   'episode':
                   {'plural': 'Episodes',
                    'container': 'episodes',
                    'dbtype': 'episode'}}

LANGUAGES = ['ar-AE', 'ar-SA', 'be-BY', 'bg-BG', 'bn-BD', 'ca-ES', 'ch-GU', 'cs-CZ',
             'da-DK', 'de-AT', 'de-CH', 'de-DE', 'el-GR', 'en-AU', 'en-CA', 'en-GB',
             'en-IE', 'en-NZ', 'en-US', 'eo-EO', 'es-ES', 'es-MX', 'et-EE', 'eu-ES',
             'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR', 'gl-ES', 'he-IL', 'hi-IN', 'hu-HU',
             'id-ID', 'it-IT', 'ja-JP', 'ka-GE', 'kk-KZ', 'kn-IN', 'ko-KR', 'lt-LT',
             'lv-LV', 'ml-IN', 'ms-MY', 'ms-SG', 'nb-NO', 'nl-NL', 'no-NO', 'pl-PL',
             'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK', 'sl-SI', 'sr-RS',
             'sv-SE', 'ta-IN', 'te-IN', 'th-TH', 'tl-PH', 'tr-TR', 'uk-UA', 'vi-VN',
             'zh-CN', 'zh-HK', 'zh-TW', 'zu-ZA']

TMDB_LISTS = {'discover':
              {'name': 'Discover {0}',
               'path': 'discover/{type}',
               'types': ['movie', 'tv']},
              'search':
              {'name': 'Search {0}',
               'path': 'search/{type}',
               'types': ['movie', 'tv', 'person']},
              'popular':
              {'name': 'Popular {0}',
               'path': '{type}/popular',
               'types': ['movie', 'tv', 'person']},
              'top_rated':
              {'name': 'Top Rated {0}',
               'path': '{type}/top_rated',
               'types': ['movie', 'tv']},
              'upcoming':
              {'name': 'Upcoming {0}',
               'path': '{type}/upcoming',
               'types': ['movie']},
              'airing_today':
              {'name': '{0} Airing Today',
               'path': '{type}/airing_today',
               'types': ['tv']},
              'now_playing':
              {'name': '{0} In Theatres',
               'path': '{type}/now_playing',
               'types': ['movie']},
              'on_the_air':
              {'name': 'Currently Airing {0}',
               'path': '{type}/on_the_air',
               'types': ['tv']},
              'cast':
              {'name': 'Cast',
               'types': ['movie', 'tv']},
              'recommendations':
              {'name': 'Recommended',
               'path': '{type}/{tmdb_id}/recommendations',
               'types': ['movie', 'tv']},
              'similar':
              {'name': 'Similar',
               'path': '{type}/{tmdb_id}/similar',
               'types': ['movie', 'tv']},
              'crew':
              {'name': 'Crew',
               'types': ['movie', 'tv']},
              'movie_keywords':
              {'name': 'Keywords',
               'path': '{type}/{tmdb_id}/keywords',
               'key': 'keywords',
               'itemtype': 'keyword',
               'url_info': 'keyword_movies',
               'types': ['movie']},
              'reviews':
              {'name': 'Reviews',
               'path': '{type}/{tmdb_id}/reviews',
               'itemtype': 'review',
               'nexttype': 'review',
               'url_info': 'textviewer',
               'types': ['movie', 'tv']},
              'posters':
              {'name': 'Posters',
               'path': '{type}/{tmdb_id}/images',
               'key': 'posters',
               'itemtype': 'image',
               'nexttype': 'image',
               'url_info': 'imageviewer',
               'types': ['movie', 'tv']},
              'fanart':
              {'name': 'Fanart',
               'path': '{type}/{tmdb_id}/images',
               'key': 'backdrops',
               'itemtype': 'image',
               'nexttype': 'image',
               'url_info': 'imageviewer',
               'types': ['movie', 'tv']},
              'seasons':
              {'name': 'Seasons',
               'path': '{type}/{tmdb_id}',
               'key': 'seasons',
               'itemtype': 'season',
               'nexttype': 'season',
               'url_info': 'episodes',
               'types': ['tv']},
              'episode_cast':
              {'name': 'Cast',
               'path': 'tv/{tmdb_id}/season/{season}/episode/{episode}/credits',
               'key': 'cast',
               'itemtype': 'person',
               'nexttype': 'person',
               'types': ['episode']},
              'episode_thumbs':
              {'name': 'Thumbs',
               'path': 'tv/{tmdb_id}/season/{season}/episode/{episode}/images',
               'key': 'stills',
               'itemtype': 'image',
               'nexttype': 'image',
               'url_info': 'imageviewer',
               'types': ['episode']},
              'stars_in_movies':
              {'name': 'Cast in Movies',
               'path': 'person/{tmdb_id}/movie_credits',
               'key': 'cast',
               'itemtype': 'movie',
               'nexttype': 'movie',
               'types': ['person']},
              'stars_in_tvshows':
              {'name': 'Cast in Tv Shows',
               'path': 'person/{tmdb_id}/tv_credits',
               'key': 'cast',
               'itemtype': 'tv',
               'nexttype': 'tv',
               'types': ['person']},
              'crew_in_movies':
              {'name': 'Crew in Movies',
               'path': 'person/{tmdb_id}/movie_credits',
               'key': 'crew',
               'itemtype': 'movie',
               'nexttype': 'movie',
               'types': ['person']},
              'crew_in_tvshows':
              {'name': 'Crew in Tv Shows',
               'path': 'person/{tmdb_id}/tv_credits',
               'key': 'crew',
               'itemtype': 'tv',
               'nexttype': 'tv',
               'types': ['person']},
              'images':
              {'name': 'Images',
               'path': 'person/{tmdb_id}/images',
               'key': 'profiles',
               'itemtype': 'image',
               'nexttype': 'image',
               'url_info': 'imageviewer',
               'types': ['person']},
              'collection':
              {'name': 'In Collection',
               'path': 'collection/{tmdb_id}',
               'tmdb_check_id': 'collection',
               'key': 'parts',
               'types': ['movie']},
              'keyword_movies':
              {'name': 'Keywords',
               'path': 'keyword/{tmdb_id}/movies',
               'key': 'results',
               'types': ['keyword']},
              'episodes':
              {'name': 'Episodes',
               'path': 'tv/{tmdb_id}/season/{season}',
               'key': 'episodes',
               'itemtype': 'episode',
               'nexttype': 'episode',
               'types': ['season']}}

TMDB_CATEGORIES = ['cast', 'recommendations', 'similar', 'crew', 'posters', 'fanart', 'movie_keywords', 'reviews',
                   'stars_in_movies', 'stars_in_tvshows', 'crew_in_movies', 'crew_in_tvshows', 'images',
                   'seasons', 'episode_cast', 'episode_thumbs']

APPEND_TO_RESPONSE = 'credits,images,release_dates,content_ratings,external_ids'
