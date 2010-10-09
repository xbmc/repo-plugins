# -*- coding: iso-8859-1 -*-
""" fmath.prime

    Start of prime number routines. Rabin-miller test works, more to come later.

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""

def fermat_little_test( p, a ):
    """ Fermat Little Test. Included as a curiosity, not useful for cryptographic use.
        p -> possiblePrime, a -> any integer
    """
    if pow(a,p-1,p) == 1 :
        return 1  # could be prime
    else:
        return 0  # is NOT prime

def rabin_miller(possiblePrime, aTestInteger):
    """ The Rabin-Miller algorithm to test possible primes
        taken from HAC algorithm 4.24, without the 't'
    """
    assert( 1<= aTestInteger <= (possiblePrime-1) ), 'test integer %d out of range for %d'%(aTestInteger,possiblePrime)
    #assert( possiblePrime%2 == 1 ), 'possiblePrime must be odd'
    # calculate s and r such that (possiblePrime-1) = (2**s)*r  with r odd
    r = possiblePrime-1
    s=0
    while (r%2)==0 :
        s+=1
        r=r/2
    y = pow(aTestInteger,r,possiblePrime)
    if ( y!=1 and y!=(possiblePrime-1) ) :
        j = 1
        while ( j <= s-1 and y!=possiblePrime-1 ):
            y = pow(y,2,possiblePrime) # (y*y) % n
            if y==1 :
                return 0 # failed - composite
            j = j+1
        if y != (possiblePrime-1):
            return 0 # failed - composite
    return 1 # success - still a possible prime


