#
# Copyright (C) 2014 Datho Digital Inc., All rights reserved
#
# Permission must be obtained from the copyright holder for any commercial use, distribution or modification of this software.
#

import subprocess
import os
import traceback
import requests
from lib import vpnmanager
import xbmc
from threading import Thread
from Queue import Queue

import gui
import config
from utils import Logger, GetPublicNetworkInformation
import common
from config import __language__
from vpnmanager import VPNServerManager


class OpenVPNExeNotFoundException(Exception):
    pass

class AccessDeniedException(Exception):
    pass




class VPNConnector:

    def __init__(self, countryName, cityName, serverAddress, custom):
        self._timeout = config.getTimeout()
        self._port = config.getPort()
        self._countryName = countryName
        self._cityName = cityName
        self._serverAddress = serverAddress
        self._actionNotification = ActionNotification()
        self._actionNotification.start()
        self._hardcodedServerAddress = False
        self._isCustom = custom



        if self._usingDathoFreeServers():
            gui.DialogOK("Using datho free servers", '', '')


    def _usingDathoFreeServers(self):
        return config.isVPNCustom() is False and vpnmanager.VPNServerManager.getInstance().usingDathoVPNServers()

    def kill(self, showBusy = False):
        if showBusy:
            self._allowActionKill()
        busy = None
        if showBusy:
            busy = gui.ShowBusy()

        ret = self._kill()

        if busy:
            busy.close()
        return ret

    def _allowActionConnect(self, extra = ''):
        self._allowAction("connecting", extra)
    def _allowActionConnected(self, extra = ''):
        self._allowAction("connected", extra)
    def _allowActionKill(self, extra = ''):
        self._allowAction("kill", extra)
    def _allowActionError(self, extra = ''):
        self._allowAction("error", extra)

    def _getUsername(self):
        user = config.getUsername()
        Logger.log("Using Datho free servers:%s" % self._usingDathoFreeServers(), Logger.LOG_DEBUG)
        if VPNServerManager.getInstance().usingDathoVPNServers() or config.isVPNCustom():
            return user
        return user + config.getPaidServersPostFix()

    def _allowAction(self, action, extra = ''):
        Logger.log("allowAction %s" % action, Logger.LOG_DEBUG)
        user = self._getUsername()
        pwd  = config.getPassword()

        data = {"username" : user, "apiKey" : pwd, "action" : action, "country" : self._countryName, "city" : self._cityName, "server" : self._serverAddress, "extra" : extra, "os" : config.getOS()}
        self._actionNotification.push(data)


    def connectToVPNServer(self):
        Logger.log("Trying to connect to server %s:%s" % (self._countryName, self._serverAddress), Logger.LOG_ERROR)

        self._allowActionConnect()

        busy = gui.ShowBusy()

        if self._shouldKillBeforeConnect():
            killSuccess = self.kill()
            # If kill was not successfully executed, it should not try to connect
            if not killSuccess:
                return
            Logger.log("Waiting openvpn to do the clean properly ...")

        authPath = self._writeAuthentication()
        if not authPath:
            return

        self._openVPNConfigPath = self._writeOpenVPNConfiguration(authPath)
        if not self._openVPNConfigPath:
            return
        return self._doConnect(busy)

    # This is the file path where the configuration file OpenVPN needs (for Win, Linux, Android, etc)
    def _getOpenVPNConfigPath(self):
        return config.getOpenVPNRealConfigFilePath()

    def _doConnect(self, busy = None):
        try:
            response = self._connect()
            self._checkStatus(response)
            if busy:
                busy.close()
        except OpenVPNExeNotFoundException:
            if busy:
                busy.close()

    def _kill(self):
        raise NotImplementedError()

    def _connect(self):
        raise NotImplementedError("")

    def _isEnabled(self, response):
        raise NotImplementedError("")

    def _shouldKillBeforeConnect(self):
        raise NotImplementedError("")

    def _connectionOkMessage(self):
        networkInfo = GetPublicNetworkInformation()
        if networkInfo:
            ipAddress, country, city = networkInfo
            return __language__(30024), __language__(30025) % ipAddress, "%s, %s" % (city.title(), country.title())
        return __language__(30026) % self._countryName, '', ''

    def _connectionFailedMessage(self):
        return __language__(30027) % self._countryName, __language__(30028), __language__(30005)


    def _checkStatus(self, response):
        if response:
            if self._isEnabled(response):
                gui.DialogOK( *self._connectionOkMessage())
            else:
                title, msg1, msg2 = self._connectionFailedMessage()
                self._allowActionKill()
                gui.DialogOK(title, msg1, msg2)

    def _writeAuthentication(self):
        authPath = os.path.join(config.PROFILE, 'temp')
        common.CheckUsername()

        user = self._getUsername()
        pwd  = config.getPassword()

        if user == '' or pwd == '':
            gui.DialogOK(__language__(30029), __language__(30030), '')
            return None

        f = open(authPath, mode='w')
        data = [user, '\r\n', pwd, '\r\n']
        f.writelines(data)
        f.close()

        return authPath


    def _writeOpenVPNConfiguration(self, authPath):
        crl  = ''
        if self._isCustom:
            openVpnConfigFilePath  = config.getOpenVPNCustomTemplateConfigFilePath()
            if not os.path.exists(openVpnConfigFilePath):
                gui.DialogOK(__language__(30049), __language__(30050), __language__(30005) )
                return None

            cert    = config.getCustomCertFilePath()
            if not os.path.exists(cert):
                gui.DialogOK(__language__(30051), __language__(30052), __language__(30005) )
                return None

            crl = config.getCustomCrlFilePath()

        else:
            openVpnConfigFilePath  = config.getOpenVPNTemplateConfigFilePath()
            cert    = config.getCertFilePath()

            if self._usingDathoFreeServers():
                cert = config.getDathoCertFilePath()
                Logger.log("Using datho cert:%s" % cert, Logger.LOG_DEBUG)

        file    = open(openVpnConfigFilePath, mode='r')
        content = file.read()
        file.close()

        authPath = authPath.replace('\\', '/')
        cert     = cert.replace('\\', '/')
        crl     = crl.replace('\\', '/')

        print "SERVER ADDRESS:", self._serverAddress

        content = content.replace('#SERVER#',               self._serverAddress)
        content = content.replace('#PORT#',                 self._port)
        content = content.replace('#CERTIFICATE#',    '"' + cert     + '"')
        content = content.replace('#AUTHENTICATION#', '"' + authPath + '"')
        content = content.replace('#CRL#', '"' + crl + '"')


        # Adding the log will disable the output to be written to stdout, so Windows will fail reading the status
        # so in case it is needed this should be added on the modifyOpenVPNConfigContent for the correspondent OS
        #content += "\r\nlog " +  "openvpn1.log"

        # The goal is to modify the OpenVPN Config for adding config options that may be needed for some OSs (like Linux Ubuntu)
        content = self._modifyOpenVPNConfigContent(content)

        Logger.log("OpenVPN configuration:%r" % content)

        cfgFilePath = self._getOpenVPNConfigPath()
        file = open(cfgFilePath, mode='w+')
        file.write(content)
        file.close()

        return cfgFilePath

    def _modifyOpenVPNConfigContent(self, content):
        return content


