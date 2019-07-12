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


# Tarsnap file format
# From: http://www.dchest.org/crypto/scrypt.html
#
# scrypt encrypted data format
# ----------------------------
#
# offset  length
# 0       6       "scrypt"
# 6       1       scrypt data file version number (== 0)
# 7       1       log2(N) (must be between 1 and 63 inclusive)
# 8       4       r (big-endian integer; must satisfy r * p < 2^30)
# 12      4       p (big-endian integer; must satisfy r * p < 2^30)
# 16      32      salt
# 48      16      first 16 bytes of SHA256(bytes 0 .. 47)
# 64      32      HMAC-SHA256(bytes 0 .. 63)
# 96      X       data xor AES256-CTR key stream generated with nonce == 0
# 96+X    32      HMAC-SHA256(bytes 0 .. 96 + (X - 1))
#
# AES256-CTR is computed with a 256-bit AES key key_enc, and HMAC-SHA256 is
# computed with a 256-bit key key_hmac, where
#   scrypt(password, salt, N, r, p, 64) == [key_enc][key_hmac]
#   Note: N, r, and p are parameters for scrypt key derivation function.


import hashlib
import hmac
import math
import os
import struct

from .hash import hash
from . import aesctr


BLOCK_SIZE = 1024

# Python 2
if bytes == str:
    MODE_READ  = 'r'
    MODE_WRITE = 'w'

    _allowed_read = ['r', 'rb']
    _allowed_write = ['w', 'wb']

    CHR0 = chr(0)

    def check_bytes(byte_array):
        return True

    def get_byte(c):
        'Converts a 1-byte string to a byte'
        return ord(c)

    def is_string(o):
        return isinstance(o, (unicode, str))

# Python 3
else:
    MODE_READ  = 'rb'
    MODE_WRITE = 'wb'

    _allowed_read = ['rb']
    _allowed_write = ['wb']

    CHR0 = bytes([0])

    def check_bytes(byte_array):
        return isinstance(byte_array, bytes)

    def get_byte(c):
        return c

    def is_string(o):
        return isinstance(o, (bytes, str))


# Python 3 doesn't have xrange
try:
    xrange
except NameError:
    xrange = range


class InvalidScryptFileFormat(Exception): pass

# @TODO: In the future we should support the ability in Python 3 to open
#        a ScryptFile with a mode of 'r' as long as the underlying fp
#        is opened for 'rb', and then perform whatever text conversion
#        normal files do when their mode is 'r'.

