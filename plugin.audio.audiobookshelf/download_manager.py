import os
import json
import xbmc
import xbmcgui
import xbmcvfs
import requests
import threading
import subprocess
from datetime import datetime


class DownloadManager:
    """Manage offline downloads of audiobooks and podcasts"""
    
    def __init__(self, addon):
        self.addon = addon
        self.download_path = self._get_download_path()
        self.metadata_file = os.path.join(self.download_path, 'downloads.json')
        self.resume_file = os.path.join(self.download_path, 'resume_positions.json')
        self.downloads = self._load_metadata()
        self.resume_positions = self._load_resume_positions()
        self.active_downloads = {}
        
    def _get_download_path(self):
        """Get configured download path"""
        path = self.addon.getSetting('download_path')
        
        # If path is empty or not set, use profile directory
        if not path or path.strip() == '':
            path = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
            path = os.path.join(path, 'downloads')
        else:
            path = xbmcvfs.translatePath(path)
        
        # Only create directory if downloads are enabled
        if self.addon.getSetting('enable_downloads').lower() == 'true':
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    pass
        
        return path
    
    def _load_metadata(self):
        """Load download metadata"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save download metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.downloads, f, indent=2)
        except Exception as e:
            xbmc.log(f"Error saving download metadata: {str(e)}", xbmc.LOGERROR)
    
    def _load_resume_positions(self):
        """Load locally saved resume positions"""
        if os.path.exists(self.resume_file):
            try:
                with open(self.resume_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_resume_positions(self):
        """Save resume positions locally"""
        try:
            with open(self.resume_file, 'w') as f:
                json.dump(self.resume_positions, f, indent=2)
        except Exception as e:
            xbmc.log(f"Error saving resume positions: {str(e)}", xbmc.LOGERROR)
    
    def save_resume_position(self, item_id, episode_id, current_time, duration, is_finished=False):
        """Save resume position locally for offline use"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        self.resume_positions[key] = {
            'item_id': item_id,
            'episode_id': episode_id,
            'current_time': current_time,
            'duration': duration,
            'is_finished': is_finished,
            'updated_at': datetime.now().isoformat(),
            'synced': False
        }
        self._save_resume_positions()
    
    def get_local_resume_position(self, item_id, episode_id=None):
        """Get locally saved resume position"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        return self.resume_positions.get(key)
    
    def mark_position_synced(self, item_id, episode_id=None):
        """Mark a resume position as synced to server"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        if key in self.resume_positions:
            self.resume_positions[key]['synced'] = True
            self._save_resume_positions()
    
    def get_unsynced_positions(self):
        """Get all resume positions that haven't been synced"""
        return {k: v for k, v in self.resume_positions.items() if not v.get('synced', False)}
    
    def sync_positions_to_server(self, library_service):
        """Sync all unsynced resume positions to server"""
        unsynced = self.get_unsynced_positions()
        synced_count = 0
        
        for key, pos in unsynced.items():
            try:
                library_service.update_media_progress(
                    pos['item_id'],
                    pos['current_time'],
                    pos['duration'],
                    is_finished=pos.get('is_finished', False),
                    episode_id=pos.get('episode_id')
                )
                self.mark_position_synced(pos['item_id'], pos.get('episode_id'))
                synced_count += 1
            except Exception as e:
                xbmc.log(f"Error syncing position for {key}: {str(e)}", xbmc.LOGERROR)
        
        if synced_count > 0:
            xbmc.log(f"Synced {synced_count} resume positions to server", xbmc.LOGINFO)
        
        return synced_count
    
    def is_downloaded(self, item_id, episode_id=None):
        """Check if item is downloaded"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        if key not in self.downloads:
            return False
        
        download_info = self.downloads[key]
        
        # For multi-file downloads, check if all files exist
        if 'files' in download_info:
            return all(os.path.exists(f['path']) for f in download_info['files'])
        
        # Single file download
        return os.path.exists(download_info.get('file_path', ''))
    
    def get_download_path_for_item(self, item_id, episode_id=None):
        """Get local file path for downloaded item"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        if key not in self.downloads:
            return None
        
        download_info = self.downloads[key]
        
        # For multi-file, return first file (caller should use get_download_info for full list)
        if 'files' in download_info and download_info['files']:
            return download_info['files'][0]['path']
        
        return download_info.get('file_path')
    
    def get_download_info(self, item_id, episode_id=None):
        """Get download metadata"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        return self.downloads.get(key)
    
    def download_item(self, item_id, item_data, library_service, episode_id=None, show_progress=True):
        """Download an item for offline playback"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        
        if self.is_downloaded(item_id, episode_id):
            if show_progress:
                xbmcgui.Dialog().notification('Already Downloaded', 
                                             item_data['title'], 
                                             xbmcgui.NOTIFICATION_INFO)
            return True
        
        if key in self.active_downloads:
            if show_progress:
                xbmcgui.Dialog().notification('Already Downloading', 
                                             item_data['title'], 
                                             xbmcgui.NOTIFICATION_INFO)
            return True
        
        item_folder = os.path.join(self.download_path, self._sanitize_filename(item_id))
        if not os.path.exists(item_folder):
            os.makedirs(item_folder)
        
        self.active_downloads[key] = True
        
        if show_progress:
            thread = threading.Thread(
                target=self._download_worker_with_progress,
                args=(item_id, item_data, library_service, episode_id, item_folder, key)
            )
            thread.daemon = True
            thread.start()
        else:
            # Synchronous download without dialog (for batch downloads)
            self._download_worker_silent(item_id, item_data, library_service, episode_id, item_folder, key)
        
        return True
    
    def _download_worker_silent(self, item_id, item_data, library_service, episode_id, item_folder, key):
        """Background download worker without progress dialog"""
        try:
            download_url = library_service.get_file_url(item_id, episode_id=episode_id)
            
            title = self._sanitize_filename(item_data['title'])
            if episode_id:
                filename = f"{title}_{episode_id}.m4b"
            else:
                filename = f"{title}.m4b"
            
            file_path = os.path.join(item_folder, filename)
            
            response = requests.get(download_url, stream=True, timeout=30)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            cover_path = self._download_cover(item_data.get('cover_url'), item_folder, item_data['title'])
            
            # Embed cover into the audio file if available
            if cover_path and os.path.exists(cover_path):
                self._embed_cover_in_file(file_path, cover_path, item_data)
            
            self.downloads[key] = {
                'item_id': item_id,
                'episode_id': episode_id,
                'title': item_data['title'],
                'podcast_title': item_data.get('podcast_title', ''),
                'file_path': file_path,
                'cover_path': cover_path,
                'duration': item_data.get('duration', 0),
                'description': item_data.get('description', ''),
                'author': item_data.get('author', ''),
                'narrator': item_data.get('narrator', ''),
                # Podcast episode publish time (epoch ms) so offline auto-play
                # can order episodes chronologically, matching the online queue.
                'published_at': item_data.get('publishedAt', 0),
                'downloaded_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(file_path),
                'is_multifile': False
            }
            self._save_metadata()
            
            del self.active_downloads[key]
            xbmc.log(f"Download completed: {filename}", xbmc.LOGINFO)
            
        except Exception as e:
            if key in self.active_downloads:
                del self.active_downloads[key]
            xbmc.log(f"Download error: {str(e)}", xbmc.LOGERROR)
            raise
    
    def download_audiobook_complete(self, item_id, item_data, library_service):
        """Download complete audiobook as one combined file"""
        key = item_id
        
        if self.is_downloaded(item_id):
            xbmcgui.Dialog().notification('Already Downloaded', 
                                         item_data['title'], 
                                         xbmcgui.NOTIFICATION_INFO)
            return True
        
        if key in self.active_downloads:
            xbmcgui.Dialog().notification('Already Downloading', 
                                         item_data['title'], 
                                         xbmcgui.NOTIFICATION_INFO)
            return True
        
        item_folder = os.path.join(self.download_path, self._sanitize_filename(item_id))
        if not os.path.exists(item_folder):
            os.makedirs(item_folder)
        
        self.active_downloads[key] = True
        
        thread = threading.Thread(
            target=self._download_combined_worker,
            args=(item_id, item_data, library_service, item_folder, key)
        )
        thread.daemon = True
        thread.start()
        
        return True
    
    def _download_combined_worker(self, item_id, item_data, library_service, item_folder, key):
        """Download audiobook as one combined file with embedded chapters"""
        try:
            audio_files = item_data.get('audio_files', [])
            chapters = item_data.get('chapters', [])
            
            if not audio_files:
                raise ValueError("No audio files found")
            
            # Sort by index
            audio_files = sorted(audio_files, key=lambda x: x.get('index', 0))
            
            # Show start notification
            xbmcgui.Dialog().notification('Download Started', f'Preparing {item_data["title"]}', xbmcgui.NOTIFICATION_INFO, 5000)
            
            # Download all individual files first
            temp_files = []
            total_files = len(audio_files)
            
            for i, audio_file in enumerate(audio_files):
                ino = audio_file.get('ino')
                file_index = audio_file.get('index', i)
                
                # Get download URL
                download_url = f"{library_service.base_url}/api/items/{item_id}/file/{ino}?token={library_service.token}"
                
                # Show progress notification for each file
                if total_files > 1:
                    xbmcgui.Dialog().notification('Download Progress', f'{item_data["title"]} - File {i+1}/{total_files}', xbmcgui.NOTIFICATION_INFO, 2000)
                
                # Download to temp file
                temp_filename = f"temp_{file_index:03d}.tmp"
                temp_path = os.path.join(item_folder, temp_filename)
                
                response = requests.get(download_url, stream=True, timeout=30)
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                temp_files.append({
                    'path': temp_path,
                    'index': file_index,
                    'duration': audio_file.get('duration', 0)
                })
            
            # Show combining notification
            xbmcgui.Dialog().notification('Download Progress', f'{item_data["title"]} - Combining files...', xbmcgui.NOTIFICATION_INFO, 3000)
            
            combined_filename = f"{self._sanitize_filename(item_data['title'])}.m4b"
            combined_path = os.path.join(item_folder, combined_filename)
            
            self._combine_audio_files(temp_files, combined_path, chapters, item_data)
            
            # Clean up temp files
            self._cleanup_temp_files(temp_files)
            
            # Download cover
            cover_path = self._download_cover(item_data.get('cover_url'), item_folder, item_data['title'])
            
            # Save metadata for single file
            self.downloads[key] = {
                'item_id': item_id,
                'episode_id': None,
                'title': item_data['title'],
                'file_path': combined_path,
                'cover_path': cover_path,
                'duration': item_data.get('duration', 0),
                'author': item_data.get('author', ''),
                'narrator': item_data.get('narrator', ''),
                'chapters': chapters,  # Preserve chapter metadata
                'downloaded_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(combined_path),
                'is_multifile': False  # Single file now
            }
            self._save_metadata()
            
            del self.active_downloads[key]
            
            xbmc.log(f"Combined download completed: {item_data['title']}", xbmc.LOGINFO)
            xbmcgui.Dialog().notification('Download Complete', item_data['title'], xbmcgui.NOTIFICATION_INFO)
            
        except Exception as e:
            if key in self.active_downloads:
                del self.active_downloads[key]
            
            xbmc.log(f"Combined download error: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Download Failed', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)
    
    def _combine_audio_files(self, temp_files, output_path, chapters, item_data):
        """Combine multiple audio files into one M4B with embedded chapters"""
        try:
            # Try to use ffmpeg for combining with chapter metadata
            import subprocess
            
            # Create input list for ffmpeg
            input_args = []
            for temp_file in sorted(temp_files, key=lambda x: x['index']):
                input_args.extend(['-i', temp_file['path']])
            
            # Build metadata file for chapters if available
            metadata_file = None
            if chapters:
                metadata_file = self._create_chapter_metadata(chapters, output_path)
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg', '-y'  # Overwrite output file
            ] + input_args + [
                '-filter_complex', f'concat=n={len(temp_files)}:v=0:a=1[out]',
                '-map', '[out]',
                '-c:a', 'aac',  # Use AAC codec for M4B compatibility
                '-b:a', '192k',  # Good quality
                '-f', 'mp4',
            ]
            
            # Add metadata if available
            if metadata_file:
                cmd.extend(['-i', metadata_file, '-map_metadata', '1'])
            
            # Add book metadata
            cmd.extend([
                '-metadata', f'title={item_data.get("title", "")}',
                '-metadata', f'artist={item_data.get("author", "")}',
                '-metadata', f'album={item_data.get("title", "")}',
                '-metadata', f'genre=Audiobook',
            ])
            
            # Add cover if available
            cover_path = item_data.get('cover_path')
            if cover_path and os.path.exists(cover_path):
                cmd.extend(['-i', cover_path, '-map', '2:0', '-disposition:v:0', 'attached_pic'])
            
            cmd.append(output_path)
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Clean up metadata file
            if metadata_file and os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            if result.returncode != 0:
                xbmc.log(f"FFmpeg combine failed: {result.stderr}", xbmc.LOGERROR)
                # Fallback to simple concatenation
                self._fallback_combine(temp_files, output_path)
            else:
                xbmc.log("Successfully combined audio files with FFmpeg and chapters", xbmc.LOGINFO)
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            xbmc.log(f"FFmpeg not available or failed: {str(e)}", xbmc.LOGWARNING)
            # Fallback to simple concatenation
            self._fallback_combine(temp_files, output_path)
    
    def _create_chapter_metadata(self, chapters, output_path):
        """Create FFmpeg metadata file for chapters"""
        try:
            metadata_path = output_path.replace('.m4b', '_metadata.txt')
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(';FFMETADATA1\n')
                
                for i, chapter in enumerate(chapters):
                    start = chapter.get('start', 0)
                    end = chapter.get('end', 0)
                    title = chapter.get('title', f'Chapter {i+1}')
                    
                    # Convert to milliseconds for FFmpeg
                    start_ms = int(start * 1000)
                    end_ms = int(end * 1000)
                    
                    f.write('[CHAPTER]\n')
                    f.write('TIMEBASE=1/1000\n')
                    f.write(f'START={start_ms}\n')
                    f.write(f'END={end_ms}\n')
                    f.write(f'title={title}\n')
            
            return metadata_path
            
        except Exception as e:
            xbmc.log(f"Failed to create chapter metadata: {str(e)}", xbmc.LOGERROR)
            return None
    
    def _fallback_combine(self, temp_files, output_path):
        """Fallback method to combine files without ffmpeg"""
        try:
            # Simple concatenation for MP3 files
            with open(output_path, 'wb') as outfile:
                for temp_file in sorted(temp_files, key=lambda x: x['index']):
                    with open(temp_file['path'], 'rb') as infile:
                        outfile.write(infile.read())
            
            xbmc.log("Used fallback concatenation method", xbmc.LOGINFO)
            
        except Exception as e:
            xbmc.log(f"Fallback combine failed: {str(e)}", xbmc.LOGERROR)
            raise
    
    def _embed_cover_in_file(self, audio_path, cover_path, item_data):
        """Embed cover image into audio file using FFmpeg"""
        try:
            # Create temporary output file
            temp_output = audio_path.replace('.m4b', '_temp.m4b').replace('.mp3', '_temp.mp3')
            
            # Build FFmpeg command to embed cover
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', audio_path,  # Input audio
                '-i', cover_path,  # Input cover
                '-map', '0:a',    # Map audio stream
                '-map', '1:v',    # Map cover as video stream
                '-c:a', 'copy',   # Copy audio codec
                '-c:v', 'mjpeg',   # Convert cover to MJPEG
                '-disposition:v:0', 'attached_pic',  # Mark as attached picture
                '-metadata', f'title={item_data.get("title", "")}',
                '-metadata', f'artist={item_data.get("author", "")}',
                '-metadata', f'album={item_data.get("title", "")}',
            ]
            
            # Add genre based on content type
            if item_data.get('episode_id'):
                cmd.extend(['-metadata', 'genre=Podcast'])
            else:
                cmd.extend(['-metadata', 'genre=Audiobook'])
            
            cmd.append(temp_output)
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Replace original with temp file
                os.remove(audio_path)
                os.rename(temp_output, audio_path)
                xbmc.log(f"Successfully embedded cover in {os.path.basename(audio_path)}", xbmc.LOGINFO)
            else:
                xbmc.log(f"Cover embedding failed: {result.stderr}", xbmc.LOGERROR)
                # Clean up temp file if it exists
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                    
        except Exception as e:
            xbmc.log(f"Cover embedding error: {str(e)}", xbmc.LOGERROR)
    
    def _cleanup_temp_files(self, temp_files):
        """Clean up temporary files"""
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file['path']):
                    os.remove(temp_file['path'])
            except:
                pass
    
    def _download_multifile_worker(self, item_id, item_data, library_service, item_folder, key):
        """Download all files for a multi-file audiobook (legacy method)"""
        try:
            audio_files = item_data.get('audio_files', [])
            if not audio_files:
                raise ValueError("No audio files found")
            
            # Sort by index
            audio_files = sorted(audio_files, key=lambda x: x.get('index', 0))
            
            total_files = len(audio_files)
            downloaded_files = []
            
            # Show start notification
            xbmcgui.Dialog().notification('Download Started', f'{item_data["title"]} - 0/{total_files} files', xbmcgui.NOTIFICATION_INFO, 5000)
            
            total_size = sum(f.get('size', 0) for f in audio_files)
            downloaded_total = 0
            
            for i, audio_file in enumerate(audio_files):
                ino = audio_file.get('ino')
                file_index = audio_file.get('index', i)
                file_duration = audio_file.get('duration', 0)
                file_size = audio_file.get('size', 0)
                
                # Create filename
                ext = os.path.splitext(audio_file.get('metadata', {}).get('filename', 'audio.mp3'))[1] or '.mp3'
                filename = f"{self._sanitize_filename(item_data['title'])}_{file_index:03d}{ext}"
                file_path = os.path.join(item_folder, filename)
                
                # Get download URL
                download_url = f"{library_service.base_url}/api/items/{item_id}/file/{ino}?token={library_service.token}"
                
                # Show progress notification for each file
                xbmcgui.Dialog().notification('Download Progress', f'{item_data["title"]} - File {i+1}/{total_files}', xbmcgui.NOTIFICATION_INFO, 2000)
                
                # Download file
                response = requests.get(download_url, stream=True, timeout=30)
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_total += len(chunk)
                
                downloaded_files.append({
                    'path': file_path,
                    'ino': ino,
                    'index': file_index,
                    'duration': file_duration,
                    'size': os.path.getsize(file_path)
                })
            
            # Download cover
            cover_path = self._download_cover(item_data.get('cover_url'), item_folder, item_data['title'])
            
            # Save metadata
            self.downloads[key] = {
                'item_id': item_id,
                'episode_id': None,
                'title': item_data['title'],
                'files': downloaded_files,
                'cover_path': cover_path,
                'duration': item_data.get('duration', 0),
                'author': item_data.get('author', ''),
                'narrator': item_data.get('narrator', ''),
                'chapters': item_data.get('chapters', []),
                'downloaded_at': datetime.now().isoformat(),
                'is_multifile': True
            }
            self._save_metadata()
            
            del self.active_downloads[key]
            
            xbmc.log(f"Download completed: {item_data['title']} ({total_files} files)", xbmc.LOGINFO)
            xbmcgui.Dialog().notification('Download Complete', item_data['title'], xbmcgui.NOTIFICATION_INFO)
            
        except Exception as e:
            if key in self.active_downloads:
                del self.active_downloads[key]
            
            xbmc.log(f"Download error: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Download Failed', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)
    
    def _cleanup_partial_download(self, downloaded_files):
        """Clean up partially downloaded files"""
        for f in downloaded_files:
            try:
                if os.path.exists(f['path']):
                    os.remove(f['path'])
            except:
                pass
    
    def _download_cover(self, cover_url, item_folder, title):
        """Download cover image"""
        if not cover_url:
            return None
        
        try:
            cover_filename = f"{self._sanitize_filename(title)}_cover.jpg"
            cover_path = os.path.join(item_folder, cover_filename)
            
            if cover_url.startswith('http'):
                response = requests.get(cover_url, timeout=10)
                with open(cover_path, 'wb') as f:
                    f.write(response.content)
            else:
                import shutil
                shutil.copy(cover_url, cover_path)
            
            return cover_path
        except Exception as e:
            xbmc.log(f"Error downloading cover: {str(e)}", xbmc.LOGWARNING)
            return None
    
    def _download_worker_with_progress(self, item_id, item_data, library_service, episode_id, item_folder, key):
        """Background download worker for single file"""
        try:
            download_url = library_service.get_file_url(item_id, episode_id=episode_id)
            
            title = self._sanitize_filename(item_data['title'])
            if episode_id:
                filename = f"{title}_{episode_id}.m4b"
            else:
                filename = f"{title}.m4b"
            
            file_path = os.path.join(item_folder, filename)
            
            # Show start notification
            xbmcgui.Dialog().notification('Download Started', item_data["title"], xbmcgui.NOTIFICATION_INFO, 5000)
            
            response = requests.get(download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            last_notification_percent = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            # Show progress notifications at 25%, 50%, 75%
                            if percent >= 75 and last_notification_percent < 75:
                                xbmcgui.Dialog().notification('Download Progress', f'{item_data["title"]} - 75%', xbmcgui.NOTIFICATION_INFO, 3000)
                                last_notification_percent = 75
                            elif percent >= 50 and last_notification_percent < 50:
                                xbmcgui.Dialog().notification('Download Progress', f'{item_data["title"]} - 50%', xbmcgui.NOTIFICATION_INFO, 3000)
                                last_notification_percent = 50
                            elif percent >= 25 and last_notification_percent < 25:
                                xbmcgui.Dialog().notification('Download Progress', f'{item_data["title"]} - 25%', xbmcgui.NOTIFICATION_INFO, 3000)
                                last_notification_percent = 25
            
            cover_path = self._download_cover(item_data.get('cover_url'), item_folder, item_data['title'])
            
            self.downloads[key] = {
                'item_id': item_id,
                'episode_id': episode_id,
                'title': item_data['title'],
                'podcast_title': item_data.get('podcast_title', ''),
                'file_path': file_path,
                'cover_path': cover_path,
                'duration': item_data.get('duration', 0),
                'description': item_data.get('description', ''),
                'author': item_data.get('author', ''),
                'narrator': item_data.get('narrator', ''),
                # Podcast episode publish time (epoch ms) so offline auto-play
                # can order episodes chronologically, matching the online queue.
                'published_at': item_data.get('publishedAt', 0),
                'downloaded_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(file_path),
                'is_multifile': False
            }
            self._save_metadata()
            
            del self.active_downloads[key]
            
            xbmc.log(f"Download completed: {filename}", xbmc.LOGINFO)
            xbmcgui.Dialog().notification('Download Complete', item_data['title'], xbmcgui.NOTIFICATION_INFO)
            
        except Exception as e:
            if key in self.active_downloads:
                del self.active_downloads[key]
            
            xbmc.log(f"Download error: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Download Failed', str(e)[:50], xbmcgui.NOTIFICATION_ERROR)
    
    def delete_download(self, item_id, episode_id=None):
        """Delete downloaded item"""
        key = f"{item_id}_{episode_id}" if episode_id else item_id
        
        if key not in self.downloads:
            return False
        
        download_info = self.downloads[key]
        
        # Delete files
        if 'files' in download_info:
            for f in download_info['files']:
                if os.path.exists(f['path']):
                    os.remove(f['path'])
        elif download_info.get('file_path') and os.path.exists(download_info['file_path']):
            os.remove(download_info['file_path'])
        
        # Delete cover
        if download_info.get('cover_path') and os.path.exists(download_info['cover_path']):
            os.remove(download_info['cover_path'])
        
        del self.downloads[key]
        self._save_metadata()
        
        xbmcgui.Dialog().notification('Download Deleted', download_info['title'], xbmcgui.NOTIFICATION_INFO)
        return True
    
    def get_all_downloads(self):
        """Get list of all downloaded items"""
        return self.downloads
    
    def delete_all_downloads(self):
        """Delete all downloaded items"""
        deleted_count = 0
        failed_count = 0
        
        for key in list(self.downloads.keys()):
            try:
                download_info = self.downloads[key]
                
                # Delete files
                if 'files' in download_info:
                    for f in download_info['files']:
                        if os.path.exists(f['path']):
                            os.remove(f['path'])
                elif download_info.get('file_path') and os.path.exists(download_info['file_path']):
                    os.remove(download_info['file_path'])
                
                # Delete cover
                if download_info.get('cover_path') and os.path.exists(download_info['cover_path']):
                    os.remove(download_info['cover_path'])
                
                # Delete item folder if empty
                item_folder = os.path.dirname(download_info.get('file_path') or 
                                             (download_info.get('files', [{}])[0].get('path') if download_info.get('files') else ''))
                if item_folder and os.path.exists(item_folder):
                    try:
                        if not os.listdir(item_folder):  # Folder is empty
                            os.rmdir(item_folder)
                    except:
                        pass
                
                deleted_count += 1
            except Exception as e:
                xbmc.log(f"Error deleting download {key}: {str(e)}", xbmc.LOGERROR)
                failed_count += 1
        
        # Clear metadata
        self.downloads.clear()
        self._save_metadata()
        
        # Clear resume positions
        self.resume_positions.clear()
        self._save_resume_positions()
        
        return deleted_count, failed_count
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for filesystem"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100]  # Limit length
    
    def get_file_for_position(self, item_id, position):
        """
        Get the correct file and seek position for a download.
        
        Returns:
            (file_path, seek_in_file, file_offset)
            - file_path: Path to the file containing this position
            - seek_in_file: Position to seek to within this file
            - file_offset: Where this file starts in the overall audiobook timeline
        """
        download_info = self.get_download_info(item_id)
        if not download_info:
            return None, 0, 0
        
        # For combined single files, just return the file and position
        if not download_info.get('is_multifile'):
            file_path = download_info.get('file_path')
            return file_path, position, 0
        
        # Legacy multi-file handling
        files = download_info.get('files', [])
        files = sorted(files, key=lambda x: x.get('index', 0))
        
        cumulative = 0
        for f in files:
            file_duration = f.get('duration', 0)
            if cumulative <= position < cumulative + file_duration:
                seek_in_file = position - cumulative
                file_offset = cumulative  # Where this file starts
                return f['path'], seek_in_file, file_offset
            cumulative += file_duration
        
        # Position beyond all files, return last file at end
        if files:
            last_file = files[-1]
            last_offset = cumulative - last_file.get('duration', 0)
            return last_file['path'], 0, last_offset
        
        return None, 0, 0


def is_network_available():
    """Check if network is available"""
    try:
        requests.get('http://www.google.com', timeout=2)
        return True
    except:
        return False
