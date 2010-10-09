#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" Testing of TKIP_MIC Class
"""
from crypto.keyedHash.tkip_mic import TKIP_MIC
from binascii_plus import *
from struct import pack, unpack
import unittest

class TKIP_MIC_Tests(unittest.TestCase):
    """ Test MIC algorithm using know values """
    def testAdrianExample1(self):
        """ Test 1 from Adrian 2002-12-12"""
        print "==== Test 1 Adrian ===="
        # raw data
        k0 = 0x00000000L      # assume is a 'dword'
        k1 = 0x00000000L
        key = pack('<II', k0, k1 ) # pack two integers into string little-endian
        a1  = a2b_p('161514131211')
        a2  = a2b_p('262524232221')
        a3  = a2b_p('363534333231') # assumed to be TA
        a4  = a2b_p('464544434241')
        tcid = 2
        payload = a2b_p('10  11  12  13  14  15  16  17  18  19  1a  1b  1c')


        # this looks like a 4 addresses example do:
        sa = a2 # a4
        da = a1 # a3
        print "key =", b2a_p(key)
        print "sa =", b2a_p(sa)
        print "da =", b2a_p(da)
        print "tcid =", tcid
        print "payload =", b2a_p(payload)
        v0 = 0x85a3fe4cL
        v1 = 0x20f4105fL
        micResultAdrian = pack('<II', v0, v1) # pack little-endian dwords into 8 octets

        tkipMic = TKIP_MIC(key)
        micResult = tkipMic.hash(sa, da, tcid, payload )
        print "expected MIC =", b2a_p(micResultAdrian)
        print "MIC Result =", b2a_p(micResult)
        v0Result, v1Result = unpack('<II', micResult)
        self.assertEqual( v0, v0Result ), 'failed vo'
        self.assertEqual( v1, v1Result ), 'failed v1'

    def testParagExample1(self):
        """ Test 2 from Parag 2002-12-16"""
        print "==== Test 2 ===="
        # raw data
        k0 = 0x01234567L
        k1 = 0x89abcdefL
        key = pack('<II', k0, k1 ) # pack two integers into string little-endian

        da = a2b_p('aaaaaaaaaaaa')
        sa = a2b_p('bbbbbbbbbbbb')
        priority = 0x03

        payload = pack('<IIIIIIIIIII',0xdeaf0005L, 0xdeaf0006L, 0xdeaf0007L, 0xdeaf0008L, 0xdeaf0009L, 0xdeaf000aL, 0xdeaf000bL, 0xdeaf000cL, 0xdeaf000dL, 0xdeaf000eL, 0x00ccdd00L)
        payload = payload[:-1] # trim off last octet
        print "key =", b2a_p(key)
        print "sa =", b2a_p(sa)
        print "da =", b2a_p(da)
        print "priority =", priority
        print "payload =", b2a_p(payload)

        # The know MIC is
        v0 = 0xe597b391L
        v1 = 0xb8c4a7b7L
        micResultParag = pack('<II', v0, v1) # pack little-endian dwords into 8 octets

        tkipMic = TKIP_MIC(key)
        tcid = priority
        micResult = tkipMic.hash(sa, da, tcid, payload )
        print "expected MIC =", b2a_p(micResultParag)
        print "MIC Result =", b2a_p(micResult)
        v0Result, v1Result = unpack('<II', micResult)
        self.assertEqual( v0, v0Result ), 'failed vo'
        self.assertEqual( v1, v1Result ), 'failed v1'

if __name__ == '__main__':
    unittest.main()  # run all the tests


