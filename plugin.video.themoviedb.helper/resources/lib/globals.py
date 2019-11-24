BASEDIR_MAIN = ['dir_tmdb', 'dir_trakt']

BASEDIR_TMDB = ['search', 'popular', 'top_rated', 'upcoming', 'airing_today', 'now_playing', 'on_the_air', 'genres']

BASEDIR_TRAKT = [
    'trakt_watchlist', 'trakt_history', 'trakt_mostwatched', 'trakt_inprogress', 'trakt_recommendations', 'trakt_myairing',
    'trakt_trending', 'trakt_popular', 'trakt_mostplayed', 'trakt_anticipated', 'trakt_boxoffice',
    'trakt_trendinglists', 'trakt_popularlists', 'trakt_likedlists', 'trakt_mylists']

TYPE_CONVERSION = {
    'movie': {
        'plural': 'Movies',
        'container': 'movies',
        'trakt': 'movie',
        'dbtype': 'movie'},
    'tv': {
        'plural': 'TV Shows',
        'container': 'tvshows',
        'trakt': 'show',
        'dbtype': 'tvshow'},
    'person': {
        'plural': 'People',
        'container': 'actors',
        'trakt': '',
        'dbtype': ''},
    'review': {
        'plural': 'Reviews',
        'container': '',
        'trakt': '',
        'dbtype': ''},
    'image': {
        'plural': 'Images',
        'container': 'images',
        'trakt': '',
        'dbtype': 'image'},
    'genre': {
        'plural': 'Genres',
        'container': 'genres',
        'trakt': '',
        'dbtype': 'genre'},
    'season': {
        'plural': 'Seasons',
        'container': 'seasons',
        'trakt': 'season',
        'dbtype': 'season'},
    'episode': {
        'plural': 'Episodes',
        'container': 'episodes',
        'trakt': 'episode',
        'dbtype': 'episode'}}

LANGUAGES = [
    'ar-AE', 'ar-SA', 'be-BY', 'bg-BG', 'bn-BD', 'ca-ES', 'ch-GU', 'cs-CZ', 'da-DK', 'de-AT', 'de-CH',
    'de-DE', 'el-GR', 'en-AU', 'en-CA', 'en-GB', 'en-IE', 'en-NZ', 'en-US', 'eo-EO', 'es-ES', 'es-MX',
    'et-EE', 'eu-ES', 'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR', 'gl-ES', 'he-IL', 'hi-IN', 'hu-HU', 'id-ID',
    'it-IT', 'ja-JP', 'ka-GE', 'kk-KZ', 'kn-IN', 'ko-KR', 'lt-LT', 'lv-LV', 'ml-IN', 'ms-MY', 'ms-SG',
    'nb-NO', 'nl-NL', 'no-NO', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK', 'sl-SI',
    'sr-RS', 'sv-SE', 'ta-IN', 'te-IN', 'th-TH', 'tl-PH', 'tr-TR', 'uk-UA', 'vi-VN', 'zh-CN', 'zh-HK',
    'zh-TW', 'zu-ZA']

BASEDIR_LISTS = {
    'dir_tmdb': {
        'name': 'TheMovieDb',
        'path': BASEDIR_TMDB,
        'types': [None]},
    'dir_trakt': {
        'name': 'Trakt',
        'path': BASEDIR_TRAKT,
        'icon': '{0}/resources/trakt.png',
        'types': [None]}}

