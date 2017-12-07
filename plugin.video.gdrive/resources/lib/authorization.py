'''
    Copyright (C) 2014-2016 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''


#
#
#
class authorization:
    # CloudService v0.2.3

    ##
    ##
    def __init__(self,username):
        self.auth = {}
        self.username = username
        self.isUpdated = False

    ##
    # Set the token of name with value provided.
    ##
    def setToken(self,name,value):
        try:
            if self.auth[name] != value:
                self.auth[name] = value
            self.isUpdated = True
        except:
            self.isUpdated = True
        self.auth[name] = value


    ##
    # Get the token of name with value provided.
    # returns: str
    ##
    def getToken(self,name):
        if name in self.auth:
            return self.auth[name]
        else:
            return ''

    ##
    # Get the count of authorization tokens
    # returns: int
    ##
    def getTokenCount(self):
        return len(self.auth)

    ##
    # Save the latest authorization tokens
    ##
    def saveTokens(self,instanceName,addon):
        for token in self.auth:
            addon.setSetting(instanceName + '_'+token, self.auth[token])

    ##
    # load the latest authorization tokens
    ##
    def loadToken(self,instanceName,addon, token):
        try:
            tokenValue = addon.getSetting(instanceName + '_'+token)
            if tokenValue != '':
              self.auth[token] = tokenValue
              return True
            else:
              return False
        except:
            return False

    ##
    # load the latest authorization tokens
    ##
    def isToken(self,instanceName, addon, token):
        try:
            if self.auth[token] != '':
              return True
            else:
              return False
        except:
            return False
