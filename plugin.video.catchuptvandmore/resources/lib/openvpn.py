# /*
# *
# * OpenVPN for Kodi.
# *
# * Copyright (C) 2015 Brian Hornsby
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *
# */

from __future__ import print_function

import os
import socket
import subprocess
import time
from builtins import object

from codequick import Script


class OpenVPNManagementInterface(object):
    def __init__(self, ip, port, openvpn=None):
        self.openvpn = openvpn
        self.ip = ip
        self.port = port
        Script.log('[OpenVPNManagementInterface] IP: [%s]' % ip)
        Script.log('[OpenVPNManagementInterface] Port: [%s]' % port)
        self.buf = b''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.ip, self.port))

    def disconnect(self):
        self.sock.close()

    def send(self, msg):
        Script.log('[OpenVPNManagementInterface] Sending: [%s]' % msg)
        self.sock.send(msg)

    def receive(self):
        buf = b''
        data = b''
        while data != b'\n':
            data = self.sock.recv(1)
            buf += data
        if len(buf) > 0:
            buf += b'\n'
        return buf


def is_running(ip, port):
    interface = OpenVPNManagementInterface(ip, port)
    try:
        interface.connect()
    except socket.error:
        Script.log('[OpenVPNManagementInterface] is_running? -> False')
        return False
    Script.log('[OpenVPNManagementInterface] is_running? -> True')
    return True


def disconnect(ip, port):
    interface = OpenVPNManagementInterface(ip, port)
    try:
        interface.connect()
        interface.send(b'signal SIGTERM\n')
        interface.disconnect()
    except socket.error:
        Script.log('[OpenVPNManagementInterface] Unable to disconnect OpenVPN', lvl=Script.ERROR)


class OpenVPN(object):
    def __init__(self,
                 openvpn,
                 ovpnconfig,
                 ip='127.0.0.1',
                 port=1337,
                 sudo=False,
                 sudopwd=None,
                 args=None,
                 timeout=1):
        self.openvpn = openvpn
        self.ovpnconfig = ovpnconfig
        self.ip = ip
        self.port = int(port)
        self.args = args
        self.timeout = timeout
        self.sudo = sudo
        self.sudopwd = sudopwd

        Script.log('OpenVPN: [%s]' % self.openvpn)
        Script.log('OpenVPN Configuration: [%s]' % self.ovpnconfig)
        Script.log('OpenVPN Management IP: [%s]' % self.ip)
        Script.log('OpenVPN Management Port: [%d]' % self.port)
        if self.args is not None:
            Script.log('Additional Arguments: [%s]' % self.args)

        if self.openvpn is None or not os.path.exists(
                self.openvpn) or not os.path.isfile(self.openvpn):
            raise RuntimeError('OpenVPN: ERROR: Specified OpenVPN does not exist')

        if self.ovpnconfig is None or not os.path.exists(
                self.ovpnconfig) or not os.path.isfile(self.ovpnconfig):
            raise RuntimeError(
                'OpenVPN: ERROR: Specified OpenVPN configuration file does not exist'
            )

        self.interface = None
        self.workdir = os.path.dirname(ovpnconfig)
        self.logfile = os.path.join(self.workdir, 'openvpn.log')

    def connect_to_interface(self):
        if self.interface is None:
            self.interface = OpenVPNManagementInterface(self.ip, self.port, self)
        try:
            self.interface.connect()
        except socket.error as exception:
            Script.log(exception)
            self.interface = None
            return False
        return True

    def disconnect(self):
        self.connect_to_interface()
        Script.log('Disconnecting OpenVPN')
        self.interface.send(b'signal SIGTERM\n')
        time.sleep(self.timeout)
        self.interface.disconnect()
        self.interface = None
        Script.log('Disconnect OpenVPN successful')

    def connect(self):
        Script.log('Connecting OpenVPN')

        isrunning = self.connect_to_interface()
        if isrunning:
            Script.log('OpenVPN is already running')
            self.interface.disconnect()
            raise RuntimeError('OpenVPN is already running')

        cmdline = '\'%s\' --cd \'%s\' --daemon --management %s %d --config \'%s\' --log \'%s\'' % (
            self.openvpn, self.workdir, self.ip, self.port, self.ovpnconfig,
            self.logfile)
        if self.args is not None:
            cmdline = '%s %s' % (cmdline, self.args)

        if self.sudo:
            Script.log('Using sudo')
            if self.sudopwd:
                cmdline = 'echo \'%s\' | sudo -S %s' % (self.sudopwd, cmdline)
            else:
                cmdline = 'sudo %s' % (cmdline)
        Script.log('Command line: [%s]' % cmdline)

        self.process = subprocess.Popen(cmdline,
                                        cwd=self.workdir,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        time.sleep(self.timeout)
        if not self.connect_to_interface():
            Script.log('Connect OpenVPN failed')
            raise RuntimeError('Unable to connect to OpenVPN management interface')

        Script.log('Connect OpenVPN successful')
