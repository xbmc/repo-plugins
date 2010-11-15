# -*- coding: utf-8 -*-
import unittest
import data

class Test(unittest.TestCase):

    def test(self):
        for q in range(0,2):
            print "Testing quality=" + str(q)
            data.setQuality(q)
            self._testLetters()

    def _testLetters(self):
        letters = data.getLetters()
        #all takes too long so test only some critical
        letters = [data.DataItem(title="1", url="/nett-tv/bokstav/1"),
                   data.DataItem(title="Å", url="/nett-tv/bokstav/" + 'å'.encode('latin-1')),
                   data.DataItem(title="S", url="/nett-tv/bokstav/s") ]
        
        self._rec(letters, 0)
        
    def _rec(self, dataset, lvl):
        assert dataset > 0 #data module uses dom so >0 implies all was found
        for d in dataset:
            if d.url.startswith("mms"): continue
            space = "".join( ["    " for _ in range(0,lvl)] )
            print space + str(d.title)
            self._rec(data.getByUrl(d.url), lvl+1)
        return


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    