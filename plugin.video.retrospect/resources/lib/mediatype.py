# SPDX-License-Identifier: GPL-3.0-or-later

# Video related items.
VIDEO = "video"
MOVIE = "movie"
TVSHOW = "tvshow"
SEASON = "season"
EPISODE = "episode"
MUSICVIDEO = "musicvideo"
VIDEO_TYPES = {VIDEO, MOVIE, TVSHOW, SEASON, EPISODE, MUSICVIDEO}

# Audio related items.
AUDIO = "music"  # Make it more in line with a generic VIDEO type.
MUSIC = "music"
SONG = "song"
ALBUM = "album"
ARTIST = "artist"
AUDIO_TYPES = {MUSIC, SONG, ALBUM, ARTIST}

# Basic folders
FOLDER = None
PAGE = "page"

PLAYABLE_TYPES = {VIDEO, MOVIE, EPISODE, MUSICVIDEO, MUSIC, SONG}
FOLDER_TYPES = {TVSHOW, SEASON, ALBUM, ARTIST, FOLDER, PAGE}
