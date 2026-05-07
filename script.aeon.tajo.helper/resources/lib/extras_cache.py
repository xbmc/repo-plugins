#!/usr/bin/python
# coding: utf-8

########################

import xbmc
import xbmcgui
import xbmcvfs
import os
import threading
import unicodedata

from resources.lib.helper import *

########################

EXTRAS_ART = 'special://home/addons/%s/resources/media/extras.png' % ADDON_ID
THEME_ART = 'special://home/addons/%s/resources/media/theme.png' % ADDON_ID

STUDIO_ART_TYPES = [
    {'addon': 'resource.images.studios.coloured', 'prefix': 'color_studio'},
    {'addon': 'resource.images.studios.white', 'prefix': 'white_studio'}
]

MAX_STUDIOS = 3

ART_KEYS_TO_REMOVE = ['extras', 'theme', 'album_soundtrack']
MUSIC_ART_KEYS_TO_REMOVE = ['extras_music', 'recordlabel']
for _i in range(1, MAX_STUDIOS + 1):
    for _sa in STUDIO_ART_TYPES:
        ART_KEYS_TO_REMOVE.append('%s_%02d' % (_sa['prefix'], _i))

########################


def _normalize(text):
    """Remove accents and convert to lowercase ASCII for matching."""
    normalized = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return stripped.lower()


def _build_studio_index(addon_id):
    """Build a dict mapping normalized studio names to original filenames (without extension)."""
    studio_dict = {}
    resource_path = xbmcvfs.translatePath('resource://%s/' % addon_id)

    try:
        dirs, files = xbmcvfs.listdir(resource_path)
        for f in files:
            if f.lower().endswith('.png') or f.lower().endswith('.jpg'):
                name_no_ext = f[:f.rfind('.')]
                key = _normalize(name_no_ext)
                if key not in studio_dict:
                    studio_dict[key] = name_no_ext
    except Exception:
        pass

    return studio_dict


def _get_studio_art(studios_string, studio_index, addon_id, prefix):
    """Find matching studio images. Returns list of (key, value) tuples."""
    results = []

    if not studios_string or not studio_index:
        return results

    studios = [s.strip() for s in studios_string.split('/') if s.strip()]

    found = 0
    for studio in studios:
        if found >= MAX_STUDIOS:
            break
        normalized = _normalize(studio)
        if normalized in studio_index:
            found += 1
            key = '%s_%02d' % (prefix, found)
            original_name = studio_index[normalized]
            value = 'resource://%s/%s.png' % (addon_id, original_name)
            results.append((key, value))

    return results


def _build_album_index():
    """Build a dict mapping (album_title, year) to album thumbnail.
       Used to find soundtrack albums matching movie/tvshow titles.
    """
    album_index = {}

    albums = json_call('AudioLibrary.GetAlbums',
                        properties=['title', 'year', 'thumbnail']
                        )
    try:
        albums_list = albums['result']['albums']
    except KeyError:
        return album_index

    for album in albums_list:
        title = album.get('title', '')
        year = album.get('year', 0)
        thumbnail = album.get('thumbnail', '')

        if title and year and thumbnail:
            key = (title.lower(), int(year))
            if key not in album_index:
                album_index[key] = thumbnail

    return album_index


def _find_soundtrack(title, originaltitle, year, album_index):
    """Check if a soundtrack album exists for a movie/tvshow.
       Returns the album thumbnail if found, None otherwise.
    """
    if not album_index or not year:
        return None

    year = int(year)

    ''' Try title first
    '''
    key = (title.lower(), year)
    if key in album_index:
        return album_index[key]

    ''' Try originaltitle if different
    '''
    if originaltitle and originaltitle.lower() != title.lower():
        key = (originaltitle.lower(), year)
        if key in album_index:
            return album_index[key]

    return None


def scan_library(force_reset=False):
    """Scan the entire library for extras folders, theme files and studio images.
       Runs in a background thread. Stores results as Art fields
       in the Kodi database via JSON-RPC.
       If force_reset is True, all custom art data is removed and rescanned from scratch.
    """
    search_extras = condition('Skin.HasSetting(SearchExtras)')
    search_themes = condition('Skin.HasSetting(playTheme)')

    studio_addons = []
    for sa in STUDIO_ART_TYPES:
        if condition('System.HasAddon(%s)' % sa['addon']):
            studio_addons.append(sa)

    if not search_extras and not search_themes and not studio_addons:
        log('LibraryScan: Nothing to scan, skipping')
        return

    thread = threading.Thread(target=_scan_worker, args=(search_extras, search_themes, studio_addons, force_reset), daemon=True)
    thread.start()


