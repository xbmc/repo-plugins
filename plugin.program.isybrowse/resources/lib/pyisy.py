'''
    PyISY
    Copyright (C) 2012 Ryan M. Kraus

    LICENSE:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    DESCRIPTION:
    This Python Module is designed to interface directly with the REST
    API interface of the ISY-99 Series of Home Automation Controllers
    from Universal Devices Incorporated.
    
    WRITTEN:    11/2012
'''

import urllib2
import urllib
from xml.dom.minidom import parseString

def open(user, password, host='isy', port='80', usehttps=False):
    out = isy(user, password, host, port, usehttps)
    if not out.Ping():
        out = dummy()
        
    return out

class isy(object):
    __x10__ = { \
        'all_off': 1, \
        'all_on': 4, \
        'on': 3, \
        'off': 11, \
        'bright': 7, \
        'dim': 15 \
        }
        
    __dummy__ = False

    def __init__(self, user, password, host='isy', port='80', usehttps=False):
        self._user = user
        self._password = password
        self._host = host
        self._port = port
        self._usehttps = usehttps
            
        self.Connect()
        
    def Connect(self):
        # create connection to ISY
        url = self._BaseURL()
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self._user, self._password)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
        
    def Ping(self):
        try:
            theurl = self._BaseURL() + 'rest/nodes/'
            #normalize the URL
            theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
            self._SendRequest(theurl)
            return True
        except urllib2.URLError:
            return False
        
    def _BaseURL(self):
        if self._usehttps:
            url = 'https://'
        else:
            url = 'http://'
        url += self._host + ':' + str(self._port) + '/'
        return url
        
    def _SendRequest(self, url):
        try:
            pagehandle = urllib2.urlopen(url)
        except urllib2.HTTPError:
            self.Connect()
            pagehandle = urllib2.urlopen(url)
            
        data = pagehandle.read()
        pagehandle.close()
        return data
        
    def _ParseNodeXML(self, data, return_node=None, return_parent=None):
        try:
		    dom = parseString(data)
        except:
            data += '>' # sometimes the xml is missing the closing bracket
            dom = parseString(data)
        node_types = ['folder', 'node', 'group']
        child_dict = {}
        for ntype in node_types:
            nodes = dom.getElementsByTagName(ntype)
            for node in nodes:
                parent = node.getElementsByTagName('parent')
                if len(parent) == 0:
                    paddr = None
                else:
                    paddr = parent[0].toxml().replace('<parent type="1">','').replace('<parent type="3">','').replace('</parent>','')
                
                if (return_node!=None) or (return_parent==paddr):
                    name = node.getElementsByTagName('name')[0].toxml().replace('<name>','').replace('</name>','')
                    addr = node.getElementsByTagName('address')[0].toxml().replace('<address>','').replace('</address>','')
                    properties = node.getElementsByTagName('property')
                    if len(properties)>0:
                        status = properties[0].toxml().split('"')
                        val_ind = status.index(' value=')+1
                        status = status[val_ind]
                    else:
                        status = '0'
                        
                    if (return_node==None) or (addr in [return_node, return_node.replace('%20', ' ')]):
                        child_dict[name] = (ntype, addr, status)
                    
        return child_dict
        
    def _ParseProgramXML(self, data, return_node=None, return_parent=None):
        # read file
        dom = parseString(data)
        # look for children of addr
        ntype = 'program'
        child_dict = {}
        nodes = dom.getElementsByTagName(ntype)
        for node in nodes:
            name = node.getElementsByTagName('name')[0].toxml().replace('<name>','').replace('</name>','')
            properties = node.toxml().split('"')
            new_addr_ind = properties.index(' id=')+1
            new_addr = properties[new_addr_ind]
            try:
                properties.index('<program enabled=')
                type = 'program'
            except ValueError:
                type ='folder'
            
            if (return_parent==None) or (new_addr!=return_parent):
                if (return_node==None) or (new_addr==return_node):
                    child_dict[name] = (type, new_addr)
                
        return child_dict
        
    def NodeOn(self, addr, val=None):
        theurl = self._BaseURL() + 'rest/nodes/' + addr + '/cmd/DON'
        if val != None:
            if val > 255:
                val = 255
            if val < 0:
                val = 0
            theurl += '/' + str(int(val))
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def NodeOn25(self, addr):
        self.NodeOn(addr, 25*255/100)
        
    def NodeOn50(self, addr):
        self.NodeOn(addr, 50*255/100)
        
    def NodeOn75(self, addr):
        self.NodeOn(addr, 75*255/100)
        
    def NodeOn100(self, addr):
        self.NodeOn(addr, 100*255/100)
        
    def NodeOff(self, addr):
        theurl = self._BaseURL() + 'rest/nodes/' + addr + '/cmd/DOF'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def NodeToggle(self, addr):
        # get node information
        info = self.NodeInfo(addr)
        
        if len(info.keys()) > 0:
            # parse node information
            NodeName = info.keys()[0]
            NodeValue = int(info[NodeName][2])
            
            # decide on action
            if NodeValue > 0:
                self.NodeOff(addr)
            else:
                self.NodeOn(addr)
            
            return True
        else:
            return False
        
    def NodeFastOn(self, addr):
        theurl = self._BaseURL() + 'rest/nodes/' + addr + '/cmd/DFON'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def NodeFastOff(self, addr):
        theurl = self._BaseURL() + 'rest/nodes/' + addr + '/cmd/DFOF'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def NodeBright(self, addr):
        theurl = self._BaseURL() + 'rest/nodes/' + addr + '/cmd/BRT'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def NodeDim(self, addr):
        theurl = self._BaseURL() + 'rest/nodes/' + addr + '/cmd/DIM'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def NodeInfo(self, addr):
        theurl = self._BaseURL() + 'rest/nodes/' + addr.replace(' ', '%20')
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        data = self._SendRequest(theurl)
        # parse response
        node = self._ParseNodeXML(data, return_node=addr)
        return node
        
    def BrowseNodes(self, addr = None):
        theurl = self._BaseURL() + 'rest/nodes/'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        data = self._SendRequest(theurl)
        children = self._ParseNodeXML(data, return_parent=addr)
        return children
        
    def X10cmd(self, addr, cmd):
        theurl = self._BaseURL() + 'rest/X10/' + addr + '/' + self.__x10__[cmd]
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        self._SendRequest(theurl)
        
    def BrowsePrograms(self, addr='0001'):
        theurl = self._BaseURL() + 'rest/programs/'
        if addr == None or addr=='':
            addr = '0001'
        theurl += addr.replace(' ', '%20')
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        data = self._SendRequest(theurl)
        programs = self._ParseProgramXML(data, return_parent=addr)
        return programs
        
    def ProgramRun(self, addr):
        theurl = self._BaseURL() + 'rest/programs/' + addr + '/run'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        data = self._SendRequest(theurl)
        
    def ProgramRunThen(self, addr):
        theurl = self._BaseURL() + 'rest/programs/' + addr + '/runThen'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        data = self._SendRequest(theurl)
        
    def ProgramRunElse(self, addr):
        theurl = self._BaseURL() + 'rest/programs/' + addr + '/runElse'
        #normalize the URL
        theurl = urllib.quote(theurl, safe="%/:=&?~#+!$,;'@()*[]")
        data = self._SendRequest(theurl)
        
