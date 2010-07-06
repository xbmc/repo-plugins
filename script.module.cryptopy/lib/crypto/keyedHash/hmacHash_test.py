#!/usr/bin/env python
""" hmacHash_test.py
    Unit tests for hmacHash.py

    So far only runs test vectors from RFC2104
    References
       [IETF]  RFC 2104 "HMAC: Keyed-Hashing for Message Authentication"
       [IETF]  RFC 2202
"""

import unittest
from crypto.keyedHash.hmacHash import HMAC, HMAC_SHA1
from crypto.hash.sha1Hash      import SHA1
from crypto.hash.md5Hash       import MD5
from binascii                  import a2b_hex, b2a_hex

class HMAC_Simple_TestCases(unittest.TestCase):
    """ HMAC constructed ny hand """
    def testSHA1_NullKey(self):
        """ HMAC_SHA1 testNullKey """
        ki = ''.join([chr(0x36) for i in range(64)])
        ko = ''.join([chr(0x5C) for i in range(64)])
        h = SHA1()
        keyedHashAlg = HMAC(SHA1,key='')
        assert ( keyedHashAlg('') == h(ko+h(ki)) ), 'Null key, Null data test'
        assert ( keyedHashAlg('a') == h(ko+h(ki+'a')) ), 'Null key, a data test'
        assert ( keyedHashAlg('ab') == h(ko+h(ki+'ab')) ), 'Null key, ab data test'
        assert ( keyedHashAlg(50*'a') == h(ko+h(ki+50*'a')) ), 'Null key, 50*a data test'
        # try hmac in two steps of 25 chrs
        manual_hmac = h(ko+h(ki+50*'a'))
        keyedHashAlg.update(25*'a')
        keyedHashAlg.update(25*'a')
        hm = keyedHashAlg.digest()
        assert (hm == manual_hmac), 'HMAC as update, update and digest'

    def testMD5_NullKey(self):
        """ HMAC_MD5 testNullKey """
        ki = ''.join([chr(0x36) for i in range(64)])
        ko = ''.join([chr(0x5C) for i in range(64)])
        h = MD5()
        keyedHashAlg = HMAC(MD5,key='')
        assert ( keyedHashAlg('') == h(ko+h(ki)) ), 'Null key, Null data test'
        assert ( keyedHashAlg('a') == h(ko+h(ki+'a')) ), 'Null key, a data test'
        assert ( keyedHashAlg('ab') == h(ko+h(ki+'ab')) ), 'Null key, ab data test'
        assert ( keyedHashAlg(50*'a') == h(ko+h(ki+50*'a')) ), 'Null key, 50*a data test'

    def testSHA1_oneByteKey(self):
        """ HMAC_SHA1 oneByteKey of 0xFF"""
        ki = ''.join([chr(0x36) for i in range(64)])
        ko = ''.join([chr(0x5C) for i in range(64)])
        ki = chr(ord(ki[0])^0xFF)+ ki[1:]
        ko = chr(ord(ko[0])^0xFF)+ ko[1:]
        h = SHA1()
        keyedHashAlg = HMAC(SHA1,chr(0xff))
        assert ( keyedHashAlg('') == h(ko+h(ki)) ), 'one byte key, Null data test'
        assert ( keyedHashAlg('a') == h(ko+h(ki+'a')) ), 'one byte key, a data test'
        assert ( keyedHashAlg('ab') == h(ko+h(ki+'ab')) ), 'one byte key, ab data test'
        assert ( keyedHashAlg(50*'a') == h(ko+h(ki+50*'a')) ), 'one byte key, 50*a data test'

class HMAC_RFC2104_TestCases(unittest.TestCase):
    """ HMAC tests from RFC2104 """

    def testRFC2104_1(self):
        """ RFC2104 test 1 and various calling methods """
        key          = chr(0x0b)*20
        keyedHashAlg = HMAC(SHA1,key)
        data         = "Hi There"
        digest       = a2b_hex('b617318655057264e28bc0b6fb378c8ef146be00')
        cd=keyedHashAlg(data)
        assert( cd == digest ), 'RFC2104 test 1 failed'

        hmac_sha1 = HMAC_SHA1(key)
        cd = hmac_sha1.hash(data)
        assert( cd == digest ), 'RFC2104 test 1 failed, HMAC_SHA1 called'

        cd = hmac_sha1.hash(data[:3],more=1)
        cd = hmac_sha1.hash(data[3:])
        assert( cd == digest ), 'RFC2104 test 1 failed, HMAC_SHA1 called twice'

        hmac_sha1.update(data[:3])
        hmac_sha1.update(data[3:])
        cd = hmac_sha1.digest()
        print b2a_hex(cd)
        assert( cd == digest ), 'RFC2104 test 1 failed, HMAC_SHA1 called with update'

        hmac_sha1.reset(data)
        cd1 = hmac_sha1.hash(data)
        cd2 = hmac_sha1.hash(data)
        print b2a_hex(cd1)
        print b2a_hex(cd2)
        assert( cd1 == cd2 ), 'hash method should default to reseting state'


    def testRFC2104_2(self):
        """ RFC2104 test 2 """
        keyedHashAlg = HMAC(SHA1)
        key          = 'Jefe'
        keyedHashAlg.setKey(key)
        data         = 'what do ya want for nothing?'
        digest       = a2b_hex('effcdf6ae5eb2fa2d27416d5f184df9c259a7c79')
        cd           = keyedHashAlg(data)
        assert( cd == digest ), 'RFC2104 test 2 failed'

    def testRFC2104_3(self):
        """ RFC2104 test 3 """
        key =         a2b_hex('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        keyedHashAlg = HMAC_SHA1(key)
        data =        50*chr(0xdd)
        digest =      a2b_hex('125d7342b9ac11cd91a39af48aa17b4f63f175d3')
        cd           = keyedHashAlg(data)
        assert( cd == digest ), 'RFC2104 test 3 failed'




if __name__ == '__main__':
    # Run the tests from the command line
    unittest.main()



