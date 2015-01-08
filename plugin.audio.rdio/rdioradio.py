# Copyright 2012 Charles Blaxland
# This file is part of rdio-xbmc.
#
# rdio-xbmc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rdio-xbmc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdio-xbmc.  If not, see <http://www.gnu.org/licenses/>.

import random
from collections import deque


class RdioRadio:

  _RETURN_TO_BASE_ARTIST_FREQUENCY = 5
  _NO_REPEAT_TRACK_COUNT = 25
  _NUM_TOP_TRACKS_TO_CHOOSE_FROM = 20
  _RELATED_ARTIST_DEPTH = 3
  _NO_REPEAT_ARTIST_COUNT = 5

  _RADIO_STATE_FILE_NAME = 'rdio-radio-state.json'
  _INITIAL_STATE = {'played_tracks': deque(), 'played_artists': deque()}

  def __init__(self, addon, rdio_api):
    self._addon = addon
    self._rdio_api = rdio_api
    self._state = addon.load_data(self._RADIO_STATE_FILE_NAME)
    if not self._state:
      self._state = self._INITIAL_STATE


  def start_radio(self, base_artist, user = None):
    self._state = self._INITIAL_STATE
    self._state['base_artist'] = base_artist
    self._state['user'] = user
    self._save_state()


  def next_track(self):
    track = None
    base_artist = self._state['base_artist']
    last_artist = self._state['played_artists'][-1] if self._state['played_artists'] else None
    user = self._state['user']
    artist_blacklist = [base_artist] + list(self._state['played_artists'])
    use_base_artist = not last_artist or random.randint(1, self._RETURN_TO_BASE_ARTIST_FREQUENCY) == 1

    attempt_number = 0
    while not track:
      artist = base_artist if use_base_artist else self._choose_artist(last_artist, user, artist_blacklist)
      if artist:
        track = self._choose_track(artist, user)
        if not track:
          self._addon.log_debug("No tracks found for artist %s, adding to blacklist" % artist)
          artist_blacklist.append(artist)
      else:
        self._addon.log_debug("Didn't find an artist")
        attempt_number = attempt_number + 1
        if attempt_number == 1:
          self._addon.log_debug("Allowing base artist and artist repeats")
          artist_blacklist = list(set(artist_blacklist) - (set([base_artist]) | set(self._state['played_artists'])))
        if attempt_number == 2:
          self._addon.log_debug("Allowing track repeats")
          artist_blacklist = []
          self._state['played_tracks'] = deque()
        if attempt_number >= 3:
          self._addon.log_debug("Giving up")
          break

    if track:
      self._record_played_track(track)

    self._save_state()
    return track


  def _choose_artist(self, last_artist, user, artist_blacklist = None, depth = 1):
    self._addon.log_debug("Choosing artist with last artist %s" % last_artist)

    candidate_artist_keys = self._candidate_artists(last_artist, user, artist_blacklist)
    if candidate_artist_keys:
      chosen_artist = random.choice(candidate_artist_keys)
    else:
      chosen_artist = None

    self._addon.log_debug("Chose artist: %s" % str(chosen_artist))
    return chosen_artist


  def _candidate_artists(self, last_artist, user, artist_blacklist = None, artist_recurse_blacklist = None, depth = 1):
    self._addon.log_debug("Finding candidate artists with last artist %s" % last_artist)
    if artist_blacklist is None:
      artist_blacklist = []

    related_artist_keys = self._cached_value('related_artists_' + last_artist,
        lambda: [artist['key'] for artist in self._rdio_api.call('getRelatedArtists', artist = last_artist)])

    allowed_related_artist_keys = list(set(related_artist_keys) - set(artist_blacklist))

    if not user:
      self._addon.log_debug("Candidate artists: %s" % str(allowed_related_artist_keys))
      return allowed_related_artist_keys

    collection_artist_keys = self._cached_value('artists_in_collection_' + user,
      lambda: [artist['artistKey'] for artist in self._rdio_api.call('getArtistsInCollection', user = user)])

    self._addon.log_debug("Related artists: %s, collection artists: %s, blacklist: %s" % (str(allowed_related_artist_keys), str(collection_artist_keys), str(artist_blacklist)))
    candidate_artist_keys = list(set(allowed_related_artist_keys) & set(collection_artist_keys))
    self._addon.log_debug("Candidate artists: %s" % str(candidate_artist_keys))

    if not candidate_artist_keys and depth < self._RELATED_ARTIST_DEPTH:
      if artist_recurse_blacklist is None:
        artist_recurse_blacklist = []

      artist_recurse_blacklist.append(last_artist)

      recurse_artists = list(set(related_artist_keys) - set(artist_recurse_blacklist))
      self._addon.log_debug("Recursing related artists %s, recurse blacklist: %s" % (str(recurse_artists), str(artist_recurse_blacklist)))
      for related_artist in recurse_artists:
        candidate_artist_keys = self._candidate_artists(related_artist, user, artist_blacklist, artist_recurse_blacklist, depth + 1)
        if candidate_artist_keys:
          break

    return candidate_artist_keys


  def _choose_track(self, artist, user):
    tracks = None
    if user:
      tracks = self._cached_value('artist_tracks_in_collection_%s_%s' % (artist, user), lambda: self._rdio_api.call('getTracksForArtistInCollection', artist = artist, user = user))
    else:
      tracks = self._cached_value('artist_tracks_%s' % artist, lambda: self._rdio_api.call('getTracksForArtist', artist = artist, extras = 'playCount,isInCollection', start = 0, count = self._NUM_TOP_TRACKS_TO_CHOOSE_FROM))

    chosen_track = None
    if tracks:
      played_tracks = self._state['played_tracks']
      candidate_tracks = [track for track in tracks if track['canStream'] and track['key'] not in played_tracks]
      if candidate_tracks:
        chosen_track = random.choice(candidate_tracks)

    return chosen_track


  def _save_state(self):
    self._addon.save_data(self._RADIO_STATE_FILE_NAME, self._state)


  def _cached_value(self, key, fn):
    value = None
    if key in self._state:
      value = self._state[key]
    else:
       value = fn()
       self._state[key] = value

    return value

  def _record_played_track(self, track):
    played_tracks = self._state['played_tracks']
    played_tracks.append(track['key'])
    if len(played_tracks) > self._NO_REPEAT_TRACK_COUNT:
      played_tracks.popleft()

    played_artists = self._state['played_artists']
    played_artists.append(track['artistKey'])
    if len(played_artists) > self._NO_REPEAT_ARTIST_COUNT:
      played_artists.popleft()