class dummy(object):

    __dummy__ = True

    def __init__(self, *kargs, **kwargs):
        pass
        
    def Connect(self):
        pass
        
    def Ping(self):
        return True
        
    def NodeOn(self, *kargs, **kwargs):
        pass
        
    def NodeOn25(self, *kargs, **kwargs):
        pass
        
    def NodeOn50(self, *kargs, **kwargs):
        pass
        
    def NodeOn75(self, *kargs, **kwargs):
        pass
        
    def NodeOn100(self, *kargs, **kwargs):
        pass
        
    def NodeOff(self, *kargs, **kwargs):
        pass
        
    def NodeToggle(self, *kargs, **kwargs):
        pass
        
    def NodeFastOn(self, *kargs, **kwargs):
        pass
        
    def NodeFastOff(self, *kargs, **kwargs):
        pass
        
    def NodeBright(self, *kargs, **kwargs):
        pass
        
    def NodeDim(self, *kargs, **kwargs):
        pass
        
    def NodeInfo(self, addr):
        return {'Dummy Node ' + str(addr): 
            ('node', addr, '255')}
            
    def BrowseNodes(self, addr=None):
        if addr==None:
            nodes = {'Dummy Room 1': ('folder', '1', '0'),
                'Dummy Room 2': ('folder', '2', '0')}
        elif int(addr)==1:
            nodes = {'Dummy Switch 3': ('node', '3', '255')}
        elif int(addr)==2:
            nodes = {'Dummy Switch 4': ('node', '4', '255')}
            
        return nodes
        
    def X10cmd(self, *kargs, **kwargs):
        pass
        
    def BrowsePrograms(self, addr='0001'):
        return {'Dummy Program 2': ('program', '2', '0')}
        
    def ProgramRun(self, *kargs, **kwargs):
        pass
        
    def ProgramRunThen(self, *kargs, **kwargs):
        pass
        
    def ProgramRunElse(self, *kargs, **kwargs):
        pass