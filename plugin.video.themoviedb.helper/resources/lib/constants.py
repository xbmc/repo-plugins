#!/usr/bin/env python
# -*- coding: utf-8 -*-

VALID_FILECHARS = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

LANGUAGES = [
    'ar-AE', 'ar-SA', 'be-BY', 'bg-BG', 'bn-BD', 'ca-ES', 'ch-GU', 'cs-CZ', 'da-DK', 'de-AT', 'de-CH',
    'de-DE', 'el-GR', 'en-AU', 'en-CA', 'en-GB', 'en-IE', 'en-NZ', 'en-US', 'eo-EO', 'es-ES', 'es-MX',
    'et-EE', 'eu-ES', 'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR', 'gl-ES', 'he-IL', 'hi-IN', 'hu-HU', 'id-ID',
    'it-IT', 'ja-JP', 'ka-GE', 'kk-KZ', 'kn-IN', 'ko-KR', 'lt-LT', 'lv-LV', 'ml-IN', 'ms-MY', 'ms-SG',
    'nb-NO', 'nl-NL', 'no-NO', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK', 'sl-SI',
    'sr-RS', 'sv-SE', 'ta-IN', 'te-IN', 'th-TH', 'tl-PH', 'tr-TR', 'uk-UA', 'vi-VN', 'zh-CN', 'zh-HK',
    'zh-TW', 'zu-ZA']

NO_LABEL_FORMATTING = ['details', 'seasons', 'trakt_calendar', 'trakt_myairing', 'trakt_anticipated', 'library_nextaired']

EPISODE_WIDGETS = ['trakt_calendar', 'trakt_nextepisodes', 'library_nextaired', 'trakt_upnext']

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
        'dbtype': 'video'},
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
        'dbtype': 'episode'},
    'video': {
        'plural': 'Videos',
        'container': 'videos',
        'trakt': '',
        'dbtype': 'video'}}

BASEDIR_MAIN = [
    {
        'info': 'dir_movie',
        'name': 'Movies',
        'icon': '{0}/resources/icons/tmdb/movies.png'},
    {
        'info': 'dir_tv',
        'name': 'TV Shows',
        'icon': '{0}/resources/icons/tmdb/tv.png'},
    {
        'info': 'dir_person',
        'name': 'People',
        'icon': '{0}/resources/icons/tmdb/cast.png'},
    {
        'info': 'dir_random',
        'name': 'Randomised',
        'icon': '{0}/resources/poster.png'},
    {
        'info': 'dir_discover',
        'name': 'Discover',
        'icon': '{0}/resources/poster.png'},
    {
        'info': 'dir_tmdb',
        'name': 'TheMovieDb',
        'icon': '{0}/resources/poster.png'},
    {
        'info': 'dir_trakt',
        'name': 'Trakt',
        'icon': '{0}/resources/trakt.png'}]

BASEDIR_TMDB = [
    {
        'info': 'dir_search',
        'name': 'Search{1}{0}',
        'types': ['movie', 'tv', 'person'],
        'icon': '{0}/resources/icons/tmdb/search.png'},
    {
        'info': 'popular',
        'name': 'Popular{1}{0}',
        'types': ['movie', 'tv', 'person'],
        'icon': '{0}/resources/icons/tmdb/popular.png'},
    {
        'info': 'top_rated',
        'name': 'Top Rated{1}{0}',
        'types': ['movie', 'tv'],
        'icon': '{0}/resources/icons/tmdb/toprated.png'},
    {
        'info': 'upcoming',
        'name': 'Upcoming{1}{0}',
        'types': ['movie'],
        'icon': '{0}/resources/icons/tmdb/upcoming.png'},
    {
        'info': 'trending_day',
        'name': '{0}{1}Trending Today',
        'types': ['movie', 'tv', 'person'],
        'icon': '{0}/resources/icons/tmdb/upcoming.png'},
    {
        'info': 'trending_week',
        'name': '{0}{1}Trending This Week',
        'types': ['movie', 'tv', 'person'],
        'icon': '{0}/resources/icons/tmdb/upcoming.png'},
    {
        'info': 'now_playing',
        'name': 'In Theatres',
        'types': ['movie'],
        'icon': '{0}/resources/icons/tmdb/intheatres.png'},
    {
        'info': 'airing_today',
        'name': 'Airing Today',
        'types': ['tv'],
        'icon': '{0}/resources/icons/tmdb/airing.png'},
    {
        'info': 'on_the_air',
        'name': 'Currently Airing',
        'types': ['tv'],
        'icon': '{0}/resources/icons/tmdb/airing.png'},
    {
        'info': 'library_nextaired',
        'name': 'Next Aired Library',
        'types': ['tv'],
        'icon': '{0}/resources/icons/tmdb/airing.png'},
    {
        'info': 'genres',
        'name': '{0}{1}Genres',
        'types': ['movie', 'tv'],
        'icon': '{0}/resources/icons/tmdb/genre.png'},
    {
        'info': 'revenue_movies',
        'name': 'Highest Revenue{1}{0}',
        'types': ['movie'],
        'icon': '{0}/resources/poster.png'},
    {
        'info': 'most_voted',
        'name': 'Most Voted{1}{0}',
        'types': ['movie', 'tv'],
        'icon': '{0}/resources/poster.png'}]

