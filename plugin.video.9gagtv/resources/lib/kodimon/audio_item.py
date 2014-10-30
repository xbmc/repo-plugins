__author__ = 'bromix'

from . import BaseItem


class AudioItem(BaseItem):
    INFO_TRACKNUMBER = ('tracknumber', int)
    INFO_DURATION = ('duration', int)
    INFO_YEAR = ('year', int)
    INFO_GENRE = ('genre', unicode)
    INFO_ALBUM = ('album', unicode)
    INFO_ARTIST = ('artist', unicode)
    INFO_TITLE = ('title', unicode)
    INFO_RATING = ('rating', unicode)
    INFO_LYRICS = ('lyrics', unicode)
    INFO_PLAYCOUNT = ('playcount', int)
    INFO_LASTPLAYED = ('lastplayed', unicode)

    def __init__(self, name, uri, image=u''):
        BaseItem.__init__(self, name, uri, image)
        pass

    def set_last_played(self, year, month, day, hour, minute, second=0):
        date_time_str = '%04d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, second)
        self.set_info(self.INFO_LASTPLAYED, date_time_str)
        pass

    def set_play_count(self, play_count):
        self.set_info(self.INFO_PLAYCOUNT, play_count)
        pass

    def set_lyrics(self, lyrics):
        self.set_info(self.INFO_LYRICS, lyrics)
        pass

    def set_rating(self, rating):
        _rating = int(rating)
        if _rating >= 0 and _rating <= 5:
            self.set_info(self.INFO_RATING, _rating)
        elif _rating > 5:
            self.set_info(self.INFO_RATING, 5)
        pass

    def set_title(self, title):
        self.set_info(self.INFO_TITLE, title)
        pass

    def set_artist_name(self, artist_name):
        self.set_info(self.INFO_ARTIST, artist_name)
        pass

    def set_album_name(self, album_name):
        self.set_info(self.INFO_ALBUM, album_name)
        pass

    def set_genre(self, genre):
        self.set_info(self.INFO_GENRE, genre)
        pass

    def set_year(self, year):
        self.set_info(self.INFO_YEAR, year)
        pass

    def set_track_number(self, track_number):
        self.set_info(self.INFO_TRACKNUMBER, track_number)
        pass

    def set_duration_in_milli_seconds(self, milli_seconds):
        self.set_duration_in_seconds(milli_seconds/1000)
        pass

    def set_duration_in_seconds(self, seconds):
        self.set_info(self.INFO_DURATION, seconds)
        pass

    pass
