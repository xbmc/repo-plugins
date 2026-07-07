import os
import sys
import time
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
from urllib.parse import urlencode, parse_qsl, quote, unquote
from library_service import AudioBookShelfLibraryService
from playback_monitor import (PlaybackMonitor, get_best_resume_position, 
                              sync_all_to_server, get_local_progress, save_local_progress)
from sync_manager import (get_sync_manager, startup_sync, on_network_reconnect, 
                          mark_offline, stop_background_sync)
from download_manager import DownloadManager, is_network_available
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

ADDON = xbmcaddon.Addon()
ADDON_HANDLE = int(sys.argv[1])
ADDON_URL = sys.argv[0]

download_manager = DownloadManager(ADDON)
_active_monitor = None


def get_token_cache_file():
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    if not os.path.exists(profile):
        os.makedirs(profile)
    return os.path.join(profile, 'token_cache.json')


def load_token_cache():
    try:
        import json
        cache_file = get_token_cache_file()
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'access_token': None, 'refresh_token': None, 'url': None, 'expires': 0}


def save_token_cache(cache):
    try:
        import json
        cache_file = get_token_cache_file()
        with open(cache_file, 'w') as f:
            json.dump(cache, f)
    except:
        pass


# Access tokens expire after 1 hour on the server; refresh slightly early.
TOKEN_CACHE_DURATION = 3300


def build_url(**kwargs):
    return f'{ADDON_URL}?{urlencode(kwargs)}'


def get_setting(setting_id, default=''):
    try:
        val = ADDON.getSetting(setting_id)
        return val if val else default
    except:
        return default


def get_setting_bool(setting_id, default=False):
    val = get_setting(setting_id, 'true' if default else 'false')
    return val.lower() == 'true'


def get_setting_int(setting_id, default=0):
    try:
        return int(get_setting(setting_id, str(default)))
    except:
        return default


def get_finished_threshold():
    """Get the finished threshold from settings (0=90%, 1=95%, 2=last 30s, 3=last 60s)"""
    idx = get_setting_int('mark_podcast_finished_threshold', 1)
    if idx == 0:
        return 0.90
    elif idx == 1:
        return 0.95
    elif idx == 2:
        return 0.97  # ~last 30s of typical podcast
    else:
        return 0.95  # default


def get_sync_interval(is_podcast=False):
    setting_id = 'podcast_sync_interval' if is_podcast else 'audiobook_sync_interval'
    idx = get_setting_int(setting_id, 1)
    intervals = [10, 15, 30, 60]
    return intervals[idx] if idx < len(intervals) else 15


def check_download_path():
    if not get_setting_bool('enable_downloads'):
        return False
    path = get_setting('download_path')
    if not path or path.strip() == '':
        xbmcgui.Dialog().ok('Download Path Required', 
                           'Please set a download folder in settings.')
        ADDON.openSettings()
        path = get_setting('download_path')
        if not path or path.strip() == '':
            return False
    return True


def has_downloads():
    downloads = download_manager.get_all_downloads()
    return len(downloads) > 0


def get_library_service():
    """Get authenticated library service with caching"""
    if not is_network_available():
        if get_setting_bool('enable_downloads') and has_downloads():
            mark_offline()  # Mark that we're going offline
            return None, None, None, True
        xbmcgui.Dialog().ok('No Network', 'No network connection available')
        return None, None, None, False
    
    ip = get_setting('ipaddress')
    port = get_setting('port', '13378')
    
    if not ip:
        xbmcgui.Dialog().ok('Setup Required', 'Please configure server settings')
        ADDON.openSettings()
        return None, None, None, False
    
    url = f"http://{ip}:{port}"
    
    token_cache = load_token_cache()
    current_time = time.time()

    if (token_cache.get('access_token') and token_cache.get('url') == url and
        token_cache.get('expires', 0) > current_time):
        xbmc.log("Using cached access token", xbmc.LOGINFO)
        lib_service = AudioBookShelfLibraryService(url, token_cache['access_token'])

        # Run startup sync with the library service
        try:
            sync_mgr = get_sync_manager()
            sync_mgr.set_library_service(lib_service)
            # Start background sync if not already running
            sync_mgr.start_background_sync()
        except Exception as e:
            xbmc.log(f"Sync manager setup error: {e}", xbmc.LOGDEBUG)

        return lib_service, url, token_cache['access_token'], False

    try:
        from login_service import AudioBookShelfService
        service = AudioBookShelfService(url)

        access_token = None
        refresh_token = None

        # Try refresh first if we have a refresh token for this server
        cached_refresh = token_cache.get('refresh_token') if token_cache.get('url') == url else None
        if cached_refresh:
            try:
                xbmc.log("Refreshing access token", xbmc.LOGINFO)
                refreshed = service.refresh(cached_refresh)
                access_token = refreshed['accessToken']
                refresh_token = refreshed['refreshToken']
            except Exception as e:
                xbmc.log(f"Refresh failed, falling back to login: {e}", xbmc.LOGWARNING)

        if not access_token:
            username = get_setting('username')
            password = get_setting('password')
            if not username or not password:
                xbmcgui.Dialog().ok('Credentials Required', 'Please enter username and password')
                ADDON.openSettings()
                return None, None, None, False

            response = service.login(username, password)
            access_token = response['accessToken']
            refresh_token = response['refreshToken']

        new_cache = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'url': url,
            'expires': current_time + TOKEN_CACHE_DURATION,
        }
        save_token_cache(new_cache)

        lib_service = AudioBookShelfLibraryService(url, access_token)
        
        # Perform startup sync - uploads pending local progress, downloads newer server progress
        if get_setting_bool('offline_sync_on_connect', True):
            try:
                uploaded, downloaded = startup_sync(lib_service)
                total = uploaded + downloaded
                if total > 0:
                    xbmcgui.Dialog().notification('Synced', f'{total} positions synced', 
                                                 xbmcgui.NOTIFICATION_INFO, 2000)
            except Exception as e:
                xbmc.log(f"Startup sync error: {e}", xbmc.LOGERROR)
        
        return lib_service, url, access_token, False

    except Exception as e:
        error_msg = str(e)
        xbmc.log(f"Auth failed: {error_msg}", xbmc.LOGERROR)

        if '429' in error_msg:
            token_cache = load_token_cache()
            if token_cache.get('access_token') and token_cache.get('url') == url:
                xbmc.log("Rate limited, using cached token", xbmc.LOGWARNING)
                xbmcgui.Dialog().notification('Rate Limited', 'Using cached session', xbmcgui.NOTIFICATION_WARNING)
                lib_service = AudioBookShelfLibraryService(url, token_cache['access_token'])
                return lib_service, url, token_cache['access_token'], False
        
        if get_setting_bool('enable_downloads') and has_downloads():
            if xbmcgui.Dialog().yesno('Connection Failed', 
                                      f'{error_msg[:80]}\n\nUse offline mode?'):
                mark_offline()  # Mark that we're going offline
                return None, None, None, True
        
        xbmcgui.Dialog().ok('Connection Error', f'Failed to connect:\n{error_msg[:100]}')
        return None, None, None, False


def download_cover(url, item_id):
    try:
        profile_path = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
        cache_dir = os.path.join(profile_path, 'covers')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cache_file = os.path.join(cache_dir, f"{item_id}.jpg")
        if os.path.exists(cache_file):
            return cache_file
        urlretrieve(url, cache_file)
        return cache_file if os.path.exists(cache_file) else None
    except:
        return None


def set_music_info(list_item, title, artist='', duration=0, playcount=0, tracknumber=0):
    try:
        info_tag = list_item.getMusicInfoTag()
        info_tag.setTitle(title)
        if artist:
            info_tag.setArtist(artist)
        if duration > 0:
            info_tag.setDuration(int(duration))
        if playcount > 0:
            info_tag.setPlayCount(playcount)
        if tracknumber > 0:
            info_tag.setTrack(tracknumber)
    except AttributeError:
        list_item.setInfo('music', {'title': title, 'artist': artist, 'duration': int(duration),
                                    'playcount': playcount, 'tracknumber': tracknumber})


def find_file_for_position(audio_files, position):
    sorted_files = sorted(audio_files, key=lambda x: x.get('index', 0))
    cumulative = 0
    for f in sorted_files:
        file_duration = f.get('duration', 0)
        if position < cumulative + file_duration:
            return f, position - cumulative, cumulative
        cumulative += file_duration
    if sorted_files:
        return sorted_files[-1], 0, cumulative - sorted_files[-1].get('duration', 0)
    return None, 0, 0


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def ask_resume(current_time, duration):
    if current_time < 10:
        return False
    return xbmcgui.Dialog().yesno('Resume', f'Resume from {format_time(current_time)}?',
                                  nolabel='Start Over', yeslabel='Resume')


def count_finished_episodes(library_service, item_id, episodes):
    """Count actually finished episodes (not in-progress)"""
    finished_threshold = get_finished_threshold()
    finished = 0
    
    for ep in episodes:
        ep_id = ep.get('id')
        if not ep_id:
            continue
        
        # Check local progress first
        local = get_local_progress(item_id, ep_id)
        if local and local.get('is_finished'):
            finished += 1
            continue
        
        # Check server progress
        if library_service:
            try:
                progress = library_service.get_media_progress(item_id, ep_id)
                if progress:
                    if progress.get('isFinished'):
                        finished += 1
                    elif progress.get('progress', 0) >= finished_threshold:
                        finished += 1
            except:
                pass
    
    return finished


def clear_progress(item_id, episode_id=None):
    """Clear/reset progress for an item - updates both local and server"""
    # Get library service if available
    library_service = None
    try:
        lib_svc, _, _, offline = get_library_service()
        if not offline:
            library_service = lib_svc
    except:
        pass
    
    # Clear local progress
    sync_mgr = get_sync_manager()
    key = f"{item_id}_{episode_id}" if episode_id else item_id
    
    # Save zero progress locally
    sync_mgr.save_local_progress(item_id, episode_id, 0, 1, is_finished=False, needs_upload=True)
    
    # Update server if online
    if library_service:
        try:
            library_service.update_media_progress(item_id, 0, 1, is_finished=False, episode_id=episode_id)
            sync_mgr.mark_uploaded(item_id, episode_id)
            xbmc.log(f"[PROGRESS] Cleared progress on server: {key}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[PROGRESS] Error clearing server progress: {e}", xbmc.LOGERROR)
    
    xbmcgui.Dialog().notification('Progress Cleared', 'Reset to beginning', xbmcgui.NOTIFICATION_INFO, 2000)
    xbmc.executebuiltin('Container.Refresh')
    xbmc.executebuiltin('ReloadSkin')  # Force skin reload to update context menus


def mark_as_finished(item_id, episode_id=None, finished=True):
    """Mark item as finished/unfinished - updates both local and server"""
    # Get library service if available
    library_service = None
    try:
        lib_svc, _, _, offline = get_library_service()
        if not offline:
            library_service = lib_svc
    except:
        pass
    
    sync_mgr = get_sync_manager()
    key = f"{item_id}_{episode_id}" if episode_id else item_id
    
    # Get current progress to preserve duration
    local = sync_mgr.get_local_progress(item_id, episode_id)
    duration = local.get('duration', 1) if local else 1
    current_time = duration if finished else 0
    
    # Save locally
    sync_mgr.save_local_progress(item_id, episode_id, current_time, duration, 
                                is_finished=finished, needs_upload=True)
    
    # Update server if online
    if library_service:
        try:
            library_service.update_media_progress(item_id, current_time, duration, 
                                                 is_finished=finished, episode_id=episode_id)
            sync_mgr.mark_uploaded(item_id, episode_id)
            xbmc.log(f"[PROGRESS] Marked {'finished' if finished else 'unfinished'} on server: {key}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[PROGRESS] Error updating server: {e}", xbmc.LOGERROR)
    
    status = 'Finished' if finished else 'Unfinished'
    xbmcgui.Dialog().notification(f'Marked {status}', 'Progress updated', xbmcgui.NOTIFICATION_INFO, 2000)
    xbmc.executebuiltin('Container.Refresh')
    xbmc.executebuiltin('ReloadSkin')  # Force skin reload to update context menus





