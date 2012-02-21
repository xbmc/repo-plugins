# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2011>  <BestRussianTV>
#
#       This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
class Client:
    AccessCredentials = (object)
    def __init__(self):
        self.AccessCredentials = AccessCredentials()
    

class AccessCredentials:
    req = ''
    LoginCountry = ''
    StbMacAddress = ''
    UserLogin = ''
    UserPassword = ''
    UserSystemID = ''
    UserSystemPassword = ''
    clientIP = ''
    sessionID = ''
    settings = []
    def get(self):
        set = ''
        if self.LoginCountry == '' and self.StbMacAddress == '' and self.UserLogin == '' and self.UserPassword == '' and self.UserSystemID == '' and self.UserSystemPassword == '' and self.clientIP == '' and self.sessionID == '' and len(self.settings) == 0:
            self.req = '<d4p1:clientCredentials xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Media.Client" i:nil="true" />'
        else:    
            self.req = '<d4p1:clientCredentials xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Media.Client">'
            if self.LoginCountry != '':
                self.LoginCountry = '<d5p1:LoginCountry>' + self.LoginCountry + '</d5p1:LoginCountry>'
            else:
                self.LoginCountry = '<d5p1:LoginCountry i:nil="true" />'    
            if self.StbMacAddress != '':
                self.StbMacAddress = '<d5p1:StbMacAddress>' + self.StbMacAddress + '</d5p1:StbMacAddress>'
            else:
                self.StbMacAddress = '<d5p1:StbMacAddress i:nil="true" />'
            if self.UserLogin != '':
                self.UserLogin = '<d5p1:UserLogin>' + self.UserLogin + '</d5p1:UserLogin>'
            else:
                self.UserLogin = '<d5p1:UserLogin i:nil="true" />'
            if self.UserPassword != '':
                self.UserPassword = '<d5p1:UserPassword>' + self.UserPassword + '</d5p1:UserPassword>'
            else:
                self.UserPassword = '<d5p1:UserPassword i:nil="true" />' 
            if self.UserSystemID != '':
                self.UserSystemID = '<d5p1:UserSystemID>' + self.UserSystemID + '</d5p1:UserSystemID>'
            else:
                self.UserSystemID = '<d5p1:UserSystemID i:nil="true" />'
            if self.UserSystemPassword != '':
                self.UserSystemPassword = '<d5p1:UserSystemPassword>' + self.UserSystemPassword + '</d5p1:UserSystemPassword>'
            else:
                self.UserSystemPassword = '<d5p1:UserSystemPassword i:nil="true" />'
            if self.clientIP != '':
                self.clientIP = '<d5p1:clientIP>' + self.clientIP + '</d5p1:clientIP>'
            else:
                self.clientIP = '<d5p1:clientIP i:nil="true" />'
            if self.sessionID != '':
                self.sessionID = '<d5p1:sessionID>' + self.sessionID + '</d5p1:sessionID>'
            else:
                self.sessionID = '<d5p1:sessionID i:nil="true" />'
            if len(self.settings) == 0:
                set = '<d5p1:settings xmlns:d6p1="http://schemas.datacontract.org/2004/07/IVS.Common" />'
            self.req = self.req + self.LoginCountry + self.StbMacAddress + self.UserLogin + self.UserPassword + self.UserSystemID + self.UserSystemPassword + self.clientIP + self.sessionID + set + '</d4p1:clientCredentials>'
        return self.req            
                                              
             