def _scan_worker(search_extras, search_themes, studio_addons, force_reset=False):
    """Background worker that scans movies and tvshows."""
    if force_reset:
        log('LibraryScan: Full reset scan started', force=True)
    else:
        log('LibraryScan: Scan started', force=True)

    monitor = xbmc.Monitor()

    extras_folder = xbmc.getInfoLabel('Skin.String(extras_folder)')
    if not extras_folder:
        extras_folder = 'extras'

    ''' Build studio indexes once
    '''
    studio_indexes = {}
    for sa in studio_addons:
        studio_indexes[sa['addon']] = _build_studio_index(sa['addon'])
        log('LibraryScan: Loaded %d studio images from %s' % (len(studio_indexes[sa['addon']]), sa['addon']), force=True)

    ''' Build album index for soundtrack matching
    '''
    album_index = {}
    if search_extras:
        album_index = _build_album_index()
        if album_index:
            log('LibraryScan: Loaded %d albums from music library' % len(album_index), force=True)

    ''' Determine which properties to request
    '''
    properties = ['file', 'art']
    if studio_addons:
        properties.append('studio')
    if album_index:
        properties.extend(['title', 'year', 'originaltitle'])

    ''' Get all movies and tvshows
    '''
    movies_list = []
    tvshows_list = []

    movies = json_call('VideoLibrary.GetMovies',
                       properties=properties,
                       sort={'method': 'title'}
                       )
    try:
        movies_list = movies['result']['movies']
    except KeyError:
        pass

    tvshows = json_call('VideoLibrary.GetTVShows',
                        properties=properties,
                        sort={'method': 'title'}
                        )
    try:
        tvshows_list = tvshows['result']['tvshows']
    except KeyError:
        pass

    total = len(movies_list) + len(tvshows_list)
    if total == 0:
        log('LibraryScan: No items in library, skipping scan')
        return

    progress = xbmcgui.DialogProgressBG()
    progress.create(ADDON.getLocalizedString(32037), ADDON.getLocalizedString(32038))
    processed = 0
    extras_count = 0
    theme_count = 0
    studio_count = 0
    soundtrack_count = 0

    ''' Scan movies
    '''
    for movie in movies_list:
        if monitor.abortRequested():
            progress.close()
            return

        dbid = movie.get('movieid')
        path = movie.get('file', '')
        current_art = movie.get('art', {})
        art_update = {}

        if force_reset:
            for key in ART_KEYS_TO_REMOVE:
                if key in current_art:
                    art_update[key] = None
            current_art = {}

        if dbid and path:
            movie_folder = os.path.dirname(path)
            if movie_folder:

                if search_extras:
                    extras_path = os.path.join(movie_folder, extras_folder) + os.sep
                    has_extras = xbmcvfs.exists(extras_path)
                    had_extras = 'extras' in current_art

                    if has_extras and not had_extras:
                        art_update['extras'] = EXTRAS_ART
                        extras_count += 1
                    elif not has_extras and had_extras:
                        art_update['extras'] = None
                    elif has_extras:
                        extras_count += 1

                if search_themes:
                    theme_path = os.path.join(movie_folder, 'theme.mp3')
                    has_theme = xbmcvfs.exists(theme_path)
                    had_theme = 'theme' in current_art

                    if has_theme and not had_theme:
                        art_update['theme'] = THEME_ART
                        theme_count += 1
                    elif not has_theme and had_theme:
                        art_update['theme'] = None
                    elif has_theme:
                        theme_count += 1

            if album_index:
                soundtrack = _find_soundtrack(
                    movie.get('title', ''),
                    movie.get('originaltitle', ''),
                    movie.get('year', 0),
                    album_index
                )
                had_soundtrack = 'album_soundtrack' in current_art

                if soundtrack and not had_soundtrack:
                    art_update['album_soundtrack'] = soundtrack
                    soundtrack_count += 1
                elif not soundtrack and had_soundtrack:
                    art_update['album_soundtrack'] = None
                elif soundtrack:
                    soundtrack_count += 1

            studios_string = get_joined_items(movie.get('studio', []))
            for sa in studio_addons:
                new_studios = _get_studio_art(studios_string, studio_indexes[sa['addon']], sa['addon'], sa['prefix'])
                new_dict = dict(new_studios)

                needs_update = False
                for key, value in new_studios:
                    if key not in current_art:
                        needs_update = True
                        break

                for i in range(1, MAX_STUDIOS + 1):
                    key = '%s_%02d' % (sa['prefix'], i)
                    if key in current_art and key not in new_dict:
                        needs_update = True
                        break

                if needs_update:
                    for key, value in new_studios:
                        art_update[key] = value
                    for i in range(1, MAX_STUDIOS + 1):
                        key = '%s_%02d' % (sa['prefix'], i)
                        if key in current_art and key not in new_dict:
                            art_update[key] = None
                    studio_count += 1

            if art_update:
                json_call('VideoLibrary.SetMovieDetails',
                          params={'movieid': dbid, 'art': art_update}
                          )

        processed += 1
        percent = int(processed * 100 / total)
        progress.update(percent, ADDON.getLocalizedString(32037), '%d / %d' % (processed, total))

    ''' Scan tvshows
    '''
    for show in tvshows_list:
        if monitor.abortRequested():
            progress.close()
            return

        dbid = show.get('tvshowid')
        path = show.get('file', '')
        current_art = show.get('art', {})
        art_update = {}

        if force_reset:
            for key in ART_KEYS_TO_REMOVE:
                if key in current_art:
                    art_update[key] = None
            current_art = {}

        if dbid and path:

            if search_extras:
                extras_path = os.path.join(path, extras_folder) + os.sep
                has_extras = xbmcvfs.exists(extras_path)
                had_extras = 'extras' in current_art

                if has_extras and not had_extras:
                    art_update['extras'] = EXTRAS_ART
                    extras_count += 1
                elif not has_extras and had_extras:
                    art_update['extras'] = None
                elif has_extras:
                    extras_count += 1

            if search_themes:
                theme_path = os.path.join(path, 'theme.mp3')
                has_theme = xbmcvfs.exists(theme_path)
                had_theme = 'theme' in current_art

                if has_theme and not had_theme:
                    art_update['theme'] = THEME_ART
                    theme_count += 1
                elif not has_theme and had_theme:
                    art_update['theme'] = None
                elif has_theme:
                    theme_count += 1

            if album_index:
                soundtrack = _find_soundtrack(
                    show.get('title', ''),
                    show.get('originaltitle', ''),
                    show.get('year', 0),
                    album_index
                )
                had_soundtrack = 'album_soundtrack' in current_art

                if soundtrack and not had_soundtrack:
                    art_update['album_soundtrack'] = soundtrack
                    soundtrack_count += 1
                elif not soundtrack and had_soundtrack:
                    art_update['album_soundtrack'] = None
                elif soundtrack:
                    soundtrack_count += 1

            studios_string = get_joined_items(show.get('studio', []))
            for sa in studio_addons:
                new_studios = _get_studio_art(studios_string, studio_indexes[sa['addon']], sa['addon'], sa['prefix'])
                new_dict = dict(new_studios)

                needs_update = False
                for key, value in new_studios:
                    if key not in current_art:
                        needs_update = True
                        break

                for i in range(1, MAX_STUDIOS + 1):
                    key = '%s_%02d' % (sa['prefix'], i)
                    if key in current_art and key not in new_dict:
                        needs_update = True
                        break

                if needs_update:
                    for key, value in new_studios:
                        art_update[key] = value
                    for i in range(1, MAX_STUDIOS + 1):
                        key = '%s_%02d' % (sa['prefix'], i)
                        if key in current_art and key not in new_dict:
                            art_update[key] = None
                    studio_count += 1

            if art_update:
                json_call('VideoLibrary.SetTVShowDetails',
                          params={'tvshowid': dbid, 'art': art_update}
                          )

        processed += 1
        percent = int(processed * 100 / total)
        progress.update(percent, ADDON.getLocalizedString(32037), '%d / %d' % (processed, total))

    progress.close()

    log('LibraryScan: Scan finished - %d extras, %d themes, %d studio updates, %d soundtracks' % (extras_count, theme_count, studio_count, soundtrack_count), force=True)


