# -*- coding: iso-8859-1 -*-

import unittest
import default
try:
    import logininfo
except ImportError:
    print "The tests require USERNAME, PASSWORD defined in logininfo.py"
    raise


class TestUtils(unittest.TestCase):
    def test_parse_datetime(self):
        dt = default.parse_datetime('Su 26.05.2012 12:11')
        self.assertEquals(dt.strftime("%Y-%m-%d %H:%M"), "2012-05-26 12:11")
        dt = default.parse_datetime('01.01.2012 23:55')
        self.assertEquals(dt.strftime("%Y-%m-%d %H:%M"), "2012-01-01 23:55")
        dt = default.parse_datetime('  Su 26.05.2012 12:11')
        self.assertEquals(dt.strftime("%Y-%m-%d %H:%M:00"), "2012-05-26 12:11:00")

    def test_parse_program_id(self):
        self.assertEquals(default.parse_program_id('program.sl?programid=720122'), '720122')
        self.assertEquals(default.parse_program_id('program.sl?programid=123456'), '123456')

    def test_search_items(self):
        default.login(logininfo.USERNAME, 
                      logininfo.PASSWORD)
        sdata = default.search_items('indiana')
        self.assertEquals(sdata[0]['url'], 'program.sl?programid=716866')
        self.assertEquals(sdata[0]['program_id'], '716866')
        self.assertEquals(sdata[0]['channel'], 'Nelonen')
        self.assertEquals(sdata[0]['start_time'], '29.04.2012 21:00:00')


if __name__ == '__main__':
    unittest.main()