BASEDIR_TRAKT = [
    {
        'info': 'trakt_collection',
        'name': '{0}{1}Collection',
        'icon': '{0}/resources/icons/trakt/watchlist.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_watchlist',
        'name': '{0}{1}Watchlist',
        'icon': '{0}/resources/icons/trakt/watchlist.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_history',
        'name': 'Your Recently Watched{1}{0}',
        'icon': '{0}/resources/icons/trakt/recentlywatched.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_mostwatched',
        'name': 'Your Most Watched{1}{0}',
        'icon': '{0}/resources/icons/trakt/mostwatched.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_inprogress',
        'name': 'Your In-Progress{1}{0}',
        'icon': '{0}/resources/icons/trakt/inprogress.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_nextepisodes',
        'name': 'Your Next Episodes',
        'icon': '{0}/resources/icons/trakt/inprogress.png',
        'types': ['tv']},
    {
        'info': 'trakt_recommendations',
        'name': '{0}{1}Recommended For You',
        'icon': '{0}/resources/icons/trakt/recommended.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_becauseyouwatched',
        'name': 'Based on Recently Watched{1}{0}',
        'icon': '{0}/resources/icons/trakt/recommended.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_becausemostwatched',
        'name': 'Based on Most Watched{1}{0}',
        'icon': '{0}/resources/icons/trakt/recommended.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_myairing',
        'name': 'Your {0}{1}Airing This Week',
        'icon': '{0}/resources/icons/trakt/airing.png',
        'types': ['tv']},
    {
        'info': 'trakt_calendar',
        'name': 'Your {0}{1}Calendar',
        'icon': '{0}/resources/icons/trakt/calendar.png',
        'types': ['tv']},
    {
        'info': 'trakt_trending',
        'name': 'Trending{1}{0}',
        'icon': '{0}/resources/icons/trakt/trend.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_popular',
        'name': 'Popular{1}{0}',
        'icon': '{0}/resources/icons/trakt/popular.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_mostplayed',
        'name': 'Most Played{1}{0}',
        'icon': '{0}/resources/icons/trakt/mostplayed.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_anticipated',
        'name': 'Anticipated{1}{0}',
        'icon': '{0}/resources/icons/trakt/anticipated.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_boxoffice',
        'name': 'Top 10 Box Office{1}{0}',
        'icon': '{0}/resources/icons/trakt/boxoffice.png',
        'types': ['movie']},
    {
        'info': 'trakt_trendinglists',
        'name': 'Trending Lists',
        'icon': '{0}/resources/icons/trakt/trendinglist.png',
        'types': ['both']},
    {
        'info': 'trakt_popularlists',
        'name': 'Popular Lists',
        'icon': '{0}/resources/icons/trakt/popularlist.png',
        'types': ['both']},
    {
        'info': 'trakt_likedlists',
        'name': 'Liked Lists',
        'icon': '{0}/resources/icons/trakt/likedlist.png',
        'types': ['both']},
    {
        'info': 'trakt_mylists',
        'name': 'Your Lists',
        'icon': '{0}/resources/icons/trakt/mylists.png',
        'types': ['both']}]

BASEDIR_RANDOM = [
    {
        'info': 'random_genres',
        'name': 'Random {0}{1}Genre',
        'types': ['movie', 'tv'],
        'icon': '{0}/resources/icons/tmdb/genre.png'},
    {
        'info': 'trakt_becauseyouwatched',
        'name': 'Based on Recently Watched{1}{0}',
        'icon': '{0}/resources/icons/trakt/recommended.png',
        'types': ['movie', 'tv']},
    {
        'info': 'trakt_becausemostwatched',
        'name': 'Based on Most Watched{1}{0}',
        'icon': '{0}/resources/icons/trakt/recommended.png',
        'types': ['movie', 'tv']},
    {
        'info': 'random_trending',
        'name': 'Random Trending{1}{0}',
        'icon': '{0}/resources/icons/trakt/trend.png',
        'types': ['movie', 'tv']},
    {
        'info': 'random_popular',
        'name': 'Random Popular{1}{0}',
        'icon': '{0}/resources/icons/trakt/popular.png',
        'types': ['movie', 'tv']},
    {
        'info': 'random_mostplayed',
        'name': 'Random Most Played{1}{0}',
        'icon': '{0}/resources/icons/trakt/mostplayed.png',
        'types': ['movie', 'tv']},
    {
        'info': 'random_anticipated',
        'name': 'Random Anticipated{1}{0}',
        'icon': '{0}/resources/icons/trakt/anticipated.png',
        'types': ['movie', 'tv']},
    {
        'info': 'random_trendinglists',
        'name': 'Random Trending List',
        'icon': '{0}/resources/icons/trakt/trendinglist.png',
        'types': ['both']},
    {
        'info': 'random_popularlists',
        'name': 'Random Popular List',
        'icon': '{0}/resources/icons/trakt/popularlist.png',
        'types': ['both']},
    {
        'info': 'random_likedlists',
        'name': 'Random Liked List',
        'icon': '{0}/resources/icons/trakt/likedlist.png',
        'types': ['both']},
    {
        'info': 'random_mylists',
        'name': 'Random Your List',
        'icon': '{0}/resources/icons/trakt/mylists.png',
        'types': ['both']}]

BASEDIR_DISCOVER = [
    {
        'info': 'user_discover',
        'name': 'Discover{1}{0}',
        'types': ['movie', 'tv'],
        'icon': '{0}/resources/icons/tmdb/search.png'}]

BASEDIR_PATH = {
    'dir_movie': {
        'folders': [BASEDIR_TMDB, BASEDIR_TRAKT],
        'types': ['movie', 'both']},
    'dir_tv': {
        'folders': [BASEDIR_TMDB, BASEDIR_TRAKT],
        'types': ['tv', 'both']},
    'dir_person': {
        'folders': [BASEDIR_TMDB, BASEDIR_TRAKT],
        'types': ['person']},
    'dir_tmdb': {
        'folders': [BASEDIR_TMDB],
        'types': ['movie', 'tv', 'person', 'both']},
    'dir_trakt': {
        'folders': [BASEDIR_TRAKT],
        'types': ['movie', 'tv', 'person', 'both']},
    'dir_random': {
        'folders': [BASEDIR_RANDOM],
        'types': ['movie', 'tv', 'both']},
    'dir_discover': {
        'folders': [BASEDIR_DISCOVER],
        'types': ['movie', 'tv', 'both']}}