class CommandExecutionConnector(VPNConnector):

    def _check(self, path):
        path = path.replace('/', os.sep)
        return os.path.exists(path)

    def _getOpenVPNExecPath(self):
        raise NotImplementedError()

    def _isEnabled(self, response):
        return 'Initialization Sequence Completed' in response

    def _isDisabled(self, response):
        return 'process exiting' in response

    def _shouldKillBeforeConnect(self):
        return True

    def _addSudoIfNeeded(self, cmd):
        return cmd

    def _prepareCmdList(self):
        Logger.log("_prepareCmdList Preparing cmdList ...", Logger.LOG_DEBUG)

        executableFile = self._getOpenVPNExecPath()
        Logger.log("OpenVPN Client should be on:%s" % executableFile)
        if not executableFile:
            Logger.log('Could not find a VPN application for %s' % config.getOS(), Logger.LOG_ERROR)
            gui.DialogOK(config.TITLE + ' - ' + config.VERSION, __language__(30040) % config.getOS(), __language__(30041))
            raise OpenVPNExeNotFoundException()

        executableFile = executableFile.replace('\\', '/')
        configFilePath = self._getOpenVPNConfigPath()
        configFilePath = configFilePath.replace('\\', '/')

        cmdList = [executableFile, configFilePath]


        Logger.log("Cmd list before sudo:%r" % cmdList, Logger.LOG_DEBUG)
        cmdList = self._addSudoIfNeeded(cmdList)
        Logger.log("Cmd list before sudo:%r" % cmdList, Logger.LOG_DEBUG)
        return cmdList

    def _prepareCmd(self):
        executableFile = self._getOpenVPNExecPath()
        Logger.log("OpenVPN Client should be on:%s" % executableFile)
        if not executableFile:
            Logger.log('Could not find a VPN application for %s' % config.getOS(), Logger.LOG_ERROR)
            gui.DialogOK(config.TITLE + ' - ' + config.VERSION, __language__(30031) % config.getOS(), __language__(30032))
            raise OpenVPNExeNotFoundException()


        configFilePath = self._getOpenVPNConfigPath()


        cmdline = '"' + executableFile + '"'
        cmdline += ' '
        cmdline += '"' + configFilePath + '"'
        cmdline  = cmdline.replace('\\', '/')
        Logger.log("Cmd line before sudo:%s" % cmdline, Logger.LOG_DEBUG)
        cmdline = self._addSudoIfNeeded(cmdline)
        return cmdline

    def _accessDeniedFound(self, response):
        return False

    def _isNetworkUnreachable(self, response):
        return 'Network is unreachable' in response or 'link local: [undef]' in response

    def _authenticationFailed(self, response):
        return 'Received control message: AUTH_FAILED' in response

    def _checkStatus(self, response):
        Logger.log("_checkStatus response:%r" % response, Logger.LOG_DEBUG)
        statusOk = False
        print repr(response)
        if response:
            if self._accessDeniedFound(response):
                Logger.log("_checkStatus access is denied", Logger.LOG_ERROR)
                title, msg1, msg2 = self._accessDeniedMessage()
                self.kill()
            elif self._authenticationFailed(response):
                Logger.log("_checkStatus authetication failed", Logger.LOG_ERROR)
                title, msg1, msg2 = __language__(30038), __language__(30005), ""
            elif self._isEnabled(response):
                Logger.log("_checkStatus enabled", Logger.LOG_DEBUG)
                title, msg1, msg2 = self._connectionOkMessage()
                statusOk = True
            elif self._isNetworkUnreachable(response):
                Logger.log("_checkStatus network unreachable", Logger.LOG_DEBUG)
                title, msg1, msg2 = __language__(30039), __language__(30004), ""
            else:
                Logger.log("_checkStatus failed other reason", Logger.LOG_DEBUG)
                self.kill()
                title, msg1, msg2 = self._connectionFailedMessage()

            if statusOk:
                self._allowActionConnected()
            else:
                self._allowActionError(title + " " + msg1)
            gui.DialogOK(title, msg1, msg2)

    def _shouldUseCmdList(self):
        return False

    def _connect(self):
        if self._shouldUseCmdList():
            cmd = self._prepareCmdList()
        else:
            cmd = self._prepareCmd()
        response = self._executeCommand(cmd, self._timeout)
        return response

    def _needShell(self):
        raise NotImplementedError()

    def _getStartupInfo(self):
        return None

    def _keepWaiting(self, response):
        return not (self._isEnabled(response) or self._isDisabled(response))

    def _getOpenVPNOutput(self):
        if self._check(config.OpenVPNLogFilePath):
            f  = open(config.OpenVPNLogFilePath, mode='r')
            data = f.read()
            f.close()
            return data
        return None            

    # The file must be erased before using it to avoid reading all data
    def _eraseOpenVPNLogFile(self):
        try:
            Logger.log("Trying to erase OpenVPN Log file", Logger.LOG_DEBUG)
            os.unlink(config.OpenVPNLogFilePath)
        except Exception, e:
            Logger.log("There was an error trying to erase OpenVPN Log File:%r" % repr(e), Logger.LOG_ERROR)

    def _executeCommand(self, cmd, timeout=0):

        shell = self._needShell()
        si = self._getStartupInfo()

        self._eraseOpenVPNLogFile()
        f  = open(config.OpenVPNLogFilePath, mode='w')

        ps = subprocess.Popen(cmd, shell=shell, stdout=f, startupinfo=si)

        while timeout > 0:
            xbmc.sleep(1000)
            timeout -= 1

            ret = self._getOpenVPNOutput()

            if not self._keepWaiting(ret):
                timeout = 0

        f.close()
        return ret


