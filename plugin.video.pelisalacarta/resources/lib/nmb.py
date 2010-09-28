# -*- mode: python; tab-width: 4 -*-
# $Id: nmb.py,v 1.9 2003/04/19 09:44:43 miketeo Exp $
#
# Copyright (C) 2001 Michael Teo <michaelteo@bigfoot.com>
# nmb.py - NetBIOS library
#
# This software is provided 'as-is', without any express or implied warranty. 
# In no event will the author be held liable for any damages arising from the 
# use of this software.
#
# Permission is granted to anyone to use this software for any purpose, 
# including commercial applications, and to alter it and redistribute it 
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not 
#    claim that you wrote the original software. If you use this software 
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
#
# 2. Altered source versions must be plainly marked as such, and must not be 
#    misrepresented as being the original software.
#
# 3. This notice cannot be removed or altered from any source distribution.
#

import os, sys, socket, string, re, select, errno
from random import randint
from struct import *



CVS_REVISION = '$Revision: 1.9 $'

# Taken from socket module reference
INADDR_ANY = ''
BROADCAST_ADDR = '<broadcast>'

# Default port for NetBIOS name service
NETBIOS_NS_PORT = 137
# Default port for NetBIOS session service
NETBIOS_SESSION_PORT = 139

# Owner Node Type Constants
NODE_B = 0x00
NODE_P = 0x01
NODE_M = 0x10
NODE_RESERVED = 0x11

# Name Type Constants
TYPE_UNKNOWN = 0x01
TYPE_WORKSTATION = 0x00
TYPE_CLIENT = 0x03
TYPE_SERVER = 0x20
TYPE_DOMAIN_MASTER = 0x1B
TYPE_MASTER_BROWSER = 0x1D
TYPE_BROWSER = 0x1E

NAME_TYPES = { TYPE_UNKNOWN: 'Unknown', TYPE_WORKSTATION: 'Workstation', TYPE_CLIENT: 'Client',
               TYPE_SERVER: 'Server', TYPE_MASTER_BROWSER: 'Master Browser', TYPE_BROWSER: 'Browser Server',
               TYPE_DOMAIN_MASTER: 'Domain Master' }



def strerror(errclass, errcode):
    if errclass == ERRCLASS_OS:
        return 'OS Error', os.strerror(errcode)
    elif errclass == ERRCLASS_QUERY:
        return 'Query Error', QUERY_ERRORS.get(errcode, 'Unknown error')
    elif errclass == ERRCLASS_SESSION:
        return 'Session Error', SESSION_ERRORS.get(errcode, 'Unknown error')
    else:
        return 'Unknown Error Class', 'Unknown Error'
    
    

class NetBIOSError(Exception): pass
class NetBIOSTimeout(Exception): pass



class NBHostEntry:

    def __init__(self, nbname, nametype, ip):
        self.__nbname = nbname
        self.__nametype = nametype
        self.__ip = ip

    def get_nbname(self):
        return self.__nbname

    def get_nametype(self):
        return self.__nametype

    def get_ip(self):
        return self.__ip

    def __repr__(self):
        return '<NBHostEntry instance: NBname="' + self.__nbname + '", IP="' + self.__ip + '">'



class NBNodeEntry:
    
    def __init__(self, nbname, nametype, isgroup, nodetype, deleting, isconflict, isactive, ispermanent):
        self.__nbname = nbname
        self.__nametype = nametype
        self.__isgroup = isgroup
        self.__nodetype = nodetype
        self.__deleting = deleting
        self.__isconflict = isconflict
        self.__isactive = isactive
        self.__ispermanent = ispermanent

    def get_nbname(self):
        return self.__nbname

    def get_nametype(self):
        return self.__nametype

    def is_group(self):
        return self.__isgroup

    def get_nodetype(self):
        return self.__nodetype

    def is_deleting(self):
        return self.__deleting

    def is_conflict(self):
        return self.__isconflict

    def is_active(self):
        return self.__isactive

    def is_permanent(self):
        return self.__ispermanent

    def __repr__(self):
        s = '<NBNodeEntry instance: NBname="' + self.__nbname + '" NameType="' + NAME_TYPES[self.__nametype] + '"'
        if self.__isactive:
            s = s + ' ACTIVE'
        if self.__isgroup:
            s = s + ' GROUP'
        if self.__isconflict:
            s = s + ' CONFLICT'
        if self.__deleting:
            s = s + ' DELETING'
        return s
            


