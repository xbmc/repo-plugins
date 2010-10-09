#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.keyedHash.tkip_key_mixing
    Tests for TKIP key mixing function
    Paul Lambert
    November 4, 2002
"""
import unittest
from crypto.keyedHash.tkip_key_mixing import TKIP_Mixer
from struct import pack, unpack
from binascii_plus import a2b_p, b2a_p, b2a_hex

class TKIP_Mixer_Know_Answer_Tests(unittest.TestCase):
    """ Test TKIP Mixing using know values (aka test vectors) """
    def testTKIP_Mixer_KnowValues(self):
        """ Test using vectors from IEEE 802.11TGi D2.4.2 """
        for testCase in TKIP_MixerTestCases:
            description = testCase['testCase']
            tk          = a2b_p(testCase['TK'])
            ta          = a2b_p(testCase['TA'])
            iv32        = a2b_p(testCase['IV32'])  # last 4 octets of PN/IV field
            iv16        = a2b_p(testCase['IV16'])
            # NOTE - iv16 and iv32 are confused notation from early drafts
            #        may not match notation in the future

            pnField = iv16[1]+iv16[0] +  iv32[3]+iv32[2]+iv32[1]+iv32[0]
            pn = unpack('<Q', pnField + 2*chr(0) )[0]

            knownP1key  = a2b_p(testCase['P1K'])
            knownRC4Key = a2b_p(testCase['RC4KEY'])

            print '==========================================================='
            print 'testCase:%s'%description
            print 'TK:      %s'%b2a_p(tk)[9:]
            print 'TA:      %s'%b2a_p(ta)[9:]
            print 'IV32:    %s'%b2a_p(iv32)[9:]
            print 'IV16:    %s'%b2a_p(iv16)[9:]
            keyId = 0
            eh1 = chr((ord(pnField[1])|0x20)&0x7f)
            eh = pnField[0]+eh1+pnField[1]+chr((keyId<<6)|0x20)+pnField[2:]
            print 'EncHdr:  %s    (with KeyId=0)' % b2a_p(eh)[9:]
            print 'PNfield: %s' % b2a_p(pnField)[9:]
            print 'PNvalue: hex 0x%012X   decimal %d' % (pn,pn)
            #print 'TSC:    [0x%04x, 0x%04x, 0x%04x]' % (unpack('<H',pnField[0:2])[0],\
            #               unpack('<H',pnField[2:4])[0],unpack('<H',pnField[4:6])[0])

            mixer = TKIP_Mixer(tk,ta)
            newRC4Key = mixer.newKey(pnField)

            p1kstring = ''.join([pack('>H',i) for i in mixer.phase1Key])   # a list of int's
            print 'TTAK:    [0x%04x, 0x%04x, 0x%04x, 0x%04x, 0x%04x]' % (mixer.phase1Key[0], \
                        mixer.phase1Key[1],mixer.phase1Key[2],mixer.phase1Key[3],mixer.phase1Key[4])
            print 'P1K:     %s'%b2a_p(p1kstring)[9:]
            #print 'knownP1K:%s'%b2a_p(knownP1key)[9:]
            self.assertEqual( p1kstring, knownP1key),'Phase1 Keys dont match'

            print 'RC4Key:  %s'% b2a_p(newRC4Key)[9:]
            #print 'knownRC4Key:     %s'% b2a_p(knownRC4Key)[9:]
            self.assertEqual( newRC4Key, knownRC4Key ),'Final Key does not match'
            print '==========================================================='

    def xtestTKIP_Mixer_Sequence(self):
        """ Test TKIP Mixing using alternate calling approaches """
        key = 16*chr(0)
        ta  = 6*chr(0)
        tscOctets = 6*chr(0)

        keyMixer = TKIP_Mixer(key)
        keyMixer.setTA(ta)
        newKey = keyMixer.newKey(tscOctets)

        keyMixer = TKIP_Mixer()
        keyMixer.setTA(ta)
        keyMixer.setKey(key)
        newKey = keyMixer.newKey(tscOctets)

        keyMixer = TKIP_Mixer(transmitterAddress=ta)
        keyMixer.setKey(key)
        newKey = keyMixer.newKey(tscOctets)


    def xtestGunarExample1(self):
        """ Test example from Gunnar 2003-01-27 """
        tk1 = a2b_p( "A9 90 6D C8 3E 78 92 3F 86 04 E9 9E F6 CD BA BB" )
        ta = a2b_p( "50 30 F1 84 44 08" )
        iv32  = a2b_p( "B5039776" ) #   [transmitted as B5 03 97 76]
        iv16  = a2b_p( "E70C" )
        p1k   = a2b_p( "26D5  F1E1  2A59  2021  0E8E" )
        rc4Key = a2b_p( "E7 67 0C 68 15 E0 2E 3F 1C 15 92 92 D4 E2 78 82" )
        mixer = TKIP_Mixer(tk1,ta)
        newRC4Key = mixer.newKey(iv16+iv32)
        print "=== Gunnar Example ==="
        print "rc4Key = ", b2a_p( rc4Key )
        print "newRC4Key = ", b2a_p( newRC4Key )
        print "knownp1K = ", b2a_p( p1k )
        print "calcp1K = %04X %04X %04x %04x %04x" % (mixer.phase1Key[0],mixer.phase1Key[1],mixer.phase1Key[2],mixer.phase1Key[3],mixer.phase1Key[4])
        self.assertEqual(rc4Key,newRC4Key)

    def xtestTKIP_Mixer_TV_values(self):
        """ Test using vectors from IEEE 802.11TGi D2.4.2 """
        for testCase in TKIP_TestVector:
            description = testCase['testCase']
            tk          = a2b_p(testCase['TK'])
            ta          = a2b_p(testCase['TA'])
            pn          = testCase['PN']
            pnField     = pack('<Q', pn)[:6]

            print '==========================================================='
            print 'testCase:%s'%description
            print 'TK:      %s'%b2a_p(tk)[9:]
            print 'TA:      %s'%b2a_p(ta)[9:]
            keyId = 0
            eh1 = chr((ord(pnField[1])|0x20)&0x7f)
            eh = pnField[0]+eh1+pnField[1]+chr((keyId<<6)|0x20)+pnField[2:]
            print 'EncHdr:  %s    (with KeyId=0)' % b2a_p(eh)[9:]
            print 'PNfield: %s' % b2a_p(pnField)[9:]
            print 'PNvalue: 0x%06X' % pn
            print 'TSC?:    [0x%04x, 0x%04x, 0x%04x]' % (unpack('<H',pnField[0:2])[0],\
                           unpack('<H',pnField[2:4])[0],unpack('<H',pnField[4:6])[0])

            mixer = TKIP_Mixer(tk,ta)
            newRC4Key = mixer.newKey(pnField)
            p1kstring = ''.join([pack('>H',i) for i in mixer.phase1Key])   # a list of int's
            print 'TTAK:   [0x%04x, 0x%04x, 0x%04x, 0x%04x, 0x%04x]' % (mixer.phase1Key[0], \
                        mixer.phase1Key[1],mixer.phase1Key[2],mixer.phase1Key[3],mixer.phase1Key[4])
            print 'P1K:     %s'%b2a_p(p1kstring)[9:]

            print 'RC4Key:  %s' % b2a_p( newRC4Key )[9:]
            print 'kRC4Key: %s' % b2a_p( a2b_p(testCase['RC4KEY']))[9:]
            self.assertEqual(newRC4Key, a2b_p(testCase['RC4KEY']))
            print '==========================================================='

""" TKIP_Mixer Know Answer Tests from IEEE TGi """
TKIP_MixerTestCases = [
    {'testCase': "IEEE TGi TKIP_Mixer Test vector #1",
     'TK'    : "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
     'TA'    : "10 22 33 44 55 66",
     'IV32'  : "00000000",
     'IV16'  : "0000",
     'P1K'   : "3DD2  016E  76F4  8697  B2E8",
     'RC4KEY': "00 20 00 33 EA 8D 2F 60 CA 6D 13 74 23 4A 66 0B"},

    {'testCase': "IEEE TGi TKIP_Mixer Test vector #2",
     'TK'    : "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
     'TA'    : "10 22 33 44 55 66",
     'IV32'  : "00000000",   #[transmitted as 00 00 00 00]
     'IV16'  : "0001",
     'P1K'   : "3DD2  016E  76F4  8697  B2E8",
     'RC4KEY': "00 20 01 90 FF DC 31 43 89 A9 D9 D0 74 FD 20 AA"},

    {'testCase':"IEEE TGi TKIP_Mixer Test vector #3",
     'TK'      : "63 89 3B 25 08 40 B8 AE 0B D0 FA 7E 61 D2 78 3E",
     'TA'      : "64 F2 EA ED DC 25",
     'IV32'  : "20DCFD43",
     'IV16'  : "FFFF",
     'P1K'   : "7C67  49D7  9724  B5E9  B4F1",
     'RC4KEY': "FF 7F FF 93 81 0F C6 E5 8F 5D D3 26 25 15 44 CE"},

    {'testCase': "IEEE TGi TKIP_Mixer Test vector #4",
     'TK'    : "63 89 3B 25 08 40 B8 AE 0B D0 FA 7E 61 D2 78 3E",
     'TA'    : "64 F2 EA ED DC 25",
     'IV32'  : "20DCFD44",
     'IV16'  : "0000",
     'P1K'   : "5A5D  73A8  A859  2EC1  DC8B",
     'RC4KEY': "00 20 00 49 8C A4 71 FC FB FA A1 6E 36 10 F0 05"},

    {'testCase': "IEEE TGi TKIP_Mixer Test vector #5",
     'TK'    : "98 3A 16 EF 4F AC B3 51 AA 9E CC 27 1D 73 09 E2",
     'TA'    : "50 9C 4B 17 27 D9",
     'IV32'  : "F0A410FC",
     'IV16'  : "058C",
     'P1K'   : "F2DF  EBB1  88D3  5923  A07C",
     'RC4KEY': "05 25 8C F4 D8 51 52 F4 D9 AF 1A 64 F1 D0 70 21"},

    {'testCase': "IEEE TGi TKIP_Mixer Test vector #6",
     'TK'    : "98 3A 16 EF 4F AC B3 51 AA 9E CC 27 1D 73 09 E2",
     'TA'    : "50 9C 4B 17 27 D9",
     'IV32'  : "F0A410FC",
     'IV16'  : "058D",
     'P1K'   : "F2DF  EBB1  88D3  5923  A07C ",
     'RC4KEY': "05 25 8D 09 F8 15 43 B7 6A 59 6F C2 C6 73 8B 30"},

    {'testCase': "IEEE TGi TKIP_Mixer Test vector #7",
     'TK'    : "C8 AD C1 6A 8B 4D DA 3B 4D D5 B6 54 38 35 9B 05",
     'TA'    : "94 5E 24 4E 4D 6E",
     'IV32'  : "8B1573B7",
     'IV16'  : "30F8",
     'P1K'   : "EFF1  3F38  A364  60A9  76F3",
     'RC4KEY': "30 30 F8 65 0D A0 73 EA 61 4E A8 F4 74 EE 03 19"},

    {'testCase': "IEEE TGi TKIP_Mixer Test vector #8",
     'TK'    : "C8 AD C1 6A 8B 4D DA 3B 4D D5 B6 54 38 35 9B 05",
     'TA'    : "94 5E 24 4E 4D 6E",
     'IV32'  : "8B1573B7",
     'IV16'  : "30F9",
     'P1K'   : "EFF1  3F38  A364  60A9  76F3",
     'RC4KEY': "30 30 F9 31 55 CE 29 34 37 CC 76 71 27 16 AB 8F"}
    ]

TKIP_TestVector = [
    {'testCase': "-------------TKIP Test Vector 1",
     'TK'    : "00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f",
     'TA'    : "10 22 33 44 55 66",
     'PN'    : 0x000000000000,
     'RC4KEY': "00 20 00 33 EA 8D 2F 60 CA 6D 13 74 23 4A 66 0B"},
    {'testCase': "-------------IEEE TGi TKIP_Mixer Test vector #6 Mod to PN",
     'TK'    : "98 3A 16 EF 4F AC B3 51 AA 9E CC 27 1D 73 09 E2",
     'TA'    : "50 9C 4B 17 27 D9",
     'PN'    : 0xF0A410FC058D,    # [transmitted as:  8D 25 05 DefKeyID FC 10 A4 F0]
     'RC4KEY': "05 25 8D 09 F8 15 43 B7 6A 59 6F C2 C6 73 8B 30"}]

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()