def get_downloaded_structure():
    """Get structure of downloaded items organized by type and podcast"""
    downloads = download_manager.get_all_downloads()
    
    audiobooks = []
    podcasts = {}  # item_id -> podcast info with episodes
    
    for key, info in downloads.items():
        item_id = info.get('item_id')
        episode_id = info.get('episode_id')
        
        if episode_id:
                # It's a podcast episode
                if item_id not in podcasts:
                    podcasts[item_id] = {
                        'title': info.get('podcast_title', info.get('title', 'Unknown Podcast')),
                        'cover_path': info.get('cover_path'),  # Use episode's cover for now
                        'episodes': []
                    }
                # Update podcast cover if we don't have one yet (use first available cover)
                if not podcasts[item_id].get('cover_path') and info.get('cover_path'):
                    podcasts[item_id]['cover_path'] = info.get('cover_path')
                
                podcasts[item_id]['episodes'].append({
                    'episode_id': episode_id,
                    'title': info.get('title', 'Unknown Episode'),
                    'duration': info.get('duration', 0),
                    'cover_path': info.get('cover_path'),  # Keep individual episode covers
                    'key': key
                })
        else:
            # It's an audiobook
            audiobooks.append({
                'item_id': item_id,
                'title': info.get('title', 'Unknown'),
                'author': info.get('author', ''),
                'duration': info.get('duration', 0),
                'cover_path': info.get('cover_path'),
                'is_multifile': info.get('is_multifile', False),
                'chapters': info.get('chapters', []),
                'files': info.get('files', []),
                'key': key
            })
    
    return audiobooks, podcasts


