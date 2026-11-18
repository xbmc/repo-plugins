import xbmc
import xbmcaddon
import time
import threading

# Import from sync_manager for all progress operations
from sync_manager import (
    get_sync_manager, 
    get_local_progress, 
    save_local_progress, 
    get_best_resume_position,
    sync_all_to_server,
    mark_synced
)


class PlaybackMonitor:
    """Monitor playback and sync progress - works for both streamed and downloaded content"""
    
    def __init__(self, library_service, item_id, duration, episode_id=None,
                 sync_enabled=True, sync_on_stop=True, sync_interval=15,
                 finished_threshold=0.95, file_offset=0):
        """
        Initialize playback monitor.
        
        Args:
            library_service: Service for server communication
            item_id: Library item ID
            duration: Total duration of the OVERALL audiobook (not just this file)
            episode_id: Episode ID (for podcasts)
            sync_enabled: Whether to sync progress
            sync_on_stop: Whether to sync when playback stops
            sync_interval: Interval between syncs in seconds
            finished_threshold: Progress percentage to mark as finished
            file_offset: For multi-file audiobooks, where this file starts in the 
                        overall timeline. Added to player position for sync.
        """
        self.library_service = library_service
        self.item_id = item_id
        self.episode_id = episode_id
        self.duration = max(duration, 1)
        self.player = xbmc.Player()
        self.session_id = None
        self.is_monitoring = False
        self.monitor_thread = None
        self.sync_enabled = sync_enabled
        self.sync_on_stop = sync_on_stop
        self.sync_interval = sync_interval
        self.finished_threshold = finished_threshold
        self.file_offset = file_offset  # Offset for multi-file audiobooks
        self.start_position = 0
        self.last_position = 0
        self.last_synced_position = 0
        self.is_finished = False
        # File this monitor tracks; stop when the playlist moves on.
        self.playing_file = None
        
        # Initialize sync manager with library service
        self.sync_mgr = get_sync_manager()
        self.sync_mgr.set_library_service(library_service)
        
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        xbmc.log(f"[MONITOR] Created for {key}, duration={duration:.1f}s, file_offset={file_offset:.1f}s, "
                f"sync_enabled={sync_enabled}, library_service={'YES' if library_service else 'NO'}", xbmc.LOGINFO)
    
    def start_monitoring_async(self, start_position=0):
        """Start monitoring in background"""
        self.start_position = start_position
        self.is_monitoring = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
        
        xbmc.log(f"[MONITOR] Started for {self.item_id} at {start_position:.1f}s", xbmc.LOGINFO)
    
    def _monitor_worker(self):
        """Background monitoring worker"""
        try:
            # Wait for player to start
            wait_count = 0
            while not self.player.isPlaying() and wait_count < 60:
                xbmc.sleep(500)
                wait_count += 1
            
            if not self.player.isPlaying():
                xbmc.log("[MONITOR] Player never started", xbmc.LOGWARNING)
                return
            
            xbmc.sleep(1500)
            
            # Try to get duration from player if we don't have a valid one
            if self.duration <= 1:
                try:
                    player_duration = self.player.getTotalTime()
                    if player_duration > 1:
                        self.duration = player_duration
                        xbmc.log(f"[MONITOR] Got duration from player: {self.duration:.1f}s", xbmc.LOGINFO)
                except:
                    pass
            
            # Seek to position if needed
            if self.start_position > 0:
                try:
                    xbmc.sleep(500)
                    self.player.seekTime(self.start_position)
                    xbmc.log(f"[MONITOR] Seeked to {self.start_position:.1f}s", xbmc.LOGINFO)
                except Exception as e:
                    xbmc.log(f"[MONITOR] Seek error: {str(e)}", xbmc.LOGERROR)
            
            # Start session if we have library service
            if self.library_service and self.sync_enabled:
                try:
                    session = self.library_service.start_playback_session(self.item_id, self.episode_id)
                    if session:
                        self.session_id = session.get('id')
                        xbmc.log(f"[MONITOR] Started session: {self.session_id}", xbmc.LOGINFO)
                except Exception as e:
                    xbmc.log(f"[MONITOR] Session start error: {str(e)}", xbmc.LOGDEBUG)
            
            # Bind this monitor to the file that is now playing.
            try:
                self.playing_file = self.player.getPlayingFile()
            except Exception:
                self.playing_file = None

            last_sync_time = time.time()
            self.last_position = self.start_position
            self.last_synced_position = self.start_position
            # For time_listened since the last session sync.
            self._session_clock = time.time()
            self._session_position = self.start_position + self.file_offset

            # Main monitoring loop
            while self.is_monitoring:
                try:
                    if not self.player.isPlayingAudio():
                        xbmc.log("[MONITOR] Audio playback stopped", xbmc.LOGINFO)
                        break

                    # Playlist advanced: stop before saving the next item's time here.
                    if self.playing_file:
                        try:
                            current_file = self.player.getPlayingFile()
                        except Exception:
                            current_file = self.playing_file
                        if current_file and current_file != self.playing_file:
                            xbmc.log("[MONITOR] Playing file changed (playlist advanced); stopping monitor", xbmc.LOGINFO)
                            break

                    current_time = self.player.getTime()
                    self.last_position = current_time
                    
                    # Update duration from player if still not set properly
                    if self.duration <= 1:
                        try:
                            player_duration = self.player.getTotalTime()
                            if player_duration > 1:
                                self.duration = player_duration
                                xbmc.log(f"[MONITOR] Updated duration from player: {self.duration:.1f}s", xbmc.LOGINFO)
                        except:
                            pass
                    
                    # Periodic sync
                    elapsed = time.time() - last_sync_time
                    if self.sync_enabled and elapsed >= self.sync_interval:
                        # Only sync if position changed significantly (more than 5 seconds)
                        if abs(current_time - self.last_synced_position) > 5:
                            xbmc.log(f"[MONITOR] Periodic sync at {current_time:.1f}s", xbmc.LOGINFO)
                            self._save_progress(current_time, is_final=False)
                            self._sync_session(current_time)
                            self.last_synced_position = current_time
                        last_sync_time = time.time()
                    
                except Exception as e:
                    xbmc.log(f"[MONITOR] Loop error: {str(e)}", xbmc.LOGERROR)
                
                xbmc.sleep(2000)
            
            # Final sync when playback stops
            if self.sync_on_stop and self.last_position > 0:
                xbmc.log(f"[MONITOR] Final sync at {self.last_position:.1f}s", xbmc.LOGINFO)
                self._save_progress(self.last_position, is_final=True)
            
            # Close session, recording the final position in the same call
            if self.session_id and self.library_service:
                try:
                    overall_time = self.last_position + self.file_offset
                    self.library_service.close_playback_session(
                        self.session_id,
                        current_time=overall_time,
                        duration=self.duration,
                        time_listened=self._listened_since_last_sync(self.last_position)
                    )
                    xbmc.log(f"[MONITOR] Closed session: {self.session_id}", xbmc.LOGINFO)
                except:
                    pass
            
            xbmc.log("[MONITOR] Stopped", xbmc.LOGINFO)
            
        except Exception as e:
            xbmc.log(f"[MONITOR] Worker error: {str(e)}", xbmc.LOGERROR)
    
    def _listened_since_last_sync(self, current_time):
        """Seconds listened since the last sync: min(position delta, wall-clock time)."""
        overall_time = current_time + self.file_offset
        wall_elapsed = time.time() - getattr(self, '_session_clock', time.time())
        position_delta = overall_time - getattr(self, '_session_position', overall_time)
        return max(0, min(position_delta, wall_elapsed))

    def _sync_session(self, current_time):
        """Push the current position to the open server-side playback session."""
        if not self.session_id or not self.library_service:
            return
        try:
            overall_time = current_time + self.file_offset
            listened = self._listened_since_last_sync(current_time)
            self.library_service.sync_playback_session(
                self.session_id, overall_time, self.duration, time_listened=listened)
            self._session_clock = time.time()
            self._session_position = overall_time
            xbmc.log(f"[MONITOR] Session synced at {overall_time:.1f}s "
                     f"(+{listened:.0f}s listened)", xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log(f"[MONITOR] Session sync error: {str(e)}", xbmc.LOGDEBUG)

    def _save_progress(self, current_time, is_final=False):
        """Save progress using sync_manager"""
        try:
            # Add file_offset to get the overall audiobook position
            # current_time is the position within this file
            # file_offset is where this file starts in the overall audiobook
            overall_time = current_time + self.file_offset
            
            # Calculate progress percentage using overall time
            progress_pct = overall_time / self.duration if self.duration > 0 else 0
            
            # Determine if finished - only on final sync and if past threshold
            finished = False
            if is_final and progress_pct >= self.finished_threshold:
                finished = True
                xbmc.log(f"[MONITOR] Marking as finished: {progress_pct*100:.1f}% >= {self.finished_threshold*100:.1f}%", xbmc.LOGINFO)
            
            if finished:
                self.is_finished = True
            
            xbmc.log(f"[MONITOR] Saving: file_time={current_time:.1f}s + offset={self.file_offset:.1f}s = "
                    f"overall={overall_time:.1f}s / {self.duration:.1f}s ({progress_pct*100:.1f}%) "
                    f"finished={finished} is_final={is_final}", xbmc.LOGINFO)
            
            # Use sync_manager for all progress operations - pass OVERALL time
            if is_final:
                # Final sync - use on_playback_stop for full sync handling
                self.sync_mgr.on_playback_stop(
                    self.item_id, 
                    self.episode_id, 
                    overall_time,  # Use overall time, not file time
                    self.duration, 
                    is_finished=finished
                )
            else:
                # Periodic sync
                self.sync_mgr.on_playback_progress(
                    self.item_id, 
                    self.episode_id, 
                    overall_time,  # Use overall time, not file time
                    self.duration, 
                    is_finished=finished
                )
            
        except Exception as e:
            xbmc.log(f"[MONITOR] Save progress error: {str(e)}", xbmc.LOGERROR)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)


# Re-export the functions from sync_manager for backward compatibility
# These are already imported at the top and can be used directly:
# - get_local_progress
# - save_local_progress  
# - get_best_resume_position
# - sync_all_to_server
# - mark_synced

# For explicit backward compatibility exports
__all__ = [
    'PlaybackMonitor',
    'get_local_progress',
    'save_local_progress',
    'get_best_resume_position',
    'sync_all_to_server',
    'mark_synced'
]
