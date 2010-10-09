#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.ccm_test

    Tests for CCM encryption, uses AES for base algorithm

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.

    July 24, 2002
"""
import unittest
from crypto.cipher.ccm      import CCM
from crypto.cipher.aes      import AES
from crypto.cipher.base     import noPadding
from crypto.common          import xor
from binascii_plus          import a2b_p, b2a_p

class CCM_AES128_TestVectors(unittest.TestCase):
    """ Test CCM with AES128 algorithm using know values """
    def testKnowValues(self):
        """ Test using vectors from..."""
        def CCMtestVector(testCase,macSize,key,nonce,addAuth,pt,kct):
            """ CCM test vectors using AES algorithm """
            print '%s %s %s'%('='*((54-len(testCase))/2),testCase,'='*((54-len(testCase))/2))
            key,nonce,pt,addAuth,kct = a2b_p(key),a2b_p(nonce),a2b_p(pt),a2b_p(addAuth),a2b_p(kct)

            alg = CCM(AES(key,keySize=len(key)),macSize=macSize, nonceSize=len(nonce))

            print 'alg=%s%skeySize=%3d   blockSize=%3d   M=%2d    L=%2d'%(alg.baseCipher.name,
                              ' '*(10-len(alg.baseCipher.name)),
                              alg.keySize, alg.blockSize, alg.M, alg.L)
            print 'key:    %s'%b2a_p(key)[9:]
            print 'nonce:  %s'%b2a_p(nonce)[9:]
            print 'addAuth:%s'%b2a_p(addAuth)[9:]
            print 'pt:     %s'%b2a_p(pt)[9:]
            ct  = alg.encrypt(pt,nonce=nonce,addAuthData=addAuth)
            print 'ct:     %s'%b2a_p(ct)[9:]
            print 'kct:    %s'%b2a_p(kct)[9:]
            print '========================================================'
            self.assertEqual( ct, kct )
            dct = alg.decrypt(ct,nonce=nonce,addAuthData=addAuth)
            self.assertEqual( dct, pt )

        CCMtestVector(
            testCase =   "CCM Packet Vector #1 (from D.W.)",
            macSize  =    8,
            key      =   "C0 C1 C2 C3 C4 C5 C6 C7  C8 C9 CA CB CC CD CE CF",
            nonce    =   "00 00 00 03 02 01 00 A0  A1 A2 A3 A4 A5",
            addAuth  =   "00 01 02 03 04 05 06 07",
            pt       = """                         08 09 0A 0B 0C 0D 0E 0F
                          10 11 12 13 14 15 16 17  18 19 1A 1B 1C 1D 1E """,
            kct      = """                         58 8C 97 9A 61 C6 63 D2
                          F0 66 D0 C2 C0 F9 89 80  6D 5F 6B 61 DA C3 84 17
                          E8 D1 2C FD F9 26 E0 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet, no A4 and no QC",
            macSize  =    8,
            key      =   "c0 c1 c2 c3 c4 c5 c6 c7  c8 c9 ca cb cc cd ce cf",
            nonce    =   "00 00 02 2d 49 97 b4 06  05 04 03 02 01",
            addAuth  = """08 41 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00""",
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """1e e5 2d 13 b1 be 3f 20  42 5b 3f de dd d4 55 2b
                          98 71 d8 7b 65 8c fd 57  f7 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet, no A4 and no QC, retry",
            macSize  =    8,
            key      =   "c0 c1 c2 c3 c4 c5 c6 c7  c8 c9 ca cb cc cd ce cf",
            nonce    =   "00 00 02 2d 49 97 b4 06  05 04 03 02 01",
            addAuth  = """08 41 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00 """,
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """1e e5 2d 13 b1 be 3f 20  42 5b 3f de dd d4 55 2b
                          98 71 d8 7b 65 8c fd 57  f7 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet,A4 with no QC ",
            macSize  =    8,
            key      =   "c0 c1 c2 c3 c4 c5 c6 c7  c8 c9 ca cb cc cd ce cf",
            nonce    =   "00 00 02 2d 49 97 b4 00  00 00 00 00 01",
            addAuth  = """08 43 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00 41 42  43 44 45 46 """,
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """3b e9 b2 46 c6 fc 7a 51  55 1e 14 c6 a8 85 28 bc
                          06 56 67 c8 ef 30 b3 12  69 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet,A4 and QC ",
            macSize  =    8,
            key      =   "c0 c1 c2 c3 c4 c5 c6 c7  c8 c9 ca cb cc cd ce cf",
            nonce    =   "04 00 02 2d 49 97 b4 00  00 00 00 00 01",
            addAuth  = """88 43 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00 41 42  43 44 45 46 04 00""",
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """46 72 f2 9e 41 54 e9 11  58 47 c2 a9 ae dc 10 0c
                          e8 82 53 bd a2 04 ae 1d  33 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet,QC no A4",
            macSize  =    8,
            key      =   "c0 c1 c2 c3 c4 c5 c6 c7  c8 c9 ca cb cc cd ce cf",
            nonce    =   "04 00 02 2d 49 97 b4 00  00 00 00 00 01",
            addAuth  = """88 41 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00 04 00 """,
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """46 72 f2 9e 41 54 e9 11  58 47 c2 a9 ae dc 10 0c
                          e8 dc 91 98 bf 6a 52 c8  03 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet,QC no A4",
            macSize  =    8,
            key      =   "c0 c1 c2 c3 c4 c5 c6 c7  c8 c9 ca cb cc cd ce cf",
            nonce    =   "04 00 02 2d 49 97 b4 00  00 00 00 00 01",
            addAuth  = """88 41 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00 04 00  """,
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """46 72 f2 9e 41 54 e9 11  58 47 c2 a9 ae dc 10 0c
                          e8 dc 91 98 bf 6a 52 c8  03 """)
        CCMtestVector(
            testCase =   "IEEE 802.11 Data Packet, no A4, No QC, WEP preset",
            macSize  =    8,
            key      =   "00 01 02 03 04 05 06 07  08 c9 0a 0b 0c 0d 0e 0f",
            nonce    =   "00 00 02 2d 49 97 b4 06  05 04 03 02 01",
            addAuth  = """08 41 00 06 25 a7 c4 36  00 02 2d 49 97 b4 00 06
                          25 a7 c4 36 e0 00 """,
            pt       = """aa aa 03 00 00 00 88 8e  01 01 00 00 00 00 00 00
                          00""",
            kct      = """de bf 2c c9 94 e6 5a 70  2c ee e3 19 84 21 39 c3
                          f2 9a 2e 12 63 11 74 5f  3c """)


        CCMtestVector(
            testCase =   "KAT#  1 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "04 e5 1c f0 20 2d 4c 59  0f d2 e1 28 a5 7c 50 30",
            nonce    =   "f1 84 44 08 ab ae a5 b8  fc ba 33 2e 78",
            addAuth  = """ """,
            pt       = """ """,
            kct      = """6f b0 8f 1f a0 ec e1 f0 """)

        CCMtestVector(
            testCase =   "KAT#  2 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "c4 85 98 ee 34 6c 62 1e  c9 7c 1f 67 ce 37 11 85",
            nonce    =   "51 4a 8a 19 f2 bd d5 2f  3a b5 03 97 76",
            addAuth  = """0c """,
            pt       = """e7 """,
            kct      = """13 6d 5e af 39 d5 d3 6f  27 """)

        CCMtestVector(
            testCase =   "KAT#  3 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "f8 ba 1a 55 d0 2f 85 ae  96 7b b6 2f b6 cd a8 eb",
            nonce    =   "7e 78 a0 50 68 dd e8 3a  11 40 85 a2 ea",
            addAuth  = """10 """,
            pt       = """ """,
            kct      = """b8 01 6f 2e fc 56 b2 31 """)

        CCMtestVector(
            testCase =   "KAT#  4 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "0c 84 68 50 ee c1 76 2c  88 de af 2e e9 f4 6a 07",
            nonce    =   "cc ee 9b fb 82 2d 5d 12  fe 9e 30 8f 7a",
            addAuth  = """ """,
            pt       = """05 """,
            kct      = """7d d0 b5 77 e9 0c 1c de  b5 """)

        CCMtestVector(
            testCase =   "KAT#  5 - AES_CCM 128 M= 4 L= 2",
            macSize  =    4,
            key      =   "77 a5 59 75 29 27 20 97  a6 03 d5 91 31 f3 cb ba",
            nonce    =   "97 ea 83 a0 63 4b 5e d7  62 7e b9 df 22",
            addAuth  = """17 fc 89 c1 fc 0d 63 98  c3 d9 57 7d f7 63 c8 b6
                          a8 8a df 36 91 """,
            pt       = """5e 05 74 03 42 de 19 41 """,
            kct      = """0c 5f 95 1b 27 29 6a 16  a8 2a 32 d5 """)

        CCMtestVector(
            testCase =   "KAT#  6 - AES_CCM 128 M= 6 L= 2",
            macSize  =    6,
            key      =   "8b ca 94 dd 82 f4 ea 74  bf a2 1f 09 1e 67 85 40",
            nonce    =   "cf b7 a6 2e 88 01 3b d6  d3 af fc c1 91",
            addAuth  = """ca 30 a0 e7 50 07 97 22  71 """,
            pt       = """04 1e bc 2f dc a0 f3 a5  ae 2c 1b d0 36 83 1c 95
                          49 6c 5f 4d bf 3d 55 9e  72 de 80 2a 18 """,
            kct      = """ad 81 34 7b 1f 61 6e b5  34 c0 e9 a0 7b ed 92 57
                          11 cf 4a 4b 2c 3f 9b 01  25 7a 9a e2 76 e6 c1 83
                          f0 2f ad """)

        CCMtestVector(
            testCase =   "KAT#  7 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "df 11 db 8e f8 22 73 47  01 59 14 0d d6 46 a2 2f",
            nonce    =   "c5 d6 81 5d 5a 6d 72 40  ee a5 8c 89 a2",
            addAuth  = """70 7f cf 24 b3 2d 38 33  0c f6 70 a5 5a 0f e3 4f
                          ad 2b 1c 29 """,
            pt       = """eb c9 6c 76 02 """,
            kct      = """55 17 b7 c5 78 27 3c dd  6a 15 43 9c a0 """)

        CCMtestVector(
            testCase =   "KAT#  8 - AES_CCM 128 M=10 L= 2",
            macSize  =    10,
            key      =   "eb d8 72 fb c3 f3 a0 74  89 8f 8b 2f bb 90 96 66",
            nonce    =   "d6 c6 38 d6 82 45 de c6  9a 74 80 f3 51",
            addAuth  = """c9 6b e2 76 fb e6 c1 27  f2 8a 8c 8e 58 32 f8 b3
                          41 a2 19 a5 74 """,
            pt       = """94 6b """,
            kct      = """55 cd b0 f0 72 a0 b4 31  37 85 31 55 """)

        CCMtestVector(
            testCase =   "KAT#  9 - AES_CCM 128 M=12 L= 2",
            macSize  =    12,
            key      =   "3b b2 5e fd de ff 30 12  2f df d0 66 9d a7 ff e0",
            nonce    =   "3c 0e 37 28 96 9b 95 4f  26 3a 80 18 a9",
            addAuth  = """f9 a6 """,
            pt       = """ef 70 a8 b0 51 46 24 81  92 2e 93 fa 94 71 ac 65
                          77 3f 5a f2 84 30 fd ab  bf f9 43 b9 """,
            kct      = """aa 27 4b a3 37 2e f5 d6  cc ae fe 16 8f de 14 63
                          37 83 e7 d3 0b cc 4a 8f  dc f0 18 c9 c6 79 e8 b9
                          10 95 43 3b bf f2 89 f0 """)

        CCMtestVector(
            testCase =   "KAT# 10 - AES_CCM 128 M=14 L= 2",
            macSize  =    14,
            key      =   "98 c7 fe 73 71 62 4c 9f  fd 3c b3 d9 fb 77 6a f7",
            nonce    =   "1e ea 4e 1f 58 80 4b 97  17 23 0a d0 61",
            addAuth  = """c2 fc a1 """,
            pt       = """46 41 5c 6b 81 ec a4 89  89 ab fd a2 2d 3a 0b fc
                          9c c1 fc 07 93 63 """,
            kct      = """64 e2 0b 0c ef d8 2a 00  27 ed 0f f2 90 1b d3 b7
                          b0 67 6c 1c 4a 4c b7 5c  40 0f db 9c 87 9e 99 c5
                          77 1a 9a 52 """)

        CCMtestVector(
            testCase =   "KAT# 11 - AES_CCM 128 M=16 L= 2",
            macSize  =    16,
            key      =   "eb 1d 3c 1d b4 a4 c5 e2  66 8d 9b 50 f4 fd 56 f6",
            nonce    =   "ef ec 95 20 16 91 83 57  0c 4c cd ee a0",
            addAuth  = """48 1b db 34 98 0e 03 81  24 a1 db 1a 89 2b ec 36
                          6a ce 5e ec 40 73 e7 23  98 be ca 86 f4 b3 """,
            pt       = """50 a4 20 b9 3c ef f4 e7  62 """,
            kct      = """6f 55 64 96 29 95 40 49  34 84 5e 64 dc 68 3c 5f
                          40 dc ec 0a 30 17 e5 df  ee """)

        CCMtestVector(
            testCase =   "KAT# 12 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "0c fd f2 47 24 c5 8e b8  35 66 53 39 e8 1c 37 c0",
            nonce    =   "95 68 e2 e4 55 2d 5f 72  bb 70 ca 3f 3a",
            addAuth  = """5e 55 6e ac 1b f5 4b d5  4e db 23 21 75 43 03 02
                          4c 71 b0 ce fd """,
            pt       = """ae 60 c4 8b a9 b5 f8 2c  2f eb 07 e2 9d 82 6b 95
                          a7 64 """,
            kct      = """42 eb e1 dc be 9b 60 7b  f8 d4 cb 21 6a 7b 5a 57
                          c7 1e 55 97 96 a1 a6 bf  33 2a """)

        CCMtestVector(
            testCase =   "KAT# 13 - AES_CCM 128 M= 8 L= 3",
            macSize  =    8,
            key      =   "cc dd 57 cb 5c 0e 5f cd  88 5e 9a 42 39 e9 b9 ca",
            nonce    =   "d6 0d 64 37 59 79 c2 fc  9a c5 f0 99",
            addAuth  = """7d 86 5c 44 c0 6f 28 a6  46 b3 80 49 4b 50 """,
            pt       = """f6 85 9a fb 79 8b 8a 4b  a4 ad 6d 31 99 85 bc 42
                          9e 8f 0a fa """,
            kct      = """fd f2 3f 1f c5 27 9e ec  06 b5 29 e7 69 96 da 50
                          f9 b3 16 5b 6b 27 2c c7  df 89 06 05 """)

        CCMtestVector(
            testCase =   "KAT# 14 - AES_CCM 128 M= 8 L= 4",
            macSize  =    8,
            key      =   "46 75 97 1a 48 d0 8c 5b  c3 53 cb cd ba 82 e9 34",
            nonce    =   "37 b3 25 a9 8f 9c 1b d9  c9 3c f3",
            addAuth  = """15 2d 76 """,
            pt       = """83 ab 9d 98 """,
            kct      = """db 12 ef 44 3e f0 a6 aa  d4 2f 35 28 """)

        CCMtestVector(
            testCase =   "KAT# 15 - AES_CCM 128 M= 8 L= 5",
            macSize  =    8,
            key      =   "32 c6 33 dd 03 9e 4d 75  20 c7 40 ec 29 fa 75 9b",
            nonce    =   "53 f8 69 fe 27 9a f0 f9  f8 a6",
            addAuth  = """2e e1 a3 04 cf 1d 3e 75  fe """,
            pt       = """54 16 e3 52 bf d2 70 3d  24 2f 66 c1 ef 48 9e 49
                          bc 3c fe 3f ce 38 95 82  0e 87 """,
            kct      = """11 62 22 64 5e 6c a0 d1  c9 95 3a 1b 00 04 59 4e
                          3c 90 f0 56 c6 04 f5 37  7e 5a d3 c0 50 0b 33 3a
                          4c 19 """)

        CCMtestVector(
            testCase =   "KAT# 16 - AES_CCM 128 M= 8 L= 6",
            macSize  =    8,
            key      =   "91 f2 47 2d 7a 12 1c 9c  dd 4b 6c 90 80 67 5a 10",
            nonce    =   "20 aa 00 eb 1f ed cb c9  33",
            addAuth  = """9d 52 4a e1 96 d8 ec 48  62 02 be 5c 45 45 67 2a """,
            pt       = """e8 a8 29 8c 0b aa 91 90  34 7c eb 9a ab ff d8 3d
                          48 86 e5 c2 53 e2 """,
            kct      = """86 09 aa 4b 03 c5 67 99  a9 84 4d 4d 62 75 c0 bd
                          09 43 f2 69 12 46 88 fa  fd ae 6e 06 6a 73 """)

        CCMtestVector(
            testCase =   "KAT# 17 - AES_CCM 128 M= 8 L= 7",
            macSize  =    8,
            key      =   "e3 14 d7 0f 1f 9e 85 e7  d2 d6 59 6e 55 d4 f9 a8",
            nonce    =   "12 e4 a2 8a f7 f3 71 4d",
            addAuth  = """f6 62 2e 59 32 f2 18 45  09 23 76 d4 a0 62 a1 5e
                          4f aa 28 8b 84 35 bc d8  ac 5a 7e c4 44 e8 """,
            pt       = """4b """,
            kct      = """5a be a2 22 f4 13 94 50  27 """)

        CCMtestVector(
            testCase =   "KAT# 18 - AES_CCM 128 M= 8 L= 8",
            macSize  =    8,
            key      =   "50 53 8b 62 e8 14 02 c2  ee 11 8a 66 62 b4 77 07",
            nonce    =   "7e d7 94 53 e4 a1 8d",
            addAuth  = """48 d5 42 89 16 be 95 29  35 37 b9 aa 08 """,
            pt       = """60 43 8c c6 48 4d 6e d0  50 b0 1e 77 fd 8e 43 19
                          81 a2 33 6d 02 f8 cb 84 """,
            kct      = """bf fa bd 07 33 ed 9f 6c  90 7c b6 32 0a bf 32 7e
                          c3 a5 78 85 5b f2 e2 56  72 c9 3c cc a4 a3 f2 9c """)

        CCMtestVector(
            testCase =   "KAT# 19 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "98 8a bd c2 3a 65 bb 5d  cd 99 f9 42 67 d3 0b 45",
            nonce    =   "c7 8e 7d fa 21 24 5a 43  90 8f 80 b3 8b",
            addAuth  = """ """,
            pt       = """0a 33 d2 12 79 8c f1 32  c5 51 db fd 53 27 7e b4
                          c9 e5 cc 07 e3 c2 e8 1c  58 2e 7d a6 c4 b1 34 5a
                          74 """,
            kct      = """f3 1f 8e fa 43 b4 cf 36  1d 20 34 62 05 b0 cc fd
                          c1 81 79 17 b4 99 c5 84  3e b6 6e c0 b9 6d 27 e5
                          85 9a a9 bd ae a8 00 d1  7a """)

        CCMtestVector(
            testCase =   "KAT# 20 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "e0 d7 27 f8 10 5b 00 6d  88 22 96 89 5f 74 dc 0c",
            nonce    =   "e5 99 95 c7 ed 2a b0 35  7b 0e 7b fd b6",
            addAuth  = """c5 """,
            pt       = """d0 44 95 d5 24 bb a6 5e  87 f8 5b 00 d0 48 56 4f
                          a2 04 df a9 9d 79 94 55  32 67 23 cd 7c 2f 7a 36
                          95 """,
            kct      = """ee b1 9c c2 e1 a3 71 3a  a0 eb 2f da 57 f3 d3 d8
                          e2 c8 2d e1 2f 39 49 5a  ce 8e b0 5d 14 07 9a a2
                          04 e6 29 62 3b a3 a3 0b  ea """)

        CCMtestVector(
            testCase =   "KAT# 21 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "df 19 a2 25 47 cd 66 d8  75 16 de 8a 18 22 54 26",
            nonce    =   "c0 8c 9b 85 9a a1 86 50  89 59 2f 7c be",
            addAuth  = """9e 27 """,
            pt       = """16 5c 95 80 5b d4 ac a2  9d 4e 62 a2 84 31 1b 6f
                          5f a9 b8 2d 27 23 88 f2  92 2d 9b 7e """,
            kct      = """62 b3 51 dd bc e7 cd f5  80 e8 c8 fd 2b 79 e4 8e
                          42 31 11 32 52 b8 6e 7e  bd 7a 73 3f 0c 85 7f a6
                          5d 2e 14 4a """)

        CCMtestVector(
            testCase =   "KAT# 22 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "b1 20 0c 9a 41 66 58 4d  08 1b 9d ee 30 9b 9e e7",
            nonce    =   "a7 89 88 53 2f 4c 75 0b  02 63 3f 1b d9",
            addAuth  = """86 52 43 02 de 79 1d 5c  3e 3b 3f 93 b5 2c 75 """,
            pt       = """92 0a a8 c6 d5 4e a8 d7  e6 c3 fb 9d 6d 9c 9f 8d
                          bb 1c ab bb 41 59 d8 93  80 f5 53 40 89 """,
            kct      = """2f 8c ac 1a b1 20 0c 0e  41 6c 95 91 b2 6e 89 07
                          75 9b 57 5a eb 90 76 14  f4 fe 64 bb 3c 45 ad 77
                          38 90 37 33 97 """)

        CCMtestVector(
            testCase =   "KAT# 23 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "c1 56 c1 1d 02 ff 67 d7  72 bd d2 1f 33 59 12 be",
            nonce    =   "5b 1f e2 48 8e 6c fe 20  23 77 61 d9 d0",
            addAuth  = """d9 da 29 4c d5 20 30 26  2e a0 10 25 e8 e4 20 1e """,
            pt       = """ """,
            kct      = """f1 22 23 f0 46 71 13 f1 """)

        CCMtestVector(
            testCase =   "KAT# 24 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "1b 13 51 12 e0 2e 26 14  5a e5 55 0d 79 b1 5a fc",
            nonce    =   "70 00 f2 88 ef 21 d3 28  61 7a de da 5b",
            addAuth  = """6b 27 87 7e cd 15 af 07  ea f3 06 4d c1 35 cd b9
                          64 """,
            pt       = """2e 01 11 9a a1 e1 b6 95  cd 74 22 96 84 8d 0e f2
                          40 ba 3d 29 56 75 7b 43 """,
            kct      = """b1 0d 5b a6 c6 9e bf 40  52 cc bf 5e 51 65 8c 95
                          3c 99 f3 9d 18 d8 34 f4  ed 7b b4 c9 7e 3a 6b 39 """)

        CCMtestVector(
            testCase =   "KAT# 25 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "99 1c d1 06 71 c6 58 db  fd 3e 86 b3 c2 51 ac 0f",
            nonce    =   "d8 ea cc b4 56 b7 ff 99  98 b4 59 bc b3",
            addAuth  = """ed b9 79 05 b3 09 98 54  8f e1 05 d2 26 16 86 2d
                          1d 2d dc c7 33 cd 71 fe  b5 a7 53 ae ba eb b1 7d """,
            pt       = """37 e6 72 ae 6a da 05 dd  88 9d """,
            kct      = """db f0 80 9a 74 d3 c6 62  0b f4 c5 1c 91 6c 93 16
                          01 f2 """)

        CCMtestVector(
            testCase =   "KAT# 26 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "5f c7 0b 97 11 75 ff bc  69 da e3 e8 bf 08 73 bd",
            nonce    =   "f8 bb 2c a4 db a6 59 98  d4 2a 28 56 c3",
            addAuth  = """71 04 9a 00 2a 1b e2 5c  7b f2 85 8c 31 18 0d ce
                          94 f1 8d 20 79 82 """,
            pt       = """ """,
            kct      = """0d 25 b4 0f 5a be 36 19 """)

        CCMtestVector(
            testCase =   "KAT# 27 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "17 40 8b dc 9c 5e 13 94  29 35 dd 2e 7d bd 54 37",
            nonce    =   "14 7a 47 0d ff ab 27 4c  ab a4 38 5d f2",
            addAuth  = """ """,
            pt       = """df """,
            kct      = """dc 49 af 7a 17 61 ce e6  c7 """)

        CCMtestVector(
            testCase =   "KAT# 28 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "96 c6 9e f0 99 fc e0 3d  12 fe 0d a0 67 71 6f 0c",
            nonce    =   "ed 65 37 be f8 08 79 83  78 53 5d 4a 4c",
            addAuth  = """3a f1 fa c1 76 5a 19 29  cf 5c 5f 21 94 ac eb 3a
                          6d 7e 07 ca 76 fd d7 2b  6f e4 51 f8 c9 b4 b4 c4 """,
            pt       = """e0 35 """,
            kct      = """d9 b4 34 ee cd 33 3a e8  6c 24 """)

        CCMtestVector(
            testCase =   "KAT# 29 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "ca f7 8d 13 4b e2 09 8f  32 62 af 07 32 7c 9f c0",
            nonce    =   "88 f1 c3 89 76 70 b9 22  72 a1 ae 92 13",
            addAuth  = """38 fa 4b bd ca 0b 8f bb  94 1d 23 a1 84 40 """,
            pt       = """e2 16 5a """,
            kct      = """36 59 64 75 bc a9 1f 8e  a1 54 81 """)

        CCMtestVector(
            testCase =   "KAT# 30 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "ea 76 e2 95 20 f6 cd 6a  7e 43 b1 5f e4 71 df 47",
            nonce    =   "68 1f 2c 11 7d 97 10 34  76 3c 3e c5 9b",
            addAuth  = """d2 30 20 84 10 67 54 a5  82 32 75 """,
            pt       = """4a 27 7e 05 """,
            kct      = """88 cc 3d 7d 34 da 0b 2e  ff 30 97 e5 """)

        CCMtestVector(
            testCase =   "KAT# 31 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "f6 84 fd e0 d5 87 c9 24  66 e0 d3 d6 d6 05 7c ed",
            nonce    =   "aa 81 33 0b c8 f8 24 82  df 99 d7 57 6b",
            addAuth  = """47 99 ee 5f 0c 60 6a 8a  d5 1c 04 16 ce 19 63 """,
            pt       = """49 7d 2b 08 01 """,
            kct      = """c0 2c e4 d5 88 3e e5 36  4a d9 fc c0 ac """)

        CCMtestVector(
            testCase =   "KAT# 32 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "75 29 fb 1c db d2 72 2f  14 89 d7 c8 48 29 72 d7",
            nonce    =   "17 35 b5 aa d2 90 97 28  2f e3 fa 11 37",
            addAuth  = """7d 13 21 e4 5c 3c 79 a4  29 78 4c 5c 1f 8c c0 """,
            pt       = """d8 94 34 c2 73 b7 """,
            kct      = """09 b0 a7 5e 52 66 8c d3  6d 29 97 59 c7 ea """)

        CCMtestVector(
            testCase =   "KAT# 33 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "63 9d ac 12 4a 9a 47 03  9c 2b 63 8f 66 48 0b b8",
            nonce    =   "2f 2d 59 97 8d 0e ef 44  3e 5a ce 50 9b",
            addAuth  = """c4 35 4b f6 ca f3 48 4e  6f 2a f3 6f ed ff 1f dc
                          0b """,
            pt       = """0b 22 97 03 7c 02 9e """,
            kct      = """b5 c3 f8 0f 56 b1 9d d8  2c f0 f0 cf dd 7a 22 """)

        CCMtestVector(
            testCase =   "KAT# 34 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "25 69 2d 57 e1 de d4 f5  08 34 40 98 c8 fc 70 1e",
            nonce    =   "a2 db d6 96 04 25 2c 2f  d6 3e e7 a9 6b",
            addAuth  = """d4 fd 14 f8 18 57 """,
            pt       = """69 12 08 9c 94 60 c1 25 """,
            kct      = """81 58 32 b4 97 2d 35 e8  0e 9c 10 c0 e0 6b 58 64 """)

        CCMtestVector(
            testCase =   "KAT# 35 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "f6 92 a4 95 3e b4 97 c1  cc f1 a1 47 ad 12 59 f1",
            nonce    =   "e6 cd 88 fd 72 96 90 68  02 24 9d 5c b8",
            addAuth  = """db 1b f5 a4 56 93 74 fd  cf 34 eb """,
            pt       = """fc dc 43 ed 68 17 37 ac  8d """,
            kct      = """ba d6 85 af 4c 35 15 03  26 6f 97 69 4f 54 62 7f
                          ed """)

        CCMtestVector(
            testCase =   "KAT# 36 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "94 c6 17 0a 9b d0 c6 dc  e5 66 7b be 9f e9 4e 5d",
            nonce    =   "b2 bb 6a aa c5 88 ce fb  4e fc c6 2b 61",
            addAuth  = """a4 d9 a5 be 4f ee d2 bc  eb 0d 9e 59 75 19 72 98
                          f3 be 45 6a 23 ef a9 c7  ed 56 14 """,
            pt       = """aa d9 7b 99 47 22 07 9a  25 30 """,
            kct      = """11 d7 a8 6e 94 9c 06 d2  48 15 60 2d ca a1 a1 8c
                          be 48 """)

        CCMtestVector(
            testCase =   "KAT# 37 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "13 28 d8 ea cf 6f 77 da  12 24 72 5b bb 07 43 d2",
            nonce    =   "21 43 19 d3 f8 67 20 f6  53 3a f5 f1 6c",
            addAuth  = """60 1b 7c aa d5 54 1e 9a  7e ea fa """,
            pt       = """d5 87 65 96 de 32 a1 e7  85 83 78 """,
            kct      = """22 1c f0 92 45 71 38 e7  00 21 af 45 d3 31 28 01
                          69 3a 47 """)

        CCMtestVector(
            testCase =   "KAT# 38 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "54 7b 02 1b ef 8c 1c 0f  f1 04 ba 1d bf 0e 2c 0b",
            nonce    =   "f7 a8 59 5b d6 5d 23 e9  cb 17 b1 e1 92",
            addAuth  = """ """,
            pt       = """64 8c ec 53 c4 79 fe 41  53 17 ba 8e """,
            kct      = """6f 52 93 85 89 87 15 21  29 d5 dd 85 0d dc 3d 58
                          60 fb 8a b2 """)

        CCMtestVector(
            testCase =   "KAT# 39 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "31 4b 5f 29 01 80 0f 0a  6a 4f ad 8d d1 9b b1 13",
            nonce    =   "2a a9 31 4e c4 ef 5b 71  b5 3b 2c da 17",
            addAuth  = """92 52 e0 44 24 d5 29 f0  00 96 6b a8 87 90 0c 07
                          eb c1 a8 51 02 f0 d0 07  80 20 3d """,
            pt       = """40 8d 60 be f0 3c b1 8a  1f 4f 40 5d 9f """,
            kct      = """99 a7 5d db a3 72 9f c7  41 22 ba e0 25 4b 7f ba
                          05 a1 4b cf 09 """)

        CCMtestVector(
            testCase =   "KAT# 40 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "b7 32 3f 57 b7 e5 3d b7  4e bd e0 88 d2 d3 e1 61",
            nonce    =   "4e 78 a2 6b 45 93 d0 96  9c 8f 9f 63 c1",
            addAuth  = """f6 fb 75 4a eb 40 7a 91  6a d8 2c 27 13 01 97 9f
                          85 ff 01 80 8e 51 67 29  15 e5 72 """,
            pt       = """46 64 14 a0 82 4e 25 9d  ef 30 9d 9a 1b 54 """,
            kct      = """f9 a1 27 c7 67 4b 39 ea  50 30 c3 eb 45 b1 ff b8
                          b4 5c 86 72 b2 7b """)

        CCMtestVector(
            testCase =   "KAT# 41 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "48 28 39 bc 82 e9 4a d1  55 8f b6 79 0b 3e 36 6f",
            nonce    =   "b8 ed 08 17 e6 f6 df 07  5e f7 87 d2 ef",
            addAuth  = """3c 16 89 0f 70 b2 1c ab  ba 2b a7 84 35 b0 66 2a
                          b6 1c db 78 42 """,
            pt       = """52 13 fe 0f 90 8c c5 69  a1 6e 48 c8 c5 d3 92 """,
            kct      = """c0 64 0e a7 0a d5 46 f7  3e 7e 44 5f 96 78 f5 57
                          36 22 d9 77 74 93 a4 """)

        CCMtestVector(
            testCase =   "KAT# 42 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "73 62 b6 9c e4 dd 9f 02  75 36 9a 60 24 e5 96 69",
            nonce    =   "c0 a7 67 e3 ba 5c 5d 86  10 6e eb f4 9f",
            addAuth  = """2e 37 47 00 22 cc 59 91  a4 a4 13 a0 d8 5a c1 ef
                          eb 9a 4a """,
            pt       = """16 6a 40 a6 70 60 b2 a6  58 af 1a d5 73 8f 7d 12 """,
            kct      = """90 42 65 e5 35 01 bf dd  93 71 87 bd 4c 6c 29 bf
                          85 b1 c2 7a 92 70 bb c1 """)

        CCMtestVector(
            testCase =   "KAT# 43 - AES_CCM 128 M= 8 L= 2",
            macSize  =    8,
            key      =   "63 de fa 62 5f 45 09 34  78 8f b4 1b 32 69 cc 94",
            nonce    =   "7f 9d 39 9d 87 26 be f8  10 71 92 90 30",
            addAuth  = """ee 42 eb """,
            pt       = """0f 3c 27 63 46 fe 7a 72  ad 46 6b 39 a5 62 d5 52
                          5a """,
            kct      = """68 72 5d 02 05 49 78 34  6a 7b f5 4e df c6 e6 d8
                          e6 6c 5c 7e e0 3d f8 0a  b0 """)

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()


