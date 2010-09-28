# -*- mode: python; tab-width: 4 -*-
# $Id: smb.py,v 1.15 2003/02/22 08:03:19 miketeo Exp $
#
# Copyright (C) 2001 Michael Teo <michaelteo@bigfoot.com>
# smb.py - SMB/CIFS library
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
import nmb
from random import randint
from struct import *

# Try to load amkCrypto's DES module to perform password encryption if required.
try:
    from Crypto.Cipher import DES
    amk_crypto = 1
except ImportError:
    # Try to load mxCrypto's DES module to perform password encryption if required.
    try:
        from Crypto.Ciphers import DES
        amk_crypto = 0
    except ImportError:
        DES = None

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

CVS_REVISION = '$Revision: 1.15 $'

# Shared Device Type
SHARED_DISK = 0x00
SHARED_PRINT_QUEUE = 0x01
SHARED_DEVICE = 0x02
SHARED_IPC = 0x03

# Extended attributes mask
ATTR_ARCHIVE = 0x020
ATTR_COMPRESSED = 0x800
ATTR_NORMAL = 0x080
ATTR_HIDDEN = 0x002
ATTR_READONLY = 0x001
ATTR_TEMPORARY = 0x100
ATTR_DIRECTORY = 0x010
ATTR_SYSTEM = 0x004

# Service Type
SERVICE_DISK = 'A:'
SERVICE_PRINTER = 'LPT1:'
SERVICE_IPC = 'IPC'
SERVICE_COMM = 'COMM'
SERVICE_ANY = '?????'

# Server Type (Can be used to mask with SMBMachine.get_type() or SMBDomain.get_type())
SV_TYPE_WORKSTATION = 0x00000001
SV_TYPE_SERVER      = 0x00000002
SV_TYPE_SQLSERVER   = 0x00000004
SV_TYPE_DOMAIN_CTRL = 0x00000008
SV_TYPE_DOMAIN_BAKCTRL = 0x00000010
SV_TYPE_TIME_SOURCE    = 0x00000020
SV_TYPE_AFP            = 0x00000040
SV_TYPE_NOVELL         = 0x00000080
SV_TYPE_DOMAIN_MEMBER = 0x00000100
SV_TYPE_PRINTQ_SERVER = 0x00000200
SV_TYPE_DIALIN_SERVER = 0x00000400
SV_TYPE_XENIX_SERVER  = 0x00000800
SV_TYPE_NT        = 0x00001000
SV_TYPE_WFW       = 0x00002000
SV_TYPE_SERVER_NT = 0x00004000
SV_TYPE_POTENTIAL_BROWSER = 0x00010000
SV_TYPE_BACKUP_BROWSER    = 0x00020000
SV_TYPE_MASTER_BROWSER    = 0x00040000
SV_TYPE_DOMAIN_MASTER     = 0x00080000
SV_TYPE_LOCAL_LIST_ONLY = 0x40000000
SV_TYPE_DOMAIN_ENUM     = 0x80000000

# Options values for SMB.stor_file and SMB.retr_file
SMB_O_CREAT = 0x10   # Create the file if file does not exists. Otherwise, operation fails.
SMB_O_EXCL = 0x00    # When used with SMB_O_CREAT, operation fails if file exists. Cannot be used with SMB_O_OPEN.
SMB_O_OPEN = 0x01    # Open the file if the file exists
SMB_O_TRUNC = 0x02   # Truncate the file if the file exists

# Share Access Mode
SMB_SHARE_COMPAT = 0x00
SMB_SHARE_DENY_EXCL = 0x10
SMB_SHARE_DENY_WRITE = 0x20
SMB_SHARE_DENY_READEXEC = 0x30
SMB_SHARE_DENY_NONE = 0x40
SMB_ACCESS_READ = 0x00
SMB_ACCESS_WRITE = 0x01
SMB_ACCESS_READWRITE = 0x02
SMB_ACCESS_EXEC = 0x03



def strerror(errclass, errcode):
    if errclass == 0x01:
        return 'OS error', ERRDOS.get(errcode, 'Unknown error')
    elif errclass == 0x02:
        return 'Server error', ERRSRV.get(errcode, 'Unknown error')
    elif errclass == 0x03:
        return 'Hardware error', ERRHRD.get(errcode, 'Unknown error')
    # This is not a standard error class for SMB
    elif err_class == 0x80:
        return 'Browse error', ERRBROWSE.get(errcode, 'Unknown error')
    elif errclass == 0xff:
        return 'Bad command', 'Bad command. Please file bug report'
    else:
        return 'Unknown error', 'Unknown error'

    

# Raised when an error has occured during a session
class SessionError(Exception): pass

# Raised when an supported feature is present/required in the protocol but is not
# currently supported by pysmb
class UnsupportedFeature(Exception): pass

# Contains information about a SMB shared device/service
class SharedDevice:

    def __init__(self, name, type, comment):
        self.__name = name
        self.__type = type
        self.__comment = comment

    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

    def get_comment(self):
        return self.__comment

    def __repr__(self):
        return '<SharedDevice instance: name=' + self.__name + ', type=' + str(self.__type) + ', comment="' + self.__comment + '">'