def scan_music_library(force_reset=False):
    """Scan the music library for extras folders and record label images in album directories.
       Runs in a background thread. Stores results as Art fields
       in the Kodi database via JSON-RPC.
    """
    search_extras = condition('Skin.HasSetting(SearchExtrasMusic)')
    search_recordlabel = condition('Skin.HasSetting(imagesRecord)') and condition('System.HasAddon(resource.images.recordlabels.white)')

    if not search_extras and not search_recordlabel:
        log('MusicScan: Nothing to scan, skipping')
        return

    thread = threading.Thread(target=_scan_music_worker, args=(search_extras, search_recordlabel, force_reset), daemon=True)
    thread.start()


def _scan_music_worker(search_extras, search_recordlabel, force_reset=False):
    """Background worker that scans albums for extras folders and record label images."""
    if force_reset:
        log('MusicScan: Full reset scan started', force=True)
    else:
        log('MusicScan: Scan started', force=True)

    monitor = xbmc.Monitor()

    extras_folder = xbmc.getInfoLabel('Skin.String(extras_folder)')
    if not extras_folder:
        extras_folder = 'extras'

    ''' Build record label index
    '''
    RECORDLABEL_ADDON = 'resource.images.recordlabels.white'
    recordlabel_index = {}
    if search_recordlabel:
        recordlabel_index = _build_studio_index(RECORDLABEL_ADDON)
        log('MusicScan: Loaded %d record label images from %s' % (len(recordlabel_index), RECORDLABEL_ADDON), force=True)

    ''' Build album path map from songs (only needed for extras)
    '''
    album_paths = {}
    if search_extras:
        songs = json_call('AudioLibrary.GetSongs',
                           properties=['albumid', 'file']
                           )
        try:
            songs_list = songs['result']['songs']
        except KeyError:
            songs_list = []

        for song in songs_list:
            albumid = song.get('albumid', 0)
            filepath = song.get('file', '')
            if albumid and filepath and albumid not in album_paths:
                album_paths[albumid] = os.path.dirname(filepath)

        if album_paths:
            log('MusicScan: Mapped %d album paths from songs' % len(album_paths), force=True)

    ''' Determine which properties to request
    '''
    properties = ['art']
    if search_recordlabel:
        properties.append('albumlabel')

    ''' Get all albums
    '''
    albums = json_call('AudioLibrary.GetAlbums',
                        properties=properties
                        )
    try:
        albums_list = albums['result']['albums']
    except KeyError:
        log('MusicScan: No albums in library, skipping scan')
        return

    total = len(albums_list)
    progress = xbmcgui.DialogProgressBG()
    progress.create(ADDON.getLocalizedString(32037), ADDON.getLocalizedString(32038))
    processed = 0
    extras_count = 0
    recordlabel_count = 0

    for album in albums_list:
        if monitor.abortRequested():
            progress.close()
            return

        dbid = album.get('albumid')
        current_art = album.get('art', {})
        art_update = {}

        if force_reset:
            for key in MUSIC_ART_KEYS_TO_REMOVE:
                if key in current_art:
                    art_update[key] = None
            current_art = {}

        if dbid:

            if search_extras and dbid in album_paths:
                album_folder = album_paths[dbid]

                extras_path = os.path.join(album_folder, extras_folder) + os.sep
                has_extras = xbmcvfs.exists(extras_path)
                had_extras = 'extras_music' in current_art

                if has_extras and not had_extras:
                    art_update['extras_music'] = EXTRAS_ART
                    extras_count += 1
                elif not has_extras and had_extras:
                    art_update['extras_music'] = None
                elif has_extras:
                    extras_count += 1

            if recordlabel_index:
                label_name = album.get('albumlabel', '')
                had_recordlabel = 'recordlabel' in current_art

                if label_name:
                    normalized = _normalize(label_name)
                    if normalized in recordlabel_index:
                        if not had_recordlabel:
                            original_name = recordlabel_index[normalized]
                            art_update['recordlabel'] = 'resource://%s/%s.png' % (RECORDLABEL_ADDON, original_name)
                            recordlabel_count += 1
                        else:
                            recordlabel_count += 1
                    elif had_recordlabel:
                        art_update['recordlabel'] = None
                elif had_recordlabel:
                    art_update['recordlabel'] = None

        if art_update:
            json_call('AudioLibrary.SetAlbumDetails',
                      params={'albumid': dbid, 'art': art_update}
                      )

        processed += 1
        percent = int(processed * 100 / total)
        progress.update(percent, ADDON.getLocalizedString(32037), '%d / %d' % (processed, total))

    progress.close()

    log('MusicScan: Scan finished - %d music extras, %d record labels' % (extras_count, recordlabel_count), force=True)
