import os
import calendar
import datetime
import logging

from primitives import *
from constants import *
from helpers import OrderedAttrDict, utc


"""
The AS types and their FLV representations.
"""

log = logging.getLogger('flvlib.astypes')


class MalformedFLV(Exception):
    pass


# Number
def get_number(f, max_offset=None):
    return get_double(f)

def make_number(num):
    return make_double(num)


# Boolean
def get_boolean(f, max_offset=None):
    value = get_ui8(f)
    return bool(value)

def make_boolean(value):
    return make_ui8((value and 1) or 0)


# String
def get_string(f, max_offset=None):
    # First 16 bits are the string's length
    length = get_ui16(f)
    # Then comes the string itself
    ret = f.read(length)
    return ret

def make_string(string):
    if isinstance(string, unicode):
        # We need a blob, not unicode. Arbitrarily choose UTF-8
        string = string.encode('UTF-8')
    length = make_ui16(len(string))
    return length + string


# Longstring
def get_longstring(f, max_offset=None):
    # First 32 bits are the string's length
    length = get_ui32(f)
    # Then comes the string itself
    ret = f.read(length)
    return ret

def make_longstring(string):
    if isinstance(string, unicode):
        # We need a blob, not unicode. Arbitrarily choose UTF-8
        string = string.encode('UTF-8')
    length = make_ui32(len(string))
    return length + string


# ECMA Array
class ECMAArray(OrderedAttrDict):
    pass


def get_ecma_array(f, max_offset=None):
    length = get_ui32(f)
    log.debug("The ECMA array has approximately %d elements", length)
    array = ECMAArray()
    while True:
        if max_offset and (f.tell() == max_offset):
            log.debug("Prematurely terminating reading an ECMA array")
            break
        marker = get_ui24(f)
        if marker == 9:
            log.debug("Marker!")
            break
        else:
            f.seek(-3, os.SEEK_CUR)
        name, value = get_script_data_variable(f, max_offset=max_offset)
        array[name] = value
    return array

def make_ecma_array(d):
    length = make_ui32(len(d))
    rest = ''.join([make_script_data_variable(name, value)
                    for name, value in d.iteritems()])
    marker = make_ui24(9)
    return length + rest + marker


# Strict Array
def get_strict_array(f, max_offset=None):
    length = get_ui32(f)
    log.debug("The length is %d", length)
    elements = [get_script_data_value(f, max_offset=max_offset)
                for _ in xrange(length)]
    return elements

def make_strict_array(l):
    ret = make_ui32(len(l))
    rest = ''.join([make_script_data_value(value) for value in l])
    return ret + rest


# Date
def get_date(f, max_offset=None):
    timestamp = get_number(f) / 1000.0
    # From the following document:
    #   http://opensource.adobe.com/wiki/download/
    #   attachments/1114283/amf0_spec_121207.pdf
    #
    # Section 2.13 Date Type
    #
    # (...) While the design of this type reserves room for time zone offset
    # information, it should not be filled in, nor used (...)
    _ignored = get_si16(f)
    return datetime.datetime.fromtimestamp(timestamp, utc)

def make_date(date):
    if date.tzinfo:
        utc_date = date.astimezone(utc)
    else:
        # assume it's UTC
        utc_date = date.replace(tzinfo=utc)
    ret = make_number(calendar.timegm(utc_date.timetuple()) * 1000)
    offset = 0
    return ret + make_si16(offset)


# Null
def get_null(f, max_offset=None):
    return None

def make_null(none):
    return ''


# Object
class FLVObject(OrderedAttrDict):
    pass


def get_object(f, max_offset=None):
    ret = FLVObject()
    while True:
        if max_offset and (f.tell() == max_offset):
            log.debug("Prematurely terminating reading an object")
            break
        marker = get_ui24(f)
        if marker == 9:
            log.debug("Marker!")
            break
        else:
            f.seek(-3, os.SEEK_CUR)
        name, value = get_script_data_variable(f)
        setattr(ret, name, value)
    return ret

def make_object(obj):
    # If the object is iterable, serialize keys/values. If not, fall
    # back on iterating over __dict__.
    # This makes sure that make_object(get_object(StringIO(blob))) == blob
    try:
        iterator = obj.iteritems()
    except AttributeError:
        iterator = obj.__dict__.iteritems()
    ret = ''.join([make_script_data_variable(name, value)
                   for name, value in iterator])
    marker = make_ui24(9)
    return ret + marker