# Contains information about the shared file/directory
class SharedFile:

    def __init__(self, ctime, atime, mtime, filesize, allocsize, attribs, shortname, longname):
        self.__ctime = ctime
        self.__atime = atime
        self.__mtime = mtime
        self.__filesize = filesize
        self.__allocsize = allocsize
        self.__attribs = attribs
        try:
            self.__shortname = shortname[:string.index(shortname, '\0')]
        except ValueError:
            self.__shortname = shortname
        try:
            self.__longname = longname[:string.index(longname, '\0')]
        except ValueError:
            self.__longname = longname

    def get_ctime(self):
        return self.__ctime

    def get_ctime_epoch(self):
        return self.__convert_smbtime(self.__ctime)

    def get_mtime(self):
        return self.__mtime

    def get_mtime_epoch(self):
        return self.__convert_smbtime(self.__mtime)

    def get_atime(self):
        return self.__atime

    def get_atime_epoch(self):
        return self.__convert_smbtime(self.__atime)

    def get_filesize(self):
        return self.__filesize

    def get_allocsize(self):
        return self.__allocsize

    def get_attributes(self):
        return self.__attribs

    def is_archive(self):
        return self.__attribs & ATTR_ARCHIVE

    def is_compressed(self):
        return self.__attribs & ATTR_COMPRESSED

    def is_normal(self):
        return self.__attribs & ATTR_NORMAL

    def is_hidden(self):
        return self.__attribs & ATTR_HIDDEN

    def is_readonly(self):
        return self.__attribs & ATTR_READONLY

    def is_temporary(self):
        return self.__attribs & ATTR_TEMPORARY

    def is_directory(self):
        return self.__attribs & ATTR_DIRECTORY

    def is_system(self):
        return self.__attribs & ATTR_SYSTEM

    def get_shortname(self):
        return self.__shortname

    def get_longname(self):
        return self.__longname

    def __repr__(self):
        return '<SharedFile instance: shortname="' + self.__shortname + '", longname="' + self.__longname + '", filesize=' + str(self.__filesize) + '>'

    def __convert_smbtime(self, t):
        x = t >> 32
        y = t & 0xffffffffL
        geo_cal_offset = 11644473600.0  # = 369.0 * 365.25 * 24 * 60 * 60 - (3.0 * 24 * 60 * 60 + 6.0 * 60 * 60)
        return ((x * 4.0 * (1 << 30) + (y & 0xfff00000L)) * 1.0e-7 - geo_cal_offset)



# Contain information about a SMB machine
class SMBMachine:

    def __init__(self, nbname, type, comment):
        self.__nbname = nbname
        self.__type = type
        self.__comment = comment

    def __repr__(self):
        return '<SMBMachine instance: nbname="' + self.__nbname + '", type=' + hex(self.__type) + ', comment="' + self.__comment + '">'



class SMBDomain:

    def __init__(self, nbgroup, type, master_browser):
        self.__nbgroup = nbgroup
        self.__type = type
        self.__master_browser = master_browser

    def __repr__(self):
        return '<SMBDomain instance: nbgroup="' + self.__nbgroup + '", type=' + hex(self.__type) + ', master browser="' + self.__master_browser + '">'



