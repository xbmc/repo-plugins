import re
from .base_item import BaseItem


class VideoItem(BaseItem):
    INFO_GENRE = ('genre', unicode)
    INFO_YEAR = ('year', int)
    INFO_EPISODE = ('episode', int)
    INFO_SEASON = ('season', int)
    INFO_TOP250 = ('top250', int)
    INFO_TRACKNUMBER = ('tracknumber', int)
    INFO_RATING = ('rating', float)
    #INFO_WATCHED = ('watched', depreciated)
    INFO_PLAYCOUNT = ('playcount', int)
    INFO_OVERLAY = ('overlay', int)
    INFO_CAST = ('cast', list)
    INFO_CASTANDROLE = ('castandrole', list)
    INFO_DIRECTOR = ('director', unicode)
    INFO_MPAA = ('mpaa', unicode)
    INFO_PLOT = ('plot', unicode)
    INFO_PLOTOUTLINE = ('plotoutline', unicode)
    INFO_TITLE = ('title', unicode)
    INFO_ORIGINALTITLE = ('originaltitle', unicode)
    INFO_SORTTITLE = ('sorttitle', unicode)
    INFO_DURATION = ('duration', unicode)
    INFO_STUDIO = ('studio', unicode)
    INFO_TAGLINE = ('tagline', unicode)
    INFO_WRITER = ('writer', unicode)
    INFO_TVSHOWTITLE = ('tvshowtitle', unicode)
    INFO_PREMIERED = ('premiered', unicode)
    INFO_STATUS = ('status', unicode)
    INFO_CODE = ('code', unicode)
    INFO_AIRED = ('aired', unicode)
    INFO_CREDITS = ('credits', unicode)
    INFO_LASTPLAYED = ('lastplayed', unicode)
    INFO_ALBUM = ('album', unicode)
    INFO_ARTIST = ('artist', list)
    INFO_VOTES = ('votes', unicode)
    INFO_TRAILER = ('trailer', unicode)

    def __init__(self, name, uri, image=u''):
        BaseItem.__init__(self, name, uri, image)
        pass

    def set_aired(self, year, month, day):
        _data = [year, month, day]
        for i in range(len(_data)):
            _val = _data[i]
            if isinstance(_val, int):
                _val = str(_val)
                pass

            if len(_val) == 1:
                _val = '0' + _val
                pass

            _data[i] = _val
            pass

        self.set_info(self.INFO_AIRED, u'%s-%s-%s' % (_data[0], _data[1], _data[2]))
        pass

    def set_duration(self, hours, minutes, seconds=0):
        _seconds = seconds
        _seconds += minutes * 60
        _seconds += hours * 60 * 60
        self.set_duration_in_seconds(_seconds)
        pass

    def set_duration_in_minutes(self, int_minutes):
        self.set_duration_in_seconds(int_minutes * 60)
        pass

    def set_duration_in_seconds(self, int_seconds):
        minutes_str = 1

        minutes = int_seconds / 60
        if minutes == 0:
            minutes_str = 1
        else:
            minutes_str = str(minutes)

        self.set_info(self.INFO_DURATION, unicode(minutes_str))
        pass

    def set_year(self, year):
        self.set_info(self.INFO_YEAR, year)
        pass

    def set_premiered(self, year, month, day):
        date_str = u'%04d-%02d-%02d' % (year, month, day)
        self.set_info(self.INFO_PREMIERED, date_str)
        pass

    def set_plot(self, plot):
        self.set_info(self.INFO_PLOT, plot)
        pass

    def set_rating(self, rating):
        self.set_info(self.INFO_RATING, rating)
        pass

    def set_director(self, director_name):
        self.set_info(self.INFO_DIRECTOR, director_name)
        pass

    def add_cast(self, cast):
        cast_list = self.get_info(self.INFO_CAST)
        if not cast_list:
            cast_list = []
            pass

        cast_list.append(cast)
        self.set_info(self.INFO_CAST, cast_list)
        pass

    def set_imdb_id(self, url_or_id):
        re_match = re.match('(http\:\/\/)?www.imdb.(com|de)\/title\/(?P<imdbid>[t0-9]+)(\/)?', url_or_id)
        if re_match:
            self.set_info(self.INFO_CODE, re_match.group('imdbid'))
        else:
            self.set_info(self.INFO_CODE, url_or_id)
        pass

    pass