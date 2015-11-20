# -*- coding: utf-8 -*-
from urlparse import urlparse


class Structure(object):
    _fields = []

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            if k in self._fields:
                setattr(self, k, v)

    def get(self, key, default=None):
        return getattr(self, key, default)

    @property
    def label(self):
        raise NotImplementedError

    def __eq__(self, other):
        return self.asset_id == other

    def __hash__(self):
        return hash(self.asset_id)

    def __len__(self):
        return len(self._fields)

    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self.label.encode('utf-8'))


# noinspection PyUnresolvedReferences
class Show(Structure):
    _fields = [
        'asset_id',
        'pubDate',
        'series_name',
        'series_description',
        'episode_count',
        'genres',
        'show_rating',
        'thumbnail_large',
        'poster_art',
        'popularity',
    ]

    @property
    def label(self):
        return self.series_name

    @property
    def label2(self):
        return '[{0}]'.format(self.show_rating)

    @property
    def icon(self):
        return self.thumbnail_large

    @property
    def thumbnail(self):
        return self.poster_art

    @property
    def info(self):
        return {
            'genre': self.genres,
            'plot': self.series_description,
            'episode': self.episode_count,
            'year': self.pubDate.split('/')[2],
            'votes': str(self.popularity),
            'mpaa': self.show_rating,
            'aired': '{2}-{1}-{0}'.format(*self.pubDate.split('/')),
        }

    @property
    def query(self):
        return {'show_id': self.asset_id, 'get': 'videos'}

    @property
    def genre(self):
        if self.genres is not None:
            return self.genres.split(',')
        else:
            return ''


# noinspection PyUnresolvedReferences
class Video(Structure):
    _fields = [
        'asset_id',
        'description',
        'dub_sub',
        'duration',
        'funimation_id',
        'number',
        'quality',
        'rating',
        'releaseDate',
        'releaseDate',
        'thumbnail_url',
        'title',
        'video_url',
    ]

    @property
    def label(self):
        if self.number:
            # self.number sometimes is a unicode str that's why we use repr()
            lbl = '%s. %s (%s)' % (repr(self.number), self.title, self.dub_sub)
        else:
            lbl = '%s (%s)' % (self.title, self.dub_sub)
        return lbl

    @property
    def sub(self):
        return self.dub_sub == 'sub'

    @property
    def dub(self):
        return self.dub_sub == 'dub'

    @property
    def label2(self):
        return '[{0}]'.format(self.rating)

    @property
    def icon(self):
        return self.thumbnail_url

    @property
    def thumbnail(self):
        return self.thumbnail_url

    @property
    def info(self):
        return {
            'plot': self.description,
            'episode': self.number,
            'year': self.releaseDate.split('/')[0],
            'mpaa': self.rating,
            'aired': self.releaseDate.replace('/', '-'),
        }

    @property
    def stream_info(self):
        if '1080' in self.quality:
            w, h = 1920, 1080
        elif '720' in self.quality:
            w, h = 1080, 720
        else:
            w, h = 640, 480
        return {
            'codec': 'mp4',
            'aspect': w / float(h),
            'width': w,
            'height': h,
            'duration': self.duration
        }

    @property
    def query(self):
        return {'videoid': self.asset_id}

    def get_video_url(self, quality):
        # 0 = 480, 1 = 720, 2 = 1080
        # This is a bit hacky but I can't really think of a good way to do it
        # with the current information the API returns.
        # Every video has one of these bit rates
        # 750,1500                  SD
        # 750,1500,2000,2500        HD720
        # 750,1500,2000,2500,4000   HD1080
        try:
            url = urlparse(self.video_url)
            # stream qualities are split by ','
            path_split = url.path.split(',')
            # sort it just to make sure it's in the correct order
            rates = sorted([int(q) for q in path_split if q.isdigit()])
            if quality == 2:
                # just get the highest quality
                rate = rates[-1]
            elif quality == 1:
                # 1080p videos always have 5 different rates
                if len(rates) == 5:  # HD1080
                    rate = rates[-2]
                else:
                    rate = rates[-1]
            else:
                rate = rates[0]
            path = path_split[0] + str(rate) + path_split[-1]
            # recreate the URL
            return '%s://%s%s?%s' % (url.scheme, url.netloc, path, url.query)
        except:
            return self.video_url
