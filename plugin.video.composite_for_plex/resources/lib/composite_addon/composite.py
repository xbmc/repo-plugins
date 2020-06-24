# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import platform
import sys
import time

from .addon.common import get_params
from .addon.constants import COMMANDS
from .addon.constants import CONFIG
from .addon.constants import MODES
from .addon.containers import Context
from .addon.logger import Logger
from .addon.settings import AddonSettings

LOG = Logger()


def run(start_time):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches, too-many-return-statements
    context = Context()
    context.settings = AddonSettings()

    if context.settings.wake_on_lan():
        from .addon.wol import wake_servers  # pylint: disable=import-outside-toplevel
        wake_servers(context)

    context.params = get_params()

    try:
        mode = int(context.params.get('mode', MODES.UNSET))
    except ValueError:
        mode = context.params.get('mode')

    command = context.params.get('command', COMMANDS.UNSET)
    path_mode = context.params.get('path_mode')

    library = path_mode is not None and path_mode.startswith('library/')
    media_id = context.params.get('media_id')
    server_uuid = context.params.get('server_uuid')

    url = context.params.get('url')

    context.settings.set_picture_mode(context.params.get('content_type') == 'image')

    _start({
        'mode': mode,
        'command': command,
        'url': url,
        'params': context.params,
        'server_uuid': server_uuid,
        'media_id': media_id
    })

    if command == COMMANDS.REFRESH:
        from .routes import refresh  # pylint: disable=import-outside-toplevel
        refresh.run(context)
        return _finished(start_time)

    if command == COMMANDS.SWITCHUSER:
        from .routes import switch_user  # pylint: disable=import-outside-toplevel
        switch_user.run(context)
        return _finished(start_time)

    if command == COMMANDS.SIGNOUT:
        from .routes import sign_out  # pylint: disable=import-outside-toplevel
        sign_out.run(context)
        return _finished(start_time)

    if command == COMMANDS.SIGNIN:
        from .routes import sign_in  # pylint: disable=import-outside-toplevel
        sign_in.run(context)
        return _finished(start_time)

    if command == COMMANDS.MANAGEMYPLEX:
        from .routes import manage_my_plex  # pylint: disable=import-outside-toplevel
        manage_my_plex.run(context)
        return _finished(start_time)

    if command == COMMANDS.MANAGESERVERS:
        from .routes import manage_servers  # pylint: disable=import-outside-toplevel
        manage_servers.run(context)
        return _finished(start_time)

    if command == COMMANDS.DELETEREFRESH:
        from .routes import delete_refresh  # pylint: disable=import-outside-toplevel
        delete_refresh.run(context)
        return _finished(start_time)

    if command == COMMANDS.UPDATE:
        from .routes import refresh_library  # pylint: disable=import-outside-toplevel
        refresh_library.run(context)
        return _finished(start_time)

    # Mark an item as watched/unwatched in plex
    if command == COMMANDS.WATCH:
        from .routes import watch_status  # pylint: disable=import-outside-toplevel
        watch_status.run(context)
        return _finished(start_time)

    # delete media from PMS
    if command == COMMANDS.DELETE:
        from .routes import delete_media  # pylint: disable=import-outside-toplevel
        delete_media.run(context)
        return _finished(start_time)

    # Display subtitle selection screen
    if command == COMMANDS.SUBS:
        from .routes import set_subtitles  # pylint: disable=import-outside-toplevel
        set_subtitles.run(context)
        return _finished(start_time)

    # Display audio stream selection screen
    if command == COMMANDS.AUDIO:
        from .routes import set_audio  # pylint: disable=import-outside-toplevel
        set_audio.run(context)
        return _finished(start_time)

    # Allow a master server to be selected (for myPlex Queue)
    if command == COMMANDS.MASTER:
        from .routes import set_master_server  # pylint: disable=import-outside-toplevel
        set_master_server.run(context)
        return _finished(start_time)

    if command == COMMANDS.DELETEPLAYLIST:
        from .routes import delete_playlist  # pylint: disable=import-outside-toplevel
        delete_playlist.run(context)
        return _finished(start_time)

    if command == COMMANDS.DELETEFROMPLAYLIST:
        from .routes import delete_playlist_item  # pylint: disable=import-outside-toplevel
        delete_playlist_item.run(context)
        return _finished(start_time)

    if command == COMMANDS.ADDTOPLAYLIST:
        from .routes import add_playlist_item  # pylint: disable=import-outside-toplevel
        add_playlist_item.run(context)
        return _finished(start_time)

    if command == COMMANDS.TEST_SKIP_INTRO_DIALOG:
        from .routes import test_skip_intro_dialog  # pylint: disable=import-outside-toplevel
        test_skip_intro_dialog.run()
        return _finished(start_time)

    if mode in [MODES.TXT_OPEN, MODES.TXT_PLAY]:
        from .routes import trakttokodi  # pylint: disable=import-outside-toplevel
        trakttokodi.run(context)
        return _finished(start_time)

    if ((path_mode in [MODES.TXT_MOVIES_LIBRARY, MODES.TXT_TVSHOWS_LIBRARY] and
         (mode is None or mode == MODES.UNSET)) or context.params.get('kodi_action')):
        from .routes import kodi_library  # pylint: disable=import-outside-toplevel
        kodi_library.run(context)
        return _finished(start_time)

    # Run a function based on the mode variable that was passed in the URL
    if (((isinstance(mode, int) and mode < 0) or (not url and (not server_uuid and not media_id)))  # pylint: disable=too-many-boolean-expressions
            and mode not in [MODES.SEARCHALL]):
        from .routes import display_sections  # pylint: disable=import-outside-toplevel
        display_sections.run(context)
        return _finished(start_time)

    if mode in [MODES.GETCONTENT, MODES.TXT_TVSHOWS, MODES.TXT_MOVIES,
                MODES.TXT_MOVIES_ON_DECK, MODES.TXT_MOVIES_RECENT_ADDED,
                MODES.TXT_MOVIES_RECENT_RELEASE, MODES.TXT_TVSHOWS_ON_DECK,
                MODES.TXT_TVSHOWS_RECENT_ADDED, MODES.TXT_TVSHOWS_RECENT_AIRED]:
        from .routes import get_content  # pylint: disable=import-outside-toplevel
        get_content.run(context, url, server_uuid, mode)
        return _finished(start_time)

    if mode == MODES.TVSHOWS:
        from .routes import process_shows  # pylint: disable=import-outside-toplevel
        process_shows.run(context, url)
        return _finished(start_time)

    if mode == MODES.MOVIES:
        from .routes import process_movies  # pylint: disable=import-outside-toplevel
        process_movies.run(context, url)
        return _finished(start_time)

    if mode == MODES.ARTISTS:
        from .routes import process_artists  # pylint: disable=import-outside-toplevel
        process_artists.run(context, url)
        return _finished(start_time)

    if mode == MODES.TVSEASONS:
        from .routes import process_seasons  # pylint: disable=import-outside-toplevel
        process_seasons.run(context, url, rating_key=context.params.get('rating_key'),
                            library=library)
        return _finished(start_time)

    if mode == MODES.PLAYLIBRARY:
        from .routes import play_library_media  # pylint: disable=import-outside-toplevel
        play_library_media.run(context, {
            'url': url,
            'server_uuid': server_uuid,
            'media_id': media_id,
            'transcode': int(context.params.get('transcode', 0)) == 1,
            'transcode_profile': context.params.get('transcode_profile')
        })
        return _finished(start_time)

    if mode == MODES.TVEPISODES:
        from .routes import process_episodes  # pylint: disable=import-outside-toplevel
        process_episodes.run(context, url, rating_key=context.params.get('rating_key'),
                             library=library)
        return _finished(start_time)

    if mode == MODES.PLEXPLUGINS:
        from .routes import process_plex_plugins  # pylint: disable=import-outside-toplevel
        process_plex_plugins.run(context, url)
        return _finished(start_time)

    if mode == MODES.PROCESSXML:
        from .routes import process_xml  # pylint: disable=import-outside-toplevel
        process_xml.run(context, url)
        return _finished(start_time)

    if mode == MODES.BASICPLAY:
        from .routes import play_media_stream  # pylint: disable=import-outside-toplevel
        play_media_stream.run(context, url)
        return _finished(start_time)

    if mode == MODES.ALBUMS:
        from .routes import process_albums  # pylint: disable=import-outside-toplevel
        process_albums.run(context, url)
        return _finished(start_time)

    if mode == MODES.TRACKS:
        from .routes import process_tracks  # pylint: disable=import-outside-toplevel
        process_tracks.run(context, url)
        return _finished(start_time)

    if mode == MODES.PHOTOS:
        from .routes import process_photos  # pylint: disable=import-outside-toplevel
        process_photos.run(context, url)
        return _finished(start_time)

    if mode == MODES.MUSIC:
        from .routes import process_music  # pylint: disable=import-outside-toplevel
        process_music.run(context, url)
        return _finished(start_time)

    if mode == MODES.VIDEOPLUGINPLAY:
        from .routes import play_video_channel  # pylint: disable=import-outside-toplevel
        play_video_channel.run(context, url, context.params.get('identifier'),
                               context.params.get('indirect'))
        return _finished(start_time)

    if mode == MODES.PLEXONLINE:
        from .routes import plex_online  # pylint: disable=import-outside-toplevel
        plex_online.run(context, url)
        return _finished(start_time)

    if mode == MODES.CHANNELINSTALL:
        from .routes import install_plugin  # pylint: disable=import-outside-toplevel
        install_plugin.run(context, url, context.params.get('name', ''))
        return _finished(start_time)

    if mode == MODES.CHANNELVIEW:
        from .routes import channel_view  # pylint: disable=import-outside-toplevel
        channel_view.run(context, url)
        return _finished(start_time)

    if mode == MODES.PLAYLIBRARY_TRANSCODE:
        from .routes import play_library_media  # pylint: disable=import-outside-toplevel
        play_library_media.run(context, {
            'url': url,
            'transcode': True
        })
        return _finished(start_time)

    if mode == MODES.MYPLEXQUEUE:
        from .routes import myplex_queue  # pylint: disable=import-outside-toplevel
        myplex_queue.run(context)
        return _finished(start_time)

    if mode == MODES.CHANNELSEARCH:
        from .routes import channel_search  # pylint: disable=import-outside-toplevel
        channel_search.run(context, url, context.params.get('prompt'))
        return _finished(start_time)

    if mode == MODES.CHANNELPREFS:
        from .routes import channel_settings  # pylint: disable=import-outside-toplevel
        channel_settings.run(context, url, context.params.get('id'))
        return _finished(start_time)

    if mode == MODES.SHARED_MOVIES:
        from .routes import display_sections  # pylint: disable=import-outside-toplevel
        display_sections.run(context, content_filter='movies', display_shared=True)
        return _finished(start_time)

    if mode == MODES.SHARED_SHOWS:
        from .routes import display_sections  # pylint: disable=import-outside-toplevel
        display_sections.run(context, content_filter='tvshows', display_shared=True)
        return _finished(start_time)

    if mode == MODES.SHARED_PHOTOS:
        from .routes import display_sections  # pylint: disable=import-outside-toplevel
        display_sections.run(context, content_filter='photos', display_shared=True)
        return _finished(start_time)

    if mode == MODES.SHARED_MUSIC:
        from .routes import display_sections  # pylint: disable=import-outside-toplevel
        display_sections.run(context, content_filter='music', display_shared=True)
        return _finished(start_time)

    if mode == MODES.SHARED_ALL:
        from .routes import display_sections  # pylint: disable=import-outside-toplevel
        display_sections.run(context, display_shared=True)
        return _finished(start_time)

    if mode == MODES.PLAYLISTS:
        from .routes import process_xml  # pylint: disable=import-outside-toplevel
        process_xml.run(context, url)
        return _finished(start_time)

    if mode == MODES.DISPLAYSERVERS:
        from .routes import display_plex_servers  # pylint: disable=import-outside-toplevel
        display_plex_servers.run(context, url)
        return _finished(start_time)

    if mode == MODES.WIDGETS:
        from .routes import widgets  # pylint: disable=import-outside-toplevel
        widgets.run(context, url)
        return _finished(start_time)

    if mode == MODES.SEARCHALL:
        from .routes import search_all  # pylint: disable=import-outside-toplevel
        search_all.run(context)
        return _finished(start_time)

    return _finished(start_time)


def _start(data):
    LOG.notice('%s %s: Kodi %s on %s with Python %s' %
               (CONFIG['name'], CONFIG['version'], CONFIG['kodi_version'],
                platform.uname()[0], '.'.join(map(str, sys.version_info))),
               no_privacy=True)  # force no privacy to avoid redacting version strings

    LOG.notice('Mode |%s| Command |%s| Url |%s| Parameters |%s| Server UUID |%s| Media Id |%s|'
               % (data.get('mode'), data.get('command'), data.get('url'),
                  data.get('params'), data.get('server_uuid'), data.get('media_id')))


def _finished(start_time):
    LOG.notice('Finished. |%.3fs|' % (time.time() - start_time))
