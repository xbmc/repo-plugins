import requests
import xbmc
import json

class AudioBookShelfLibraryService:
	"""Library service for Audiobookshelf API - Kodi 21 compatible"""
	
	def __init__(self, base_url=None, token=None):
		"""Initialize the library service with base URL and authentication token"""
		self.token = token
		self.base_url = base_url
		self.headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {token}"
		}

	def get_all_libraries(self):
		"""Get all available libraries from the server"""
		url = f"{self.base_url}/api/libraries"
		response = requests.get(url, headers=self.headers)
		response.raise_for_status()
		return response.json()

	def get_library(self, library_id, include_filterdata=False):
		"""Get details for a specific library"""
		url = f"{self.base_url}/api/libraries/{library_id}"
		params = {}
		if include_filterdata:
			params["include"] = "filterdata"
		
		response = requests.get(url, headers=self.headers, params=params)
		response.raise_for_status()
		return response.json()

	def get_library_items(self, library_id, limit=None, page=None, sort=None, desc=None, 
						  filter=None, minified=None, collapseseries=None, include=None):
		"""Get items from a specific library with optional filters"""
		url = f"{self.base_url}/api/libraries/{library_id}/items"
		params = {}
		
		if limit is not None:
			params["limit"] = limit
		if page is not None:
			params["page"] = page
		if sort is not None:
			params["sort"] = sort
		if desc is not None:
			params["desc"] = desc
		if filter is not None:
			params["filter"] = filter
		if minified is not None:
			params["minified"] = minified
		if collapseseries is not None:
			params["collapseseries"] = collapseseries
		if include is not None:
			params["include"] = include
			
		response = requests.get(url, headers=self.headers, params=params)
		response.raise_for_status()
		return response.json()

	def get_library_item_by_id(self, item_id, expanded=None, include=None, episode=None):
		"""Get detailed information about a specific library item"""
		url = f"{self.base_url}/api/items/{item_id}"
		params = {}
		
		if expanded is not None:
			params["expanded"] = expanded
		if include is not None:
			params["include"] = include
		if episode is not None:
			params["episode"] = episode
		
		response = requests.get(url, headers=self.headers, params=params)
		response.raise_for_status()
		return response.json()

	def play_library_item_by_id(self, item_id, episode_id=None, device_info=None, 
								force_direct_play=False, force_transcode=False, 
								supported_mime_types=None, media_player="unknown"):
		"""Request playback information for a library item"""
		if episode_id:
			url = f"{self.base_url}/api/items/{item_id}/play/{episode_id}"
		else:
			url = f"{self.base_url}/api/items/{item_id}/play"

		payload = {
			"forceDirectPlay": force_direct_play,
			"forceTranscode": force_transcode,
			"mediaPlayer": media_player
		}

		if device_info:
			payload["deviceInfo"] = device_info

		if supported_mime_types:
			payload["supportedMimeTypes"] = supported_mime_types

		response = requests.post(url, headers=self.headers, json=payload)
		response.raise_for_status()
		return response.json()

	def get_file_url(self, iid, episode_id=None):
		"""Get the streaming URL for an audiobook file or podcast episode"""
		try:
			# First try to get the item details to find direct file access
			item = self.get_library_item_by_id(iid, expanded=1, episode=episode_id)
			
			# For podcast episodes
			if episode_id:
				xbmc.log(f"Getting file URL for episode {episode_id}", xbmc.LOGINFO)
				
				# Look for the episode in the media
				episodes = item.get('media', {}).get('episodes', [])
				episode_data = None
				
				for ep in episodes:
					if ep.get('id') == episode_id:
						episode_data = ep
						break
				
				if episode_data:
					# Check for audioFile
					if 'audioFile' in episode_data and episode_data['audioFile']:
						audio_file = episode_data['audioFile']
						ino = audio_file.get('ino')
						
						if ino:
							direct_url = f"{self.base_url}/api/items/{iid}/file/{ino}?token={self.token}"
							xbmc.log(f"Using direct episode file URL: {direct_url}", xbmc.LOGINFO)
							return direct_url
					
					# Episode exists but no audio file - not downloaded on server
					raise Exception(f"Episode not downloaded on server")
				else:
					raise Exception(f"Episode {episode_id} not found")
			
			# For regular audiobooks - check if we can get direct file access
			media = item.get('media', {})
			audio_files = media.get('audioFiles', [])
			
			if audio_files and len(audio_files) > 0:
				# Sort by index and get the first audio file
				sorted_files = sorted(audio_files, key=lambda x: x.get('index', 0))
				audio_file = sorted_files[0]
				ino = audio_file.get('ino')
				
				if ino:
					direct_url = f"{self.base_url}/api/items/{iid}/file/{ino}?token={self.token}"
					xbmc.log(f"Using direct file URL: {direct_url}", xbmc.LOGINFO)
					return direct_url
			
			# Check for tracks (single file audiobooks like m4b)
			tracks = media.get('tracks', [])
			if tracks and len(tracks) > 0:
				# Use the content URL from track
				content_url = tracks[0].get('contentUrl')
				if content_url:
					direct_url = f"{self.base_url}{content_url}?token={self.token}"
					xbmc.log(f"Using track content URL: {direct_url}", xbmc.LOGINFO)
					return direct_url
			
			# Fallback to play session API
			xbmc.log("Falling back to play session API", xbmc.LOGINFO)
			try:
				response = self.play_library_item_by_id(
					iid,
					episode_id=episode_id,
					force_direct_play=True,
					supported_mime_types=["audio/flac", "audio/mpeg", "audio/mp4", "audio/m4b", "audio/x-m4b"]
				)

				if "audioTracks" in response and len(response["audioTracks"]) > 0:
					relative_content_url = response["audioTracks"][0]["contentUrl"]
					full_content_url = f"{self.base_url}{relative_content_url}?token={self.token}"
					xbmc.log(f"Using audioTrack URL: {full_content_url}", xbmc.LOGINFO)
					return full_content_url
			except Exception as play_err:
				xbmc.log(f"Play session API error: {str(play_err)}", xbmc.LOGDEBUG)
			
			raise Exception("No audio files found for this item")
			
		except Exception as e:
			xbmc.log(f"Error getting file URL: {str(e)}", xbmc.LOGERROR)
			raise

	def get_media_progress(self, library_item_id, episode_id=None):
		"""Get playback progress for a library item"""
		endpoint = f"/api/me/progress/{library_item_id}"
		if episode_id:
			endpoint += f"/{episode_id}"

		try:
			response = requests.get(self.base_url + endpoint, headers=self.headers)
			
			# 404 means no progress saved yet (not an error)
			if response.status_code == 404:
				xbmc.log(f"No progress found for item (new item)", xbmc.LOGINFO)
				return None
			
			response.raise_for_status()
			if not response.content:
				return None
			return response.json()
		except ValueError:
			# Kodi's bundled requests raises its own JSONDecodeError
			# (ValueError subclass), not stdlib json.JSONDecodeError.
			xbmc.log("Failed to decode JSON response for media progress", xbmc.LOGERROR)
			xbmc.log(response.text, xbmc.LOGDEBUG)
			return None
		except Exception as e:
			xbmc.log(f"Error getting media progress: {str(e)}", xbmc.LOGDEBUG)
			return None

	def update_media_progress(self, library_item_id, current_time, duration, is_finished=False, episode_id=None):
		"""Update playback progress on the server"""
		endpoint = f"/api/me/progress/{library_item_id}"
		if episode_id:
			endpoint += f"/{episode_id}"

		data = {
			"currentTime": current_time,
			"duration": duration,
			"isFinished": is_finished,
			"progress": (current_time / duration) if duration > 0 else 0
		}
		
		xbmc.log(f"[SYNC] Sending to {endpoint}: currentTime={current_time:.1f}, duration={duration:.1f}, progress={data['progress']*100:.1f}%, isFinished={is_finished}", xbmc.LOGINFO)
		
		try:
			response = requests.patch(self.base_url + endpoint, headers=self.headers, json=data)
			xbmc.log(f"[SYNC] Response status: {response.status_code}", xbmc.LOGINFO)
			response.raise_for_status()

			# A 2xx means the progress was saved. Audiobookshelf returns an
			# empty body here, and the Kodi-bundled requests raises its own
			# JSONDecodeError (a ValueError subclass, NOT the stdlib
			# json.JSONDecodeError) when parsing an empty body - so we must
			# catch ValueError, and short-circuit when there is no content.
			# Returning None on an empty-but-successful reply made SYNC_MGR
			# think the upload failed and retry it forever.
			if not response.content:
				xbmc.log(f"[SYNC] Success (empty response)", xbmc.LOGINFO)
				return {"success": True}
			try:
				result = response.json()
				xbmc.log(f"[SYNC] Success: Progress saved to server", xbmc.LOGINFO)
				return result
			except ValueError:
				xbmc.log(f"[SYNC] Success (non-JSON response)", xbmc.LOGINFO)
				return {"success": True}
				
		except requests.exceptions.HTTPError as e:
			xbmc.log(f"[SYNC] HTTP Error: {e.response.status_code} - {e.response.text[:100]}", xbmc.LOGERROR)
			return None
		except Exception as e:
			xbmc.log(f"[SYNC] Error updating media progress: {str(e)}", xbmc.LOGERROR)
			return None
	
	def start_playback_session(self, library_item_id, episode_id=None):
		"""Start a playback session on the server"""
		endpoint = f"/api/session/local"
		
		data = {
			"libraryItemId": library_item_id,
			"mediaPlayer": "Kodi",
			"deviceInfo": {
				"deviceId": "kodi-audiobookshelf-client",
				"clientName": "Kodi Audiobookshelf Client"
			}
		}
		
		if episode_id:
			data["episodeId"] = episode_id
		
		try:
			response = requests.post(self.base_url + endpoint, headers=self.headers, json=data)
			response.raise_for_status()
			session = response.json()
			xbmc.log(f"Started playback session: {session.get('id')}", xbmc.LOGINFO)
			return session
		except Exception as e:
			xbmc.log(f"Error starting playback session: {str(e)}", xbmc.LOGERROR)
			return None
	
	def sync_playback_session(self, session_id, current_time, duration, time_listened=0):
		"""Sync playback session with server"""
		endpoint = f"/api/session/local/{session_id}/sync"
		
		data = {
			"currentTime": current_time,
			"duration": duration,
			"timeListened": time_listened
		}
		
		try:
			response = requests.post(self.base_url + endpoint, headers=self.headers, json=data)
			response.raise_for_status()
			return response.json()
		except Exception as e:
			xbmc.log(f"Error syncing playback session: {str(e)}", xbmc.LOGDEBUG)
			return None
	
	def close_playback_session(self, session_id):
		"""Close a playback session on the server"""
		endpoint = f"/api/session/local/{session_id}/close"
		
		try:
			response = requests.post(self.base_url + endpoint, headers=self.headers)
			response.raise_for_status()
			xbmc.log(f"Closed playback session: {session_id}", xbmc.LOGINFO)
			return True
		except Exception as e:
			xbmc.log(f"Error closing playback session: {str(e)}", xbmc.LOGERROR)
			return False

	def get_chapters(self, library_item_id):
		"""Get chapter information for a library item"""
		try:
			item = self.get_library_item_by_id(library_item_id)
			chapters = item.get('media', {}).get('chapters', [])
			return chapters
		except Exception as e:
			xbmc.log(f"Error getting chapters: {str(e)}", xbmc.LOGERROR)
			return []

	# === PODCAST API ENDPOINTS ===
	
	def create_podcast(self, library_id, folder_id, podcast_metadata, folder_path=None):
		"""Create a new podcast in the library"""
		try:
			url = f"{self.base_url}/api/podcasts"
			payload = {
				"libraryId": library_id,
				"folderId": folder_id,
				"media": {
					"metadata": podcast_metadata
				},
				"autoDownloadEpisodes": False
			}
			
			# Add path if provided
			if folder_path:
				payload["path"] = folder_path
			
			response = requests.post(url, headers=self.headers, json=payload, timeout=30)
			response.raise_for_status()
			result = response.json()
			xbmc.log(f"Created podcast: {podcast_metadata.get('title', 'Unknown')}", xbmc.LOGINFO)
			return result
		except Exception as e:
			xbmc.log(f"Error creating podcast: {str(e)}", xbmc.LOGERROR)
			raise
	
	def get_podcast_feed(self, rss_feed, podcast_id=None):
		"""Get podcast feed information from RSS URL"""
		try:
			url = f"{self.base_url}/api/podcasts/feed"
			payload = {
				"rssFeed": rss_feed
			}
			if podcast_id:
				payload["podcastId"] = podcast_id
			
			response = requests.post(url, headers=self.headers, json=payload, timeout=30)
			response.raise_for_status()
			result = response.json()
			xbmc.log(f"Retrieved podcast feed: {rss_feed}", xbmc.LOGINFO)
			return result
		except Exception as e:
			xbmc.log(f"Error getting podcast feed: {str(e)}", xbmc.LOGERROR)
			raise
	
	def download_podcast_episodes(self, podcast_id, episode_ids):
		"""Download specific podcast episodes on the server"""
		try:
			url = f"{self.base_url}/api/podcasts/{podcast_id}/download-episodes"
			payload = episode_ids if isinstance(episode_ids, list) else [episode_ids]
			
			response = requests.post(url, headers=self.headers, json=payload, timeout=30)
			response.raise_for_status()
			result = response.json()
			xbmc.log(f"Queued download for {len(payload)} episodes", xbmc.LOGINFO)
			return result
		except Exception as e:
			xbmc.log(f"Error downloading podcast episodes: {str(e)}", xbmc.LOGERROR)
			raise
	
	def check_new_podcast_episodes(self, podcast_id):
		"""Check for new podcast episodes from RSS feed and add them to server"""
		try:
			url = f"{self.base_url}/api/podcasts/{podcast_id}/checknew"
			response = requests.get(url, headers=self.headers, timeout=30)
			response.raise_for_status()
			result = response.json()
			xbmc.log(f"Checked for new episodes: {result}", xbmc.LOGINFO)
			return result
		except Exception as e:
			xbmc.log(f"Error checking new podcast episodes: {str(e)}", xbmc.LOGERROR)
			raise
	
	def get_podcast_episode(self, podcast_id, episode_id):
		"""Get a specific podcast episode"""
		try:
			url = f"{self.base_url}/api/podcasts/{podcast_id}/episode/{episode_id}"
			response = requests.get(url, headers=self.headers, timeout=30)
			response.raise_for_status()
			result = response.json()
			xbmc.log(f"Retrieved podcast episode: {episode_id}", xbmc.LOGINFO)
			return result
		except Exception as e:
			xbmc.log(f"Error getting podcast episode: {str(e)}", xbmc.LOGERROR)
			raise
	
	def download_podcast_episodes_with_data(self, podcast_id, episode_data):
		"""Download specific podcast episodes with full episode data"""
		try:
			url = f"{self.base_url}/api/podcasts/{podcast_id}/download-episodes"
			payload = [episode_data] if isinstance(episode_data, dict) else episode_data
			
			response = requests.post(url, headers=self.headers, json=payload, timeout=30)
			response.raise_for_status()
			
			# Check if response has content
			if response.text.strip():
				result = response.json()
				xbmc.log(f"Downloaded podcast episode with data: {episode_data.get('title', 'Unknown')}", xbmc.LOGINFO)
				return result
			else:
				xbmc.log(f"Empty response from download API for: {episode_data.get('title', 'Unknown')}", xbmc.LOGWARNING)
				return {"success": False, "message": "Empty response"}
		except Exception as e:
			# Suppress JSON parsing errors if functionality is working
			error_msg = str(e)
			if "Expecting value" in error_msg and "line 1 column 1" in error_msg:
				xbmc.log(f"Suppressed JSON parsing error (functionality working): {error_msg}", xbmc.LOGDEBUG)
			else:
				xbmc.log(f"Error downloading podcast episodes with data: {error_msg}", xbmc.LOGERROR)
			raise
	
	def create_podcast_episode(self, podcast_id, episode_data):
		"""Create a new episode for a podcast"""
		try:
			# Note: Audiobookshelf doesn't support direct episode creation
			# Episodes must be added via RSS feed processing
			# This function is kept for compatibility but should not be used
			xbmc.log(f"Direct episode creation not supported - use feed API instead", xbmc.LOGWARNING)
			return None
		except Exception as e:
			xbmc.log(f"Error in create_podcast_episode: {str(e)}", xbmc.LOGERROR)
			raise
