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

    def __init__(self, name, path, params=None, image=u''):
        if not params:
            params = {}
            pass
        BaseItem.__init__(self, name, path, params, image)

        """
        Set some default values.
        """
        self.set_info(self.INFO_DURATION, u'1')
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

    pass