class UnixVPNConnector(CommandExecutionConnector):

    def _accessDeniedFound(self, response):
        return 'TUNSETIFF tun: Operation not permitted' in response

    def _accessDeniedMessage(self):
        return __language__(30033) , __language__(30034), __language__(30035)

    def _getStdErrOutput(self):
        f  = open(config.StdErrLogFilePath, mode='r')
        data = f.read()
        f.close()
        return data

    def _waitUntilVPNIsDisabled(self, timeout = 90, checkForSudoFailed = True):
        Logger.log("Waiting until VPN is completely disabled")
        sleep_time_s = 1
        while timeout > 0:

            ret = self._getStdErrOutput()
            if "incorrect password attempt" in ret:
                raise AccessDeniedException(__language__(30036))

            if "openvpn: no process found" in ret:
                Logger.log("openvpn process was not found, so assuming vpn is disabled", Logger.LOG_DEBUG)
                return True

            xbmc.sleep(sleep_time_s * 1000)
            timeout -= sleep_time_s

            ret = self._getOpenVPNOutput()
            # Even if it is disabled or the file does not exists (because it never started running) the VPN is disabled
            if ret is None or self._isDisabled(ret):
                Logger.log("VPN is disabled now")
                return True


        Logger.log("VPN has not been disabled...", Logger.LOG_ERROR)
        print ret
        return False


    def _getKillCmd(self):
        if self._shouldUseCmdList():
            killCmd = self._killCmdPath()
            Logger.log("Kill cmd path:%s" % killCmd, Logger.LOG_DEBUG)
            return [killCmd, '-SIGINT' , 'openvpn']
        else:
            return 'killall -SIGINT openvpn'


    def _kill(self):
        ret = False
        try:
            Logger.log("Unix trying to kill openvpn")
            # We should try with sigint so let openvpn to disconnect properly
            cmd = self._getKillCmd()
            Logger.log("Killing cmd:%r" % cmd)
            cmd = self._addSudoIfNeeded(cmd)

            shell = self._needShell()
            strErrFile  = open(config.StdErrLogFilePath, mode='w')

            ps = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=strErrFile)
            ret = self._waitUntilVPNIsDisabled(checkForSudoFailed = True)
            strErrFile.close()
        except AccessDeniedException, e:
            gui.DialogOK(e.args[0], __language__(30037), __language__(30005))
            return False
        except Exception:
            Logger.log("Unix kill there was an error trying to kill the VPN", Logger.LOG_ERROR)
            traceback.print_exc()
            return False
        return True


    def _needShell(self):
        return not self._shouldUseCmdList()

    # There are two possible ways of executing the openVpn. Using Shell (and command line) or not using it (which allows openvpn to be part of 'sudoers'
    # which will make the cmd a List instead of a line
    # In case we are providing a pwd to sudo we must use Shell (for stdin redirection)
    def _shouldUseCmdList(self):
        sudo, sudopwd = config.getSudo()
        return not sudopwd

    def _addSudoIfNeeded(self, cmds):
        sudo, sudopwd = config.getSudo()

        if sudo:
            Logger.log("Should use sudo")
            if sudopwd:
                cmds = 'echo %s | sudo -S %s' % (sudopwd, cmds)
            else:
                # If there is no need for password, cmd Line must be used
                cmdList = ['sudo']
                cmdList.extend( cmds )
                cmds = cmdList
        return cmds

    def _killCmdPath(self):
        path = '/usr/bin/killall'
        if self._check(path):
            return path
        path = '/bin/killall'
        if self._check(path):
            return path
        return '/sbin/killall'




