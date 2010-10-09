#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" fmath.prime_test

    Test for prime number routines

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""
import unittest
from fmath.prime import rabin_miller
from string import split,atoi

class primeTests(unittest.TestCase):
    """ Tests for the rabin_miller probabilistic primality """
    def testKnowPrimes(self):
        """ Test a few known primes """
        for prime in knownPrimes:
            for testNum in (2,3,5,7,9,13,17,19,21,27,33,101,205):
                assert( rabin_miller(prime, testNum) ), 'Prime: %d should pass rabin miller test using %d!'%(prime,testNum)
    def testKnowComposites(self):
        """ Test a few known primes """
        for nonPrime in knownComposites:
            witness = 1
            for testNum in (2,3,5,7,9,13,17,19,21,27,33,101,205):
                if not rabin_miller(nonPrime, testNum):
                    witness = 0
                #print witness, nonPrime, testNum
            assert( not witness ), 'NonPrime: %d should Fail rabin miller tests!'%nonPrime
    def test50K(self):
        """ Test all composites below the first 50000 primes
            print out the maxium witness number required """
        f=open('primes_1st_50k.txt','r')
        s=f.read()
        f.close()
        ps=split(s)
        primes_1st_50k = [atoi(i) for i in ps]
        maxWitness = 2
        lastPrime = 2
        for prime in primes_1st_50k[1:]:
            for composite in range(lastPrime+2,prime,2):
                for witness in primes_1st_50k:
                    if not rabin_miller(composite, witness):
                        if witness > maxWitness:
                            maxWitness = witness
                            print 'composite, maxWitness',composite,maxWitness
                        lastPrime = prime
                        break
                #assert(witness!=primes_1st_50K[-1]),'MR test failed!!!!!!!'
            lastPrime = prime
        print 'last tested',prime

knownPrimes =     [611693, 611707, 611729, 611753, 611791,
                   611801, 611803, 611827, 611833, 611837,
                   611839, 611873, 611879, 611887, 611903,
                   611921, 611927, 611939, 611951, 611953]

knownComposites = [611695, 611709, 611723, 611757, 611793,
                   611805, 611807, 611829, 611835, 611800,
                   611841, 611875, 611881, 611889, 611905,
                   611923, 611925, 611941, 611947, 611937]

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()



