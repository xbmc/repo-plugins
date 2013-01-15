import unittest
import scraper

class UniversityIT(unittest.TestCase):

    def test_get_universities_partial(self):
        yale = {
            'url': u'http://www.academicearth.org/universities/yale',
            'name': u'Yale',
            'icon': u'http://ae_img.s3.amazonaws.com/University/3/200x100_Logo.jpg',
        }

        unis = scraper.University.get_universities_partial()

        # currently there are 41 universities
        self.assertTrue(len(unis) > 35)

        # hopefully Yale will always be there...
        self.assertTrue(yale in unis)

    def test_from_url(self):
        url = 'http://www.academicearth.org/universities/university-of-oxford'
        uni = scraper.University.from_url(url)

        assert uni['name'] == 'Oxford'
        assert uni['description'].startswith('The University of Oxford')
        assert len(uni['courses']) > 7
        assert len(uni['lectures']) > 0



class SubjectIT(unittest.TestCase):

    def test_get_subjects_partial(self):
        prog = {
            'url': u'http://www.academicearth.org/subjects/programming',
            'name': u'Programming',
        }

        subjs = scraper.Subject.get_subjects_partial()

        # currently 67
        self.assertTrue(len(subjs) > 64)
        self.assertTrue(prog in subjs)

    def test_from_url(self):
        url = 'http://www.academicearth.org/subjects/programming'
        subj = scraper.Subject.from_url(url)

        assert subj['name'] == 'Programming'
        assert subj['description'].startswith('Computer programmers code and')

        # Both currently at 17
        assert len(subj['courses']) > 15
        assert len(subj['lectures']) > 15