class LinuxVPNConnector(UnixVPNConnector):

    def _getOpenVPNExecPath(self):
        path = '/usr/sbin/openvpn'
        if self._check(path):
            return path
        return None

    def _modifyOpenVPNConfigContent(self, content):
        content += "\r\nscript-security 2\r\n"
        content += "up /etc/openvpn/update-resolv-conf\r\n"
        content += "down /etc/openvpn/update-resolv-conf\r\n"
        return content


class OpenElecVPNConnector(UnixVPNConnector):

    def _getOpenVPNExecPath(self):
        path = '/usr/sbin/openvpn'
        if self._check(path):
            return path

        return None


class RaspBMCVPNConnector(UnixVPNConnector):

    def _getOpenVPNExecPath(self):
        path = '/usr/sbin/openvpn'
        if self._check(path):
            return path

        path = '/usr/bin/openvpn'
        if self._check(path):
            return path

        return None



class WindowsVPNConnector(CommandExecutionConnector):

    def _kill(self):
        Logger.log("Windows kill VPN connection")
        try:
            si = self._getStartupInfo()
            # si = subprocess.STARTUPINFO
            # si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            # si.wShowWindow = subprocess._subprocess.SW_HIDE

            ps  = subprocess.Popen('TASKKILL /F /IM openvpn.exe', shell=True, stdout=subprocess.PIPE, startupinfo=None)
            ps.wait()
        except Exception:
            Logger.log("Windows kill there was an error trying to kill the VPN", Logger.LOG_ERROR)
            traceback.print_exc()
            return False

        return True

    def _needShell(self):
        return False

    def _getStartupInfo(self):
        si = subprocess.STARTUPINFO
        si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess._subprocess.SW_HIDE
        return si

    def _accessDeniedFound(self, response):
        return 'route addition failed using CreateIpForwardEntry: Access is denied' in response or \
               ("FlushIpNetTable failed on interface" in response and "Access is denied" in response)

    def _accessDeniedMessage(self):
        return 'It seems you don\'t have permissions to perform this action', 'Please try running XBMC as Administrator', ''

    def _getOpenVPNExecPath(self):
        path = 'C:/Program Files/OpenVPN/bin/openvpn.exe'
        if self._check(path):
            return path

        path = 'C:/Program Files (x86)/OpenVPN/bin/openvpn.exe'
        if self._check(path):
            return path

        return None


class ActionNotification(Thread):

    def __init__(self):
        Thread.__init__(self)
        self._queue = Queue()

    def push(self, data):
        self._queue.put(data)

    def run(self):
        while True:
            data = self._queue.get()
            Logger.log("ActionNotification: %r" % data, Logger.LOG_DEBUG)
            try:
                ret = requests.post(config.getActionUrl(), data)
                Logger.log("ActionNotification ret:%s" % ret.status_code, Logger.LOG_DEBUG)
            except Exception:
                Logger.log("There was an error while logging action %r" % data, Logger.LOG_ERROR)