class NetBIOS:

    # Creates a NetBIOS instance without specifying any default NetBIOS domain nameserver.
    # All queries will be sent through the servport.
    def __init__(self, servport = NETBIOS_NS_PORT):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.bind(( INADDR_ANY, 0 ))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except socket.error, ex:
            s.close()
            raise NetBIOSError, ex

        self.__sock = s
        self.__servport = NETBIOS_NS_PORT
        self.__nameserver = None
        self.__broadcastaddr = BROADCAST_ADDR

    # Set the default NetBIOS domain nameserver.
    def set_nameserver(self, nameserver):
        self.__nameserver = nameserver

    # Return the default NetBIOS domain nameserver, or None if none is specified.
    def get_nameserver(self):
        return self.__nameserver

    # Set the broadcast address to be used for query.
    def set_broadcastaddr(self, broadcastaddr):
        self.__broadcastaddr = broadcastaddr

    # Return the broadcast address to be used, or BROADCAST_ADDR if default broadcast address is used.   
    def get_broadcastaddr(self):
        return self.__broadcastaddr

    # Returns a list of NBHostEntry instances containing the host information for nbname.
    # If a NetBIOS domain nameserver has been specified, it will be used for the query.
    # Otherwise, the query is broadcasted on the broadcast address.
    def gethostbyname(self, nbname, type = TYPE_WORKSTATION, scope = None, timeout = 1):
        return self.__queryname(nbname, self.__nameserver, type, scope, timeout)

    # Returns a list of NBNodeEntry instances containing node status information for nbname.
    # If destaddr contains an IP address, then this will become an unicast query on the destaddr.
    # Raises NetBIOSTimeout if timeout (in secs) is reached.
    # Raises NetBIOSError for other errors
    def getnodestatus(self, nbname, destaddr = None, type = TYPE_WORKSTATION, scope = None, timeout = 1):
        if destaddr:
            return self.__querynodestatus(nbname, destaddr, type, scope, timeout)
        else:
            return self.__querynodestatus(nbname, self.__nameserver, type, scope, timeout)
    
    def __queryname(self, nbname, destaddr, type, scope, timeout):
        netbios_name = string.upper(nbname)
        trn_id = randint(1, 32000)
        qn_label = encode_name(netbios_name, type, scope)

        if destaddr:
            req = pack('>HHHHHH', trn_id, 0x0100, 0x01, 0x00, 0x00, 0x00) + qn_label + pack('>HH', 0x20, 0x01)
        else:
            req = pack('>HHHHHH', trn_id, 0x0110, 0x01, 0x00, 0x00, 0x00) + qn_label + pack('>HH', 0x20, 0x01)
            destaddr = self.__broadcastaddr

        wildcard_query = netbios_name == '*'

        self.__sock.sendto(req, 0, ( destaddr, self.__servport ))
        
        addrs = [ ]
        tries = 3
        while 1:
            try:
                ready, _, _ = select.select([ self.__sock.fileno() ], [ ] , [ ], timeout)
                if not ready:
                    if tries and not wildcard_query:
                        # Retry again until tries == 0
                        self.__sock.sendto(req, 0, ( destaddr, self.__servport ))
                        tries = tries - 1
                    elif wildcard_query:
                        return addrs
                    else:
                        raise NetBIOSTimeout
                else:
                    data, _ = self.__sock.recvfrom(65536, 0)
                    if unpack('>H', data[:2])[0] == trn_id:
                        rcode = ord(data[3]) & 0x0f
                        if rcode:
                            if rcode == 0x03:
                                # Name error. Name was not registered on server.
                                return None
                            else:
                                raise NetBIOSError, ( 'Negative name query response', ERRCLASS_QUERY, rcode )
                            
                        qn_length, qn_name, qn_scope = decode_name(data[12:])
                        offset = 20 + qn_length
                        num_records = (unpack('>H', data[offset:offset + 2])[0] - 2) / 4
                        offset = offset + 4
                        for i in range(0, num_records):
                            # In Python2, we can use socket.inet_ntoa(data[58 + i * 4:62 + i * 4]) to convert
                            addrs.append(NBHostEntry(string.rstrip(qn_name[:-1]) + qn_scope, ord(qn_name[-1]), '%d.%d.%d.%d' % unpack('4B', (data[offset:offset + 4]))))
                            offset = offset + 4

                        if not wildcard_query:
                            return addrs
            except select.error, ex:
                if ex[0] != errno.EINTR and ex[0] != errno.EAGAIN:
                    raise NetBIOSError, ( 'Error occurs while waiting for response', ERRCLASS_OS, ex[0] )
            except socket.error, ex:
                pass

    def __querynodestatus(self, nbname, destaddr, type, scope, timeout):
        netbios_name = string.upper(nbname)
        trn_id = randint(1, 32000)
        qn_label = encode_name(netbios_name, type, scope)

        if destaddr:
            req = pack('>HHHHHH', trn_id, 0x0100, 0x01, 0x00, 0x00, 0x00) + qn_label + pack('>HH', 0x21, 0x01)
        else:
            req = pack('>HHHHHH', trn_id, 0x0110, 0x01, 0x00, 0x00, 0x00) + qn_label + pack('>HH', 0x21, 0x01)
            destaddr = self.__broadcastaddr

        tries = 3
        while 1:
            try:
                self.__sock.sendto(req, 0, ( destaddr, self.__servport ))
                ready, _, _ = select.select([ self.__sock.fileno() ], [ ] , [ ], timeout)
                if not ready:
                    if tries:
                        # Retry again until tries == 0
                        tries = tries - 1
                    else:
                        raise NetBIOSTimeout
                else:
                    data, _ = self.__sock.recvfrom(65536, 0)
                    if unpack('>H', data[:2])[0] == trn_id:
                        rcode = ord(data[3]) & 0x0f
                        if rcode:
                            if rcode == 0x03:
                                # Name error. Name was not registered on server.
                                return None
                            else:
                                raise NetBIOSError, ( 'Negative name query response', ERRCLASS_QUERY, rcode )
                            
                        nodes = [ ]
                        num_names = ord(data[56])
                        for i in range(0, num_names):
                            rec_start = 57 + i * 18
                            name = re.sub(chr(0x20) + '*$', '', data[rec_start:rec_start + 15])
                            type, flags = unpack('>BH', data[rec_start + 15: rec_start + 18])
                            nodes.append(NBNodeEntry(name, type, flags & 0x8000, flags & 0x6000,
                                                     flags & 0x1000, flags & 0x0800, flags & 0x0400,
                                                     flags & 0x0200))
                             
                        return nodes
            except select.error, ex:
                if ex[0] != errno.EINTR and ex[0] != errno.EAGAIN:
                    raise NetBIOSError, ( 'Error occurs while waiting for response', ERRCLASS_OS, ex[0] )
            except socket.error, ex:
                pass
        