TMDB_LISTS = {
    'discover': {
        'name': 'Discover {0}',
        'path': 'discover/{type}',
        'types': ['movie', 'tv']},
    'search': {
        'name': 'Search {0}',
        'path': 'search/{type}',
        'types': ['movie', 'tv', 'person']},
    'popular': {
        'name': 'Popular {0}',
        'path': '{type}/popular',
        'types': ['movie', 'tv', 'person']},
    'top_rated': {
        'name': 'Top Rated {0}',
        'path': '{type}/top_rated',
        'types': ['movie', 'tv']},
    'upcoming': {
        'name': 'Upcoming {0}',
        'path': '{type}/upcoming',
        'types': ['movie']},
    'airing_today': {
        'name': '{0} Airing Today',
        'path': '{type}/airing_today',
        'types': ['tv']},
    'now_playing': {
        'name': '{0} In Theatres',
        'path': '{type}/now_playing',
        'types': ['movie']},
    'on_the_air': {
        'name': 'Currently Airing {0}',
        'path': '{type}/on_the_air',
        'types': ['tv']},
    'genre': {
        'name': '{0} Genre',
        'path': 'discover/{type}',
        'url_ext': 'with_genres={tmdb_id}',
        'types': ['movie', 'tv']},
    'genres': {
        'name': '{0} Genres',
        'path': 'genre/{type}/list',
        'key': 'genres',
        'url_info': 'genre',
        'itemtype': 'genre',
        'types': ['movie', 'tv']},
    'cast': {
        'name': 'Cast',
        'types': ['movie', 'tv']},
    'recommendations': {
        'name': 'Recommended',
        'path': '{type}/{tmdb_id}/recommendations',
        'types': ['movie', 'tv']},
    'similar': {
        'name': 'Similar',
        'path': '{type}/{tmdb_id}/similar',
        'types': ['movie', 'tv']},
    'crew': {
        'name': 'Crew',
        'types': ['movie', 'tv']},
    'movie_keywords': {
        'name': 'Keywords',
        'path': '{type}/{tmdb_id}/keywords',
        'key': 'keywords',
        'itemtype': 'keyword',
        'url_info': 'keyword_movies',
        'types': ['movie']},
    'reviews': {
        'name': 'Reviews',
        'path': '{type}/{tmdb_id}/reviews',
        'itemtype': 'review',
        'nexttype': 'review',
        'url_info': 'textviewer',
        'types': ['movie', 'tv']},
    'posters': {
        'name': 'Posters',
        'path': '{type}/{tmdb_id}/images',
        'key': 'posters',
        'itemtype': 'image',
        'nexttype': 'image',
        'url_info': 'imageviewer',
        'types': ['movie', 'tv']},
    'fanart': {
        'name': 'Fanart',
        'path': '{type}/{tmdb_id}/images',
        'key': 'backdrops',
        'itemtype': 'image',
        'nexttype': 'image',
        'url_info': 'imageviewer',
        'types': ['movie', 'tv']},
    'seasons': {
        'name': 'Seasons',
        'path': '{type}/{tmdb_id}',
        'key': 'seasons',
        'itemtype': 'season',
        'nexttype': 'season',
        'url_info': 'episodes',
        'types': ['tv']},
    'episode_cast': {
        'name': 'Cast',
        'path': 'tv/{tmdb_id}/season/{season}/episode/{episode}/credits',
        'key': 'cast',
        'itemtype': 'person',
        'nexttype': 'person',
        'types': ['episode']},
    'episode_thumbs': {
        'name': 'Thumbs',
        'path': 'tv/{tmdb_id}/season/{season}/episode/{episode}/images',
        'key': 'stills',
        'itemtype': 'image',
        'nexttype': 'image',
        'url_info': 'imageviewer',
        'types': ['episode']},
    'stars_in_movies': {
        'name': 'Cast in Movies',
        'path': 'person/{tmdb_id}/movie_credits',
        'key': 'cast',
        'itemtype': 'movie',
        'nexttype': 'movie',
        'types': ['person']},
    'stars_in_tvshows': {
        'name': 'Cast in Tv Shows',
        'path': 'person/{tmdb_id}/tv_credits',
        'key': 'cast',
        'itemtype': 'tv',
        'nexttype': 'tv',
        'types': ['person']},
    'crew_in_movies': {
        'name': 'Crew in Movies',
        'path': 'person/{tmdb_id}/movie_credits',
        'key': 'crew',
        'itemtype': 'movie',
        'nexttype': 'movie',
        'types': ['person']},
    'crew_in_tvshows': {
        'name': 'Crew in Tv Shows',
        'path': 'person/{tmdb_id}/tv_credits',
        'key': 'crew',
        'itemtype': 'tv',
        'nexttype': 'tv',
        'types': ['person']},
    'images': {
        'name': 'Images',
        'path': 'person/{tmdb_id}/images',
        'key': 'profiles',
        'itemtype': 'image',
        'nexttype': 'image',
        'url_info': 'imageviewer',
        'types': ['person']},
    'collection': {
        'name': 'In Collection',
        'path': 'collection/{tmdb_id}',
        'tmdb_check_id': 'collection',
        'key': 'parts',
        'types': ['movie']},
    'keyword_movies': {
        'name': 'Keywords',
        'path': 'keyword/{tmdb_id}/movies',
        'key': 'results',
        'types': ['keyword']},
    'episodes': {
        'name': 'Episodes',
        'path': 'tv/{tmdb_id}/season/{season}',
        'key': 'episodes',
        'itemtype': 'episode',
        'nexttype': 'episode',
        'types': ['season']}}

