# Copyright (C) 2026, JRiver
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import urllib.request
import base64
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

MCWS_URL = "/MCWS/v1"
ALIVE_URL = "/Alive"
AUTH_URL = "/Authenticate"
BROWSE_CHILDREN_URL = "/Browse/Children?ID={id}&Token={token}"
BROWSE_IMAGE_URL = "/Browse/Image?ID={id}&Width={width}&Height={height}&Token={token}&LibId={library}"
BROWSE_FILES_URL = "/Browse/Files?ID={id}&Action=json&Token={token}"
FILE_IMAGE_URL = "/File/GetImage?File={key}&ThumbnailSize=large&Token={token}&LibId={library}"
FILE_CONTENT_URL = "/File/GetFile?File={key}&Playback=2&Token={token}{conversion}"
FILE_INFO_URL = "/File/GetInfo?File={key}&Action=json&Token={token}"
LOOKUP_URL = "https://webplay.jriver.com/libraryserver/lookup?id={access}"
LIBRARIES_URL = "/Library/List?Token={token}"
FIELDS = "&Fields=" + quote_plus("Key,Name,Album,Artist,Duration,Media Type,Media Sub Type,File Type,Date,Description,Genre,Series,Season,Episode,Bookmark")

def reset():
   xbmcgui.Window(10000).setProperty("JRMC_TOKEN", None)

def connect(showUI=False):
   token = getToken()
   if token:
      return True

   # Lookup Access Key if necessary
   try:
      setBaseAddress()

   except Exception as e:
      if showUI:
         xbmcgui.Dialog().notification(getDisplayString(30103), f"{e}")
      xbmc.log(f"JRIVER: {e}", xbmc.LOGWARNING)
      return False
   
   server_name = ""

   if showUI:
      xbmcgui.Dialog().notification(getDisplayString(30100), getDisplayString(30101))
   xbmc.log("JRIVER: Connecting to " + getBaseURL(), xbmc.LOGINFO)

   # Check if server is running/responding
   try:
      url = getBaseURL() + ALIVE_URL
      with urllib.request.urlopen(url) as response:
         data = response.read().decode("utf-8")
     
      if not "Status=\"OK\"" in data:
         raise Exception()

      root = ET.fromstring(data)
      for item in root.findall('Item'):
         if item.get("Name") == "FriendlyName":
            server_name = item.text
   
   except Exception as e:
      xbmc.log("JRIVER: " + getDisplayString(30200) + f"{e}", xbmc.LOGWARNING)
      if showUI:
         xbmcgui.Dialog().notification(getDisplayString(30103), getDisplayString(30200))
      return False

   # Try to authenticate and get token
   try:
      url = getBaseURL() + AUTH_URL
      username = xbmcaddon.Addon().getSettingString("username")
      password = xbmcaddon.Addon().getSettingString("password")
      credentials = f"{username}:{password}".encode("utf-8")
      base64_credentials = base64.b64encode(credentials).decode("utf-8")
      headers = {"Authorization": f"Basic {base64_credentials}"}
      req = urllib.request.Request(url, headers=headers)

      with urllib.request.urlopen(req) as response:
         data = response.read().decode("utf-8")
         
      if not "Status=\"OK\"" in data:
         raise Exception()

      root = ET.fromstring(data)
      for item in root.findall("Item"):
         if item.get("Name") == "Token":
            xbmcgui.Window(10000).setProperty("JRMC_TOKEN", item.text)
            if showUI:
               xbmcgui.Dialog().notification(getDisplayString(30100), getDisplayString(30102))
            setLoadedLibrary(server_name)
            return True

      return False
    
   except Exception as e:
      xbmc.log("JRIVER: " + getDisplayString(30201), xbmc.LOGWARNING)
      if showUI:
         xbmcgui.Dialog().notification(getDisplayString(30103), getDisplayString(30201))
      return False