DETAILED_CATEGORIES = [
    {
        'info': 'cast',
        'name': 'Cast',
        'icon': '{0}/resources/icons/tmdb/cast.png',
        'types': ['movie', 'tv']},
    {
        'info': 'recommendations',
        'name': 'Recommended',
        'icon': '{0}/resources/icons/tmdb/recommended.png',
        'types': ['movie', 'tv']},
    {
        'info': 'similar',
        'name': 'Similar',
        'icon': '{0}/resources/icons/tmdb/similar.png',
        'types': ['movie', 'tv']},
    {
        'info': 'crew',
        'name': 'Crew',
        'icon': '{0}/resources/icons/tmdb/cast.png',
        'types': ['movie', 'tv']},
    {
        'info': 'posters',
        'name': 'Posters',
        'icon': '{0}/resources/icons/tmdb/images.png',
        'types': ['movie', 'tv']},
    {
        'info': 'fanart',
        'name': 'Fanart',
        'icon': '{0}/resources/icons/tmdb/images.png',
        'types': ['movie', 'tv']},
    {
        'info': 'movie_keywords',
        'name': 'Keywords',
        'icon': '{0}/resources/icons/tmdb/tags.png',
        'types': ['movie']},
    {
        'info': 'reviews',
        'name': 'Reviews',
        'icon': '{0}/resources/icons/tmdb/reviews.png',
        'types': ['movie', 'tv']},
    {
        'info': 'stars_in_movies',
        'name': 'Cast in Movies',
        'icon': '{0}/resources/icons/tmdb/movies.png',
        'types': ['person']},
    {
        'info': 'stars_in_tvshows',
        'name': 'Cast in TV Shows',
        'icon': '{0}/resources/icons/tmdb/tv.png',
        'types': ['person']},
    {
        'info': 'crew_in_movies',
        'name': 'Crew in Movies',
        'icon': '{0}/resources/icons/tmdb/movies.png',
        'types': ['person']},
    {
        'info': 'crew_in_tvshows',
        'name': 'Crew in TV Shows',
        'icon': '{0}/resources/icons/tmdb/tv.png',
        'types': ['person']},
    {
        'info': 'images',
        'name': 'Images',
        'icon': '{0}/resources/icons/tmdb/images.png',
        'types': ['person']},
    {
        'info': 'seasons',
        'name': 'Seasons',
        'icon': '{0}/resources/icons/tmdb/episodes.png',
        'types': ['tv']},
    {
        'info': 'episode_cast',
        'name': 'Cast',
        'icon': '{0}/resources/icons/tmdb/cast.png',
        'types': ['episode']},
    {
        'info': 'episode_thumbs',
        'name': 'Thumbs',
        'icon': '{0}/resources/icons/tmdb/images.png',
        'types': ['episode']},
    {
        'info': 'videos',
        'name': 'Videos',
        'icon': '{0}/resources/icons/tmdb/movies.png',
        'types': ['movie', 'tv', 'episode']},
    {
        'info': 'trakt_inlists',
        'name': 'In Trakt Lists',
        'icon': '{0}/resources/icons/tmdb/trakt.png',
        'url_key': 'imdb_id',
        'types': ['movie', 'tv']}]

RANDOM_LISTS = {
    'random_genres': 'genres',
    'random_trendinglists': 'trakt_trendinglists',
    'random_popularlists': 'trakt_popularlists',
    'random_likedlists': 'trakt_likedlists',
    'random_mylists': 'trakt_mylists'}

RANDOM_TRAKT = {
    'random_trending': 'trakt_trending',
    'random_popular': 'trakt_popular',
    'random_mostplayed': 'trakt_mostplayed',
    'random_anticipated': 'trakt_anticipated'}