class ScryptFile(object):

    MODE_READ  = MODE_READ
    MODE_WRITE = MODE_WRITE

    def __init__(self, fp, password, N = None, r = None, p = None, salt = None, mode = None):

        # No explicit mode...
        if mode is None:

            # Does the file have a mode?
            if hasattr(fp, 'mode'):
                mode = fp.mode

            # Otherwise, we can figure out what the valid mode is
            elif N is not None or r is not None or p is not None or salt is not None:
                mode = ScryptFile.MODE_WRITE
            else:
                mode = ScryptFile.MODE_READ

        self._mode = mode

        # This only matters to Python 3
        if password is not None and not check_bytes(password):
            raise ValueError('password must be a byte array')
        if salt is not None and not check_bytes(salt):
            raise ValueError('salt must be a byte array')

        # Make sure our parameters are sane and line up with the file's mode
        if self._mode in _allowed_write:
            if N is None or r is None or p is None:
                raise Exception("Must specify N, r and p for file open for writing")
            if salt is None:
                salt = os.urandom(32)
            elif len(salt) != 32:
                raise ValueError('The salt must be 32 bytes in length')
            key = hash(password, salt, N, r, p, 64)
        elif self._mode in _allowed_read:
            if N is not None or r is not None or p is not None or salt is not None:
                raise Exception("Cannot specify N, r, p or salt for file open for reading (values detected from file)")
            key = None
        else:
            raise Exception('Unknown mode %r' % self._mode)

        # scrypt parameters for derived key
        self._password = password
        self._salt = salt
        self._key = key

        self._N = N
        self._r = r
        self._p = p

        # File state
        if hasattr(fp, 'close'):
            self._filename = None
            self._fp = fp
        elif is_string(fp):
            self._filename = fp
            self._fp = open(fp, self._mode)
        else:
            raise ValueError('fp must be a file-like object or a filename')
        self._closed = False
        self._done_header = False
        self._read_finished = False

        # Buffers for reading and writing
        self._encrypted_buffer = b''
        self._decrypted_buffer = b''

        # The cryptographic engine
        self._crypto = None

        # Whether the final checksum is valid; file not fully read = None, otherwise: True/False
        self._valid = None

    def _load_get_attr(self, name):
        'Return an internal attribute after ensuring the headers is loaded if necessary.'
        if self._mode in _allowed_read and self._N is None:
            self._read_header()
        return getattr(self, name)

    password = property(lambda s: s._password)
    salt = property(lambda s: s._load_get_attr('_salt'))
    key = property(lambda s: s._load_get_attr('_key'))

    N = property(lambda s: s._load_get_attr('_N'))
    r = property(lambda s: s._load_get_attr('_r'))
    p = property(lambda s: s._load_get_attr('_p'))

    closed = property(lambda s: s._closed)
    valid = property(lambda s: s._valid)

    # Some things to better behave line a file-like object
    encoding = property(lambda s: s._fp._encoding)
    errors = property(lambda s: s._fp._errors)
    mode = property(lambda s: s._mode)
    name = property(lambda s: s._fp.name)
    #newlines = property(lambda s: s._fp.newlines)    # This requires more work to make work

    # @TODO; test with print
    #def _set_softspace(self, value):
    #    self._fp.softspace = value
    #softspace = property(lambda s: s._fp.softspace, _set_softspace)

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        if self._filename is not None:
            self.close()
        else:
            self.finalize()
        return False

    def fileno(self):
        '''Integer "file descriptor" for the underlying file object.

        This is needed for lower-level file interfaces, such os.read().'''

        return self._fp.fileno()

    def isatty(self):
        '''True if the underlying file is connected to a tty device.'''

        return self._fp.isatty()

    def close(self):
        '''Close the underlying file.

        Sets data attribute .closed to True. A closed file cannot be used for
        further I/O operations. close() may be called more than once without
        error. Some kinds of file objects (for example, opened by popen())
        may return an exit status upon closing.'''

        if self._mode in _allowed_write and self._valid is None:
            self._finalize_write()
        result = self._fp.close()
        self._closed = True

        return result

    def finalize(self):
        '''Write the final checksum without closing the file.

        This may be required if the underlying file obeject cannot be closed
        in a meaningful way (for example: StringIO will release underlying
        memory)'''

        if self._mode in _allowed_write and self._valid is None:
            self._finalize_write()

    @staticmethod
    def verify_file(fp, password):
        'Returns whether a scrypt encrypted file is valid.'

        sf = ScryptFile(fp = fp, password = password)
        for line in sf: pass
        sf.close()
        return sf.valid

    # Read operations
    def readline(self, size = None):
        '''Next line from the decrypted file, as a string.

        Retain newline.  A non-negative size argument limits the maximum
        number of bytes to return (an incomplete line may be returned then).
        Return an empty string at EOF.'''

        if self.closed: raise ValueError('file closed')
        if self._mode in _allowed_write:
            raise Exception('file opened for write only')
        if self._read_finished: return None

        line = b''
        while not line.endswith(b'\n') and not self._read_finished and (size is None or len(line) <= size):
            line += self.read(1)
        return line

    def readlines(self, sizehint = None):
        '''list of strings, each a decrypted line from the file.

        Call readline() repeatedly and return a list of the lines so read.
        The optional size argument, if given, is an approximate bound on the
        total number of bytes in the lines returned.'''

        return list(self)

    def __iter__(self):
        while True:
            line = self.readline()
            if not line: raise StopIteration()
            yield line

    def _read_header(self):
        '''Read and parse the header and calculate derived keys.'''

        try:
            # Read the entire header
            header = self._fp.read(96)
            if len(header) != 96:
                raise InvalidScryptFileFormat("Incomplete header")

            # Magic number
            if header[0:6] != b'scrypt':
                raise InvalidScryptFileFormat('Invalid magic number").')

            # Version (we only support 0)
            version = get_byte(header[6])
            if version != 0:
                raise InvalidScryptFileFormat('Unsupported version (%d)' % version)

            # Scrypt parameters
            self._N = 1 << get_byte(header[7])
            (self._r, self._p) = struct.unpack('>II', header[8:16])
            self._salt = header[16:48]

            # Generate the key
            self._key = hash(self._password, self._salt, self._N, self._r, self._p, 64)

            # Header Checksum
            checksum = header[48:64]
            calculate_checksum = hashlib.sha256(header[0:48]).digest()[:16]
            if checksum != calculate_checksum:
                raise InvalidScryptFileFormat('Incorrect header checksum')

            # Stream checksum
            checksum = header[64:96]
            self._checksumer = hmac.new(self.key[32:], msg = header[0:64], digestmod = hashlib.sha256)
            if checksum != self._checksumer.digest():
                raise InvalidScryptFileFormat('Incorrect header stream checksum')
            self._checksumer.update(header[64:96])

            # Prepare the AES engine
            self._crypto = aesctr.AESCounterModeOfOperation(key = self.key[:32])

            self._done_header = True

        except InvalidScryptFileFormat as e:
            self.close()
            raise e

        except Exception as e:
            self.close()
            raise InvalidScryptFileFormat('Header error (%s)' % e)


    def _check_final_checksum(self, checksum):
        'Checks the final checksum at the end of the file.'

        self._valid = (checksum == self._checksumer.digest())

    def read(self, size = None):
        '''Read at most size bytes, returned as a string.

        If the size argument is negative or omitted, read until EOF is reached.
        Notice that when in non-blocking mode, less data than what was requested
        may be returned, even if no size parameter was given.'''

        if self.closed: raise ValueError('File closed')
        if self._mode in _allowed_write:
            raise Exception('File opened for write only')
        if not self._done_header:
            self._read_header()

        # The encrypted file has been entirely read, so return as much as they want
        # and remove the returned portion from the decrypted buffer
        if self._read_finished:
            if size is None:
                decrypted = self._decrypted_buffer
            else:
                decrypted = self._decrypted_buffer[:size]
            self._decrypted_buffer = self._decrypted[len(decrypted):]
            return decrypted

        # Read everything in one chunk
        if size is None or size < 0:
            self._encrypted_buffer = self._fp.read()
            self._read_finished = True

        else:
            # We fill the encrypted buffer (keeping it with a minimum of 32 bytes in case of the
            # end-of-file checksum) and decrypt into a decrypted buffer 1 block at a time
            while not self._read_finished:

                # We have enough decrypted bytes (or will after decrypting the encrypted buffer)
                available = len(self._decrypted_buffer) + len(self._encrypted_buffer) - 32
                if available >= size: break

                # Read a little extra for the possible final checksum
                data = self._fp.read(BLOCK_SIZE)

                # No data left; we're done
                if not data:
                    self._read_finished = True
                    break

                self._encrypted_buffer += data

        # Decrypt as much of the encrypted data as possible (leaving the final check sum)
        safe = self._encrypted_buffer[:-32]
        self._encrypted_buffer = self._encrypted_buffer[-32:]
        self._decrypted_buffer += self._crypto.decrypt(safe)
        self._checksumer.update(safe)

        # We read all the bytes, only the checksum remains
        if self._read_finished:
            self._check_final_checksum(self._encrypted_buffer)

        # Send back the number of bytes requests and remove them from the buffer
        decrypted = self._decrypted_buffer[:size]
        self._decrypted_buffer = self._decrypted_buffer[size:]

        return decrypted

    # Write operations
    def flush(self):
        "Flush the underlying file object's I/O buffer."

        if self._mode in _allowed_write:
            self._fp.flush()

    def writelines(self, sequence):
        '''Write the strings to the underlying file object.

        Note that newlines are not added.  The sequence can be any iterable object
        producing strings. This is equivalent to calling write() for each string.'''

        self.write(''.join(sequence))

    def _write_header(self):
        'Writes the header to the underlying file object.'

        header = b'scrypt' + CHR0 + struct.pack('>BII', int(math.log(self.N, 2)), self.r, self.p) + self.salt

        # Add the header checksum to the header
        checksum = hashlib.sha256(header).digest()[:16]
        header += checksum

        # Add the header stream checksum
        self._checksumer = hmac.new(self.key[32:], msg = header, digestmod = hashlib.sha256)
        checksum = self._checksumer.digest()
        header += checksum
        self._checksumer.update(checksum)

        # Write the header
        self._fp.write(header)

        # Prepare the AES engine
        self._crypto = aesctr.AESCounterModeOfOperation(key = self.key[:32])
        #self._crypto = aes(self.key[:32])

        self._done_header = True

    def _finalize_write(self):
        'Finishes any unencrypted bytes and writes the final checksum.'

        # Make sure we have written the header
        if not self._done_header:
            self._write_header()

        # Write the remaining decrypted part to disk
        block = self._crypto.encrypt(self._decrypted_buffer)
        self._decrypted = ''
        self._fp.write(block)
        self._checksumer.update(block)

        # Write the final checksum
        self._fp.write(self._checksumer.digest())
        self._valid = True

    def write(self, str):
        '''Write string str to the underlying file.

        Note that due to buffering, flush() or close() may be needed before
        the file on disk reflects the data written.'''

        if self.closed: raise ValueError('File closed')
        if self._mode in _allowed_read:
            raise Exception('File opened for read only')

        if self._valid is not None:
            raise Exception('file already finalized')

        if not self._done_header:
            self._write_header()

        # Encrypt and write the data
        encrypted = self._crypto.encrypt(str)
        self._checksumer.update(encrypted)
        self._fp.write(encrypted)

