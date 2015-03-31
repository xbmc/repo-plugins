import struct

"""
The internal FLV representations of numbers.
"""


__all__ = ['get_ui32', 'make_ui32', 'get_si32_extended', 'make_si32_extended',
           'get_ui24', 'make_ui24', 'get_ui16', 'make_ui16',
           'get_si16', 'make_si16', 'get_ui8', 'make_ui8',
           'get_double', 'make_double', 'EndOfFile']


class EndOfFile(Exception):
    pass


# UI32
def get_ui32(f):
    try:
        ret = struct.unpack(">I", f.read(4))[0]
    except struct.error:
        raise EndOfFile
    return ret

def make_ui32(num):
    return struct.pack(">I", num)


# SI32 extended
def get_si32_extended(f):
    # The last 8 bits are the high 8 bits of the whole number
    # That's how Adobe likes it. Go figure...
    low_high = f.read(4)
    if len(low_high) < 4:
        raise EndOfFile
    combined = low_high[3] + low_high[:3]
    return struct.unpack(">i", combined)[0]

def make_si32_extended(num):
    ret = struct.pack(">i", num)
    return ret[1:] + ret[0]


# UI24
def get_ui24(f):
    try:
        high, low = struct.unpack(">BH", f.read(3))
    except struct.error:
        raise EndOfFile
    ret = (high << 16) + low
    return ret

def make_ui24(num):
    ret = struct.pack(">I", num)
    return ret[1:]


# UI16
def get_ui16(f):
    try:
        ret = struct.unpack(">H", f.read(2))[0]
    except struct.error:
        raise EndOfFile
    return ret

def make_ui16(num):
    return struct.pack(">H", num)


# SI16
def get_si16(f):
    try:
        ret = struct.unpack(">h", f.read(2))[0]
    except struct.error:
        raise EndOfFile
    return ret

def make_si16(num):
    return struct.pack(">h", num)


# UI8
def get_ui8(f):
    try:
        ret = struct.unpack("B", f.read(1))[0]
    except struct.error:
        raise EndOfFile
    return ret

def make_ui8(num):
    return struct.pack("B", num)



# DOUBLE
def get_double(f):
    data = f.read(8)
    try:
        ret = struct.unpack(">d", data)[0]
    except struct.error:
        raise EndOfFile
    return ret

def make_double(num):
    return struct.pack(">d", num)