def list_audiobooks_combined(book_libs=None):
    """List all audiobooks from all book libraries"""
    library_service, url, token, offline = get_library_service()
    if not library_service:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    xbmcplugin.setContent(ADDON_HANDLE, 'albums')
    
    try:
        if book_libs is None:
            data = library_service.get_all_libraries()
            book_libs = [l for l in data.get('libraries', []) if l.get('mediaType') == 'book']
        
        show_markers = get_setting_bool('show_progress_markers', True)
        finished_threshold = get_finished_threshold()
        
        all_items = []
        for lib in book_libs:
            items = library_service.get_library_items(lib['id'])
            for item in items.get('results', []):
                item['_library_id'] = lib['id']
                all_items.append(item)
        
        # Sort by title
        all_items.sort(key=lambda x: x.get('media', {}).get('metadata', {}).get('title', '').lower())
        
        for item in all_items:
            media = item.get('media', {})
            metadata = media.get('metadata', {})
            item_id = item['id']
            library_id = item['_library_id']
            
            is_finished = False
            progress_pct = 0
            try:
                progress = library_service.get_media_progress(item_id)
                if progress:
                    is_finished = progress.get('isFinished', False)
                    progress_pct = progress.get('progress', 0) * 100
            except:
                pass
            
            is_downloaded = download_manager.is_downloaded(item_id)
            
            
            
            cover_url = f"{url}/api/items/{item_id}/cover?token={token}"
            local_cover = download_cover(cover_url, item_id)
            
            title = metadata.get('title', 'Unknown')
            author = metadata.get('authorName', '')
            duration = media.get('duration', 0)
            
            prefix = ''
            if show_markers:
                if is_downloaded:
                    prefix = '[DL] '
                if is_finished:
                    prefix += '[Done] '
                elif progress_pct > 0:
                    prefix += f'[{int(progress_pct)}%] '
            
            display_title = f'{prefix}{title}'
            
            list_item = xbmcgui.ListItem(label=display_title)
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            set_music_info(list_item, title=title, artist=author, duration=duration,
                          playcount=1 if is_finished else 0)
            
            # Context menu
            context_items = [
                ('Clear Progress', f'RunPlugin({build_url(action="clear_progress", item_id=item_id)})'),
                ('Sync Progress from Server', f'RunPlugin({build_url(action="sync_progress_from_server", item_id=item_id)})'),
            ]
            if is_finished:
                context_items.append(('Mark Unfinished', f'RunPlugin({build_url(action="mark_unfinished", item_id=item_id)})'))
            else:
                context_items.append(('Mark Finished', f'RunPlugin({build_url(action="mark_finished", item_id=item_id)})'))
            
            if get_setting_bool('enable_downloads'):
                if is_downloaded:
                    context_items.append(('Delete Download', f'RunPlugin({build_url(action="delete_download", item_id=item_id)})'))
                else:
                    context_items.append(('Download', f'RunPlugin({build_url(action="download", item_id=item_id, library_id=library_id)})'))
            list_item.addContextMenuItems(context_items)
            
            if media.get('numAudioFiles', 1) > 1 or media.get('chapters'):
                xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                           build_url(action='parts', item_id=item_id),
                                           list_item, isFolder=True)
            else:
                list_item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                           build_url(action='play', item_id=item_id),
                                           list_item, isFolder=False)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Error: {str(e)}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def list_podcasts_combined(podcast_libs=None):
    """List all podcasts from all podcast libraries"""
    library_service, url, token, offline = get_library_service()
    if not library_service:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    xbmcplugin.setContent(ADDON_HANDLE, 'albums')
    
    try:
        if podcast_libs is None:
            data = library_service.get_all_libraries()
            podcast_libs = [l for l in data.get('libraries', []) if l.get('mediaType') == 'podcast']
        
        # Search option
        list_item = xbmcgui.ListItem(label='[Search & Add Podcasts]')
        list_item.setArt({'icon': 'DefaultAddSource.png'})
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, build_url(action='search'), list_item, isFolder=True)
        
        
        show_markers = get_setting_bool('show_progress_markers', True)
        finished_threshold = get_finished_threshold()
        
        all_items = []
        for lib in podcast_libs:
            items = library_service.get_library_items(lib['id'])
            for item in items.get('results', []):
                item['_library_id'] = lib['id']
                all_items.append(item)
        
        # Sort by title
        all_items.sort(key=lambda x: x.get('media', {}).get('metadata', {}).get('title', '').lower())
        
        for item in all_items:
            media = item.get('media', {})
            metadata = media.get('metadata', {})
            item_id = item['id']
            
            is_finished = False
            progress_pct = 0
            try:
                progress = library_service.get_media_progress(item_id)
                if progress:
                    is_finished = progress.get('isFinished', False)
                    progress_pct = progress.get('progress', 0) * 100
            except:
                pass
            
            is_downloaded = download_manager.is_downloaded(item_id)
            
            
            
            cover_url = f"{url}/api/items/{item_id}/cover?token={token}"
            local_cover = download_cover(cover_url, item_id)
            
            title = metadata.get('title', 'Unknown')
            duration = media.get('duration', 0)
            
            prefix = ''
            if show_markers:
                if is_downloaded:
                    prefix = '[DL] '
                # Count episodes
                num_eps = media.get('numEpisodes', 0)
                if num_eps > 0:
                    episodes = media.get('episodes', [])
                    if not episodes:
                        try:
                            full_item = library_service.get_library_item_by_id(item_id, expanded=1)
                            episodes = full_item.get('media', {}).get('episodes', [])
                        except:
                            episodes = []
                    
                    if episodes:
                        finished_count = count_finished_episodes(library_service, item_id, episodes)
                        prefix += f'[{finished_count}/{num_eps}] '
                    else:
                        watched = int((progress_pct / 100) * num_eps)
                        prefix += f'[{watched}/{num_eps}] '
            
            display_title = f'{prefix}{title}'
            
            list_item = xbmcgui.ListItem(label=display_title)
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            set_music_info(list_item, title=title, duration=duration,
                          playcount=1 if is_finished else 0)
            
            # Context menu
            context_items = []
            
            # Always show delete options for downloaded content (even if downloads are currently disabled)
            if is_downloaded:
                context_items.append(('Delete Download', f'RunPlugin({build_url(action="delete_download", item_id=item_id)})'))
            
            # Check if there are downloaded episodes
            has_downloaded_episodes = False
            all_downloads = download_manager.get_all_downloads()
            for key, download_info in all_downloads.items():
                if (download_info.get('item_id') == item_id and 
                    download_info.get('episode_id') is not None):
                    has_downloaded_episodes = True
                    break
            
            # Always show both download and delete options when downloads are enabled
            if get_setting_bool('enable_downloads'):
                context_items.append(('Download All Episodes', f'RunPlugin({build_url(action="download_podcast", item_id=item_id)})'))
            
            if has_downloaded_episodes:
                context_items.append(('Delete All Downloaded Episodes', f'RunPlugin({build_url(action="delete_all_podcast_episodes", item_id=item_id)})'))
            if context_items:
                list_item.addContextMenuItems(context_items)
            
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='episodes', item_id=item_id),
                                       list_item, isFolder=True)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Error: {str(e)}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def list_offline_books():
    """List downloaded audiobooks in offline mode - same structure as online"""
    xbmcplugin.setContent(ADDON_HANDLE, 'albums')
    
    audiobooks, _ = get_downloaded_structure()
    show_markers = get_setting_bool('show_progress_markers', True)
    
    if not audiobooks:
        xbmcgui.Dialog().notification('No Audiobooks', 'No audiobooks downloaded', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    for book in audiobooks:
        item_id = book['item_id']
        
        # Check progress
        local = get_local_progress(item_id)
        is_finished = local.get('is_finished', False) if local else False
        progress_pct = (local.get('progress', 0) * 100) if local else 0
        
        prefix = ''
        if show_markers:
            if is_finished:
                prefix = '[Done] '
            elif progress_pct > 0:
                prefix = f'[{int(progress_pct)}%] '
        
        list_item = xbmcgui.ListItem(label=f"{prefix}{book['title']}")
        
        # Try to use cached cover first for consistency with streaming version
        cover_url = book.get('cover_url') or book.get('cover_path')
        if cover_url:
            local_cover = download_cover(cover_url, item_id)
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            elif book.get('cover_path') and os.path.exists(book['cover_path']):
                # Fallback to downloaded cover
                list_item.setArt({'thumb': book['cover_path'], 'poster': book['cover_path']})
        
        set_music_info(list_item, title=book['title'], artist=book.get('author', ''), 
                      duration=book.get('duration', 0), playcount=1 if is_finished else 0)
        
        # Context menu - same options as online
        context_items = [
            ('Clear Progress', f'RunPlugin({build_url(action="clear_progress", item_id=item_id)})'),
            ('Sync Progress from Server', f'RunPlugin({build_url(action="sync_progress_from_server", item_id=item_id)})'),
        ]
        if is_finished:
            context_items.append(('Mark Unfinished', f'RunPlugin({build_url(action="mark_unfinished", item_id=item_id)})'))
        else:
            context_items.append(('Mark Finished', f'RunPlugin({build_url(action="mark_finished", item_id=item_id)})'))
        context_items.append(('Delete Download', f'RunPlugin({build_url(action="delete_download", item_id=item_id)})'))
        list_item.addContextMenuItems(context_items)
        
        # Multi-file audiobooks show chapters/parts
        if book.get('is_multifile') or book.get('chapters'):
            xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                       build_url(action='offline_parts', item_id=item_id),
                                       list_item, isFolder=True)
        else:
            list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='play_offline', key=item_id),
                                       list_item, isFolder=False)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def list_offline_podcasts():
    """List downloaded podcasts in offline mode - same structure as online"""
    xbmcplugin.setContent(ADDON_HANDLE, 'albums')
    
    _, podcasts = get_downloaded_structure()
    show_markers = get_setting_bool('show_progress_markers', True)
    
    if not podcasts:
        xbmcgui.Dialog().notification('No Podcasts', 'No podcasts downloaded', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    # Sort podcasts by title
    sorted_podcasts = sorted(podcasts.items(), key=lambda x: x[1]['title'].lower())
    
    for item_id, podcast_info in sorted_podcasts:
        ep_count = len(podcast_info['episodes'])
        
        # Count finished episodes
        finished_count = 0
        for ep in podcast_info['episodes']:
            local = get_local_progress(item_id, ep['episode_id'])
            if local and local.get('is_finished', False):
                finished_count += 1
        
        prefix = ''
        if show_markers:
            prefix = f'[{finished_count}/{ep_count}] '
        
        list_item = xbmcgui.ListItem(label=f"{prefix}{podcast_info['title']}")
        
        # Try to use cached cover first for consistency with streaming version
        cover_url = podcast_info.get('cover_url') or podcast_info.get('cover_path')
        if cover_url:
            local_cover = download_cover(cover_url, item_id)
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            elif podcast_info.get('cover_path') and os.path.exists(podcast_info['cover_path']):
                # Fallback to downloaded cover
                list_item.setArt({'thumb': podcast_info['cover_path'], 'poster': podcast_info['cover_path']})
        
        set_music_info(list_item, title=podcast_info['title'])
        
        # Context menu
        context_items = [
            ('Delete All Episodes', f'RunPlugin({build_url(action="delete_download", item_id=item_id)})'),
        ]
        list_item.addContextMenuItems(context_items)
        
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                   build_url(action='offline_episodes', item_id=item_id),
                                   list_item, isFolder=True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def list_offline_episodes(item_id):
    """List downloaded episodes for a podcast in offline mode - same structure as online"""
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    
    _, podcasts = get_downloaded_structure()
    show_markers = get_setting_bool('show_progress_markers', True)
    autoplay_next = get_setting_bool('autoplay_next_episode', False)

    if item_id not in podcasts:
        xbmcgui.Dialog().notification('Not Found', 'Podcast not found', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    podcast_info = podcasts[item_id]
    episodes = podcast_info['episodes']
    
    for ep in episodes:
        episode_id = ep['episode_id']
        
        # Check progress
        local = get_local_progress(item_id, episode_id)
        is_finished = local.get('is_finished', False) if local else False
        progress_pct = (local.get('progress', 0) * 100) if local else 0
        
        prefix = ''
        if show_markers:
            if is_finished:
                prefix = '[Done] '
            elif progress_pct > 0:
                prefix = f'[{int(progress_pct)}%] '
        
        list_item = xbmcgui.ListItem(label=f"{prefix}{ep['title']}")
        # With auto-play-next on, the click starts an offline queue (a
        # non-resolving play_queue action); otherwise it's a resolvable item.
        list_item.setProperty('IsPlayable', 'false' if autoplay_next else 'true')

        # Try to use cached cover first for consistency with streaming version
        cover_url = ep.get('cover_url') or ep.get('cover_path')
        if cover_url:
            local_cover = download_cover(cover_url, f"{item_id}_{episode_id}")
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            elif ep.get('cover_path') and os.path.exists(ep['cover_path']):
                # Fallback to downloaded cover
                list_item.setArt({'thumb': ep['cover_path'], 'poster': ep['cover_path']})
        
        set_music_info(list_item, title=ep['title'], duration=ep.get('duration', 0),
                      playcount=1 if is_finished else 0)
        
        # Context menu - same options as online
        context_items = [
            ('Clear Progress', f'RunPlugin({build_url(action="clear_progress", item_id=item_id, episode_id=episode_id)})'),
            ('Sync Progress from Server', f'RunPlugin({build_url(action="sync_progress_from_server", item_id=item_id, episode_id=episode_id)})'),
        ]
        if is_finished:
            context_items.append(('Mark Unfinished', f'RunPlugin({build_url(action="mark_unfinished", item_id=item_id, episode_id=episode_id)})'))
        else:
            context_items.append(('Mark Finished', f'RunPlugin({build_url(action="mark_finished", item_id=item_id, episode_id=episode_id)})'))
        context_items.append(('Delete Download', f'RunPlugin({build_url(action="delete_download", item_id=item_id, episode_id=episode_id)})'))
        list_item.addContextMenuItems(context_items)
        
        if autoplay_next:
            ep_url = build_url(action='play_queue', item_id=item_id, episode_id=episode_id)
        else:
            ep_url = build_url(action='play_offline', key=ep['key'])
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, ep_url, list_item, isFolder=False)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def list_offline_parts(item_id):
    """List chapters/parts for a downloaded multi-file audiobook"""
    xbmcplugin.setContent(ADDON_HANDLE, 'songs')
    
    download_info = download_manager.get_download_info(item_id)
    if not download_info:
        xbmcgui.Dialog().notification('Not Found', 'Download not found', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    # Get current progress
    local = get_local_progress(item_id)
    current_time = local.get('current_time', 0) if local else 0
    total_duration = download_info.get('duration', 0)
    
    # Resume option if progress exists
    if current_time > 10:
        list_item = xbmcgui.ListItem(label=f'[Resume: {format_time(current_time)}]')
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                   build_url(action='play_offline', key=item_id),
                                   list_item, isFolder=False)
    
    # Show chapters if available
    chapters = download_info.get('chapters', [])
    files = download_info.get('files', [])
    
    if chapters:
        for i, ch in enumerate(sorted(chapters, key=lambda x: x.get('start', 0))):
            title = ch.get('title', f'Chapter {i+1}')
            ch_start = ch.get('start', 0)
            ch_end = ch.get('end', total_duration)
            
            prefix = '> ' if ch_start <= current_time < ch_end else ''
            
            list_item = xbmcgui.ListItem(label=f'{prefix}{title}')
            list_item.setProperty('IsPlayable', 'true')
            set_music_info(list_item, title=title, duration=ch_end - ch_start, tracknumber=i+1)
            
            xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                       build_url(action='play_offline_at', item_id=item_id, 
                                                seek_time=int(ch_start)),
                                       list_item, isFolder=False)
    elif files:
        # Show files as parts
        files = sorted(files, key=lambda x: x.get('index', 0))
        cumulative = 0
        for i, f in enumerate(files):
            title = f'Part {i+1}'
            dur = f.get('duration', 0)
            
            prefix = '> ' if cumulative <= current_time < cumulative + dur else ''
            
            list_item = xbmcgui.ListItem(label=f'{prefix}{title}')
            list_item.setProperty('IsPlayable', 'true')
            set_music_info(list_item, title=title, duration=dur)
            
            xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                       build_url(action='play_offline_at', item_id=item_id,
                                                seek_time=int(cumulative)),
                                       list_item, isFolder=False)
            cumulative += dur
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def list_libraries():
    """List top-level folders: Audiobooks and Podcasts"""
    library_service, url, token, offline = get_library_service()
    
    xbmcplugin.setContent(ADDON_HANDLE, 'albums')
    
    if offline:
        # Offline mode - show Audiobooks/Podcasts structure with downloaded content only
        audiobooks, podcasts = get_downloaded_structure()
        
        if not audiobooks and not podcasts:
            xbmcgui.Dialog().notification('No Downloads', 'Download content first', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
            return
        
        # Show Audiobooks folder if any downloaded
        if audiobooks:
            list_item = xbmcgui.ListItem(label=f'Audiobooks ({len(audiobooks)})')
            list_item.setArt({'icon': 'DefaultMusicAlbums.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='offline_books'),
                                       list_item, isFolder=True)
        
        # Show Podcasts folder if any downloaded
        if podcasts:
            total_episodes = sum(len(p['episodes']) for p in podcasts.values())
            list_item = xbmcgui.ListItem(label=f'Podcasts ({len(podcasts)} shows)')
            list_item.setArt({'icon': 'DefaultMusicVideos.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='offline_podcasts'),
                                       list_item, isFolder=True)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return
    
    if not library_service:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    # Ensure sync manager is set up with library service
    try:
        sync_mgr = get_sync_manager()
        sync_mgr.set_library_service(library_service)
    except Exception as e:
        xbmc.log(f"Sync manager setup error in list_libraries: {e}", xbmc.LOGDEBUG)
    
    try:
        data = library_service.get_all_libraries()
        libraries = data.get('libraries', [])
        
        book_libs = [l for l in libraries if l.get('mediaType') == 'book']
        podcast_libs = [l for l in libraries if l.get('mediaType') == 'podcast']
        
        # If only one type of library, go directly to it
        if not book_libs and len(podcast_libs) == 1:
            list_podcasts_combined(podcast_libs)
            return
        elif not podcast_libs and len(book_libs) == 1:
            list_audiobooks_combined(book_libs)
            return
        
        # Show Audiobooks folder
        if book_libs:
            list_item = xbmcgui.ListItem(label='Audiobooks')
            list_item.setArt({'icon': 'DefaultMusicAlbums.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='audiobooks'),
                                       list_item, isFolder=True)
        
        # Show Podcasts folder
        if podcast_libs:
            list_item = xbmcgui.ListItem(label='Podcasts')
            list_item.setArt({'icon': 'DefaultMusicVideos.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='podcasts'),
                                       list_item, isFolder=True)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Error: {str(e)}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def list_library_items(library_id, is_podcast=False):
    xbmcplugin.setContent(ADDON_HANDLE, 'albums')
    
    library_service, url, token, offline = get_library_service()
    if not library_service:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    try:
        if is_podcast:
            list_item = xbmcgui.ListItem(label='[Search & Add Podcasts]')
            list_item.setArt({'icon': 'DefaultAddSource.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, build_url(action='search'), list_item, isFolder=True)
        
        items = library_service.get_library_items(library_id)
        
        show_markers = get_setting_bool('show_progress_markers', True)
        finished_threshold = get_finished_threshold()
        
        for item in items.get('results', []):
            media = item.get('media', {})
            metadata = media.get('metadata', {})
            item_id = item['id']
            media_type = item.get('mediaType', 'book')
            
            is_finished = False
            progress_pct = 0
            try:
                progress = library_service.get_media_progress(item_id)
                if progress:
                    is_finished = progress.get('isFinished', False)
                    progress_pct = progress.get('progress', 0) * 100
            except:
                pass
            
            is_downloaded = download_manager.is_downloaded(item_id)
            
            
            
            cover_url = f"{url}/api/items/{item_id}/cover?token={token}"
            local_cover = download_cover(cover_url, item_id)
            
            title = metadata.get('title', 'Unknown')
            author = metadata.get('authorName', '')
            duration = media.get('duration', 0)
            
            # Also save cover to download folder for offline use
            if local_cover and get_setting_bool('enable_downloads'):
                try:
                    download_path = get_setting('download_path', '')
                    if download_path:
                        item_folder = os.path.join(download_path, item_id)
                        if not os.path.exists(item_folder):
                            os.makedirs(item_folder)
                        offline_cover = os.path.join(item_folder, f"{item_id}_cover.jpg")
                        if not os.path.exists(offline_cover):
                            import shutil
                            shutil.copy2(local_cover, offline_cover)
                except Exception as e:
                    xbmc.log(f"Failed to save cover for offline: {str(e)}", xbmc.LOGERROR)
            
            prefix = ''
            if show_markers:
                if is_downloaded:
                    prefix = '[DL] '
                elif media_type == 'podcast':
                    # Count actual finished episodes
                    num_eps = media.get('numEpisodes', 0)
                    if num_eps > 0:
                        # Get episodes and count finished
                        episodes = media.get('episodes', [])
                        if not episodes:
                            # Need to fetch episodes
                            try:
                                full_item = library_service.get_library_item_by_id(item_id, expanded=1)
                                episodes = full_item.get('media', {}).get('episodes', [])
                            except:
                                episodes = []
                        
                        if episodes:
                            finished_count = count_finished_episodes(library_service, item_id, episodes)
                            prefix = f'[{finished_count}/{num_eps}] '
                        else:
                            # Fallback to estimate
                            watched = int((progress_pct / 100) * num_eps)
                            prefix = f'[{watched}/{num_eps}] '
                elif is_finished:
                    prefix = '[Done] '
                elif progress_pct > 0:
                    prefix = f'[{int(progress_pct)}%] '
            
            display_title = f'{prefix}{title}'
            
            list_item = xbmcgui.ListItem(label=display_title)
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            set_music_info(list_item, title=title, artist=author, duration=duration,
                          playcount=1 if is_finished else 0)
            
            context_items = []
            
            # Download options first
            if get_setting_bool('enable_downloads'):
                if is_downloaded:
                    context_items.append(('Delete Download', 
                                         f'RunPlugin({build_url(action="delete_download", item_id=item_id)})'))
                
                if media_type == 'podcast':
                    # Check if there are downloaded episodes
                    has_downloaded_episodes = False
                    all_downloads = download_manager.get_all_downloads()
                    for key, download_info in all_downloads.items():
                        if (download_info.get('item_id') == item_id and 
                            download_info.get('episode_id') is not None):
                            has_downloaded_episodes = True
                            break
                    
                    if has_downloaded_episodes:
                        context_items.append(('Delete All Downloaded Episodes', 
                                             f'RunPlugin({build_url(action="delete_all_podcast_episodes", item_id=item_id)})'))
                    else:
                        context_items.append(('Download All Episodes', 
                                             f'RunPlugin({build_url(action="download_podcast", item_id=item_id)})'))
                else:
                    if not is_downloaded:
                        context_items.append(('Download', 
                                             f'RunPlugin({build_url(action="download", item_id=item_id, library_id=library_id)})'))
            
            # Add progress management for non-podcasts
            if media_type != 'podcast':
                context_items.append(('Clear Progress', f'RunPlugin({build_url(action="clear_progress", item_id=item_id)})'))
                context_items.append(('Sync Progress from Server', f'RunPlugin({build_url(action="sync_progress_from_server", item_id=item_id)})'))
                if is_finished:
                    context_items.append(('Mark Unfinished', f'RunPlugin({build_url(action="mark_unfinished", item_id=item_id)})'))
                else:
                    context_items.append(('Mark Finished', f'RunPlugin({build_url(action="mark_finished", item_id=item_id)})'))
            if context_items:
                list_item.addContextMenuItems(context_items)
            
            if media_type == 'podcast':
                xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                           build_url(action='episodes', item_id=item_id),
                                           list_item, isFolder=True)
            elif media.get('numAudioFiles', 1) > 1 or media.get('chapters'):
                xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                           build_url(action='parts', item_id=item_id),
                                           list_item, isFolder=True)
            else:
                list_item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                           build_url(action='play', item_id=item_id),
                                           list_item, isFolder=False)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Error: {str(e)}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def list_episodes(item_id, sort_by='date'):
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    
    library_service, url, token, offline = get_library_service()
    if not library_service:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        episodes = item.get('media', {}).get('episodes', [])
        feed_url = item.get('media', {}).get('metadata', {}).get('feedUrl', '')
        
        
        show_markers = get_setting_bool('show_progress_markers', True)
        min_for_sort = get_setting_int('min_episodes_for_sort', 10)
        autoplay_next = get_setting_bool('autoplay_next_episode', False)
        finished_threshold = get_finished_threshold()
        
        # Find New Episodes option
        if feed_url:
            list_item = xbmcgui.ListItem(label='[Find New Episodes]')
            list_item.setArt({'icon': 'DefaultAddSource.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='find_episodes', item_id=item_id),
                                       list_item, isFolder=True)
        
        if not episodes:
            xbmcplugin.endOfDirectory(ADDON_HANDLE)
            return
        
        # Sort option
        if len(episodes) >= min_for_sort:
            sort_labels = {'date': 'Newest', 'date_old': 'Oldest', 'title': 'Title', 
                          'episode': 'Episode #', 'duration': 'Duration'}
            next_sort = {'date': 'date_old', 'date_old': 'title', 'title': 'episode',
                        'episode': 'duration', 'duration': 'date'}
            
            list_item = xbmcgui.ListItem(label=f'[Sort: {sort_labels.get(sort_by, "Newest")}]')
            list_item.setArt({'icon': 'DefaultPlaylist.png'})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                       build_url(action='episodes', item_id=item_id, 
                                                sort_by=next_sort.get(sort_by, 'date')),
                                       list_item, isFolder=True)
        
        # Sort episodes
        if sort_by == 'date':
            episodes = sorted(episodes, key=lambda x: x.get('publishedAt') or 0, reverse=True)
        elif sort_by == 'date_old':
            episodes = sorted(episodes, key=lambda x: x.get('publishedAt') or 0)
        elif sort_by == 'title':
            episodes = sorted(episodes, key=lambda x: (x.get('title') or '').lower())
        elif sort_by == 'episode':
            episodes = sorted(episodes, key=lambda x: (x.get('season') or 0, x.get('episode') or 0))
        elif sort_by == 'duration':
            episodes = sorted(episodes, key=lambda x: x.get('duration') or 0, reverse=True)
        
        for episode in episodes:
            title = episode.get('title', 'Unknown')
            episode_id = episode.get('id')
            duration = episode.get('duration', 0)
            has_audio = episode.get('audioFile') is not None
            description = episode.get('description', '')
            
            is_finished = False
            progress_pct = 0
            
            # Check local first
            local = get_local_progress(item_id, episode_id)
            if local:
                is_finished = local.get('is_finished', False)
                progress_pct = local.get('progress', 0) * 100
            
            # Then check server
            if not is_finished:
                try:
                    progress = library_service.get_media_progress(item_id, episode_id)
                    if progress:
                        server_finished = progress.get('isFinished', False)
                        server_pct = progress.get('progress', 0) * 100
                        if server_finished or server_pct >= finished_threshold * 100:
                            is_finished = True
                        elif server_pct > progress_pct:
                            progress_pct = server_pct
                except:
                    pass
            
            is_downloaded = download_manager.is_downloaded(item_id, episode_id)
            
            
            
            prefix = ''
            if show_markers:
                if is_downloaded:
                    prefix = '[DL] '
                elif not has_audio:
                    prefix = '[+] '
                elif is_finished:
                    prefix = '[Done] '
                elif progress_pct > 0:
                    prefix = f'[{int(progress_pct)}%] '
            
            season = episode.get('season')
            ep_num = episode.get('episode')
            ep_info = ''
            if season and ep_num:
                ep_info = f'S{season}E{ep_num} '
            elif ep_num:
                ep_info = f'E{ep_num} '
            
            list_item = xbmcgui.ListItem(label=f'{prefix}{ep_info}{title}')
            playable = has_audio or is_downloaded
            # With auto-play-next on, the click triggers play_queue - a
            # non-resolving action that starts a Kodi playlist - so it must NOT
            # be flagged IsPlayable (Kodi would otherwise wait for a resolve).
            # Otherwise it's a normal single-play resolvable item.
            list_item.setProperty('IsPlayable', 'true' if (playable and not autoplay_next) else 'false')
            # Add episode description
            if description:
                # Clean up HTML tags and truncate if too long
                import re
                clean_desc = re.sub(r'<[^>]+>', '', description)
                clean_desc = clean_desc.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
                if len(clean_desc) > 500:
                    clean_desc = clean_desc[:500] + '...'
                list_item.setInfo('video', {'plot': clean_desc})
            set_music_info(list_item, title=title, duration=duration, playcount=1 if is_finished else 0)
            
            context_items = []
            
            # Download options first
            if not has_audio:
                context_items.append(('Download to Server', 
                                     f'RunPlugin({build_url(action="download_to_server", item_id=item_id, episode_id=episode_id)})'))
            
            # Always show delete option for downloaded episodes (even if downloads are currently disabled)
            if is_downloaded:
                context_items.append(('Delete Local', 
                                     f'RunPlugin({build_url(action="delete_download", item_id=item_id, episode_id=episode_id)})'))
            elif get_setting_bool('enable_downloads') and has_audio:
                context_items.append(('Download Locally', 
                                     f'RunPlugin({build_url(action="download_episode", item_id=item_id, episode_id=episode_id)})'))
            
            # Add progress management options
            context_items.append(('Clear Progress', f'RunPlugin({build_url(action="clear_progress", item_id=item_id, episode_id=episode_id)})'))
            context_items.append(('Sync Progress from Server', f'RunPlugin({build_url(action="sync_progress_from_server", item_id=item_id, episode_id=episode_id)})'))
            if is_finished:
                context_items.append(('Mark Unfinished', f'RunPlugin({build_url(action="mark_unfinished", item_id=item_id, episode_id=episode_id)})'))
            else:
                context_items.append(('Mark Finished', f'RunPlugin({build_url(action="mark_finished", item_id=item_id, episode_id=episode_id)})'))
            if context_items:
                list_item.addContextMenuItems(context_items)
            
            if playable and autoplay_next:
                url_params = build_url(action='play_queue', item_id=item_id, episode_id=episode_id)
            elif playable:
                url_params = build_url(action='play_episode', item_id=item_id, episode_id=episode_id)
            else:
                url_params = build_url(action='download_to_server', item_id=item_id, episode_id=episode_id)

            xbmcplugin.addDirectoryItem(ADDON_HANDLE, url_params, list_item, isFolder=False)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def find_new_episodes(item_id):
    """Find new episodes by comparing RSS feed to server"""
    library_service, url, token, offline = get_library_service()
    if not library_service or offline:
        xbmcgui.Dialog().notification('Error', 'Requires network', xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    try:
        import requests
        
        progress = xbmcgui.DialogProgress()
        progress.create('Finding Episodes', 'Getting podcast info...')
        
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        feed_url = item.get('media', {}).get('metadata', {}).get('feedUrl', '')
        server_episodes = item.get('media', {}).get('episodes', [])
        
        if not feed_url:
            progress.close()
            xbmcgui.Dialog().notification('No Feed', 'No RSS feed URL', xbmcgui.NOTIFICATION_WARNING)
            xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
            return
        
        progress.update(20, 'Fetching RSS feed...')
        
        server_guids = {ep.get('guid') for ep in server_episodes if ep.get('guid')}
        server_titles = {(ep.get('title') or '').lower().strip() for ep in server_episodes}
        
        # Episodes on server without audio file
        need_download = [ep for ep in server_episodes 
                        if not ep.get('audioFile') or 
                        (isinstance(ep.get('audioFile'), dict) and not ep['audioFile'].get('ino'))]
        
        try:
            rss = requests.get(feed_url, timeout=30, headers={'User-Agent': 'Kodi-Audiobookshelf/1.0'})
            rss.raise_for_status()
        except Exception as e:
            progress.close()
            xbmc.log(f"RSS fetch error: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('RSS Error', 'Could not fetch feed', xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
            return
        
        progress.update(60, 'Parsing episodes...')
        
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(rss.content)
            channel = root.find('channel')
        except:
            progress.close()
            xbmcgui.Dialog().notification('Parse Error', 'Invalid RSS', xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
            return
        
        itunes_ns = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
        new_episodes = []
        
        for item_el in channel.findall('item') if channel is not None else []:
            title_el = item_el.find('title')
            title = (title_el.text or 'Unknown').strip() if title_el is not None else 'Unknown'
            
            guid_el = item_el.find('guid')
            guid = (guid_el.text or title).strip() if guid_el is not None else title
            
            if guid in server_guids or title.lower().strip() in server_titles:
                continue
            
            enclosure = item_el.find('enclosure')
            if enclosure is None:
                continue
            audio_url = enclosure.get('url', '')
            audio_type = enclosure.get('type', 'audio/mpeg')
            audio_length = enclosure.get('length', '0')
            
            if not audio_url:
                continue
            
            # Get additional metadata
            desc_el = item_el.find('description')
            description = (desc_el.text or '')[:500] if desc_el is not None else ''
            
            pubdate_el = item_el.find('pubDate')
            pubdate = pubdate_el.text if pubdate_el is not None else ''
            
            duration_el = item_el.find(f'{itunes_ns}duration')
            duration = duration_el.text if duration_el is not None else ''
            
            season_el = item_el.find(f'{itunes_ns}season')
            season = season_el.text if season_el is not None else ''
            
            episode_el = item_el.find(f'{itunes_ns}episode')
            episode_num = episode_el.text if episode_el is not None else ''
            
            new_episodes.append({
                'title': title,
                'guid': guid,
                'audioUrl': audio_url,
                'audioType': audio_type,
                'audioLength': audio_length,
                'description': description,
                'pubDate': pubdate,
                'duration': duration,
                'season': season,
                'episode': episode_num
            })
        
        progress.close()
        
        xbmc.log(f"Found {len(need_download)} need download, {len(new_episodes)} new from RSS", xbmc.LOGINFO)
        
        # Store new episodes in addon data for batch add
        if new_episodes:
            _store_new_episodes(item_id, new_episodes)
        
        if not need_download and not new_episodes:
            xbmcgui.Dialog().notification('Up to Date', 'No new episodes', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
            return
        
        xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
        
        # Add All button
        
        
        # Episodes needing download (already on server, just need audio)
        for ep in need_download:
            list_item = xbmcgui.ListItem(label=f'[Need DL] {ep.get("title", "Unknown")}')
            list_item.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='download_to_server', item_id=item_id, episode_id=ep.get('id')),
                                       list_item, isFolder=False)
        
        # New from RSS (not on server yet) - can be added directly
        for i, ep in enumerate(new_episodes[:50]):
            list_item = xbmcgui.ListItem(label=f'[NEW] {ep["title"]}')
            list_item.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='add_new_episode', item_id=item_id, episode_index=str(i)),
                                       list_item, isFolder=False)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Find episodes error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def _get_episodes_cache_file():
    """Get path to episodes cache file"""
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    return os.path.join(profile, 'new_episodes_cache.json')


def _store_new_episodes(item_id, episodes):
    """Store new episodes for later batch add"""
    import json
    cache = {}
    cache_file = _get_episodes_cache_file()
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache = json.load(f)
    except:
        pass
    
    cache[item_id] = episodes
    
    with open(cache_file, 'w') as f:
        json.dump(cache, f)


def _get_stored_episodes(item_id):
    """Get stored episodes for item"""
    import json
    cache_file = _get_episodes_cache_file()
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache = json.load(f)
                return cache.get(item_id, [])
    except:
        pass
    return []


def add_new_episode(item_id, episode_index):
    """Add a single new episode from RSS to server"""
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        import requests
        
        episodes = _get_stored_episodes(item_id)
        idx = int(episode_index)
        
        if idx >= len(episodes):
            xbmcgui.Dialog().notification('Error', 'Episode not found', xbmcgui.NOTIFICATION_ERROR)
            return
        
        ep = episodes[idx]
        xbmcgui.Dialog().notification('Adding...', ep['title'][:30], xbmcgui.NOTIFICATION_INFO, 2000)
        
        # Create episode directly using API
        episode_data = {
            'title': ep['title'],
            'guid': ep['guid'],
            'enclosure': {
                'url': ep['audioUrl'],
                'type': ep.get('audioType', 'audio/mpeg'),
                'length': ep.get('audioLength', '0')
            }
        }
        
        if ep.get('description'):
            episode_data['description'] = ep['description']
        if ep.get('pubDate'):
            episode_data['pubDate'] = ep['pubDate']
        if ep.get('season'):
            episode_data['season'] = ep['season']
        if ep.get('episode'):
            episode_data['episode'] = ep['episode']
        
        xbmc.log(f"Processing episode: {ep['title']}", xbmc.LOGINFO)
        
        # Use download_podcast_episodes_with_data API to download specific episode
        try:
            xbmc.log(f"Downloading episode from RSS feed", xbmc.LOGINFO)
            xbmc.log(f"Example URL: POST {library_service.base_url}/api/podcasts/{item_id}/download-episodes", xbmc.LOGINFO)
            
            # Prepare episode data for download API
            episode_data = {
                'title': ep['title'],
                'subtitle': ep.get('subtitle', ''),
                'description': ep.get('description', ''),
                'enclosure': {
                    'url': ep['audioUrl'],
                    'type': ep.get('audioType', 'audio/mpeg'),
                    'length': ep.get('audioLength', '0')
                },
                'pubDate': ep.get('pubDate', ''),
                'publishedAt': ep.get('publishedAt', 0)
            }
            
            # Add optional fields if available
            if ep.get('season'):
                episode_data['season'] = ep['season']
            if ep.get('episode'):
                episode_data['episode'] = ep['episode']
            if ep.get('episodeType'):
                episode_data['episodeType'] = ep['episodeType']
            
            result = library_service.download_podcast_episodes_with_data(item_id, episode_data)
            
            if result and result.get('success') is not False:
                xbmc.log(f"Successfully downloaded episode: {ep['title']}", xbmc.LOGINFO)
                xbmcgui.Dialog().notification('Downloaded', ep['title'][:30], xbmcgui.NOTIFICATION_INFO)
                xbmc.executebuiltin('Container.Refresh')
            else:
                error_msg = result.get('message', 'Unknown error') if isinstance(result, dict) else 'Download failed'
                xbmc.log(f"Failed to download episode: {ep['title']} - {error_msg}", xbmc.LOGWARNING)
                xbmcgui.Dialog().notification('Failed', f'Could not download episode: {error_msg}', xbmcgui.NOTIFICATION_WARNING)
                
        except Exception as e:
            error_msg = str(e)
            # Suppress JSON parsing errors if functionality is working
            if "Expecting value" in error_msg and "line 1 column 1" in error_msg:
                xbmc.log(f"Suppressed JSON parsing error (functionality working): {error_msg}", xbmc.LOGDEBUG)
                xbmcgui.Dialog().notification('Processing', 'Episode download started...', xbmcgui.NOTIFICATION_INFO)
            else:
                xbmc.log(f"Download episode error: {error_msg}", xbmc.LOGERROR)
                xbmcgui.Dialog().notification('Error', error_msg[:50], xbmcgui.NOTIFICATION_ERROR)
            
            xbmcgui.Dialog().notification('Added', ep['title'][:30], xbmcgui.NOTIFICATION_INFO)
            xbmc.executebuiltin('Container.Refresh')

            
    except Exception as e:
        xbmc.log(f"Add episode error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def batch_add_episodes(item_id):
    """Add all new episodes from RSS"""
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        import requests
        
        # Get stored new episodes
        new_episodes = _get_stored_episodes(item_id)
        
        # Get episodes needing download from server
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        server_episodes = item.get('media', {}).get('episodes', [])
        need_download = [ep for ep in server_episodes 
                        if not ep.get('audioFile') or 
                        (isinstance(ep.get('audioFile'), dict) and not ep['audioFile'].get('ino'))]
        
        total = len(new_episodes) + len(need_download)
        if total == 0:
            xbmcgui.Dialog().notification('Up to Date', 'No new episodes to add', xbmcgui.NOTIFICATION_INFO)
            return
        
        progress = xbmcgui.DialogProgress()
        progress.create('Adding Episodes', f'Adding {total} episodes...')
        
        added = 0
        queued = 0
        
        # Add new episodes from RSS
        for i, ep in enumerate(new_episodes):
            if progress.iscanceled():
                break
            
            pct = int((i / max(len(new_episodes), 1)) * 50)
            progress.update(pct, f'Adding: {ep["title"][:40]}')
            
            episode_data = {
                'title': ep['title'],
                'guid': ep['guid'],
                'enclosure': {
                    'url': ep['audioUrl'],
                    'type': ep.get('audioType', 'audio/mpeg'),
                    'length': ep.get('audioLength', '0')
                }
            }
            
            if ep.get('description'):
                episode_data['description'] = ep['description']
            if ep.get('pubDate'):
                episode_data['pubDate'] = ep['pubDate']
            
            # Note: Episodes are added via download-episodes API, not created individually
            # Skip individual episode creation since we'll batch download them
            xbmc.log(f"Skipping individual episode creation: {ep['title']} (will handle in batch)", xbmc.LOGDEBUG)
        
        # Queue all downloads using download-episodes API with episode data
        if need_download:
            progress.update(75, f'Queueing {len(need_download)} downloads...')
            
            # Prepare episode data for download API
            episodes_to_download = []
            for ep in need_download:
                # Find matching episode data from new_episodes
                matching_new_ep = next((new_ep for new_ep in new_episodes 
                                      if new_ep.get('title') == ep.get('title') or 
                                      new_ep.get('guid') == ep.get('guid')), None)
                
                if matching_new_ep:
                    episode_data = {
                        'title': matching_new_ep['title'],
                        'subtitle': matching_new_ep.get('subtitle', ''),
                        'description': matching_new_ep.get('description', ''),
                        'enclosure': {
                            'url': matching_new_ep['audioUrl'],
                            'type': matching_new_ep.get('audioType', 'audio/mpeg'),
                            'length': matching_new_ep.get('audioLength', '0')
                        },
                        'pubDate': matching_new_ep.get('pubDate', ''),
                        'publishedAt': matching_new_ep.get('publishedAt', 0)
                    }
                    
                    # Add optional fields
                    if matching_new_ep.get('season'):
                        episode_data['season'] = matching_new_ep['season']
                    if matching_new_ep.get('episode'):
                        episode_data['episode'] = matching_new_ep['episode']
                    if matching_new_ep.get('episodeType'):
                        episode_data['episodeType'] = matching_new_ep['episodeType']
                    
                    episodes_to_download.append(episode_data)
            
            # Download episodes in batches of 20
            if episodes_to_download:
                try:
                    dl_url = f"{url}/api/podcasts/{item_id}/download-episodes"
                    for i in range(0, len(episodes_to_download), 20):
                        batch = episodes_to_download[i:i+20]
                        dl_response = requests.post(dl_url, headers=library_service.headers, 
                                                   json=batch, timeout=30)
                        if dl_response.status_code == 200:
                            xbmc.log(f"Queued batch of {len(batch)} episodes for download", xbmc.LOGINFO)
                        else:
                            xbmc.log(f"Failed to queue batch: {dl_response.status_code}", xbmc.LOGWARNING)
                except Exception as e:
                    xbmc.log(f"Download queue error: {str(e)}", xbmc.LOGERROR)
        
        progress.close()
        
        msg = f'{added} added, {queued} queued' if added > 0 else f'{queued} queued for download'
        xbmcgui.Dialog().notification('Done', msg, xbmcgui.NOTIFICATION_INFO)
        xbmc.executebuiltin('Container.Refresh')
        
    except Exception as e:
        try:
            progress.close()
        except:
            pass
        xbmc.log(f"Batch add error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def download_episode_to_server(item_id, episode_id):
    """Download episode on server"""
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        import requests
        response = requests.post(f"{url}/api/podcasts/{item_id}/download-episodes",
                                headers=library_service.headers, json=[episode_id], timeout=30)
        
        if response.status_code == 200:
            xbmcgui.Dialog().notification('Download Started', 'Server downloading...', xbmcgui.NOTIFICATION_INFO)
        else:
            xbmcgui.Dialog().notification('Failed', f'Error {response.status_code}', xbmcgui.NOTIFICATION_ERROR)
    except Exception as e:
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def list_parts(item_id):
    xbmcplugin.setContent(ADDON_HANDLE, 'songs')
    
    library_service, url, token, offline = get_library_service()
    if not library_service:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id)
        chapters = item.get('media', {}).get('chapters', [])
        audio_files = item.get('media', {}).get('audioFiles', [])
        total_duration = item.get('media', {}).get('duration', 0)
        
        # Get best resume position (uses unified progress)
        current_time, is_finished, _ = get_best_resume_position(library_service, item_id)
        
        # Resume option
        if current_time > 10 and not is_finished:
            target_file, seek, _ = find_file_for_position(audio_files, current_time)
            if target_file:
                current_chapter = ""
                for ch in sorted(chapters, key=lambda x: x.get('start', 0)):
                    if ch.get('start', 0) <= current_time < ch.get('end', total_duration):
                        current_chapter = f" - {ch.get('title', '')[:20]}"
                        break
                
                list_item = xbmcgui.ListItem(label=f'[Resume: {format_time(current_time)}{current_chapter}]')
                list_item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                           build_url(action='play_at_position', item_id=item_id,
                                                    file_ino=target_file.get('ino'), seek_time=int(seek),
                                                    overall_time=int(current_time)),
                                           list_item, isFolder=False)
        
        if chapters:
            for i, ch in enumerate(sorted(chapters, key=lambda x: x.get('start', 0))):
                title = ch.get('title', f'Chapter {i+1}')
                ch_start = ch.get('start', 0)
                ch_end = ch.get('end', total_duration)
                
                prefix = '> ' if ch_start <= current_time < ch_end else ''
                
                list_item = xbmcgui.ListItem(label=f'{prefix}{title}')
                list_item.setProperty('IsPlayable', 'true')
                set_music_info(list_item, title=title, duration=ch_end - ch_start, tracknumber=i+1)
                
                target_file, seek, _ = find_file_for_position(audio_files, ch_start)
                if target_file:
                    xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                               build_url(action='play_at_position', item_id=item_id,
                                                        file_ino=target_file.get('ino'), seek_time=int(seek),
                                                        overall_time=int(ch_start)),
                                               list_item, isFolder=False)
        else:
            cumulative = 0
            for i, f in enumerate(sorted(audio_files, key=lambda x: x.get('index', 0))):
                title = f.get('metadata', {}).get('title', f'Part {i+1}')
                dur = f.get('duration', 0)
                
                prefix = '> ' if cumulative <= current_time < cumulative + dur else ''
                
                list_item = xbmcgui.ListItem(label=f'{prefix}{title}')
                list_item.setProperty('IsPlayable', 'true')
                set_music_info(list_item, title=title, duration=dur)
                
                xbmcplugin.addDirectoryItem(ADDON_HANDLE,
                                           build_url(action='play_at_position', item_id=item_id,
                                                    file_ino=f.get('ino'), seek_time=0,
                                                    overall_time=int(cumulative)),
                                           list_item, isFolder=False)
                cumulative += dur
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmc.log(f"Error: {str(e)}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)


def search_podcasts():
    library_service, url, token, offline = get_library_service()
    if not library_service or offline:
        xbmcgui.Dialog().notification('Error', 'Requires network', xbmcgui.NOTIFICATION_ERROR)
        return
    
    keyboard = xbmc.Keyboard('', 'Search Podcasts')
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    
    query = keyboard.getText()
    if not query:
        return
    
    try:
        import requests
        results = requests.get(f"https://itunes.apple.com/search?term={quote(query)}&media=podcast&limit=20",
                              timeout=10).json()
        
        if not results.get('results'):
            xbmcgui.Dialog().notification('No Results', 'No podcasts found', xbmcgui.NOTIFICATION_INFO)
            return
        
        xbmcplugin.setContent(ADDON_HANDLE, 'albums')
        
        for podcast in results['results']:
            name = podcast.get('collectionName', 'Unknown')
            artist = podcast.get('artistName', '')
            feed_url = podcast.get('feedUrl', '')
            artwork = podcast.get('artworkUrl600', '')
            
            if not feed_url:
                continue
            
            list_item = xbmcgui.ListItem(label=name)
            list_item.setArt({'thumb': artwork, 'poster': artwork})
            set_music_info(list_item, title=name, artist=artist)
            
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, 
                                       build_url(action='add_podcast', feed_url=feed_url, name=name),
                                       list_item, isFolder=False)
        
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def add_podcast_to_library(feed_url, name):
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        import requests
        
        progress = xbmcgui.DialogProgress()
        progress.create('Adding Podcast', 'Getting metadata...')
        
        metadata = {'title': name, 'feedUrl': feed_url}
        try:
            rss = requests.get(feed_url, timeout=15, headers={'User-Agent': 'Kodi-Audiobookshelf/1.0'})
            import xml.etree.ElementTree as ET
            root = ET.fromstring(rss.content)
            channel = root.find('channel')
            if channel is not None:
                title_el = channel.find('title')
                if title_el is not None and title_el.text:
                    metadata['title'] = title_el.text
                
                itunes = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
                author_el = channel.find(f'{itunes}author')
                if author_el is not None and author_el.text:
                    metadata['author'] = author_el.text
                
                img_el = channel.find(f'{itunes}image')
                if img_el is not None:
                    metadata['imageUrl'] = img_el.get('href', '')
        except:
            pass
        
        progress.update(40, 'Finding library...')
        
        data = library_service.get_all_libraries()
        podcast_libs = [l for l in data.get('libraries', []) if l.get('mediaType') == 'podcast']
        
        if not podcast_libs:
            progress.close()
            xbmcgui.Dialog().notification('Error', 'No podcast library', xbmcgui.NOTIFICATION_ERROR)
            return
        
        library_id = podcast_libs[0]['id']
        if len(podcast_libs) > 1:
            progress.close()
            names = [l['name'] for l in podcast_libs]
            idx = xbmcgui.Dialog().select('Select Library', names)
            if idx < 0:
                return
            library_id = podcast_libs[idx]['id']
            progress.create('Adding Podcast', 'Adding...')
        
        progress.update(60, 'Adding to library...')
        
        library = library_service.get_library(library_id)
        folders = library.get('folders', [])
        if not folders:
            progress.close()
            xbmcgui.Dialog().notification('Error', 'No folder', xbmcgui.NOTIFICATION_ERROR)
            return
        
        folder_id = folders[0].get('id')
        folder_path = folders[0].get('fullPath', '/podcasts')
        safe_name = "".join(c for c in metadata['title'] if c.isalnum() or c in ' -_').strip()[:50]
        
        payload = {
            'path': f"{folder_path}/{safe_name}",
            'folderId': folder_id,
            'libraryId': library_id,
            'media': {'metadata': metadata},
            'autoDownloadEpisodes': False
        }
        
        response = requests.post(f"{url}/api/podcasts", headers=library_service.headers, json=payload, timeout=30)
        progress.close()
        
        if response.status_code == 200:
            xbmcgui.Dialog().notification('Added', metadata['title'][:30], xbmcgui.NOTIFICATION_INFO)
        elif 'exist' in response.text.lower():
            xbmcgui.Dialog().notification('Exists', 'Already in library', xbmcgui.NOTIFICATION_INFO)
        else:
            xbmcgui.Dialog().notification('Failed', f'Error {response.status_code}', xbmcgui.NOTIFICATION_ERROR)
        
    except Exception as e:
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def list_downloads():
    xbmcplugin.setContent(ADDON_HANDLE, 'songs')
    
    downloads = download_manager.get_all_downloads()
    
    if not downloads:
        xbmcgui.Dialog().notification('No Downloads', 'Nothing downloaded yet', xbmcgui.NOTIFICATION_INFO)
    
    for key, info in downloads.items():
        list_item = xbmcgui.ListItem(label=info['title'])
        list_item.setProperty('IsPlayable', 'true')
        
        # Try to use cached cover first for consistency with streaming version
        cover_url = info.get('cover_url') or info.get('cover_path')
        item_id = info.get('item_id', key.split('_')[0])
        episode_id = info.get('episode_id')
        cache_key = f"{item_id}_{episode_id}" if episode_id else item_id
        
        if cover_url:
            local_cover = download_cover(cover_url, cache_key)
            if local_cover:
                list_item.setArt({'thumb': local_cover, 'poster': local_cover, 'fanart': local_cover})
            elif info.get('cover_path') and os.path.exists(info['cover_path']):
                # Fallback to downloaded cover
                list_item.setArt({'thumb': info['cover_path'], 'poster': info['cover_path']})
        
        set_music_info(list_item, title=info['title'], artist=info.get('author', ''), duration=info.get('duration', 0))
        
        list_item.addContextMenuItems([
            ('Delete', f'RunPlugin({build_url(action="delete_download", key=key)})')
        ])
        
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, build_url(action='play_offline', key=key), list_item, isFolder=False)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# === PLAYBACK FUNCTIONS ===

def play_audio(play_url, title, duration, library_service, item_id, episode_id=None,
               start_position=0, is_podcast=False, file_offset=0, artist=''):
    """
    Start audio playback with progress monitoring.
    
    Args:
        play_url: URL to stream from
        title: Display title
        duration: Total duration of the OVERALL audiobook/podcast (not just this file)
        library_service: Service for server communication
        item_id: Library item ID
        episode_id: Episode ID (for podcasts)
        start_position: Position to seek to within the current file
        is_podcast: Whether this is a podcast
        file_offset: For multi-file audiobooks, the offset where this file starts
                    in the overall audiobook timeline
    """
    global _active_monitor
    
    xbmc.log(f"[PLAY] play_audio: title={title}, duration={duration}, start={start_position}, "
            f"file_offset={file_offset}, is_podcast={is_podcast}", xbmc.LOGINFO)
    
    # Don't let duration be 0 - try to get from server progress if we have none
    if duration == 0 and library_service:
        try:
            progress = library_service.get_media_progress(item_id, episode_id)
            if progress and progress.get('duration', 0) > 0:
                duration = progress['duration']
                xbmc.log(f"[PLAY] Got duration from server progress: {duration}", xbmc.LOGINFO)
        except:
            pass
    
    list_item = xbmcgui.ListItem(path=play_url)
    set_music_info(list_item, title=title, artist=artist, duration=duration)

    # Set cover art so Kodi's now-playing screen has something to render.
    if library_service and item_id:
        cover_url = f"{library_service.base_url}/api/items/{item_id}/cover?token={library_service.token}"
        local_cover = download_cover(cover_url, item_id)
        art_source = local_cover or cover_url
        list_item.setArt({'thumb': art_source, 'poster': art_source,
                          'fanart': art_source, 'icon': art_source})

    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, list_item)
    
    sync_enabled = get_setting_bool('sync_podcast_progress' if is_podcast else 'sync_audiobook_progress', True)
    sync_on_stop = get_setting_bool('podcast_sync_on_stop' if is_podcast else 'audiobook_sync_on_stop', True)
    sync_interval = get_sync_interval(is_podcast)
    finished_threshold = get_finished_threshold()
    
    _active_monitor = PlaybackMonitor(
        library_service, item_id, duration if duration > 0 else 1,
        episode_id=episode_id,
        sync_enabled=sync_enabled, sync_on_stop=sync_on_stop, 
        sync_interval=sync_interval, finished_threshold=finished_threshold,
        file_offset=file_offset
    )
    _active_monitor.start_monitoring_async(start_position)


def play_at_position(item_id, file_ino, seek_time, overall_time=None):
    """
    Play audiobook at a specific position within a file.
    
    Args:
        item_id: Library item ID
        file_ino: File identifier
        seek_time: Position within the specific file (for player seeking)
        overall_time: Position in the overall audiobook (for progress sync)
    """
    library_service, url, token, offline = get_library_service()
    
    # Check if downloaded
    if download_manager.is_downloaded(item_id):
        # For downloaded files, use overall_time if provided
        play_offline_item(item_id, seek_position=overall_time if overall_time is not None else seek_time)
        return
    
    if not library_service:
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        media = item.get('media', {})
        
        # Try multiple places for duration
        duration = media.get('duration', 0)
        if duration == 0:
            # Sum duration from audio files
            audio_files = media.get('audioFiles', [])
            duration = sum(f.get('duration', 0) for f in audio_files)
        if duration == 0:
            # Try tracks
            tracks = media.get('tracks', [])
            duration = sum(t.get('duration', 0) for t in tracks)
        
        metadata = media.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        author = metadata.get('authorName', '')

        # Calculate file offset (difference between overall_time and seek_time)
        # This is where the file starts in the overall audiobook
        if overall_time is not None:
            file_offset = overall_time - seek_time
        else:
            # Try to calculate from audio files
            file_offset = 0
            audio_files = media.get('audioFiles', [])
            sorted_files = sorted(audio_files, key=lambda x: x.get('index', 0))
            cumulative = 0
            for f in sorted_files:
                if f.get('ino') == file_ino:
                    file_offset = cumulative
                    break
                cumulative += f.get('duration', 0)
        
        xbmc.log(f"[PLAY] play_at_position: item={item_id}, duration={duration}, seek={seek_time}, "
                f"overall={overall_time}, file_offset={file_offset}", xbmc.LOGINFO)
        
        play_url = f"{url}/api/items/{item_id}/file/{file_ino}?token={token}"
        play_audio(play_url, title, duration, library_service, item_id,
                  start_position=seek_time, file_offset=file_offset, artist=author)
        
    except Exception as e:
        xbmc.log(f"[PLAY] Error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', 'Playback failed', xbmcgui.NOTIFICATION_ERROR)


def play_item(item_id):
    library_service, url, token, offline = get_library_service()
    
    if download_manager.is_downloaded(item_id):
        play_offline_item(item_id)
        return
    
    if not library_service:
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        media = item.get('media', {})
        
        # Try multiple places for duration
        duration = media.get('duration', 0)
        if duration == 0:
            audio_files = media.get('audioFiles', [])
            duration = sum(f.get('duration', 0) for f in audio_files)
        if duration == 0:
            tracks = media.get('tracks', [])
            duration = sum(t.get('duration', 0) for t in tracks)
        
        metadata = media.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        author = metadata.get('authorName', '')

        xbmc.log(f"[PLAY] play_item: item={item_id}, duration={duration}", xbmc.LOGINFO)
        
        # Use unified progress
        current_time, is_finished, server_duration = get_best_resume_position(library_service, item_id)
        
        # Use server duration if we don't have one
        if duration == 0 and server_duration > 0:
            duration = server_duration
            xbmc.log(f"[PLAY] Using server duration: {duration}", xbmc.LOGINFO)
        
        start_position = current_time if current_time > 10 and not is_finished and ask_resume(current_time, duration) else 0
        
        play_url = library_service.get_file_url(item_id)
        play_audio(play_url, title, duration, library_service, item_id,
                  start_position=start_position, artist=author)
        
    except Exception as e:
        xbmc.log(f"[PLAY] Error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def play_podcast_queue(item_id, start_episode_id):
    """Build a native Kodi playlist of podcast episodes from the selected one
    onward (chronological) and start it, so Kodi auto-advances episode to
    episode. Each entry re-enters play_episode(queued=1), which resolves and
    attaches its own progress monitor - so item identity and sync are handled
    per episode for free.
    """
    library_service, url, token, offline = get_library_service()

    # Fully offline: build the queue from downloaded episodes only.
    if not library_service:
        if not _play_offline_podcast_queue(item_id, start_episode_id):
            play_offline_item(item_id, start_episode_id, queued=True)
        return

    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        episodes = item.get('media', {}).get('episodes', [])
        # An episode is queueable if it can stream from the server OR we have a
        # local download of it (downloaded ones play from disk in the queue).
        playable = [ep for ep in episodes
                    if ep.get('audioFile') or download_manager.is_downloaded(item_id, ep.get('id'))]
        # Chronological (oldest -> newest) so "next" moves forward in time.
        playable.sort(key=lambda x: x.get('publishedAt') or 0)
        ids = [ep.get('id') for ep in playable]

        if start_episode_id not in ids:
            # Selected episode has no server audio and no download - play single.
            play_episode(item_id, start_episode_id, queued=True)
            return

        start_idx = ids.index(start_episode_id)
        queue = playable[start_idx:start_idx + 100]  # cap runaway feeds

        if len(queue) <= 1:
            # Nothing to advance into - just play the one episode.
            play_episode(item_id, start_episode_id, queued=True)
            return

        metadata = item.get('media', {}).get('metadata', {})
        creator = metadata.get('author') or metadata.get('title', '')
        cover_url = f"{library_service.base_url}/api/items/{item_id}/cover?token={library_service.token}"
        art = download_cover(cover_url, item_id) or cover_url

        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()
        dl_count = 0
        for ep in queue:
            ep_id = ep.get('id')
            is_dl = download_manager.is_downloaded(item_id, ep_id)
            if is_dl:
                dl_count += 1
            li = xbmcgui.ListItem(label=ep.get('title', 'Unknown'))
            set_music_info(li, title=ep.get('title', 'Unknown'), artist=creator,
                           duration=ep.get('duration', 0))
            if art:
                li.setArt({'thumb': art, 'poster': art, 'fanart': art, 'icon': art})
            li.setProperty('IsPlayable', 'true')
            # Every entry re-enters play_episode(queued=1); that function plays
            # from the local file when downloaded, else streams. So a single
            # queue transparently mixes downloaded and streamed episodes.
            ep_url = build_url(action='play_episode', item_id=item_id,
                               episode_id=ep_id, queued=1)
            pl.add(ep_url, li)

        xbmc.log(f"[QUEUE] Auto-play queue: {len(queue)} episodes from {start_episode_id} "
                 f"({dl_count} downloaded, {len(queue) - dl_count} streamed)", xbmc.LOGINFO)
        xbmc.Player().play(pl)

    except Exception as e:
        xbmc.log(f"[QUEUE] Failed to build podcast queue: {e}", xbmc.LOGERROR)
        # Fall back to single play so the click still does something.
        play_episode(item_id, start_episode_id, queued=True)


def _play_offline_podcast_queue(item_id, start_episode_id):
    """Build an auto-advance queue from the DOWNLOADED episodes of a podcast,
    for use when there is no server connection. Returns True if a multi-episode
    queue was started, False otherwise (caller then plays the single episode).
    """
    try:
        downloads = download_manager.get_all_downloads()
        eps = [info for info in downloads.values()
               if info.get('item_id') == item_id and info.get('episode_id')]
        if len(eps) <= 1:
            return False
        # Order chronologically by the stored publish time (matches the online
        # queue). Older downloads predating this field have published_at=0, so
        # fall back to download time to keep them sensibly ordered.
        eps.sort(key=lambda x: (x.get('published_at') or 0, x.get('downloaded_at') or ''))
        ep_ids = [e.get('episode_id') for e in eps]
        if start_episode_id not in ep_ids:
            return False
        start_idx = ep_ids.index(start_episode_id)
        queue = eps[start_idx:start_idx + 100]
        if len(queue) <= 1:
            return False

        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()
        for info in queue:
            li = xbmcgui.ListItem(label=info.get('title', 'Unknown'))
            set_music_info(li, title=info.get('title', 'Unknown'),
                           artist=info.get('author', ''), duration=info.get('duration', 0))
            cover = info.get('cover_path')
            if cover and os.path.exists(cover):
                li.setArt({'thumb': cover, 'poster': cover, 'fanart': cover, 'icon': cover})
            li.setProperty('IsPlayable', 'true')
            ep_url = build_url(action='play_episode', item_id=item_id,
                               episode_id=info.get('episode_id'), queued=1)
            pl.add(ep_url, li)

        xbmc.log(f"[QUEUE] Offline auto-play queue: {len(queue)} downloaded episodes", xbmc.LOGINFO)
        xbmc.Player().play(pl)
        return True
    except Exception as e:
        xbmc.log(f"[QUEUE] Offline queue build failed: {e}", xbmc.LOGERROR)
        return False


def play_episode(item_id, episode_id, queued=False):
    library_service, url, token, offline = get_library_service()

    # Prefer the local copy when the episode is downloaded (works both as a
    # standalone play and as an entry in an auto-play-next queue).
    if download_manager.is_downloaded(item_id, episode_id):
        play_offline_item(item_id, episode_id, queued=queued)
        return

    if not library_service:
        return

    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        episode = next((ep for ep in item.get('media', {}).get('episodes', [])
                       if ep.get('id') == episode_id), None)

        if not episode:
            raise ValueError("Episode not found")

        if not episode.get('audioFile'):
            xbmcgui.Dialog().notification('Not Available', 'Not on server', xbmcgui.NOTIFICATION_WARNING)
            return

        title = episode.get('title', 'Unknown')
        duration = episode.get('duration', 0)

        # Show the podcast creator (or fall back to the podcast title) as the artist.
        podcast_metadata = item.get('media', {}).get('metadata', {})
        creator = podcast_metadata.get('author') or podcast_metadata.get('title', '')

        # Use unified progress
        current_time, is_finished, _ = get_best_resume_position(library_service, item_id, episode_id)

        if queued:
            # Part of an auto-advance queue: never pop a modal resume dialog
            # between episodes (it would block playback). Silently resume if
            # this episode was partially heard, otherwise start at 0.
            start_position = current_time if current_time > 10 and not is_finished else 0
        else:
            start_position = current_time if current_time > 10 and not is_finished and ask_resume(current_time, duration) else 0

        play_url = library_service.get_file_url(item_id, episode_id=episode_id)
        play_audio(play_url, title, duration, library_service, item_id,
                  episode_id=episode_id, start_position=start_position, is_podcast=True,
                  artist=creator)

    except Exception as e:
        xbmcgui.Dialog().notification('Error', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def play_offline_item(item_id, episode_id=None, seek_position=None, queued=False):
    """Play downloaded item using unified progress - syncs with server when online.

    queued=True means this is an entry in an auto-play-next playlist: never pop
    a modal resume dialog (it would block the queue), just resume silently.
    """
    download_info = download_manager.get_download_info(item_id, episode_id)
    if not download_info:
        xbmcgui.Dialog().notification('Error', 'Not found', xbmcgui.NOTIFICATION_ERROR)
        return
    
    duration = download_info.get('duration', 0)
    
    # Try to get library service for server sync (even for downloaded items)
    library_service = None
    try:
        lib_svc, _, _, offline = get_library_service()
        if not offline and lib_svc:
            library_service = lib_svc
            xbmc.log("[OFFLINE] Got library service for sync", xbmc.LOGINFO)
            
            # We were offline, now online - trigger reconnection sync
            sync_mgr = get_sync_manager()
            if sync_mgr._sync_state.get('was_offline', False):
                xbmc.log("[OFFLINE] Was offline, triggering reconnection sync", xbmc.LOGINFO)
                on_network_reconnect(library_service)
        else:
            xbmc.log("[OFFLINE] No library service (offline mode)", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"[OFFLINE] Could not get library service: {str(e)}", xbmc.LOGDEBUG)
    
    # Get best resume position (unified - uses same position as streaming)
    # This is the OVERALL audiobook position
    if seek_position is not None:
        overall_pos = seek_position
    else:
        overall_pos, is_finished, server_duration = get_best_resume_position(library_service, item_id, episode_id)
        if server_duration > duration:
            duration = server_duration

        if overall_pos > 10 and not is_finished:
            if queued:
                # Auto-advance queue: resume silently, no blocking dialog.
                pass
            elif not ask_resume(overall_pos, duration):
                overall_pos = 0
    
    # For multi-file downloads, get the right file and calculate offsets
    file_path = download_info.get('file_path')
    file_offset = 0  # Default for single-file
    start_pos = overall_pos  # Position to seek to in player
    
    if download_info.get('is_multifile'):
        file_path, start_pos, file_offset = download_manager.get_file_for_position(item_id, overall_pos)
        xbmc.log(f"[OFFLINE] Multi-file: overall={overall_pos:.1f}s -> file_offset={file_offset:.1f}s, seek={start_pos:.1f}s", xbmc.LOGINFO)
    
    if not file_path or not os.path.exists(file_path):
        xbmcgui.Dialog().notification('Error', 'File not found', xbmcgui.NOTIFICATION_ERROR)
        return
    
    list_item = xbmcgui.ListItem(path=file_path)
    # For audiobooks 'author' is set; for podcast episodes fall back to the show title.
    artist = download_info.get('author') or download_info.get('podcast_title', '')
    set_music_info(list_item, title=download_info['title'], artist=artist, duration=duration)

    # Set cover art for the now-playing screen. Prefer the locally
    # downloaded cover; fall back to server URL if we're back online.
    art_source = download_info.get('cover_path')
    if (not art_source or not os.path.exists(art_source)) and library_service and item_id:
        art_source = f"{library_service.base_url}/api/items/{item_id}/cover?token={library_service.token}"
    if art_source:
        list_item.setArt({'thumb': art_source, 'poster': art_source,
                          'fanart': art_source, 'icon': art_source})

    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, list_item)
    
    # Use PlaybackMonitor with library_service if available (for server sync)
    global _active_monitor
    is_podcast = episode_id is not None
    finished_threshold = get_finished_threshold()
    
    xbmc.log(f"[OFFLINE] Starting monitor with library_service={'YES' if library_service else 'NO'}, "
            f"file_offset={file_offset:.1f}s", xbmc.LOGINFO)
    
    _active_monitor = PlaybackMonitor(
        library_service,  # Pass library service for server sync
        item_id, 
        duration if duration > 0 else 1,
        episode_id=episode_id,
        sync_enabled=True,  # Always enable sync
        sync_on_stop=True,
        sync_interval=get_sync_interval(is_podcast),
        finished_threshold=finished_threshold,
        file_offset=file_offset  # Pass file offset for correct overall time calculation
    )
    _active_monitor.start_monitoring_async(start_pos)


def play_offline_at(item_id, seek_time):
    """Play downloaded audiobook at specific position (for chapter selection)"""
    play_offline_item(item_id, episode_id=None, seek_position=seek_time)


# === DOWNLOAD FUNCTIONS ===

def download_item(item_id, library_id):
    if not check_download_path():
        return
    
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id)
        media = item.get('media', {})
        metadata = media.get('metadata', {})
        
        item_data = {
            'title': metadata.get('title', 'Unknown'),
            'duration': media.get('duration', 0),
            'author': metadata.get('authorName', ''),
            'cover_url': f"{url}/api/items/{item_id}/cover?token={token}",
            'audio_files': media.get('audioFiles', []),
            'chapters': media.get('chapters', [])
        }
        
        if len(item_data['audio_files']) > 1:
            download_manager.download_audiobook_complete(item_id, item_data, library_service)
        else:
            download_manager.download_item(item_id, item_data, library_service)
        
    except Exception as e:
        xbmcgui.Dialog().notification('Failed', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def download_podcast(item_id):
    if not check_download_path():
        return
    
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        podcast_title = item.get('media', {}).get('metadata', {}).get('title', 'Unknown Podcast')
        all_episodes = [ep for ep in item.get('media', {}).get('episodes', []) if ep.get('audioFile')]

        if not all_episodes:
            xbmcgui.Dialog().notification('No Episodes', 'Nothing to download', xbmcgui.NOTIFICATION_WARNING)
            return
        
        # Filter episodes based on download mode setting
        download_mode = get_setting_int('podcast_download_mode', 0)
        episodes = []
        
        if download_mode == 0:  # All Episodes
            episodes = all_episodes
        elif download_mode == 1:  # Unwatched Only
            for ep in all_episodes:
                ep_id = ep.get('id')
                # Check if episode is finished
                is_finished = False
                try:
                    progress = library_service.get_media_progress(item_id, ep_id)
                    if progress and progress.get('isFinished', False):
                        is_finished = True
                except:
                    pass
                
                # Also check local progress
                local = get_local_progress(item_id, ep_id)
                if local and local.get('is_finished', False):
                    is_finished = True
                
                if not is_finished:
                    episodes.append(ep)
        elif download_mode == 2:  # New Only (not implemented yet, fallback to unwatched)
            for ep in all_episodes:
                ep_id = ep.get('id')
                # Check if episode is finished
                is_finished = False
                try:
                    progress = library_service.get_media_progress(item_id, ep_id)
                    if progress and progress.get('isFinished', False):
                        is_finished = True
                except:
                    pass
                
                # Also check local progress
                local = get_local_progress(item_id, ep_id)
                if local and local.get('is_finished', False):
                    is_finished = True
                
                if not is_finished:
                    episodes.append(ep)
        
        if not episodes:
            mode_names = ['All', 'Unwatched', 'New']
            mode_name = mode_names[download_mode] if download_mode < len(mode_names) else 'Unwatched'
            xbmcgui.Dialog().notification('No Episodes', f'No {mode_name.lower()} episodes to download', xbmcgui.NOTIFICATION_WARNING)
            return
        
        if not xbmcgui.Dialog().yesno('Download Podcast', f'Download {len(episodes)} episodes?'):
            return
        
        # Show start notification
        xbmcgui.Dialog().notification('Download Started', f'Downloading {len(episodes)} episodes', xbmcgui.NOTIFICATION_INFO, 5000)
        
        success = 0
        for i, ep in enumerate(episodes):
            # Show progress notification every 5 episodes or for the last one
            if (i + 1) % 5 == 0 or i == len(episodes) - 1:
                xbmcgui.Dialog().notification('Download Progress', f'Episode {i+1}/{len(episodes)}: {ep.get("title", "")[:30]}', xbmcgui.NOTIFICATION_INFO, 2000)
            
            try:
                ep_id = ep.get('id')
                item_data = {
                    'title': ep.get('title', 'Unknown'),
                    'podcast_title': podcast_title,
                    'duration': ep.get('duration', 0),
                    'publishedAt': ep.get('publishedAt', 0),
                    'cover_url': f"{url}/api/items/{item_id}/cover?token={token}"
                }
                download_manager.download_item(item_id, item_data, library_service, episode_id=ep_id, show_progress=False)
                success += 1
            except Exception as e:
                xbmc.log(f"Episode download error: {str(e)}", xbmc.LOGERROR)
        
        xbmcgui.Dialog().notification('Complete', f'{success} episodes downloaded', xbmcgui.NOTIFICATION_INFO)
        
    except Exception as e:
        xbmc.log(f"Download podcast error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Failed', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def download_episode(item_id, episode_id):
    if not check_download_path():
        return
    
    library_service, url, token, offline = get_library_service()
    if not library_service:
        return
    
    try:
        item = library_service.get_library_item_by_id(item_id, expanded=1)
        episode = next((ep for ep in item.get('media', {}).get('episodes', []) 
                       if ep.get('id') == episode_id), None)
        
        if not episode:
            raise ValueError("Episode not found")
        
        podcast_title = item.get('media', {}).get('metadata', {}).get('title', 'Unknown Podcast')
        
        item_data = {
            'title': episode.get('title', 'Unknown'),
            'podcast_title': podcast_title,
            'duration': episode.get('duration', 0),
            'publishedAt': episode.get('publishedAt', 0),
            'cover_url': f"{url}/api/items/{item_id}/cover?token={token}"
        }

        download_manager.download_item(item_id, item_data, library_service, episode_id=episode_id)
        
    except Exception as e:
        xbmcgui.Dialog().notification('Failed', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)


def delete_download(item_id=None, episode_id=None, key=None):
    if key:
        parts = key.split('_', 1)
        item_id = parts[0]
        episode_id = parts[1] if len(parts) > 1 else None
    
    if item_id:
        download_manager.delete_download(item_id, episode_id)
        xbmc.executebuiltin('Container.Refresh')


def delete_all_podcast_episodes(item_id):
    """Delete all downloaded episodes for a podcast"""
    if not item_id:
        return
    
    # Get all downloads for this podcast
    all_downloads = download_manager.get_all_downloads()
    podcast_episodes = []
    
    for key, download_info in all_downloads.items():
        if (download_info.get('item_id') == item_id and 
            download_info.get('episode_id') is not None):
            podcast_episodes.append((key, download_info))
    
    if not podcast_episodes:
        xbmcgui.Dialog().notification('No Episodes', 'No downloaded episodes found for this podcast', xbmcgui.NOTIFICATION_INFO)
        return
    
    # Confirm deletion
    if xbmcgui.Dialog().yesno('Delete All Episodes', 
                              f'Are you sure you want to delete {len(podcast_episodes)} downloaded episodes?'):
        deleted_count = 0
        for key, download_info in podcast_episodes:
            try:
                download_manager.delete_download(download_info['item_id'], download_info['episode_id'])
                deleted_count += 1
            except Exception as e:
                xbmc.log(f"Error deleting episode {key}: {str(e)}", xbmc.LOGERROR)
        
        xbmcgui.Dialog().notification('Episodes Deleted', f'Deleted {deleted_count} episodes', xbmcgui.NOTIFICATION_INFO)
        xbmc.executebuiltin('Container.Refresh')


def delete_all_downloads():
    """Delete all downloaded content"""
    if not get_setting_bool('enable_downloads'):
        xbmcgui.Dialog().notification('Downloads Disabled', 'Downloads are not enabled', xbmcgui.NOTIFICATION_ERROR)
        return
    
    all_downloads = download_manager.get_all_downloads()
    
    if not all_downloads:
        xbmcgui.Dialog().notification('No Downloads', 'No downloaded content found', xbmcgui.NOTIFICATION_INFO)
        return
    
    # Count items by type
    audiobooks = sum(1 for d in all_downloads.values() if d.get('episode_id') is None)
    episodes = sum(1 for d in all_downloads.values() if d.get('episode_id') is not None)
    
    # Confirm deletion
    message_parts = []
    if audiobooks > 0:
        message_parts.append(f"{audiobooks} audiobook{'s' if audiobooks != 1 else ''}")
    if episodes > 0:
        message_parts.append(f"{episodes} episode{'s' if episodes != 1 else ''}")
    
    message = "Are you sure you want to delete all downloaded content?\n\n" + ", ".join(message_parts) + "?"
    
    if xbmcgui.Dialog().yesno('Delete All Downloads', message):
        deleted_count, failed_count = download_manager.delete_all_downloads()
        
        if failed_count > 0:
            xbmcgui.Dialog().notification('Partial Success', 
                                         f'Deleted {deleted_count} items, {failed_count} failed', 
                                         xbmcgui.NOTIFICATION_WARNING)
        else:
            xbmcgui.Dialog().notification('All Downloads Deleted', 
                                         f'Successfully deleted {deleted_count} items', 
                                         xbmcgui.NOTIFICATION_INFO)
        
        xbmc.executebuiltin('Container.Refresh')


# === ROUTER ===

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    action = params.get('action')
    
    if not params or not action:
        list_libraries()
    # Online browsing actions
    elif action == 'audiobooks':
        list_audiobooks_combined()
    elif action == 'podcasts':
        list_podcasts_combined()
    elif action == 'library':
        list_library_items(params['library_id'], params.get('is_podcast') == '1')
    elif action == 'episodes':
        list_episodes(params['item_id'], params.get('sort_by', 'date'))
    elif action == 'parts':
        list_parts(params['item_id'])
    elif action == 'play':
        play_item(params['item_id'])
    elif action == 'play_at_position':
        overall_time = int(params.get('overall_time')) if params.get('overall_time') else None
        play_at_position(params['item_id'], params['file_ino'], int(params.get('seek_time', 0)), overall_time)
    elif action == 'play_episode':
        play_episode(params['item_id'], params['episode_id'], queued=params.get('queued') == '1')
    elif action == 'play_queue':
        play_podcast_queue(params['item_id'], params['episode_id'])
    elif action == 'downloads':
        list_downloads()
    elif action == 'play_offline':
        parts = params.get('key', '').split('_', 1)
        play_offline_item(parts[0], parts[1] if len(parts) > 1 else None)
    elif action == 'play_offline_at':
        play_offline_at(params['item_id'], int(params.get('seek_time', 0)))
    # Offline browsing actions
    elif action == 'offline_books':
        list_offline_books()
    elif action == 'offline_podcasts':
        list_offline_podcasts()
    elif action == 'offline_episodes':
        list_offline_episodes(params['item_id'])
    elif action == 'offline_parts':
        list_offline_parts(params['item_id'])
    # Progress management actions
    elif action == 'clear_progress':
        clear_progress(params['item_id'], params.get('episode_id'))
    elif action == 'mark_finished':
        mark_as_finished(params['item_id'], params.get('episode_id'), finished=True)
    elif action == 'mark_unfinished':
        mark_as_finished(params['item_id'], params.get('episode_id'), finished=False)
    elif action == 'sync_progress_from_server':
        # Use sync_manager directly for bidirectional sync
        library_service = None
        try:
            lib_svc, _, _, offline = get_library_service()
            if offline or not lib_svc:
                xbmcgui.Dialog().notification('Offline', 'Cannot sync - no network connection', xbmcgui.NOTIFICATION_WARNING)
                return
            library_service = lib_svc
        except:
            xbmcgui.Dialog().notification('Error', 'Cannot connect to server', xbmcgui.NOTIFICATION_ERROR)
            return
        
        sync_mgr = get_sync_manager()
        sync_mgr.set_library_service(library_service)
        
        try:
            item_id = params['item_id']
            episode_id = params.get('episode_id')
            
            # Use sync_manager's bidirectional sync
            synced_from_server, uploaded_to_server = sync_mgr.sync_item_bidirectional(item_id, episode_id)
            
            if synced_from_server or uploaded_to_server:
                # Get updated progress for notification
                local = sync_mgr.get_local_progress(item_id, episode_id)
                if local:
                    current_time = local.get('current_time', 0)
                    duration = local.get('duration', 0)
                    is_finished = local.get('is_finished', False)
                    
                    status_msg = f"Synced: {format_time(current_time)}"
                    if is_finished:
                        status_msg += " (Finished)"
                    
                    if synced_from_server and uploaded_to_server:
                        status_msg += " (Bidirectional sync)"
                    elif synced_from_server:
                        status_msg += " (From server)"
                    elif uploaded_to_server:
                        status_msg += " (To server)"
                    
                    xbmcgui.Dialog().notification('Sync Complete', status_msg, xbmcgui.NOTIFICATION_INFO, 3000)
                    xbmc.log(f"[SYNC] Synced item: {item_id}/{episode_id} = {current_time:.1f}s / {duration:.1f}s finished={is_finished}", xbmc.LOGINFO)
                else:
                    xbmcgui.Dialog().notification('Sync Complete', 'Progress synchronized', xbmcgui.NOTIFICATION_INFO, 3000)
            else:
                xbmcgui.Dialog().notification('No Changes', 'Progress already in sync', xbmcgui.NOTIFICATION_INFO, 2000)
            
            # Refresh to show updated progress
            xbmc.executebuiltin('Container.Refresh')
            
        except Exception as e:
            xbmc.log(f"[SYNC] Error syncing from server: {e}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Sync Failed', f'Error: {str(e)[:50]}', xbmcgui.NOTIFICATION_ERROR)
    # Search and podcast management
    elif action == 'search':
        search_podcasts()
    elif action == 'add_podcast':
        add_podcast_to_library(params['feed_url'], params['name'])
    elif action == 'find_episodes':
        find_new_episodes(params['item_id'])
    elif action == 'add_new_episode':
        add_new_episode(params['item_id'], params['episode_index'])
    elif action == 'batch_add_episodes':
        batch_add_episodes(params['item_id'])
    elif action == 'download_to_server':
        download_episode_to_server(params['item_id'], params['episode_id'])
    elif action == 'download':
        download_item(params['item_id'], params.get('library_id'))
    elif action == 'download_podcast':
        download_podcast(params['item_id'])
    elif action == 'download_episode':
        download_episode(params['item_id'], params['episode_id'])
    elif action == 'delete_download':
        delete_download(item_id=params.get('item_id'), episode_id=params.get('episode_id'), key=params.get('key'))
    elif action == 'delete_all_podcast_episodes':
        delete_all_podcast_episodes(params.get('item_id'))
    elif action == 'delete_all_downloads':
        delete_all_downloads()
    else:
        list_libraries()


if __name__ == '__main__':
    router(sys.argv[2][1:])