def setBaseAddress():
   address = xbmcaddon.Addon().getSettingString("library")
   use_https = xbmcaddon.Addon().getSettingBool("secure")
   use_local_ip = xbmcaddon.Addon().getSettingBool("local_ip")
   if not address:
      address = ""
   elif not ":" in address:
      # Look up access key
      try:
         url = LOOKUP_URL.format(access=address)
        
         with urllib.request.urlopen(url) as response:
            data = response.read().decode("utf-8")
      except Exception as e:
         xbmc.log("JRIVER: " + getDisplayString(30203), xbmc.LOGINFO)
         raise Exception( getDisplayString(30203))
         
      if not "Status=\"OK\"" in data:
         xbmc.log("JRIVER: " + getDisplayString(30204), xbmc.LOGINFO)
         raise Exception( getDisplayString(30204))

      try:
         address = ""
         root = ET.fromstring(data)
         ip = root.find("ip").text
         port = root.find("https_port" if use_https else "port").text

         if use_local_ip:
            local_ips = root.find("localiplist").text.split(",")
            ip = local_ips[0]

         xbmc.log("JRIVER: " + f"{ip} {port}", xbmc.LOGINFO)
         address = ip + ":" + port

      except Exception as e:
         xbmc.log("JRIVER: " + getDisplayString(30204), xbmc.LOGINFO)
         raise Exception( getDisplayString(30204))

   xbmcgui.Window(10000).setProperty("JRMC_URL", ("https://" if use_https else "http://") + address + MCWS_URL)

def getBaseURL():
   return xbmcgui.Window(10000).getProperty("JRMC_URL") 

def getToken():
   return xbmcgui.Window(10000).getProperty("JRMC_TOKEN")

def getDisplayString(id):
   return xbmcaddon.Addon().getLocalizedString(id)

def getLibChildren(parentId):

   if not connect():
      return

   try:
      url = getBaseURL() + BROWSE_CHILDREN_URL.format(id=parentId, token=getToken())
      with urllib.request.urlopen(url) as response:
         data = response.read().decode("utf-8")
           
      if not "Status=\"OK\"" in data:
         raise Exception()

      children = []
      root = ET.fromstring(data)
      for item in root.findall("Item"):
         child = {
            "Name": item.get("Name"),
            "ID": item.text,
            "Icon": getBrowseImageURL(item.text, 500, 500)
         }
         children.append(child)

      return children
       
   except Exception as e:
      # xbmcgui.Dialog().notification("Error", f"{e}")
      xbmc.log(f"JRIVER: {e}", xbmc.LOGWARNING)

def getLibFiles(parentId):

   if not connect():
      return

   token = xbmcgui.Window(10000).getProperty("JRMC_TOKEN")
   try:
      url = getBaseURL() + BROWSE_FILES_URL.format(id=parentId, token=token) + FIELDS
      with urllib.request.urlopen(url) as response:
         data = response.read().decode("utf-8")
         
      files = json.loads(data)
      return files
       
   except Exception as e:
      xbmc.log(f"JRIVER: {e}", xbmc.LOGWARNING)

def getFileInfo(fileKey):

   if not connect():
      return

   token = xbmcgui.Window(10000).getProperty("JRMC_TOKEN")
   try:
      url = getBaseURL() + FILE_INFO_URL.format(key=fileKey, token=token)
      with urllib.request.urlopen(url) as response:
         data = response.read().decode("utf-8")
         
      info = json.loads(data)
      if info and len(info) > 0:
         return info[0]
       
   except Exception as e:
      xbmc.log(f"JRIVER: {e}", xbmc.LOGWARNING)

def getFileImageURL(file_key):
   return getBaseURL() + FILE_IMAGE_URL.format(key=file_key, token=getToken(), library=getLoadedLibrary())

def getFileContentURL(file_key, convert):
   return getBaseURL() + FILE_CONTENT_URL.format(key=file_key, conversion=convert, token=getToken())

def getBrowseImageURL(browse_id, height, width):
   return getBaseURL() + BROWSE_IMAGE_URL.format(id=browse_id,  height=height, width=width, token=getToken(), library=getLoadedLibrary())

def getLoadedLibrary():
   return xbmcgui.Window(10000).getProperty("JRMC_LIBID")

def setLoadedLibrary(serverName):

   library_id = "Library0"
   try:
      url = getBaseURL() + LIBRARIES_URL.format(token=getToken())
      with urllib.request.urlopen(url) as response:
         data = response.read().decode("utf-8")

      root = ET.fromstring(data) 
      for item in root.findall("Item"):
        if "Loaded" in item.get("Name") and item.text == "1":
           library_id = item.get("Name")[0:-6]
           break
         
   except Exception as e:
      xbmc.log(f"JRIVER: {e}", xbmc.LOGWARNING)

   xbmcgui.Window(10000).setProperty("JRMC_LIBID", f"{serverName}_{library_id}")