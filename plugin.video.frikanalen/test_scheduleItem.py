import frikanalen

from unittest import TestCase


class TestScheduleItem(TestCase):
    def test_from_response(self):
        progs = sorted(frikanalen.today_programs())
        for p in progs:
            if p.video is not None:
                print str(p.video.name.encode('utf-8'))
            print str(p.starttime)

        assert len(progs) > 0
        frikanalen.whats_on()

