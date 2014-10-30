
class TemplateModel(object):
    _common_fields = [
        'nid',
        'show_thumbnail',
        'title',
        'total',
        'votes'
    ]

    _fields = []

    def __init__(self, **kwargs):
        self._fields.extend(self._common_fields)
        for k, v in kwargs.iteritems():
            if k in self._fields:
                setattr(self, k, v)

    @property
    def icon(self):
        return self.show_thumbnail

    @property
    def thumbnail(self):
        return self.show_thumbnail

    @property
    def label(self):
        return self.title

    @property
    def query_string(self):
        raise NotImplementedError()

    @property
    def stream_info(self):
        if self.quality == 4000:
            w, h = 1920, 1080
        elif self.quality == 3500:
            w, h = 1080, 720
        else:
            w, h = 640, 480
        aspect = w / float(h)

        si = {
            'codec': 'mp4',
            'aspect': aspect,
            'width': w,
            'height': h,
            'duration': self.duration
        }

        return si

    @property
    def sub(self):
        return self.sub_dub == 'Sub'

    @property
    def dub(self):
        return self.sub_dub == 'Dub'

    def get(self, key, default=None):
        return getattr(self, key, default)

    # not sure if i like this, might show to much info
    def __repr__(self):
        return repr(self.__dict__)


class Show(TemplateModel):
    _fields = [
        'all_terms',
        'maturity_rating',
        'mobile_banner_large',
        'post_date',
        'show_thumbnail_accedo',
        'similar_shows',
        'video_section',
    ]

    @property
    def thumbnail(self):
        return self.mobile_banner_large

    @property
    def label2(self):
        return '[' + self.maturity_rating + ']'

    @property
    def vtypes(self):
        vt = ','.join([i.lower() for i in self.video_section])
        return vt

    @property
    def info(self):
        video_info = {
            'genre': ', '.join(self.all_terms),
            'votes': self.votes,
            'aired': self.post_date.strftime('%Y-%m-%d'),
            'year': self.post_date.strftime('%Y'),
        }

        return video_info

    @property
    def query_string(self):
        qry = {
            'id': self.nid,
            'folder': 'true',
            'path': '/show',
            'vtypes': self.vtypes,
        }

        return qry

    @property
    def stream_info(self):
        raise NotImplementedError()

    @property
    def sub(self):
        raise NotImplementedError()

    @property
    def dub(self):
        raise NotImplementedError()


class Episode(TemplateModel):
    _fields = [
        'aip',
        'duration',
        'episode_number',
        'episode_thumbnail',
        'exclusive',
        'funimation_id',
        'language',
        'promo',
        'rating',
        'show_title',
        'sub_dub',
        'type',
        'video_quality',
        'video_thumbnail_accedo'
    ]

    @property
    def label(self):
        lbl = '%d. %s (%s)' % (self.episode_number, self.title, self.sub_dub)
        return lbl

    @property
    def thumbnail(self):
        return self.episode_thumbnail

    @property
    def quality(self):
        count = self.video_quality.count('HD (720)')
        if count >= 2:
            return 4000
        elif count == 1:
            return 3500
        else:
            return 2000

    @property
    def info(self):
        video_info = {
            'duration': self.duration,
            'episode': self.episode_number,
            'votes': self.votes,
            'tvshowtitle': self.show_title,
        }

        return video_info

    @property
    def query_string(self):
        qry = {
            'id': self.nid,
            'path': '/show/episodes',
            'videoid': self.funimation_id,
        }

        return qry


class Movie(TemplateModel):
    _fields = [
        'aip',
        'duration',
        'funimation_id',
        'language',
        'mobile_banner_large',
        'promo',
        'rating',
        'show_title',
        'sub_dub',
        'term',
        'tv_key_art',
        'video_quality',
        'video_thumbnail_accedo',
    ]

    @property
    def quality(self):
        count = self.video_quality.count('HD (720)')
        if count >= 2:
            return 4000
        elif count == 1:
            return 3500
        else:
            return 2000

    @property
    def info(self):
        video_info = {
            'duration': self.duration,
            'votes': self.votes,
            'mpaa': self.rating,
        }

        return video_info

    @property
    def query_string(self):
        qry = {
            'id': self.nid,
            'path': '/show/episodes',
            'videoid': self.funimation_id,
        }

        return qry


class Clip(TemplateModel):
    _fields = [
        'duration',
        'funimation_id',
        'funimationid',
        'post_date',
        'rating',
        'show_id',
        'show_title',
        'term',
        'type',
        'video_thumbnail_accedo',
    ]

    @property
    def quality(self):
            return 2000

    @property
    def info(self):
        video_info = {
            'duration': self.duration,
            'tvshowtitle': self.show_title,
        }

        return video_info

    @property
    def query_string(self):
        qry = {
            'id': self.nid,
            'path': '/show/episodes',
            'videoid': self.funimation_id,
        }

        return qry

    @property
    def sub(self):
        raise NotImplementedError()

    @property
    def dub(self):
        raise NotImplementedError()


class Trailer(TemplateModel):
    _fields = [
        'duration',
        'funimation_id',
        'is_mature',
        'show_title',
        'video_quality',
        'video_thumbnail_accedo',
    ]

    @property
    def quality(self):
        count = self.video_quality.count('HD (720)')
        if count >= 2:
            return 4000
        elif count == 1:
            return 3500
        else:
            return 2000

    @property
    def info(self):
        video_info = {
            'duration': self.duration,
            'tvshowtitle': self.show_title,
        }

        return video_info

    @property
    def query_string(self):
        qry = {
            'id': self.nid,
            'path': '/show/episodes',
            'videoid': self.funimation_id,
        }

        return qry

    @property
    def sub(self):
        raise NotImplementedError()

    @property
    def dub(self):
        raise NotImplementedError()


class ShowDetail(TemplateModel):
    _fields = [
        'aspect_ratio',
        'body',
        'featured_product',
        'genre',
        'has_episodes',
        'has_subscription',
        'has_videos',
        'is_featured',
        'maturity_rating',
        'mobile_banner_large',
        'official_trailer',
        'path',
        'post_date',
        'similar_shows',
        'teaser',
        'tv_key_art',
        'type',
        'updated_date',
        'video_types',
    ]

    @property
    def stream_info(self):
        raise NotImplementedError()

    @property
    def sub(self):
        raise NotImplementedError()

    @property
    def dub(self):
        raise NotImplementedError()


class EpisodeDetail(TemplateModel):
    _fields = [
        'aip',
        'aspect_ratio',
        'body',
        'duration',
        'episode_number',
        'funimation_id',
        'genre',
        'group_nid',
        'group_path',
        'group_title',
        'maturity_rating',
        'path',
        'post_date',
        'quality',
        'sequence_number',
        'sub_dub',
        'subscription_sunrise_date',
        'subscription_sunset_date',
        'sunrise_date',
        'sunset_date',
        'teaser',
        'type',
        'updated_date',
        'video',
        'video_quality',
    ]

    @property
    def stream_info(self):
        raise NotImplementedError()
