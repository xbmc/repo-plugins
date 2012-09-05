'''

    academicearth.api
    ~~~~~~~~~~~~~~~~~

    This module contains the API classes and method to parse information from
    the Academic Earth website.

'''
from scraper import (get_subjects, get_courses, get_subject_metadata,
                     get_course_metadata, get_lecture_metadata)


class AcademicEarth(object):
    '''The main API object. Useful as a starting point to get available
    subjects.
    '''

    def __init__(self):
        pass

    def get_subjects(self):
        '''Returns a list of subjects available on the website.'''
        return [Subject(**info) for info in get_subjects()]


class Subject(object):
    '''Object representing an Academic Earth subject.'''

    def __init__(self, url, name=None):
        self.url = url
        self._name = name
        self._courses = None
        self._lectures = None
        self._loaded = False

    @classmethod
    def from_url(cls, url):
        return cls(url=url)

    def __repr__(self):
        return u"<Subject '%s'>" % self.name

    def _load_metadata(self):
        resp = get_subject_metadata(self.url)
        if not self._name:
            self._name = resp['name']
        self._courses = [Course(**info) for info in resp['courses']]
        self._lectures = [Lecture(**info) for info in resp['lectures']]
        self._description = resp['description']
        self._loaded = True

    @property
    def name(self):
        '''Subject name'''
        if not self._name:
            self._load_metadata()
        return self._name
        
    @property
    def courses(self):
        '''List of courses available for this subject'''
        if not self._loaded:
            self._load_metadata()
        return self._courses

    @property
    def lectures(self):
        '''List of lectures available for this subject'''
        if not self._loaded:
            self._load_metadata()
        return self._lectures


class Course(object):

    def __init__(self, url, name=None, **kwargs):
        self.url = url
        self._name = name
        self._loaded = False
        self._lectures = None

    @classmethod
    def from_url(cls, url):
        return cls(url=url)

    def __repr__(self):
        return u"<Course '%s'>" % self.name

    def _load_metadata(self):
        resp = get_course_metadata(self.url)
        if not self._name:
            self._name = resp['name']
        self._lectures = [Lecture(**info) for info in resp['lectures']]
        self._loaded = True

    @property
    def name(self):
        if not self._name:
            self._load_metadata()
        return self._name

    @property
    def lectures(self):
        if not self._loaded:
            self._load_metadata()
        return self._lectures


class Lecture(object):

    def __init__(self, url, name=None, **kwargs):
        self.url = url
        self._name = name
        self._loaded = False

    @classmethod
    def from_url(cls, url):
        return cls(url=url)

    def __repr__(self):
        return u"<Lecture '%s'>" % self.name

    def _load_metadata(self):
        resp = get_lecture_metadata(self.url)
        if not self._name:
            self._name = resp['name']
        self._youtube_id = resp['youtube_id']
        self._loaded = True

    @property
    def name(self):
        if not self._name:
            self._load_metadata()
        return self._name

    @property
    def youtube_id(self):
        if not self._loaded:
            self._load_metadata()
        return self._youtube_id
