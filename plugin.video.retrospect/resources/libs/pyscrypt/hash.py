# The MIT License (MIT)
#
# Copyright (c) 2014 Richard Moore
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import hashlib
import hmac
import struct


# Python 2
if bytes == str:
    def check_bytes(byte_array):
        return True

    def get_byte(c):
        'Converts a 1-byte string to a byte'
        return ord(c)

    def chars_to_bytes(array):
        'Converts an array of integers to an array of bytes.'
        return ''.join(chr(c) for c in array)

# Python 3
else:
    xrange = range

    def check_bytes(byte_array):
        return isinstance(byte_array, bytes)

    def get_byte(c):
        return c

    def chars_to_bytes(array):
        return bytes(array)


def pbkdf2_single(password, salt, key_length, prf):
    '''Returns the result of the Password-Based Key Derivation Function 2 with
       a single iteration (i.e. count = 1).

       prf - a psuedorandom function

       See http://en.wikipedia.org/wiki/PBKDF2
    '''

    block_number = 0
    result = b''

    # The iterations
    while len(result) < key_length:
        block_number += 1
        result += prf(password, salt + struct.pack('>L', block_number))

    return result[:key_length]


def salsa20_8(B):
    '''Salsa 20/8 stream cypher; Used by BlockMix. See http://en.wikipedia.org/wiki/Salsa20'''

    # Create a working copy
    x = B[:]

    # Expanded form of this code. The expansion is significantly faster but
    # this is much easier to understand
    # ROUNDS = (
    #     (4, 0, 12, 7),   (8, 4, 0, 9),    (12, 8, 4, 13),   (0, 12, 8, 18),
    #     (9, 5, 1, 7),    (13, 9, 5, 9),   (1, 13, 9, 13),   (5, 1, 13, 18),
    #     (14, 10, 6, 7),  (2, 14, 10, 9),  (6, 2, 14, 13),   (10, 6, 2, 18),
    #     (3, 15, 11, 7),  (7, 3, 15, 9),   (11, 7, 3, 13),   (15, 11, 7, 18),
    #     (1, 0, 3, 7),    (2, 1, 0, 9),    (3, 2, 1, 13),    (0, 3, 2, 18),
    #     (6, 5, 4, 7),    (7, 6, 5, 9),    (4, 7, 6, 13),    (5, 4, 7, 18),
    #     (11, 10, 9, 7),  (8, 11, 10, 9),  (9, 8, 11, 13),   (10, 9, 8, 18),
    #     (12, 15, 14, 7), (13, 12, 15, 9), (14, 13, 12, 13), (15, 14, 13, 18),
    # )
    #
    # for (destination, a1, a2, b) in ROUNDS:
    #     a = (x[a1] + x[a2]) & 0xffffffff
    #     x[destination] ^= ((a << b)  | (a >> (32 - b))) & 0xffffffff
    for i in (8, 6, 4, 2):
        a = (x[0] + x[12]) & 0xffffffff
        x[4] ^= ((a << 7) | (a >> 25))
        a = (x[4] + x[0]) & 0xffffffff
        x[8] ^= ((a << 9) | (a >> 23))
        a = (x[8] + x[4]) & 0xffffffff
        x[12] ^= ((a << 13) | (a >> 19))
        a = (x[12] + x[8]) & 0xffffffff
        x[0] ^= ((a << 18) | (a >> 14))
        a = (x[5] + x[1]) & 0xffffffff
        x[9] ^= ((a << 7) | (a >> 25))
        a = (x[9] + x[5]) & 0xffffffff
        x[13] ^= ((a << 9) | (a >> 23))
        a = (x[13] + x[9]) & 0xffffffff
        x[1] ^= ((a << 13) | (a >> 19))
        a = (x[1] + x[13]) & 0xffffffff
        x[5] ^= ((a << 18) | (a >> 14))
        a = (x[10] + x[6]) & 0xffffffff
        x[14] ^= ((a << 7) | (a >> 25))
        a = (x[14] + x[10]) & 0xffffffff
        x[2] ^= ((a << 9) | (a >> 23))
        a = (x[2] + x[14]) & 0xffffffff
        x[6] ^= ((a << 13) | (a >> 19))
        a = (x[6] + x[2]) & 0xffffffff
        x[10] ^= ((a << 18) | (a >> 14))
        a = (x[15] + x[11]) & 0xffffffff
        x[3] ^= ((a << 7) | (a >> 25))
        a = (x[3] + x[15]) & 0xffffffff
        x[7] ^= ((a << 9) | (a >> 23))
        a = (x[7] + x[3]) & 0xffffffff
        x[11] ^= ((a << 13) | (a >> 19))
        a = (x[11] + x[7]) & 0xffffffff
        x[15] ^= ((a << 18) | (a >> 14))
        a = (x[0] + x[3]) & 0xffffffff
        x[1] ^= ((a << 7) | (a >> 25))
        a = (x[1] + x[0]) & 0xffffffff
        x[2] ^= ((a << 9) | (a >> 23))
        a = (x[2] + x[1]) & 0xffffffff
        x[3] ^= ((a << 13) | (a >> 19))
        a = (x[3] + x[2]) & 0xffffffff
        x[0] ^= ((a << 18) | (a >> 14))
        a = (x[5] + x[4]) & 0xffffffff
        x[6] ^= ((a << 7) | (a >> 25))
        a = (x[6] + x[5]) & 0xffffffff
        x[7] ^= ((a << 9) | (a >> 23))
        a = (x[7] + x[6]) & 0xffffffff
        x[4] ^= ((a << 13) | (a >> 19))
        a = (x[4] + x[7]) & 0xffffffff
        x[5] ^= ((a << 18) | (a >> 14))
        a = (x[10] + x[9]) & 0xffffffff
        x[11] ^= ((a << 7) | (a >> 25))
        a = (x[11] + x[10]) & 0xffffffff
        x[8] ^= ((a << 9) | (a >> 23))
        a = (x[8] + x[11]) & 0xffffffff
        x[9] ^= ((a << 13) | (a >> 19))
        a = (x[9] + x[8]) & 0xffffffff
        x[10] ^= ((a << 18) | (a >> 14))
        a = (x[15] + x[14]) & 0xffffffff
        x[12] ^= ((a << 7) | (a >> 25))
        a = (x[12] + x[15]) & 0xffffffff
        x[13] ^= ((a << 9) | (a >> 23))
        a = (x[13] + x[12]) & 0xffffffff
        x[14] ^= ((a << 13) | (a >> 19))
        a = (x[14] + x[13]) & 0xffffffff
        x[15] ^= ((a << 18) | (a >> 14))


    # Add the original values
    for i in xrange(0, 16):
        B[i] = (B[i] + x[i]) & 0xffffffff