# MovieClip
class MovieClip(object):

    def __init__(self, path):
        self.path = path

    def __eq__(self, other):
        return isinstance(other, MovieClip) and self.path == other.path

    def __repr__(self):
        return "<MovieClip at %s>" % self.path

def get_movieclip(f, max_offset=None):
    ret = get_string(f)
    return MovieClip(ret)

def make_movieclip(clip):
    return make_string(clip.path)


# Undefined
class Undefined(object):

    def __eq__(self, other):
        return isinstance(other, Undefined)

    def __repr__(self):
        return '<Undefined>'

def get_undefined(f, max_offset=None):
    return Undefined()

def make_undefined(undefined):
    return ''


# Reference
class Reference(object):

    def __init__(self, ref):
        self.ref = ref

    def __eq__(self, other):
        return isinstance(other, Reference) and self.ref == other.ref

    def __repr__(self):
        return "<Reference to %d>" % self.ref

def get_reference(f, max_offset=None):
    ret = get_ui16(f)
    return Reference(ret)

def make_reference(reference):
    return make_ui16(reference.ref)


as_type_to_getter_and_maker = {
    VALUE_TYPE_NUMBER: (get_number, make_number),
    VALUE_TYPE_BOOLEAN: (get_boolean, make_boolean),
    VALUE_TYPE_STRING: (get_string, make_string),
    VALUE_TYPE_OBJECT: (get_object, make_object),
    VALUE_TYPE_MOVIECLIP: (get_movieclip, make_movieclip),
    VALUE_TYPE_NULL: (get_null, make_null),
    VALUE_TYPE_UNDEFINED: (get_undefined, make_undefined),
    VALUE_TYPE_REFERENCE: (get_reference, make_reference),
    VALUE_TYPE_ECMA_ARRAY: (get_ecma_array, make_ecma_array),
    VALUE_TYPE_STRICT_ARRAY: (get_strict_array, make_strict_array),
    VALUE_TYPE_DATE: (get_date, make_date),
    VALUE_TYPE_LONGSTRING: (get_longstring, make_longstring)
}

type_to_as_type = {
    bool: VALUE_TYPE_BOOLEAN,
    int: VALUE_TYPE_NUMBER,
    long: VALUE_TYPE_NUMBER,
    float: VALUE_TYPE_NUMBER,
    # WARNING: not supporting Longstrings here.
    # With a max length of 65535 chars, noone will notice.
    str: VALUE_TYPE_STRING,
    unicode: VALUE_TYPE_STRING,
    list: VALUE_TYPE_STRICT_ARRAY,
    dict: VALUE_TYPE_ECMA_ARRAY,
    ECMAArray: VALUE_TYPE_ECMA_ARRAY,
    datetime.datetime: VALUE_TYPE_DATE,
    Undefined: VALUE_TYPE_UNDEFINED,
    MovieClip: VALUE_TYPE_MOVIECLIP,
    Reference: VALUE_TYPE_REFERENCE,
    type(None): VALUE_TYPE_NULL
}

# SCRIPTDATAVARIABLE
def get_script_data_variable(f, max_offset=None):
    name = get_string(f)
    log.debug("The name is %s", name)
    value = get_script_data_value(f, max_offset=max_offset)
    log.debug("The value is %r", value)
    return (name, value)

def make_script_data_variable(name, value):
    log.debug("The name is %s", name)
    log.debug("The value is %r", value)
    ret = make_string(name) + make_script_data_value(value)
    return ret


# SCRIPTDATAVALUE
def get_script_data_value(f, max_offset=None):
    value_type = get_ui8(f)
    log.debug("The value type is %r", value_type)
    try:
        get_value = as_type_to_getter_and_maker[value_type][0]
    except KeyError:
        raise MalformedFLV("Invalid script data value type: %d", value_type)
    log.debug("The getter function is %r", get_value)
    value = get_value(f, max_offset=max_offset)
    return value

def make_script_data_value(value):
    value_type = type_to_as_type.get(value.__class__, VALUE_TYPE_OBJECT)
    log.debug("The value type is %r", value_type)
    #  KeyError can't happen here, because we always fall back on
    #  VALUE_TYPE_OBJECT when determining value_type
    make_value = as_type_to_getter_and_maker[value_type][1]
    log.debug("The maker function is %r", make_value)
    type_tag = make_ui8(value_type)
    ret = make_value(value)
    return type_tag + ret