# Perform first and second level encoding of name as specified in RFC 1001 (Section 4)
def encode_name(name, type, scope):
    if name == '*':
        name = name + '\0' * 15
    elif len(name) > 15:
        name = name[:15] + chr(type)
    else:
        name = string.ljust(name, 15) + chr(type)
        
    encoded_name = chr(len(name) * 2) + re.sub('.', _do_first_level_encoding, name)
    if scope:
        encoded_scope = ''
        for s in string.split(scope, '.'):
            encoded_scope = encoded_scope + chr(len(s)) + s
        return encoded_name + encoded_scope + '\0'
    else:
        return encoded_name + '\0'

# Internal method for use in encode_name()
def _do_first_level_encoding(m):
    s = ord(m.group(0))
    return string.uppercase[s >> 4] + string.uppercase[s & 0x0f]

def decode_name(name):
    name_length = ord(name[0])
    assert name_length == 32

    decoded_name = re.sub('..', _do_first_level_decoding, name[1:33])
    if name[33] == '\0':
        return 34, decoded_name, ''
    else:
        decoded_domain = ''
        offset = 34
        while 1:
            domain_length = ord(name[offset])
            if domain_length == 0:
                break
            decoded_domain = '.' + name[offset:offset + domain_length]
            offset = offset + domain_length
        return offset + 1, decoded_name, decoded_domain

