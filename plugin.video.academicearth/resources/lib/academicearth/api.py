'''
    academicearth.api
    ~~~~~~~~~~~~~~~~~

    This module contains the API classes and method to parse information from
    the Academic Earth website.
'''
import scraper


class AcademicEarth(object):
    '''The main API object. Useful as a starting point to get available
    subjects.
    '''

    def __init__(self):
        pass

    def get_subjects(self):
        '''Returns a list of subjects available on the website.'''
        return [Subject(info, partial=True) for info
                in scraper.Subject.get_subjects_partial()]

    def get_universities(self):
        '''Returns a list of universities available on the website.'''
        return [University(info, partial=True) for info
                in scraper.University.get_universities_partial()]

    def get_speakers(self):
        '''Returns a list of speakers available on the website.'''
        return [Speaker(info, partial=True) for info
                in scraper.Speaker.get_speakers_partial()]


class _BaseAPIObject(object):

    scraper_cls = scraper.University

    def __init__(self, info, partial=False):
        self._setattrs(info)
        self.partial = partial

    def __getattr__(self, name):
        if self.partial:
            self.load()
            return getattr(self, name)
        raise AttributeError, '%s instance has no attribute %s' % (self.__class__.__name__, name)

    def __repr__(self):
        return u"<%s '%s'>" % (self.__class__.__name__, self.name)

    def _setattrs(self, info):
        for attr_name, attr_value in info.items():
            setattr(self, attr_name, attr_value)

    def load(self):
        full_info = self.scraper_cls.from_url(url)
        self._setattrs(info)
        self.partial = False

    @classmethod
    def from_url(cls, url):
        info = cls.scraper_cls.from_url(url)
        return cls(info)

class _ObjectWithCoursesLectures(_BaseAPIObject):

    def _setattrs(self, info):
        for attr_name, attr_value in info.items():
            if attr_name == 'courses':
                setattr(self, attr_name, [Course(info) for info in attr_value])
            elif attr_name == 'lectures':
                setattr(self, attr_name, [Lecture(info) for info in attr_value])
            else:
                setattr(self, attr_name, attr_value)

class Subject(_ObjectWithCoursesLectures):

    scraper_cls = scraper.Subject


class University(_ObjectWithCoursesLectures):

    scraper_cls = scraper.University


class Speaker(_ObjectWithCoursesLectures):

    scraper_cls = scraper.Speaker


class Course(_BaseAPIObject):

    scraper_cls = scraper.Course

    def _setattrs(self, info):
        for attr_name, attr_value in info.items():
            if attr_name == 'lectures':
                setattr(self, attr_name, [Lecture(info) for info in attr_value])
            else:
                setattr(self, attr_name, attr_value)


class Lecture(_BaseAPIObject):
    scraper_cls = scraper.Lecture
