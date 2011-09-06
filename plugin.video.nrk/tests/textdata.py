# -*- coding: utf-8 -*-
import unittest
import data

class Test(unittest.TestCase):
    
    def setUp(self):
        self.nodes = [data.DataItem(title="1", url="/nett-tv/bokstav/1"),
                      data.DataItem(title="Å", url="/nett-tv/bokstav/" + 'å'.encode('latin-1')),
                      data.DataItem(title="S", url="/nett-tv/bokstav/s") ]
        data.setQuality('2')
        
    def test(self):
        self._rec(self.nodes, 0)

    def _rec(self, dataset, lvl):
        for d in dataset:
            assert d.title.strip() is not ""
            assert d.url.strip() is not ""
            
            if d.url.startswith("mms"):
                assert d.thumb.startswith("http://")
                continue
            
            space = "".join( ["    " for _ in range(0,lvl)] )
            print space + str(d.title)
            self._rec(data.getByUrl(d.url), lvl+1)
        return
            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    