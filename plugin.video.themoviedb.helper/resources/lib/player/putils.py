def make_playlist(episode_queue):
    """ Make a playlist from a queue of episode items """
    from xbmc import PlayList, PLAYLIST_VIDEO
    playlist = PlayList(PLAYLIST_VIDEO)
    if playlist.getposition() != 0:  # If position isn't 0 then the user is already playing from the queue
        return  # We don't want to clear the existing queue so let's exit early
    playlist.clear()  # If there's an existing playlist but we're at position 0 then it might be old so clear it
    for li in episode_queue:  # Add all our episodes in the queue
        listitem = li.get_listitem()
        playlist.add(listitem.getPath(), listitem)


def make_upnext(current_episode, next_episode):
    import AddonSignals
    from resources.lib.addon.consts import UPNEXT_EPISODE
    next_info = {
        'current_episode': {k: v(current_episode) for k, v in UPNEXT_EPISODE.items()},
        'next_episode': {k: v(next_episode) for k, v in UPNEXT_EPISODE.items()},
        'play_url': next_episode.get_url()}
    AddonSignals.sendSignal('upnext_data', next_info, source_id='plugin.video.themoviedb.helper')


def get_players_from_file():
    from json import loads
    from resources.lib.files.futils import get_files_in_folder, read_file
    from resources.lib.addon.plugin import get_setting, get_condvisibility
    from resources.lib.addon.consts import PLAYERS_BASEDIR_BUNDLED, PLAYERS_BASEDIR_USER, PLAYERS_BASEDIR_SAVE
    players = {}
    basedirs = [PLAYERS_BASEDIR_USER]
    if get_setting('bundled_players'):
        basedirs += [PLAYERS_BASEDIR_BUNDLED]
    basedirs += [PLAYERS_BASEDIR_SAVE]  # Add saved players last so they overwrite
    for basedir in basedirs:
        files = get_files_in_folder(basedir, r'.*\.json')
        for file in files:
            meta = loads(read_file(basedir + file)) or {}
            plugins = meta.get('plugin') or 'plugin.undefined'  # Give dummy name to undefined plugins so that they fail the check
            plugins = plugins if isinstance(plugins, list) else [plugins]  # Listify for simplicity of code
            for i in plugins:
                if not get_condvisibility(f'System.AddonIsEnabled({i})'):
                    break  # System doesn't have a required plugin so skip this player
            else:
                meta['plugin'] = plugins[0]
                players[file] = meta
    return players