def blockmix_salsa8(BY, Yi, r):
    '''Blockmix; Used by SMix.'''

    start = (2 * r - 1) * 16
    X = BY[start:start + 16]                                      # BlockMix - 1

    for i in xrange(0, 2 * r):                                    # BlockMix - 2

        for xi in xrange(0, 16):                                  # BlockMix - 3(inner)
            X[xi] ^= BY[i * 16 + xi]

        salsa20_8(X)                                              # BlockMix - 3(outer)
        aod = Yi + i * 16                                         # BlockMix - 4
        BY[aod:aod + 16] = X[:16]

    for i in xrange(0, r):                                        # BlockMix - 6 (and below)
        aos = Yi + i * 32
        aod = i * 16
        BY[aod:aod + 16] = BY[aos:aos + 16]

    for i in xrange(0, r):
        aos = Yi + (i * 2 + 1) * 16
        aod = (i + r) * 16
        BY[aod:aod + 16] = BY[aos:aos + 16]


def smix(B, Bi, r, N, V, X):
    '''SMix; a specific case of ROMix. See scrypt.pdf in the links above.'''

    X[:32 * r] = B[Bi:Bi + 32 * r]                   # ROMix - 1

    for i in xrange(0, N):                           # ROMix - 2
        aod = i * 32 * r                             # ROMix - 3
        V[aod:aod + 32 * r] = X[:32 * r]
        blockmix_salsa8(X, 32 * r, r)                # ROMix - 4

    for i in xrange(0, N):                           # ROMix - 6
        j = X[(2 * r - 1) * 16] & (N - 1)            # ROMix - 7
        for xi in xrange(0, 32 * r):                 # ROMix - 8(inner)
            X[xi] ^= V[j * 32 * r + xi]

        blockmix_salsa8(X, 32 * r, r)                # ROMix - 9(outer)

    B[Bi:Bi + 32 * r] = X[:32 * r]                   # ROMix - 10



def hash(password, salt, N, r, p, dkLen):
    """Returns the result of the scrypt password-based key derivation function.

       Constraints:
         r * p < (2 ** 30)
         dkLen <= (((2 ** 32) - 1) * 32
         N must be a power of 2 greater than 1 (eg. 2, 4, 8, 16, 32...)
         N, r, p must be positive
     """

    # This only matters to Python 3
    if not check_bytes(password):
        raise ValueError('password must be a byte array')

    if not check_bytes(salt):
        raise ValueError('salt must be a byte array')

    # Scrypt implementation. Significant thanks to https://github.com/wg/scrypt
    if N < 2 or (N & (N - 1)): raise ValueError('Scrypt N must be a power of 2 greater than 1')

    # A psuedorandom function
    prf = lambda k, m: hmac.new(key = k, msg = m, digestmod = hashlib.sha256).digest()

    # convert into integers
    B  = [ get_byte(c) for c in pbkdf2_single(password, salt, p * 128 * r, prf) ]
    B = [ ((B[i + 3] << 24) | (B[i + 2] << 16) | (B[i + 1] << 8) | B[i + 0]) for i in xrange(0, len(B), 4)]

    XY = [ 0 ] * (64 * r)
    V  = [ 0 ] * (32 * r * N)

    for i in xrange(0, p):
        smix(B, i * 32 * r, r, N, V, XY)

    # Convert back into bytes
    Bc = [ ]
    for i in B:
        Bc.append((i >> 0) & 0xff)
        Bc.append((i >> 8) & 0xff)
        Bc.append((i >> 16) & 0xff)
        Bc.append((i >> 24) & 0xff)

    return pbkdf2_single(password, chars_to_bytes(Bc), dkLen, prf)