def _do_first_level_decoding(m):
    s = m.group(0)
    return chr(((ord(s[0]) - ord('A')) << 4) | (ord(s[1]) - ord('A')))



class NetBIOSSession:

    def __init__(self, myname, remote_name, remote_host, host_type = TYPE_SERVER, sess_port = NETBIOS_SESSION_PORT):
        if len(myname) > 15:
            self.__myname = string.upper(myname[:15])
        else:
            self.__myname = string.upper(myname)

        assert remote_name
        if len(remote_name) > 15:
            self.__remote_name = string.upper(remote_name[:15])
        else:
            self.__remote_name = string.upper(remote_name)

        self.__remote_host = remote_host
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__sock.connect(( remote_host, sess_port ))
            self.__request_session(host_type)
        except ( socket.error, NetBIOSError ), ex2:
            try:
                self.__sock.close()
            except socket.error, ex:
                pass
            raise ex2

    def get_myname(self):
        return self.__myname

    def get_remote_host(self):
        return self.__remote_host

    def get_remote_name(self):
        return self.__remote_name

    def close(self):
        try:
            self.__sock.shutdown(2)
        except:
            pass
        try:
            self.__sock.close()
        except:
            pass

    def send_packet(self, data):
        self.__sock.send('\x00\x00' + pack('>H', len(data)) + data)

    def recv_packet(self, timeout = None):
        type, flags, data = self.__read(timeout)
        if type == 0x00:
            return data
        else:
            return None

    def __request_session(self, host_type, timeout = None):
        remote_name = encode_name(self.__remote_name, host_type, '')
        myname = encode_name(self.__myname, TYPE_WORKSTATION, '')
        
        self.__sock.send('\x81\x00' + pack('>H', len(remote_name) + len(myname)) + remote_name + myname)
        while 1:
            type, flags, data = self.__read(timeout)
            if type == 0x83:
                raise NetBIOSError, ( 'Cannot request session', ERRCLASS_SESSION, ord(data[0]) )
            elif type == 0x82:
                break
            else:
                # Ignore all other messages, most probably keepalive messages
                pass

    def __read(self, timeout = None):
        read_len = 4
        data = ''

        while read_len > 0:
            try:
                ready, _, _ = select.select([ self.__sock.fileno() ], [ ], [ ], timeout)
                if not ready:
                    raise NetBIOSTimeout
                
                data = data + self.__sock.recv(read_len)
                read_len = 4 - len(data)
            except select.error, ex:
                if ex[0] != errno.EINTR and ex[0] != errno.EAGAIN:
                    raise NetBIOSError, ( 'Error occurs while reading from remote', ERRCLASS_OS, ex[0] )
                
        type, flags, length = unpack('>ccH', data)
        if ord(flags) & 0x01:
            length = length | 0x10000
            
        read_len = length
        data = ''
        while read_len > 0:
            try:
                ready, _, _ = select.select([ self.__sock.fileno() ], [ ], [ ], timeout)
                if not ready:
                    raise NetBIOSTimeout

                data = data + self.__sock.recv(read_len)
                read_len = length - len(data)
            except select.error, ex:
                if ex[0] != errno.EINTR and ex[0] != errno.EAGAIN:
                    raise NetBIOSError, ( 'Error while reading from remote', ERRCLASS_OS, ex[0] )
                
        return ord(type), ord(flags), data



ERRCLASS_QUERY = 0x00
ERRCLASS_SESSION = 0xf0
ERRCLASS_OS = 0xff

QUERY_ERRORS = { 0x01: 'Request format error. Please file a bug report.',
                 0x02: 'Internal server error',
                 0x03: 'Name does not exist',
                 0x04: 'Unsupported request',
                 0x05: 'Request refused'
                 }

SESSION_ERRORS = { 0x80: 'Not listening on called name',
                   0x81: 'Not listening for calling name',
                   0x82: 'Called name not present',
                   0x83: 'Sufficient resources',
                   0x8f: 'Unspecified error'
                   }