# Represents a SMB session
class SMB:

    # SMB Command Codes
    SMB_COM_CREATE_DIR = 0x00
    SMB_COM_DELETE_DIR = 0x01
    SMB_COM_CLOSE = 0x04
    SMB_COM_DELETE = 0x06
    SMB_COM_RENAME = 0x07
    SMB_COM_CHECK_DIR = 0x10
    SMB_COM_READ_RAW = 0x1a
    SMB_COM_WRITE_RAW = 0x1d
    SMB_COM_TRANSACTION = 0x25
    SMB_COM_TRANSACTION2 = 0x32
    SMB_COM_OPEN_ANDX = 0x2d
    SMB_COM_READ_ANDX = 0x2e
    SMB_COM_WRITE_ANDX = 0x2f
    SMB_COM_TREE_DISCONNECT = 0x71
    SMB_COM_NEGOTIATE = 0x72
    SMB_COM_SESSION_SETUP_ANDX = 0x73
    SMB_COM_LOGOFF = 0x74
    SMB_COM_TREE_CONNECT_ANDX = 0x75
    
    # Security Share Mode (Used internally by SMB class)
    SECURITY_SHARE_MASK = 0x01
    SECURITY_SHARE_SHARE = 0x00
    SECURITY_SHARE_USER = 0x01
    
    # Security Auth Mode (Used internally by SMB class)
    SECURITY_AUTH_MASK = 0x02
    SECURITY_AUTH_ENCRYPTED = 0x02
    SECURITY_AUTH_PLAINTEXT = 0x00

    # Raw Mode Mask (Used internally by SMB class. Good for dialect up to and including LANMAN2.1)
    RAW_READ_MASK = 0x01
    RAW_WRITE_MASK = 0x02

    # Capabilities Mask (Used internally by SMB class. Good for dialect NT LM 0.12)
    CAP_RAW_MODE = 0x0001
    CAP_MPX_MODE = 0x0002
    CAP_UNICODE = 0x0004
    CAP_LARGE_FILES = 0x0008
    CAP_EXTENDED_SECURITY = 0x80000000

    # Flags1 Mask
    FLAGS1_PATHCASELESS = 0x08

    # Flags2 Mask
    FLAGS2_LONG_FILENAME = 0x0001
    FLAGS2_UNICODE = 0x8000

    def __init__(self, remote_name, remote_host, my_name = None, host_type = nmb.TYPE_SERVER, sess_port = nmb.NETBIOS_SESSION_PORT):
        # The uid attribute will be set when the client calls the login() method
        self.__uid = 0
        self.__server_os = ''
        self.__server_lanman = ''
        self.__server_domain = ''
        self.__remote_name = string.upper(remote_name)
        
        if not my_name:
            my_name = socket.gethostname()
            i = string.find(my_name, '.')
            if i > -1:
                my_name = my_name[:i]
            
        self.__sess = nmb.NetBIOSSession(my_name, remote_name, remote_host, host_type, sess_port)
        # __neg_session will initialize the following attributes -- __can_read_raw, __can_write_raw,
        # __share_mode, __max_transmit_size, __max_raw_size, __enc_key, __session_key, __auth_mode,
        # __is_pathcaseless
        self.__neg_session()
        
        # If the following assertion fails, then mean that the encryption key is not sent when
        # encrypted authentication is required by the server.
        assert (self.__auth_mode == SMB.SECURITY_AUTH_PLAINTEXT) or (self.__auth_mode == SMB.SECURITY_AUTH_ENCRYPTED and self.__enc_key and len(self.__enc_key) >= 8)

        # Call login() without any authentication information to setup a session if the remote server
        # is in share mode.
        if self.__share_mode == SMB.SECURITY_SHARE_SHARE:
            self.login('', '')

    def __del__(self):
        if self.__uid > 0:
            try:
                self.__logoff()
            except:
                pass
            self.__uid = 0
        try:
            self.__sess.close()
        except:
            pass

    def __decode_smb(self, data):
        _, cmd, err_class, _, err_code, flags1, flags2, _, tid, pid, uid, mid, wcount = unpack('<4sBBBHBH12sHHHHB', data[:33])
        param_end = 33 + wcount * 2
        return cmd, err_class, err_code, flags1, flags2, tid, uid, mid, data[33:param_end], data[param_end + 2:]

    def __decode_trans(self, params, data):
        totparamcnt, totdatacnt, _, paramcnt, paramoffset, paramds, datacnt, dataoffset, datads, setupcnt = unpack('<HHHHHHHHHB', params[:19])
        if paramcnt + paramds < totparamcnt or datacnt + datads < totdatacnt:
            has_more = 1
        else:
            has_more = 0
        paramoffset = paramoffset - 55 - setupcnt * 2
        dataoffset = dataoffset - 55 - setupcnt * 2
        return has_more, params[20:20 + setupcnt * 2], data[paramoffset:paramoffset + paramcnt], data[dataoffset:dataoffset + datacnt]

    def __send_smb_packet(self, cmd, status, flags, flags2, tid, mid, params = '', data = ''):
        wordcount = len(params)
        assert wordcount & 0x1 == 0
        
        self.__sess.send_packet(pack('<4sBLBH12sHHHHB', '\xffSMB', cmd, status, flags, flags2, '\0' * 12, tid, os.getpid(), self.__uid, mid, wordcount / 2) + params + pack('<H', len(data)) + data)

    def __neg_session(self, timeout = None):
        self.__send_smb_packet(SMB.SMB_COM_NEGOTIATE, 0, 0, 0, 0, 0, data = '\x02NT LM 0.12\x00')
        
        while 1:
            data = self.__sess.recv_packet(timeout)
            if data:
                cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                if cmd == SMB.SMB_COM_NEGOTIATE:
                    if err_class == 0x00 and err_code == 0x00:
                        sel_dialect = unpack('<H', params[:2])
                        if sel_dialect == 0xffff:
                            raise UnsupportedFeature, "Remote server does not know NT LM 0.12. Please file a request for backward compatibility support."
                        
                        # NT LM 0.12 dialect selected
                        auth, self.__maxmpx, self.__maxvc, self.__max_transmit_size, self.__max_raw_size, self.__session_key, capability, _, keylength = unpack('<BHHllll10sB', params[2:34])

                        if capability & SMB.CAP_EXTENDED_SECURITY:
                            raise UnsupportedFeature, "This version of pysmb does not support extended security validation. Please file a request for it."

                        self.__auth_mode = auth & SMB.SECURITY_AUTH_MASK
                        self.__share_mode = auth & SMB.SECURITY_SHARE_MASK
                        rawmode = capability & SMB.CAP_RAW_MODE
                        self.__can_read_raw = rawmode
                        self.__can_write_raw = rawmode
                        self.__is_pathcaseless = flags1 & SMB.FLAGS1_PATHCASELESS

                        if keylength > 0 and len(d) >= keylength:
                            self.__enc_key = d[:keylength]
                        else:
                            self.__enc_key = ''
                        return 1
                    else:
                        raise SessionError, ( "Cannot neg dialect. (ErrClass: %d and ErrCode: %d)" % ( err_class, err_code ), err_class, err_code )

    def __logoff(self):
        self.__send_smb_packet(SMB.SMB_COM_LOGOFF, 0, 0, 0, 0, 0, '\xff\x00\x00\x00', '')
            
    def __connect_tree(self, path, service, password, timeout = None):
        if password:
            # Password is only encrypted if the server passed us an "encryption" during protocol dialect
            # negotiation and mxCrypto's DES module is loaded.
            if self.__enc_key and DES:
                password = self.__deshash(password)
            self.__send_smb_packet(SMB.SMB_COM_TREE_CONNECT_ANDX, 0, 0x08, 0, 0, 0, pack('<BBHHH', 0xff, 0, 0, 0, len(password)), password + string.upper(path) + '\0' + service + '\0')
        else:
            self.__send_smb_packet(SMB.SMB_COM_TREE_CONNECT_ANDX, 0, 0x08, 0, 0, 0, pack('<BBHHH', 0xff, 0, 0, 0, 1), '\0' + string.upper(path) + '\0' + service + '\0')

        while 1:
            data = self.__sess.recv_packet(timeout)
            if data:
                cmd, err_class, err_code, flags1, flags2, tid, _, mid, params, d = self.__decode_smb(data)
                if cmd == SMB.SMB_COM_TREE_CONNECT_ANDX:
                    if err_class == 0x00 and err_code == 0x00:
                        return tid
                    else:
                        raise SessionError, ( "Cannot connect tree. (ErrClass: %d and ErrCode: %d)" % ( err_class, err_code ), err_class, err_code )

    def __disconnect_tree(self, tid):
        self.__send_smb_packet(SMB.SMB_COM_TREE_DISCONNECT, 0, 0, 0, tid, 0, '', '')

    def __open_file(self, tid, filename, open_mode, access_mode, timeout = None):
        self.__send_smb_packet(SMB.SMB_COM_OPEN_ANDX, 0, 0x08, SMB.FLAGS2_LONG_FILENAME, tid, 0, pack('<BBHHHHHLHLLL', 0xff, 0, 0, 0, access_mode, ATTR_READONLY | ATTR_HIDDEN | ATTR_ARCHIVE, 0, 0, open_mode, 0, 0, 0), filename + '\x00')
        
        while 1:
            data = self.__sess.recv_packet(timeout)
            if data:
                cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                if cmd == SMB.SMB_COM_OPEN_ANDX:
                    if err_class == 0x00 and err_code == 0x00:
                        fid, attrib, lastwritetime, datasize, grantedaccess, filetype, devicestate, action, serverfid = unpack('<HHLLHHHHL', params[4:28])
                        return fid, attrib, lastwritetime, datasize, grantedaccess, filetype, devicestate, action, serverfid
                    else:
                        raise SessionError, ( 'Open file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        
    def __close_file(self, tid, fid):
        self.__send_smb_packet(SMB.SMB_COM_CLOSE, 0, 0, 0, tid, 0, pack('<HL', fid, 0), '')

    def __trans(self, tid, setup, name, param, data, timeout = None):
        data_len = len(data)
        name_len = len(name)
        param_len = len(param)
        setup_len = len(setup)

        assert setup_len & 0x01 == 0

        param_offset = name_len + setup_len + 63
        data_offset = param_offset + param_len
            
        self.__send_smb_packet(SMB.SMB_COM_TRANSACTION, 0, self.__is_pathcaseless, SMB.FLAGS2_LONG_FILENAME, tid, 0, pack('<HHHHBBHLHHHHHBB', param_len, data_len, 1024, 65504, 0, 0, 0, 0, 0, param_len, param_offset, data_len, data_offset, setup_len / 2, 0) + setup, name + param + data)

    def __trans2(self, tid, setup, name, param, data, timeout = None):
        data_len = len(data)
        name_len = len(name)
        param_len = len(param)
        setup_len = len(setup)

        assert setup_len & 0x01 == 0

        param_offset = name_len + setup_len + 63
        data_offset = param_offset + param_len
            
        self.__send_smb_packet(SMB.SMB_COM_TRANSACTION2, 0, self.__is_pathcaseless, SMB.FLAGS2_LONG_FILENAME, tid, 0, pack('<HHHHBBHLHHHHHBB', param_len, data_len, 1024, self.__max_transmit_size, 0, 0, 0, 0, 0, param_len, param_offset, data_len, data_offset, setup_len / 2, 0) + setup, name  + param + data)

    def __query_file_info(self, tid, fid, timeout = None):
        self.__trans2(tid, '\x07\x00', '\x00', pack('<HH', fid, 0x107), '', timeout)

        while 1:
            data = self.__sess.recv_packet(timeout)
            if data:
                cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                if cmd == SMB.SMB_COM_TRANSACTION2:
                    if err_class == 0x00 and err_code == 0x00:
                        if flags2 & 0x40:
                            f1, f2 = unpack('<LL', d[47:55])
                        else:
                            f1, f2 = unpack('<LL', d[45:53])
                        return (f2 & 0xffffffffL) << 32 | f1
                    else:
                        raise SessionError, ( 'File information query failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

    def __nonraw_retr_file(self, tid, fid, offset, datasize, callback, timeout = None):
        max_buf_size = self.__max_transmit_size & ~0x3ff  # Read in multiple KB blocks
        read_offset = offset
        while read_offset < datasize:
            self.__send_smb_packet(SMB.SMB_COM_READ_ANDX, 0, 0, 0, tid, 0, pack('<BBHHLHHLH', 0xff, 0, 0, fid, read_offset, max_buf_size, max_buf_size, 0, 0), '')
            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_READ_ANDX:
                        if err_class == 0x00 and err_code == 0x00:
                            offset = unpack('<H', params[2:4])[0]
                            data_len, dataoffset = unpack('<HH', params[10+offset:14+offset])
                            if data_len == len(d):
                                callback(d)
                            else:
                                callback(d[dataoffset - 59:dataoffset - 59 + data_len])
                                read_offset = read_offset + data_len
                            break
                        else:
                            raise SessionError, ( 'Non-raw retr file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

    def __raw_retr_file(self, tid, fid, offset, datasize, callback, timeout = None):
        max_buf_size = self.__max_transmit_size & ~0x3ff  # Write in multiple KB blocks
        read_offset = offset
        while read_offset < datasize:
            self.__send_smb_packet(SMB.SMB_COM_READ_RAW, 0, 0, 0, tid, 0, pack('<HLHHLH', fid, read_offset, 0xffff, 0, 0, 0), '')
            data = self.__sess.recv_packet(timeout)
            if data:
                callback(data)
                read_offset = read_offset + len(data)
            else:
                # No data returned. Need to send SMB_COM_READ_ANDX to find out what is the error.
                self.__send_smb_packet(SMB.SMB_COM_READ_ANDX, 0, 0, 0, tid, 0, pack('<BBHHLHHLH', 0xff, 0, 0, fid, read_offset, max_buf_size, max_buf_size, 0, 0), '')
                while 1:
                    data = self.__sess.recv_packet(timeout)
                    if data:
                        cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                        if cmd == SMB.SMB_COM_READ_ANDX:
                            if err_class == 0x00 and err_code == 0x00:
                                offset = unpack('<H', params[2:4])[0]
                                data_len, dataoffset = unpack('<HH', params[10+offset:14+offset])
                                if data_len == 0:
                                    # Premature EOF!
                                    return
                                # By right we should not have data returned in the reply.
                                elif data_len == len(d):
                                    callback(d)
                                else:
                                    callback(d[dataoffset - 59:dataoffset - 59 + data_len])
                                read_offset = read_offset + data_len
                                break
                            else:
                                raise SessionError, ( 'Raw retr file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

    def __nonraw_stor_file(self, tid, fid, offset, datasize, callback, timeout = None):
        max_buf_size = self.__max_transmit_size & ~0x3ff  # Write in multiple KB blocks
        write_offset = offset
        while 1:
            data = callback(max_buf_size)
            if not data:
                break
            
            self.__send_smb_packet(SMB.SMB_COM_WRITE_ANDX, 0, 0, 0, tid, 0, pack('<BBHHLLHHHHH', 0xff, 0, 0, fid, write_offset, 0, 0, 0, 0, len(data), 59), data)
            
            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_WRITE_ANDX:
                        if err_class == 0x00 and err_code == 0x00:
                            offset = unpack('<H', params[2:4])[0]
                            write_offset = write_offset + unpack('<H', params[4+offset:6+offset])[0]
                            break
                        else:
                            raise SessionError, ( 'Non-raw store file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

    def __raw_stor_file(self, tid, fid, offset, datasize, callback, timeout = None):
        write_offset = offset
        while 1:
            read_data = callback(65535)
            if not read_data:
                break

            read_len = len(read_data)
            self.__send_smb_packet(SMB.SMB_COM_WRITE_RAW, 0, 0, 0, tid, 0, pack('<HHHLLHLHH', fid, read_len, 0, write_offset, 0, 0, 0, 0, 59), '')
            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_WRITE_RAW:
                        if err_class == 0x00 and err_code == 0x00:
                            self.__sess.send_packet(read_data)
                            write_offset = write_offset + read_len
                            break
                        else:
                            raise SessionError, ( 'Raw store file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

        # We need to close fid to check whether the last raw packet is written successfully
        self.__send_smb_packet(SMB.SMB_COM_CLOSE, 0, 0, 0, tid, 0, pack('<HL', fid, 0), '')
        while 1:
            data = self.__sess.recv_packet(timeout)
            if data:
                cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                if cmd == SMB.SMB_COM_CLOSE:
                    if err_class == 0x00 and err_code == 0x00:
                        return
                    else:
                        raise SessionError, ( 'Raw store file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

    def __browse_servers(self, server_flags, container_type, domain, timeout = None):
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\IPC$', SERVICE_ANY, timeout)

        buf = StringIO()
        try:
            if server_flags & 0x80000000:
                self.__trans(tid, '', '\\PIPE\\LANMAN\x00', '\x68\x00WrLehDz\x00' + 'B16BBDz\x00\x01\x00\xff\xff\x00\x00\x00\x80', '', timeout)
            else:
                self.__trans(tid, '', '\\PIPE\\LANMAN\x00', '\x68\x00WrLehDz\x00' + 'B16BBDz\x00\x01\x00\xff\xff' + pack('<l', server_flags)  + domain + '\x00', '', timeout)
                
            servers = [ ]
            entry_count = 0
            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_TRANSACTION:
                        if err_class == 0x00 and err_code == 0x00:
                            has_more, _, transparam, transdata = self.__decode_trans(params, d)
                            if not entry_count:
                                status, convert, entry_count, avail_entry = unpack('<HHHH', transparam[:8])
                                if status and status != 234:  # status 234 means have more data
                                    raise SessionError, ( 'Browse domains failed. (ErrClass: %d and ErrCode: %d)' % ( 0x80, status ), 0x80, status )
                            buf.write(transdata)

                            if not has_more:
                                server_data = buf.getvalue()

                                for i in range(0, entry_count):
                                    server, _, server_type, comment_offset = unpack('<16s2sll', server_data[i * 26:i * 26 + 26])
                                    idx = string.find(server, '\0')
                                    idx2 = string.find(server_data, '\0', comment_offset)
                                    if idx < 0:
                                        server = server[:idx]
                                    servers.append(container_type(server, server_type, server_data[comment_offset:idx2]))
                                return servers
                        else:
                            raise SessionError, ( 'Browse domains failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            buf.close()
            self.__disconnect_tree(tid)            
        

    def __expand_des_key(self, key):
        # Expand the key from a 7-byte password key into a 8-byte DES key
        s = chr(((ord(key[0]) >> 1) & 0x7f) << 1)
        s = s + chr(((ord(key[0]) & 0x01) << 6 | ((ord(key[1]) >> 2) & 0x3f)) << 1)
        s = s + chr(((ord(key[1]) & 0x03) << 5 | ((ord(key[2]) >> 3) & 0x1f)) << 1)
        s = s + chr(((ord(key[2]) & 0x07) << 4 | ((ord(key[3]) >> 4) & 0x0f)) << 1)
        s = s + chr(((ord(key[3]) & 0x0f) << 3 | ((ord(key[4]) >> 5) & 0x07)) << 1)
        s = s + chr(((ord(key[4]) & 0x1f) << 2 | ((ord(key[5]) >> 6) & 0x03)) << 1)
        s = s + chr(((ord(key[5]) & 0x3f) << 1 | ((ord(key[6]) >> 7) & 0x01)) << 1)
        s = s + chr((ord(key[6]) & 0x7f) << 1)
        return s

    def __deshash(self, password):
        # This is done according to Samba's encryption specification (docs/html/ENCRYPTION.html)
        if len(password) > 14:
            p14 = string.upper(password[:14])
        else:
            p14 = string.upper(password) + '\0' * (14 - len(password))
        if amk_crypto:
            p21 = DES.new(self.__expand_des_key(p14[:7])).encrypt('\x4b\x47\x53\x21\x40\x23\x24\x25') + DES.new(self.__expand_des_key(p14[7:])).encrypt('\x4b\x47\x53\x21\x40\x23\x24\x25') + '\0' * 5
            return DES.new(self.__expand_des_key(p21[:7])).encrypt(self.__enc_key) + DES.new(self.__expand_des_key(p21[7:14])).encrypt(self.__enc_key) + DES.new(self.__expand_des_key(p21[14:])).encrypt(self.__enc_key)
        else:
            p21 = DES(self.__expand_des_key(p14[:7])).encrypt('\x4b\x47\x53\x21\x40\x23\x24\x25') + DES(self.__expand_des_key(p14[7:])).encrypt('\x4b\x47\x53\x21\x40\x23\x24\x25') + '\0' * 5
            return DES(self.__expand_des_key(p21[:7])).encrypt(self.__enc_key) + DES(self.__expand_des_key(p21[7:14])).encrypt(self.__enc_key) + DES(self.__expand_des_key(p21[14:])).encrypt(self.__enc_key)

    def get_server_domain(self):
        return self.__server_domain

    def get_server_os(self):
        return self.__server_os

    def get_server_lanman(self):
        return self.__server_lanman

    def is_login_required(self):
        # Login is required if share mode is user. Otherwise only public services or services in share mode
        # are allowed.
        return self.__share_mode == SMB.SECURITY_SHARE_USER

    def login(self, name, password, domain = '', timeout = None):
        # Password is only encrypted if the server passed us an "encryption" during protocol dialect
        # negotiation and mxCrypto's DES module is loaded.
        if self.__enc_key and DES:
            password = self.__deshash(password)

        self.__send_smb_packet(SMB.SMB_COM_SESSION_SETUP_ANDX, 0, 0, 0, 0, 0, pack('<ccHHHHLHHLL', '\xff', '\0', 0, 65535, 2, os.getpid(), self.__session_key, len(password), 0, 0, SMB.CAP_RAW_MODE), password + name + '\0' + domain + '\0' + os.name + '\0' + 'pysmb\0')

        while 1:
            data = self.__sess.recv_packet(timeout)
            if data:
                cmd, err_class, err_code, flags1, flags2, _, uid, mid, params, d = self.__decode_smb(data)
                if cmd == SMB.SMB_COM_SESSION_SETUP_ANDX:
                    if err_class == 0x00 and err_code == 0x00:
                        # We will need to use this uid field for all future requests/responses
                        self.__uid = uid
                        security_bloblen = unpack('<H', params[4:6])[0]
                        if flags2 & SMB.FLAGS2_UNICODE:
                            offset = security_bloblen
                            if offset & 0x01:
                                offset = offset + 1
                            # Skip server OS
                            end = offset
                            while ord(d[end]) or ord(d[end + 1]):
                                end = end + 2
                            try:
                                self.__server_os = unicode(d[offset:end], 'utf_16_le')
                            except NameError:
                                self.__server_os = d[offset:end]
                            end = end + 2
                            offset = end
                            # Skip server lanman
                            while ord(d[end]) or ord(d[end + 1]):
                                end = end + 2
                            try:
                                self.__server_lanman = unicode(d[offset:end], 'utf_16_le')
                            except NameError:
                                self.__server_lanman = d[offset:end]
                            end = end + 2
                            offset = end
                            while ord(d[end]) or ord(d[end + 1]):
                                end = end + 2
                            try:
                                self.__server_domain = unicode(d[offset:end], 'utf_16_le')
                            except NameError:
                                self.__server_domain = d[offset:end]
                        else:
                            idx1 = string.find(d, '\0', security_bloblen)
                            if idx1 != -1:
                                self.__server_os = d[security_bloblen:idx1]
                                idx2 = string.find(d, '\0', idx1 + 1)
                                if idx2 != -1:
                                    self.__server_lanman = d[idx1 + 1:idx2]
                                    idx3 = string.find(d, '\0', idx2 + 1)
                                    if idx3 != -1:
                                        self.__server_domain = d[idx2 + 1:idx3]

                        return 1
                    else:
                        raise SessionError, ( 'Authentication failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )

    def list_shared(self, timeout = None):
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\IPC$', SERVICE_ANY, timeout)

        buf = StringIO()
        try:
            self.__trans(tid, '', '\\PIPE\\LANMAN\0', '\x00\x00WrLeh\0B13BWz\0\x01\x00\xe0\xff', '')

            numentries = 0
            share_list = [ ]
            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_TRANSACTION:
                        if err_class == 0x00 and err_code == 0x00:
                            has_more, _, transparam, transdata = self.__decode_trans(params, d)
                            if not numentries:
                                numentries = unpack('<H', transparam[4:6])[0]
                            buf.write(transdata)

                            if not has_more:
                                share_data = buf.getvalue()
                                offset = 0
                                for i in range(0, numentries):
                                    name = share_data[offset:string.find(share_data, '\0', offset)]
                                    type, commentoffset = unpack('<HH', share_data[offset + 14:offset + 18])
                                    comment = share_data[commentoffset:string.find(transdata, '\0', commentoffset)]
                                    offset = offset + 20
                                    share_list.append(SharedDevice(name, type, comment))
                                return share_list
                        else:
                            raise SessionError, ( 'List directory failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            buf.close()
            self.__disconnect_tree(tid)

    def list_path(self, service, path = '*', password = None, timeout = None):
        path = string.replace(path, '/', '\\')

        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            self.__trans2(tid, '\x01\x00', '\x00', '\x16\x00\x00\x02\x06\x00\x04\x01\x00\x00\x00\x00' + path + '\x00', '')

            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_TRANSACTION2:
                        if err_class == 0x00 and err_code == 0x00:
                            has_more, _, transparam, transdata = self.__decode_trans(params, d)
                            sid, searchcnt, eos, erroffset, lastnameoffset = unpack('<HHHHH', transparam)
                            files = [ ]
                            offset = 0
                            data_len = len(transdata)
                            while offset < data_len:
                                nextentry, fileindex, lowct, highct, lowat, highat, lowmt, highmt, lowcht, hightcht, loweof, higheof, lowsz, highsz, attrib, longnamelen, easz, shortnamelen = unpack('<lL12LLlLB', transdata[offset:offset + 69])
                                files.append(SharedFile(highct << 32 | lowct, highat << 32 | lowat, highmt << 32 | lowmt, higheof << 32 | loweof, highsz << 32 | lowsz, attrib, transdata[offset + 70:offset + 70 + shortnamelen], transdata[offset + 94:offset + 94 + longnamelen]))
                                offset = offset + nextentry
                                if not nextentry:
                                    break
                            return files
                        else:
                            raise SessionError, ( 'List path failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            self.__disconnect_tree(tid)

    def retr_file(self, service, filename, callback, mode = SMB_O_OPEN, offset = 0, password = None, timeout = None):
        filename = string.replace(filename, '/', '\\')

        fid = -1
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            fid, attrib, lastwritetime, datasize, grantedaccess, filetype, devicestate, action, serverfid = self.__open_file(tid, filename, mode, SMB_ACCESS_READ | SMB_SHARE_DENY_WRITE)

            #if not datasize:
            datasize = self.__query_file_info(tid, fid)

            if self.__can_read_raw:
                self.__raw_retr_file(tid, fid, offset, datasize, callback)
            else:
                self.__nonraw_retr_file(tid, fid, offset, datasize, callback, timeout)
        finally:
            if fid >= 0:
                self.__close_file(tid, fid)
            self.__disconnect_tree(tid)

    def stor_file(self, service, filename, callback, mode = SMB_O_CREAT | SMB_O_TRUNC, offset = 0, password = None, timeout = None):
        filename = string.replace(filename, '/', '\\')

        fid = -1
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            fid, attrib, lastwritetime, datasize, grantedaccess, filetype, devicestate, action, serverfid = self.__open_file(tid, filename, mode, SMB_ACCESS_WRITE | SMB_SHARE_DENY_WRITE)

            # If the max_transmit buffer size is more than 16KB, upload process using non-raw mode is actually
            # faster than using raw-mode.
            if self.__max_transmit_size < 16384 and self.__can_write_raw:
                # Once the __raw_stor_file returns, fid is already closed
                self.__raw_stor_file(tid, fid, offset, datasize, callback, timeout)
                fid = -1
            else:
                self.__nonraw_stor_file(tid, fid, offset, datasize, callback, timeout)
        finally:
            if fid >= 0:
                self.__close_file(tid, fid)
            self.__disconnect_tree(tid)

    def copy(self, src_service, src_path, dest_service, dest_path, callback = None, write_mode = SMB_O_CREAT | SMB_O_TRUNC, src_password = None, dest_password = None, timeout = None):
        dest_path = string.replace(dest_path, '/', '\\')
        src_path = string.replace(src_path, '/', '\\')
        src_tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + src_service, SERVICE_ANY, src_password, timeout)

        dest_tid = -1
        try:
            if src_service == dest_service:
                dest_tid = src_tid
            else:
                dest_tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + dest_service, SERVICE_ANY, dest_password, timeout)
            
            dest_fid = self.__open_file(dest_tid, dest_path, write_mode, SMB_ACCESS_WRITE | SMB_SHARE_DENY_WRITE)[0]
            src_fid, _, _, src_datasize, _, _, _, _, _ = self.__open_file(src_tid, src_path, SMB_O_OPEN, SMB_ACCESS_READ | SMB_SHARE_DENY_WRITE)

            if callback:
                callback(0, src_datasize)

            max_buf_size = (self.__max_transmit_size >> 10) << 10
            read_offset = 0
            write_offset = 0
            while read_offset < src_datasize:
                self.__send_smb_packet(SMB.SMB_COM_READ_ANDX, 0, 0, 0, src_tid, 0, pack('<BBHHLHHLH', 0xff, 0, 0, src_fid, read_offset, max_buf_size, max_buf_size, 0, 0), '')
                while 1:
                    data = self.__sess.recv_packet(timeout)
                    if data:
                        cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                        if cmd == SMB.SMB_COM_READ_ANDX:
                            if err_class == 0x00 and err_code == 0x00:
                                offset = unpack('<H', params[2:4])[0]
                                data_len, dataoffset = unpack('<HH', params[10+offset:14+offset])
                                if data_len == len(d):
                                    self.__send_smb_packet(SMB.SMB_COM_WRITE_ANDX, 0, 0, 0, dest_tid, 0, pack('<BBHHLLHHHHH', 0xff, 0, 0, dest_fid, write_offset, 0, 0, 0, 0, data_len, 59), d)
                                else:
                                    self.__send_smb_packet(SMB.SMB_COM_WRITE_ANDX, 0, 0, 0, dest_tid, 0, pack('<BBHHLLHHHHH', 0xff, 0, 0, dest_fid, write_offset, 0, 0, 0, 0, data_len, 59), d[dataoffset - 59:dataoffset - 59 + data_len])
                                while 1:
                                    data = self.__sess.recv_packet(timeout)
                                    if data:
                                        cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                                        if cmd == SMB.SMB_COM_WRITE_ANDX:
                                            if err_class == 0x00 and err_code == 0x00:
                                                offset = unpack('<H', params[2:4])[0]
                                                write_offset = write_offset + unpack('<H', params[4+offset:6+offset])[0]
                                                break
                                            else:
                                                raise SessionError, ( 'Copy (write) failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
                                read_offset = read_offset + data_len
                                if callback:
                                    callback(read_offset, src_datasize)
                                break
                            else:
                                raise SessionError, ( 'Copy (read) failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
                
        finally:
            self.__disconnect_tree(src_tid)
            if dest_tid > -1 and src_service != dest_service:
                self.__disconnect_tree(dest_tid)

    def check_dir(self, service, path, password = None, timeout = None):
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            self.__send_smb_packet(SMB.SMB_COM_CHECK_DIR, 0, 0x08, 0, tid, 0, '', '\x04' + path + '\x00')

            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_CHECK_DIR:
                        if err_class == 0x00 and err_code == 0x00:
                            return
                        else:
                            raise SessionError, ( 'Check directory failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            self.__disconnect_tree(tid)

    def remove(self, service, path, password = None, timeout = None):
        # Perform a list to ensure the path exists
        self.list_path(service, path, password, timeout)

        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            self.__send_smb_packet(SMB.SMB_COM_DELETE, 0, 0x08, 0, tid, 0, pack('<H', ATTR_HIDDEN | ATTR_SYSTEM | ATTR_ARCHIVE), '\x04' + path + '\x00')

            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_DELETE:
                        if err_class == 0x00 and err_code == 0x00:
                            return
                        else:
                            raise SessionError, ( 'Delete file failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            self.__disconnect_tree(tid)

    def rmdir(self, service, path, password = None, timeout = None):
        # Check that the directory exists
        self.check_dir(service, path, password, timeout)

        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            self.__send_smb_packet(SMB.SMB_COM_DELETE_DIR, 0, 0x08, 0, tid, 0, '', '\x04' + path + '\x00')

            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_DELETE_DIR:
                        if err_class == 0x00 and err_code == 0x00:
                            return
                        else:
                            raise SessionError, ( 'Delete directory failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            self.__disconnect_tree(tid)

    def mkdir(self, service, path, password = None, timeout = None):
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            self.__send_smb_packet(SMB.SMB_COM_CREATE_DIR, 0, 0x08, 0, tid, 0, '', '\x04' + path + '\x00')

            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_CREATE_DIR:
                        if err_class == 0x00 and err_code == 0x00:
                            return
                        else:
                            raise SessionError, ( 'Create directory failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            self.__disconnect_tree(tid)

    def rename(self, service, old_path, new_path, password = None, timeout = None):
        tid = self.__connect_tree('\\\\' + self.__remote_name + '\\' + service, SERVICE_ANY, password, timeout)
        try:
            self.__send_smb_packet(SMB.SMB_COM_RENAME, 0, 0x08, 0, tid, 0, pack('<H', ATTR_SYSTEM | ATTR_HIDDEN | ATTR_DIRECTORY), '\x04' + old_path + '\x00\x04' + new_path + '\x00')

            while 1:
                data = self.__sess.recv_packet(timeout)
                if data:
                    cmd, err_class, err_code, flags1, flags2, _, _, mid, params, d = self.__decode_smb(data)
                    if cmd == SMB.SMB_COM_RENAME:
                        if err_class == 0x00 and err_code == 0x00:
                            return 
                        else:
                            raise SessionError, ( 'Rename failed. (ErrClass: %d and ErrCode: %d)' % ( err_class, err_code ), err_class, err_code )
        finally:
            self.__disconnect_tree(tid)

    def browse_domains(self, timeout = None):
        return self.__browse_servers(SV_TYPE_DOMAIN_ENUM, SMBDomain, '')

    def browse_servers_for_domain(self, domain = None, timeout = None):
        if not domain:
            domain = self.__server_domain

        return self.__browse_servers(SV_TYPE_SERVER | SV_TYPE_PRINTQ_SERVER | SV_TYPE_WFW | SV_TYPE_NT, SMBMachine, domain)



ERRDOS = { 1: 'Invalid function',
           2: 'File not found',
           3: 'Invalid directory',
           4: 'Too many open files',
           5: 'Access denied',
           6: 'Invalid file handle. Please file a bug report.',
           7: 'Memory control blocks destroyed',
           8: 'Out of memory',
           9: 'Invalid memory block address',
           10: 'Invalid environment',
           11: 'Invalid format',
           12: 'Invalid open mode',
           13: 'Invalid data',
           15: 'Invalid drive',
           16: 'Attempt to remove server\'s current directory',
           17: 'Not the same device',
           18: 'No files found',
           32: 'Sharing mode conflicts detected',
           33: 'Lock request conflicts detected',
           80: 'File already exists'
           }

ERRSRV = { 1: 'Non-specific error',
           2: 'Bad password',
           4: 'Access denied',
           5: 'Invalid tid. Please file a bug report.',
           6: 'Invalid network name',
           7: 'Invalid device',
           49: 'Print queue full',
           50: 'Print queue full',
           51: 'EOF on print queue dump',
           52: 'Invalid print file handle',
           64: 'Command not recognized. Please file a bug report.',
           65: 'Internal server error',
           67: 'Invalid path',
           69: 'Invalid access permissions',
           71: 'Invalid attribute mode',
           81: 'Server is paused',
           82: 'Not receiving messages',
           83: 'No room to buffer messages',
           87: 'Too many remote user names',
           88: 'Operation timeout',
           89: 'Out of resources',
           91: 'Invalid user handle. Please file a bug report.',
           250: 'Temporarily unable to support raw mode for transfer',
           251: 'Temporarily unable to support raw mode for transfer',
           252: 'Continue in MPX mode',
           65535: 'Unsupported function'
           }

ERRHRD = { 19: 'Media is write-protected',
           20: 'Unknown unit',
           21: 'Drive not ready',
           22: 'Unknown command',
           23: 'CRC error',
           24: 'Bad request',
           25: 'Seek error',
           26: 'Unknown media type',
           27: 'Sector not found',
           28: 'Printer out of paper',
           29: 'Write fault',
           30: 'Read fault',
           31: 'General failure',
           32: 'Open conflicts with an existing open',
           33: 'Invalid lock request',
           34: 'Wrong disk in drive',
           35: 'FCBs not available',
           36: 'Sharing buffer exceeded'
           }

# This is not a standard error class for SMB
ERRBROWSE = { 2114: 'RAP service on server not running',
              2141: 'Server not configured for transaction. IPC$ not shared',
              6118: 'Cannot enumerate servers. Use another browse server'
              }
