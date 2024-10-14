# Public Domain SOCKS proxy protocol implementation
# Adapted from https://gist.github.com/bluec0re/cafd3764412967417fd3

from __future__ import unicode_literals

# References:
# SOCKS4 protocol http://www.openssh.com/txt/socks4.protocol
# SOCKS4A protocol http://www.openssh.com/txt/socks4a.protocol
# SOCKS5 protocol https://tools.ietf.org/html/rfc1928
# SOCKS5 username/password authentication https://tools.ietf.org/html/rfc1929

import collections
import socket

from .compat import (
    compat_struct_pack,
)

__author__ = 'Timo Schmid <coding@timoschmid.de>'

SOCKS4_VERSION = 4
SOCKS4_REPLY_VERSION = 0x00
# Excerpt from SOCKS4A protocol:
# if the client cannot resolve the destination host's domain name to find its
# IP address, it should set the first three bytes of DSTIP to NULL and the last
# byte to a non-zero value.
SOCKS4_DEFAULT_DSTIP = compat_struct_pack('!BBBB', 0, 0, 0, 0xFF)

SOCKS5_VERSION = 5
SOCKS5_USER_AUTH_VERSION = 0x01
SOCKS5_USER_AUTH_SUCCESS = 0x00


class Socks4Command(object):
    CMD_CONNECT = 0x01
    CMD_BIND = 0x02


class Socks5Command(Socks4Command):
    CMD_UDP_ASSOCIATE = 0x03


class Socks5Auth(object):
    AUTH_NONE = 0x00
    AUTH_GSSAPI = 0x01
    AUTH_USER_PASS = 0x02
    AUTH_NO_ACCEPTABLE = 0xFF  # For server response


class Socks5AddressType(object):
    ATYP_IPV4 = 0x01
    ATYP_DOMAINNAME = 0x03
    ATYP_IPV6 = 0x04


class ProxyError(socket.error):
    ERR_SUCCESS = 0x00

    def __init__(self, code=None, msg=None):
        if code is not None and msg is None:
            msg = self.CODES.get(code) or 'unknown error'
        super(ProxyError, self).__init__(code, msg)


class InvalidVersionError(ProxyError):
    def __init__(self, expected_version, got_version):
        msg = ('Invalid response version from server. Expected {0:02x} got '
               '{1:02x}'.format(expected_version, got_version))
        super(InvalidVersionError, self).__init__(0, msg)


class Socks4Error(ProxyError):
    ERR_SUCCESS = 90

    CODES = {
        91: 'request rejected or failed',
        92: 'request rejected because SOCKS server cannot connect to identd on the client',
        93: 'request rejected because the client program and identd report different user-ids'
    }


class Socks5Error(ProxyError):
    ERR_GENERAL_FAILURE = 0x01

    CODES = {
        0x01: 'general SOCKS server failure',
        0x02: 'connection not allowed by ruleset',
        0x03: 'Network unreachable',
        0x04: 'Host unreachable',
        0x05: 'Connection refused',
        0x06: 'TTL expired',
        0x07: 'Command not supported',
        0x08: 'Address type not supported',
        0xFE: 'unknown username or invalid password',
        0xFF: 'all offered authentication methods were rejected'
    }


class ProxyType(object):
    SOCKS4 = 0
    SOCKS4A = 1
    SOCKS5 = 2


Proxy = collections.namedtuple('Proxy', (
    'type', 'host', 'port', 'username', 'password', 'remote_dns'))
