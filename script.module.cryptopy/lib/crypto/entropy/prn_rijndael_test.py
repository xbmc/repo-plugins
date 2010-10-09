#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.entropy.prn_rijndael_test

    Unit test for prn_rijndael

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""

from crypto.entropy.prn_rijndael import PRN_Rijndael
from binascii import b2a_hex

""" Not much of a test yet .... """

if __name__ == "__main__":
    r = PRN_Rijndael()
    for i in range(20):
        print b2a_hex(r.getSomeBytes())
    for i in range (20):
        r.getBytes(i)
    for i in range(40):
        c=r.getBytes(i)
        print b2a_hex(r.getBytes(i))
        r.reseed(c)