TMDB_LISTS = {
    'search': {
        'path': 'search/{type}',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'popular': {
        'path': '{type}/popular',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'top_rated': {
        'path': '{type}/top_rated',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'upcoming': {
        'path': '{type}/upcoming',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'trending_day': {
        'path': 'trending/{type}/day',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'trending_week': {
        'path': 'trending/{type}/week',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'now_playing': {
        'path': '{type}/now_playing',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'airing_today': {
        'path': '{type}/airing_today',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'on_the_air': {
        'path': '{type}/on_the_air',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': '{type}'},
    'genres': {
        'path': 'genre/{type}/list',
        'key': 'genres',
        'url_info': 'genre',
        'url_type': '{type}',
        'item_tmdbtype': 'genre'},
    'discover': {
        'path': 'discover/{type}',
        'key': 'results',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': '{type}'},
    'genre': {
        'path': 'discover/{type}',
        'key': 'results',
        'url_info': 'details',
        'url_ext': 'with_genres={tmdb_id}',
        'dbid_sorting': True,
        'item_tmdbtype': '{type}'},
    'recommendations': {
        'path': '{type}/{tmdb_id}/recommendations',
        'key': 'results',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': '{type}'},
    'similar': {
        'path': '{type}/{tmdb_id}/similar',
        'key': 'results',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': '{type}'},
    'movie_keywords': {
        'path': '{type}/{tmdb_id}/keywords',
        'key': 'keywords',
        'url_info': 'keyword_movies',
        'url_type': 'movie',
        'dbid_sorting': True,
        'item_tmdbtype': 'keyword'},
    'reviews': {
        'path': '{type}/{tmdb_id}/reviews',
        'key': 'results',
        'url_info': 'textviewer',
        'item_tmdbtype': 'review'},
    'posters': {
        'path': '{type}/{tmdb_id}/images',
        'key': 'posters',
        'url_info': 'imageviewer',
        'item_tmdbtype': 'image'},
    'fanart': {
        'path': '{type}/{tmdb_id}/images',
        'key': 'backdrops',
        'url_info': 'imageviewer',
        'item_tmdbtype': 'image'},
    'seasons': {
        'path': '{type}/{tmdb_id}',
        'key': 'seasons',
        'url_info': 'episodes',
        'url_tmdb_id': '{tmdb_id}',
        'item_tmdbtype': 'season'},
    'episode_cast': {
        'path': 'tv/{tmdb_id}/season/{season}/episode/{episode}/credits',
        'key': 'cast',
        'url_info': 'details',
        'url_tmdb_id': '{tmdb_id}',
        'item_tmdbtype': 'person'},
    'episode_thumbs': {
        'path': 'tv/{tmdb_id}/season/{season}/episode/{episode}/images',
        'key': 'stills',
        'url_info': 'imageviewer',
        'url_tmdb_id': '{tmdb_id}',
        'item_tmdbtype': 'image'},
    'stars_in_movies': {
        'path': 'person/{tmdb_id}/movie_credits',
        'key': 'cast',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': 'movie'},
    'stars_in_tvshows': {
        'path': 'person/{tmdb_id}/tv_credits',
        'key': 'cast',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': 'tv'},
    'crew_in_movies': {
        'path': 'person/{tmdb_id}/movie_credits',
        'key': 'crew',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': 'movie'},
    'crew_in_tvshows': {
        'path': 'person/{tmdb_id}/tv_credits',
        'key': 'crew',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': 'tv'},
    'videos': {
        'path': '{type}/{tmdb_id}/videos',
        'key': 'results',
        'url_info': 'details',
        'item_tmdbtype': 'video'},
    'images': {
        'path': 'person/{tmdb_id}/images',
        'key': 'profiles',
        'url_info': 'imageviewer',
        'item_tmdbtype': 'image'},
    'collection': {
        'path': 'collection/{tmdb_id}',
        'tmdb_check_id': 'collection',
        'key': 'parts',
        'url_info': 'details',
        'item_tmdbtype': 'movie'},
    'keyword_movies': {
        'path': 'keyword/{tmdb_id}/movies',
        'key': 'results',
        'url_info': 'details',
        'dbid_sorting': True,
        'item_tmdbtype': '{type}'},
    'revenue_movies': {
        'path': 'discover/{type}',
        'key': 'results',
        'url_info': 'details',
        'url_ext': 'sort_by=revenue.desc',
        'item_tmdbtype': '{type}'},
    'most_voted': {
        'path': 'discover/{type}',
        'key': 'results',
        'url_info': 'details',
        'url_ext': 'sort_by=vote_count.desc',
        'item_tmdbtype': '{type}'},
    'episodes': {
        'path': 'tv/{tmdb_id}/season/{season}',
        'key': 'episodes',
        'url_info': 'details',
        'url_tmdb_id': '{tmdb_id}',
        'item_tmdbtype': 'episode'}}

APPEND_TO_RESPONSE = 'credits,images,release_dates,content_ratings,external_ids,videos,movie_credits,tv_credits'

TRAKT_LISTS = {
    'trakt_watchlist': {
        'path': 'users/{user_slug}/watchlist/{type}/{sortmethod}',
        'req_auth': True,
        'item_tmdbtype': '{type}'},
    'trakt_recommendations': {
        'path': 'recommendations/{type}?ignore_collected=true',
        'req_auth': True,
        'item_tmdbtype': '{type}'},
    'trakt_trending': {
        'path': '{type}/trending',
        'item_tmdbtype': '{type}'},
    'trakt_popular': {
        'path': '{type}/popular',
        'item_tmdbtype': '{type}'},
    'trakt_mostplayed': {
        'path': '{type}/played/weekly',
        'item_tmdbtype': '{type}'},
    'trakt_anticipated': {
        'path': '{type}/anticipated',
        'item_tmdbtype': '{type}'},
    'trakt_boxoffice': {
        'path': '{type}/boxoffice',
        'item_tmdbtype': '{type}'},
    'trakt_userlist': {
        'path': 'users/{user_slug}/lists/{list_slug}/items',
        'item_tmdbtype': '{type}'},
    'trakt_trendinglists': {
        'path': 'lists/trending',
        'item_tmdbtype': '{type}'},
    'trakt_popularlists': {
        'path': 'lists/popular',
        'item_tmdbtype': '{type}'},
    'trakt_likedlists': {
        'path': 'users/likes/lists',
        'req_auth': True,
        'item_tmdbtype': '{type}'},
    'trakt_mylists': {
        'path': 'users/{user_slug}/lists',
        'req_auth': True,
        'item_tmdbtype': '{type}'},
    'trakt_inlists': {
        'path': 'movies/{imdb_id}/lists',
        'url_key': 'imdb_id',
        'item_tmdbtype': '{type}'},
    'trakt_myairing': {
        'path': 'calendars/my/{type}',
        'req_auth': True,
        'item_tmdbtype': '{type}'},
    'trakt_airing': {
        'path': 'calendars/all/{type}',
        'item_tmdbtype': '{type}'},
    'trakt_premiering': {
        'path': 'calendars/all/{type}/premieres',
        'item_tmdbtype': '{type}'}}

TRAKT_MANAGEMENT = ['collection_add', 'collection_remove', 'watchlist_add', 'watchlist_remove', 'history_add', 'history_remove']

TRAKT_USERLISTS = ['trakt_mylists', 'trakt_trendinglists', 'trakt_popularlists', 'trakt_likedlists', 'trakt_inlists']

TRAKT_HISTORY = ['trakt_nextepisodes', 'trakt_inprogress', 'trakt_history', 'trakt_mostwatched']

MAIN_CALENDAR = [
    ('Today', 0, 1), ('Tomorrow', 1, 1), ('{0}', 2, 1), ('{0}', 3, 1), ('{0}', 4, 1), ('{0}', 5, 1), ('{0}', 6, 1)]

TRAKT_CALENDAR = [
    ('Last Fortnight', -14, 14), ('Last Week', -7, 7), ('Yesterday', -1, 1)] + MAIN_CALENDAR + [('Next Week', 0, 7)]

LIBRARY_CALENDAR = [
    ('Last Fortnight', -14, 14), ('Last Week', -7, 7), ('Yesterday', -1, 1)] + MAIN_CALENDAR + [
    ('Next {0}', 7, 1), ('Next {0}', 8, 1), ('Next {0}', 9, 1), ('Next {0}', 10, 1), ('Next {0}', 11, 1),
    ('Next {0}', 12, 1), ('Next {0}', 13, 1), ('This Week', 0, 7), ('This Fornight', 0, 14), ('All Items', 0, 365)]

USER_DISCOVER_LISTITEMS_BASEDIR = [
    {'label': 'Discover {0} w/ Below Settings', 'url': {'info': 'user_discover', 'method': 'open'}},
    {'label': 'Match Method', 'url': {'info': 'user_discover', 'method': 'with_separator'}},
    {'label': 'Sort Method', 'url': {'info': 'user_discover', 'method': 'sort_by'}}]

USER_DISCOVER_LISTITEMS_ADDRULE = [
    {'label': 'Clear Settings', 'url': {'info': 'user_discover', 'method': 'clear'}},
    {'label': 'Add Rule...', 'url': {'info': 'user_discover', 'method': 'add_rule'}}]

USER_DISCOVER_LISTITEMS_START = [
    {'label': 'With Genres', 'url': {'info': 'user_discover', 'method': 'with_genres'}},
    {'label': 'Without Genres', 'url': {'info': 'user_discover', 'method': 'without_genres'}},
    {'label': 'With Companies', 'url': {'info': 'user_discover', 'method': 'with_companies'}},
    {'label': 'With Keywords', 'url': {'info': 'user_discover', 'method': 'with_keywords'}},
    {'label': 'Without Keywords', 'url': {'info': 'user_discover', 'method': 'without_keywords'}}]

USER_DISCOVER_LISTITEMS_FINISH = [
    {'label': 'Vote Count ( > or = )', 'url': {'info': 'user_discover', 'method': 'vote_count.gte'}},
    {'label': 'Vote Count ( < or = )', 'url': {'info': 'user_discover', 'method': 'vote_count.lte'}},
    {'label': 'Vote Average ( > or = )', 'url': {'info': 'user_discover', 'method': 'vote_average.gte'}},
    {'label': 'Vote Average ( < or = )', 'url': {'info': 'user_discover', 'method': 'vote_average.lte'}},
    {'label': 'Runtime (Minutes) ( > or = )', 'url': {'info': 'user_discover', 'method': 'with_runtime.gte'}},
    {'label': 'Runtime (Minutes) ( < or = )', 'url': {'info': 'user_discover', 'method': 'with_runtime.lte'}}]

USER_DISCOVER_LISTITEMS_MOVIES = USER_DISCOVER_LISTITEMS_START + [
    {'label': 'With Cast', 'url': {'info': 'user_discover', 'method': 'with_cast'}},
    {'label': 'With Crew', 'url': {'info': 'user_discover', 'method': 'with_crew'}},
    {'label': 'With People', 'url': {'info': 'user_discover', 'method': 'with_people'}},
    {'label': 'Primary Release Year', 'url': {'info': 'user_discover', 'method': 'primary_release_year'}},
    {'label': 'Primary Release Date After', 'url': {'info': 'user_discover', 'method': 'primary_release_date.gte'}},
    {'label': 'Primary Release Date Before', 'url': {'info': 'user_discover', 'method': 'primary_release_date.lte'}},
    {'label': 'Release Date After', 'url': {'info': 'user_discover', 'method': 'release_date.gte'}},
    {'label': 'Release Date Before', 'url': {'info': 'user_discover', 'method': 'release_date.lte'}},
    {'label': 'Release Type', 'url': {'info': 'user_discover', 'method': 'with_release_type'}},
    {'label': 'Release Region', 'url': {'info': 'user_discover', 'method': 'region'}}] + USER_DISCOVER_LISTITEMS_FINISH

USER_DISCOVER_LISTITEMS_TVSHOWS = USER_DISCOVER_LISTITEMS_START + [
    {'label': 'With Networks', 'url': {'info': 'user_discover', 'method': 'with_networks'}},
    {'label': 'Air Date After', 'url': {'info': 'user_discover', 'method': 'air_date.gte'}},
    {'label': 'Air Date Before', 'url': {'info': 'user_discover', 'method': 'air_date.lte'}},
    {'label': 'First Air Date After', 'url': {'info': 'user_discover', 'method': 'first_air_date.gte'}},
    {'label': 'First Air Date Before', 'url': {'info': 'user_discover', 'method': 'first_air_date.lte'}},
    {'label': 'First Air Year', 'url': {'info': 'user_discover', 'method': 'first_air_date_year'}}] + USER_DISCOVER_LISTITEMS_FINISH

USER_DISCOVER_SORTBY_MOVIES = [
    'popularity.asc', 'popularity.desc', 'release_date.asc', 'release_date.desc', 'revenue.asc', 'revenue.desc',
    'primary_release_date.asc', 'primary_release_date.desc', 'original_title.asc', 'original_title.desc',
    'vote_average.asc', 'vote_average.desc', 'vote_count.asc', 'vote_count.desc']

USER_DISCOVER_SORTBY_TVSHOWS = [
    'vote_average.desc', 'vote_average.asc', 'first_air_date.desc', 'first_air_date.asc', 'popularity.desc', 'popularity.asc']

USER_DISCOVER_RELEASETYPES = [
    {'name': 'Premiere', 'id': 1},
    {'name': 'Theatrical (limited)', 'id': 2},
    {'name': 'Theatrical', 'id': 3},
    {'name': 'Digital', 'id': 4},
    {'name': 'Physical', 'id': 5},
    {'name': 'TV', 'id': 6}]

USER_DISCOVER_RELATIVEDATES = [
    'primary_release_date.gte', 'primary_release_date.lte', 'release_date.gte', 'release_date.lte',
    'air_date.gte', 'air_date.lte', 'first_air_date.gte', 'first_air_date.lte']

USER_DISCOVER_REGIONS = [
    {'id': 'AD', 'name': u'Andorra (AD)'},
    {'id': 'AE', 'name': u'United Arab Emirates (AE)'},
    {'id': 'AF', 'name': u'Afghanistan (AF)'},
    {'id': 'AG', 'name': u'Antigua and Barbuda (AG)'},
    {'id': 'AI', 'name': u'Anguilla (AI)'},
    {'id': 'AL', 'name': u'Albania (AL)'},
    {'id': 'AM', 'name': u'Armenia (AM)'},
    {'id': 'AO', 'name': u'Angola (AO)'},
    {'id': 'AQ', 'name': u'Antarctica (AQ)'},
    {'id': 'AR', 'name': u'Argentina (AR)'},
    {'id': 'AS', 'name': u'American Samoa (AS)'},
    {'id': 'AT', 'name': u'Austria (AT)'},
    {'id': 'AU', 'name': u'Australia (AU)'},
    {'id': 'AW', 'name': u'Aruba (AW)'},
    {'id': 'AX', 'name': u'Åland Islands (AX)'},
    {'id': 'AZ', 'name': u'Azerbaijan (AZ)'},
    {'id': 'BA', 'name': u'Bosnia and Herzegovina (BA)'},
    {'id': 'BB', 'name': u'Barbados (BB)'},
    {'id': 'BD', 'name': u'Bangladesh (BD)'},
    {'id': 'BE', 'name': u'Belgium (BE)'},
    {'id': 'BF', 'name': u'Burkina Faso (BF)'},
    {'id': 'BG', 'name': u'Bulgaria (BG)'},
    {'id': 'BH', 'name': u'Bahrain (BH)'},
    {'id': 'BI', 'name': u'Burundi (BI)'},
    {'id': 'BJ', 'name': u'Benin (BJ)'},
    {'id': 'BL', 'name': u'Saint Barthélemy (BL)'},
    {'id': 'BM', 'name': u'Bermuda (BM)'},
    {'id': 'BN', 'name': u'Brunei Darussalam (BN)'},
    {'id': 'BO', 'name': u'Bolivia (BO)'},
    {'id': 'BQ', 'name': u'Bonaire (BQ)'},
    {'id': 'BR', 'name': u'Brazil (BR)'},
    {'id': 'BS', 'name': u'Bahamas (BS)'},
    {'id': 'BT', 'name': u'Bhutan (BT)'},
    {'id': 'BV', 'name': u'Bouvet Island (BV)'},
    {'id': 'BW', 'name': u'Botswana (BW)'},
    {'id': 'BY', 'name': u'Belarus (BY)'},
    {'id': 'BZ', 'name': u'Belize (BZ)'},
    {'id': 'CA', 'name': u'Canada (CA)'},
    {'id': 'CC', 'name': u'Cocos (CC)'},
    {'id': 'CD', 'name': u'Congo (CD)'},
    {'id': 'CF', 'name': u'Central African Republic (CF)'},
    {'id': 'CG', 'name': u'Congo (CG)'},
    {'id': 'CH', 'name': u'Switzerland (CH)'},
    {'id': 'CI', 'name': u'Côte d\'Ivoire (CI)'},
    {'id': 'CK', 'name': u'Cook Islands (CK)'},
    {'id': 'CL', 'name': u'Chile (CL)'},
    {'id': 'CM', 'name': u'Cameroon (CM)'},
    {'id': 'CN', 'name': u'China (CN)'},
    {'id': 'CO', 'name': u'Colombia (CO)'},
    {'id': 'CR', 'name': u'Costa Rica (CR)'},
    {'id': 'CU', 'name': u'Cuba (CU)'},
    {'id': 'CV', 'name': u'Cabo Verde (CV)'},
    {'id': 'CW', 'name': u'Curaçao (CW)'},
    {'id': 'CX', 'name': u'Christmas Island (CX)'},
    {'id': 'CY', 'name': u'Cyprus (CY)'},
    {'id': 'CZ', 'name': u'Czechia (CZ)'},
    {'id': 'DE', 'name': u'Germany (DE)'},
    {'id': 'DJ', 'name': u'Djibouti (DJ)'},
    {'id': 'DK', 'name': u'Denmark (DK)'},
    {'id': 'DM', 'name': u'Dominica (DM)'},
    {'id': 'DO', 'name': u'Dominican Republic (DO)'},
    {'id': 'DZ', 'name': u'Algeria (DZ)'},
    {'id': 'EC', 'name': u'Ecuador (EC)'},
    {'id': 'EE', 'name': u'Estonia (EE)'},
    {'id': 'EG', 'name': u'Egypt (EG)'},
    {'id': 'EH', 'name': u'Western Sahara (EH)'},
    {'id': 'ER', 'name': u'Eritrea (ER)'},
    {'id': 'ES', 'name': u'Spain (ES)'},
    {'id': 'ET', 'name': u'Ethiopia (ET)'},
    {'id': 'FI', 'name': u'Finland (FI)'},
    {'id': 'FJ', 'name': u'Fiji (FJ)'},
    {'id': 'FK', 'name': u'Falkland Islands (FK)'},
    {'id': 'FM', 'name': u'Micronesia (FM)'},
    {'id': 'FO', 'name': u'Faroe Islands (FO)'},
    {'id': 'FR', 'name': u'France (FR)'},
    {'id': 'GA', 'name': u'Gabon (GA)'},
    {'id': 'GB', 'name': u'United Kingdom (GB)'},
    {'id': 'GD', 'name': u'Grenada (GD)'},
    {'id': 'GE', 'name': u'Georgia (GE)'},
    {'id': 'GF', 'name': u'French Guiana (GF)'},
    {'id': 'GG', 'name': u'Guernsey (GG)'},
    {'id': 'GH', 'name': u'Ghana (GH)'},
    {'id': 'GI', 'name': u'Gibraltar (GI)'},
    {'id': 'GL', 'name': u'Greenland (GL)'},
    {'id': 'GM', 'name': u'Gambia (GM)'},
    {'id': 'GN', 'name': u'Guinea (GN)'},
    {'id': 'GP', 'name': u'Guadeloupe (GP)'},
    {'id': 'GQ', 'name': u'Equatorial Guinea (GQ)'},
    {'id': 'GR', 'name': u'Greece (GR)'},
    {'id': 'GS', 'name': u'South Georgia and the South Sandwich Islands (GS)'},
    {'id': 'GT', 'name': u'Guatemala (GT)'},
    {'id': 'GU', 'name': u'Guam (GU)'},
    {'id': 'GW', 'name': u'Guinea-Bissau (GW)'},
    {'id': 'GY', 'name': u'Guyana (GY)'},
    {'id': 'HK', 'name': u'Hong Kong (HK)'},
    {'id': 'HM', 'name': u'Heard Island and McDonald Islands (HM)'},
    {'id': 'HN', 'name': u'Honduras (HN)'},
    {'id': 'HR', 'name': u'Croatia (HR)'},
    {'id': 'HT', 'name': u'Haiti (HT)'},
    {'id': 'HU', 'name': u'Hungary (HU)'},
    {'id': 'ID', 'name': u'Indonesia (ID)'},
    {'id': 'IE', 'name': u'Ireland (IE)'},
    {'id': 'IL', 'name': u'Israel (IL)'},
    {'id': 'IM', 'name': u'Isle of Man (IM)'},
    {'id': 'IN', 'name': u'India (IN)'},
    {'id': 'IO', 'name': u'British Indian Ocean Territory (IO)'},
    {'id': 'IQ', 'name': u'Iraq (IQ)'},
    {'id': 'IR', 'name': u'Iran (IR)'},
    {'id': 'IS', 'name': u'Iceland (IS)'},
    {'id': 'IT', 'name': u'Italy (IT)'},
    {'id': 'JE', 'name': u'Jersey (JE)'},
    {'id': 'JM', 'name': u'Jamaica (JM)'},
    {'id': 'JO', 'name': u'Jordan (JO)'},
    {'id': 'JP', 'name': u'Japan (JP)'},
    {'id': 'KE', 'name': u'Kenya (KE)'},
    {'id': 'KG', 'name': u'Kyrgyzstan (KG)'},
    {'id': 'KH', 'name': u'Cambodia (KH)'},
    {'id': 'KI', 'name': u'Kiribati (KI)'},
    {'id': 'KM', 'name': u'Comoros (KM)'},
    {'id': 'KN', 'name': u'Saint Kitts and Nevis (KN)'},
    {'id': 'KP', 'name': u'Korea (KP)'},
    {'id': 'KR', 'name': u'Korea (KR)'},
    {'id': 'KW', 'name': u'Kuwait (KW)'},
    {'id': 'KY', 'name': u'Cayman Islands (KY)'},
    {'id': 'KZ', 'name': u'Kazakhstan (KZ)'},
    {'id': 'LA', 'name': u'Lao People\'s Democratic Republic (LA)'},
    {'id': 'LB', 'name': u'Lebanon (LB)'},
    {'id': 'LC', 'name': u'Saint Lucia (LC)'},
    {'id': 'LI', 'name': u'Liechtenstein (LI)'},
    {'id': 'LK', 'name': u'Sri Lanka (LK)'},
    {'id': 'LR', 'name': u'Liberia (LR)'},
    {'id': 'LS', 'name': u'Lesotho (LS)'},
    {'id': 'LT', 'name': u'Lithuania (LT)'},
    {'id': 'LU', 'name': u'Luxembourg (LU)'},
    {'id': 'LV', 'name': u'Latvia (LV)'},
    {'id': 'LY', 'name': u'Libya (LY)'},
    {'id': 'MA', 'name': u'Morocco (MA)'},
    {'id': 'MC', 'name': u'Monaco (MC)'},
    {'id': 'MD', 'name': u'Moldova (MD)'},
    {'id': 'ME', 'name': u'Montenegro (ME)'},
    {'id': 'MF', 'name': u'Saint Martin (MF)'},
    {'id': 'MG', 'name': u'Madagascar (MG)'},
    {'id': 'MH', 'name': u'Marshall Islands (MH)'},
    {'id': 'MK', 'name': u'North Macedonia (MK)'},
    {'id': 'ML', 'name': u'Mali (ML)'},
    {'id': 'MM', 'name': u'Myanmar (MM)'},
    {'id': 'MN', 'name': u'Mongolia (MN)'},
    {'id': 'MO', 'name': u'Macao (MO)'},
    {'id': 'MP', 'name': u'Northern Mariana Islands (MP)'},
    {'id': 'MQ', 'name': u'Martinique (MQ)'},
    {'id': 'MR', 'name': u'Mauritania (MR)'},
    {'id': 'MS', 'name': u'Montserrat (MS)'},
    {'id': 'MT', 'name': u'Malta (MT)'},
    {'id': 'MU', 'name': u'Mauritius (MU)'},
    {'id': 'MV', 'name': u'Maldives (MV)'},
    {'id': 'MW', 'name': u'Malawi (MW)'},
    {'id': 'MX', 'name': u'Mexico (MX)'},
    {'id': 'MY', 'name': u'Malaysia (MY)'},
    {'id': 'MZ', 'name': u'Mozambique (MZ)'},
    {'id': 'NA', 'name': u'Namibia (NA)'},
    {'id': 'NC', 'name': u'New Caledonia (NC)'},
    {'id': 'NE', 'name': u'Niger (NE)'},
    {'id': 'NF', 'name': u'Norfolk Island (NF)'},
    {'id': 'NG', 'name': u'Nigeria (NG)'},
    {'id': 'NI', 'name': u'Nicaragua (NI)'},
    {'id': 'NL', 'name': u'Netherlands (NL)'},
    {'id': 'NO', 'name': u'Norway (NO)'},
    {'id': 'NP', 'name': u'Nepal (NP)'},
    {'id': 'NR', 'name': u'Nauru (NR)'},
    {'id': 'NU', 'name': u'Niue (NU)'},
    {'id': 'NZ', 'name': u'New Zealand (NZ)'},
    {'id': 'OM', 'name': u'Oman (OM)'},
    {'id': 'PA', 'name': u'Panama (PA)'},
    {'id': 'PE', 'name': u'Peru (PE)'},
    {'id': 'PF', 'name': u'French Polynesia (PF)'},
    {'id': 'PG', 'name': u'Papua New Guinea (PG)'},
    {'id': 'PH', 'name': u'Philippines (PH)'},
    {'id': 'PK', 'name': u'Pakistan (PK)'},
    {'id': 'PL', 'name': u'Poland (PL)'},
    {'id': 'PM', 'name': u'Saint Pierre and Miquelon (PM)'},
    {'id': 'PN', 'name': u'Pitcairn (PN)'},
    {'id': 'PR', 'name': u'Puerto Rico (PR)'},
    {'id': 'PS', 'name': u'Palestine (PS)'},
    {'id': 'PT', 'name': u'Portugal (PT)'},
    {'id': 'PW', 'name': u'Palau (PW)'},
    {'id': 'PY', 'name': u'Paraguay (PY)'},
    {'id': 'QA', 'name': u'Qatar (QA)'},
    {'id': 'RE', 'name': u'Réunion (RE)'},
    {'id': 'RO', 'name': u'Romania (RO)'},
    {'id': 'RS', 'name': u'Serbia (RS)'},
    {'id': 'RU', 'name': u'Russian Federation (RU)'},
    {'id': 'RW', 'name': u'Rwanda (RW)'},
    {'id': 'SA', 'name': u'Saudi Arabia (SA)'},
    {'id': 'SB', 'name': u'Solomon Islands (SB)'},
    {'id': 'SC', 'name': u'Seychelles (SC)'},
    {'id': 'SD', 'name': u'Sudan (SD)'},
    {'id': 'SE', 'name': u'Sweden (SE)'},
    {'id': 'SG', 'name': u'Singapore (SG)'},
    {'id': 'SH', 'name': u'Saint Helena (SH)'},
    {'id': 'SI', 'name': u'Slovenia (SI)'},
    {'id': 'SJ', 'name': u'Svalbard and Jan Mayen (SJ)'},
    {'id': 'SK', 'name': u'Slovakia (SK)'},
    {'id': 'SL', 'name': u'Sierra Leone (SL)'},
    {'id': 'SM', 'name': u'San Marino (SM)'},
    {'id': 'SN', 'name': u'Senegal (SN)'},
    {'id': 'SO', 'name': u'Somalia (SO)'},
    {'id': 'SR', 'name': u'Suriname (SR)'},
    {'id': 'SS', 'name': u'South Sudan (SS)'},
    {'id': 'ST', 'name': u'Sao Tome and Principe (ST)'},
    {'id': 'SV', 'name': u'El Salvador (SV)'},
    {'id': 'SX', 'name': u'Sint Maarten (SX)'},
    {'id': 'SY', 'name': u'Syrian Arab Republic (SY)'},
    {'id': 'SZ', 'name': u'Eswatini (SZ)'},
    {'id': 'TC', 'name': u'Turks and Caicos Islands (TC)'},
    {'id': 'TD', 'name': u'Chad (TD)'},
    {'id': 'TF', 'name': u'French Southern Territories (TF)'},
    {'id': 'TG', 'name': u'Togo (TG)'},
    {'id': 'TH', 'name': u'Thailand (TH)'},
    {'id': 'TJ', 'name': u'Tajikistan (TJ)'},
    {'id': 'TK', 'name': u'Tokelau (TK)'},
    {'id': 'TL', 'name': u'Timor-Leste (TL)'},
    {'id': 'TM', 'name': u'Turkmenistan (TM)'},
    {'id': 'TN', 'name': u'Tunisia (TN)'},
    {'id': 'TO', 'name': u'Tonga (TO)'},
    {'id': 'TR', 'name': u'Turkey (TR)'},
    {'id': 'TT', 'name': u'Trinidad and Tobago (TT)'},
    {'id': 'TV', 'name': u'Tuvalu (TV)'},
    {'id': 'TW', 'name': u'Taiwan (TW)'},
    {'id': 'TZ', 'name': u'Tanzania (TZ)'},
    {'id': 'UA', 'name': u'Ukraine (UA)'},
    {'id': 'UG', 'name': u'Uganda (UG)'},
    {'id': 'US', 'name': u'United States of America (US)'},
    {'id': 'UY', 'name': u'Uruguay (UY)'},
    {'id': 'UZ', 'name': u'Uzbekistan (UZ)'},
    {'id': 'VA', 'name': u'Holy See (VA)'},
    {'id': 'VC', 'name': u'Saint Vincent and the Grenadines (VC)'},
    {'id': 'VE', 'name': u'Venezuela (VE)'},
    {'id': 'VG', 'name': u'Virgin Islands (VG)'},
    {'id': 'VI', 'name': u'Virgin Islands (VI)'},
    {'id': 'VN', 'name': u'Viet Nam (VN)'},
    {'id': 'VU', 'name': u'Vanuatu (VU)'},
    {'id': 'WF', 'name': u'Wallis and Futuna (WF)'},
    {'id': 'WS', 'name': u'Samoa (WS)'},
    {'id': 'YE', 'name': u'Yemen (YE)'},
    {'id': 'YT', 'name': u'Mayotte (YT)'},
    {'id': 'ZA', 'name': u'South Africa (ZA)'},
    {'id': 'ZM', 'name': u'Zambia (ZM)'},
    {'id': 'ZW', 'name': u'Zimbabwe (ZW)'}]