DETAILED_CATEGORIES = [
    'cast', 'recommendations', 'similar', 'crew', 'posters', 'fanart', 'movie_keywords', 'reviews',
    'stars_in_movies', 'stars_in_tvshows', 'crew_in_movies', 'crew_in_tvshows', 'images',
    'seasons', 'trakt_upnext', 'episode_cast', 'episode_thumbs', 'trakt_inlists']

APPEND_TO_RESPONSE = 'credits,images,release_dates,content_ratings,external_ids'

TRAKT_LISTLISTS = ['trakt_mylists', 'trakt_trendinglists', 'trakt_popularlists', 'trakt_likedlists', 'trakt_inlists']

TRAKT_HISTORYLISTS = ['trakt_inprogress', 'trakt_history', 'trakt_mostwatched']

TRAKT_LISTS = {
    'trakt_watchlist': {
        'name': 'Watchlist {0}',
        'path': 'users/{user_slug}/watchlist/{type}',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_history': {
        'name': 'Your Recently Watched {0}',
        'path': 'users/{user_slug}/history/{type}',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_inprogress': {
        'name': 'Your In-Progress {0}',
        'icon': '{0}/resources/trakt.png',
        'types': ['tv']},
    'trakt_mostwatched': {
        'name': 'Your Most Watched {0}',
        'path': 'users/{user_slug}/watched/{type}',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_recommendations': {
        'name': '{0} Recommended For You',
        'path': 'recommendations/{type}?ignore_collected=true',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_trending': {
        'name': 'Trending {0}',
        'path': '{type}/trending',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_popular': {
        'name': 'Popular {0}',
        'path': '{type}/popular',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_mostplayed': {
        'name': 'Most Played {0}',
        'path': '{type}/played/weekly',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_anticipated': {
        'name': 'Anticipated {0}',
        'path': '{type}/anticipated',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_boxoffice': {
        'name': 'Top 10 Box Office {0}',
        'path': '{type}/boxoffice',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie']},
    'trakt_userlist': {
        'name': 'User List',
        'path': 'users/{user_slug}/lists/{list_slug}/items',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie', 'tv']},
    'trakt_trendinglists': {
        'name': 'Trending Lists',
        'path': 'lists/trending',
        'icon': '{0}/resources/trakt.png',
        'types': ['both']},
    'trakt_popularlists': {
        'name': 'Popular Lists',
        'path': 'lists/popular',
        'icon': '{0}/resources/trakt.png',
        'types': ['both']},
    'trakt_likedlists': {
        'name': 'Liked Lists',
        'path': 'users/likes/lists',
        'icon': '{0}/resources/trakt.png',
        'types': ['both']},
    'trakt_mylists': {
        'name': 'Your Lists',
        'path': 'users/{user_slug}/lists',
        'icon': '{0}/resources/trakt.png',
        'types': ['both']},
    'trakt_inlists': {
        'name': 'Found in Lists',
        'path': 'movies/{imdb_id}/lists',
        'url_key': 'imdb_id',
        'icon': '{0}/resources/trakt.png',
        'types': ['movie']},
    'trakt_myairing': {
        'name': 'Your {0} Airing This Week',
        'path': 'calendars/my/{type}',
        'icon': '{0}/resources/trakt.png',
        'types': ['tv']},
    'trakt_airing': {
        'name': 'Currently Airing {0}',
        'path': 'calendars/all/{type}',
        'icon': '{0}/resources/trakt.png',
        'types': ['tv']},
    'trakt_upnext': {
        'name': 'Up Next',
        'path': 'shows/{imdb_id}/progress/watched',
        'url_key': 'imdb_id',
        'icon': '{0}/resources/trakt.png',
        'types': ['tv']},
    'trakt_premiering': {
        'name': 'Premiering {0}',
        'path': 'calendars/all/{type}/premieres',
        'icon': '{0}/resources/trakt.png',
        'types': ['tv']}}
