# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import os, time

from xml.dom import minidom

from icecast_common import *

CACHE_FILE_NAME = 'icecast.cache'
TIMESTAMP_FILE_NAME = 'icecast.timestamp'

# Compose the cache file name
def getCacheFileName():
  cache_file_dir = getUserdataDir()
  cache_file_name = os.path.join(cache_file_dir,CACHE_FILE_NAME)
  return cache_file_name

# Compose the timestamp file name
def getTimestampFileName():
  cache_file_dir = getUserdataDir()
  timestamp_file_name = os.path.join(cache_file_dir,TIMESTAMP_FILE_NAME)
  return timestamp_file_name

# Read the XML file form local cache
def readLocalXML():
  cache_file_name = getCacheFileName()
  f = open(cache_file_name,'rb')
  xml = f.read()
  f.close()
  return xml

# Overwrite the local cache
def writeLocalXML(xml):
  cache_file_name = getCacheFileName() 
  f = open(cache_file_name,'wb')
  f.write(xml)
  f.close()

# Build the list of genres from DOM
def buildGenreList(dom):
  genre_hash = {}
  genres = dom.getElementsByTagName("genre")
  for genre in genres:
    genre_name = getText(genre.childNodes)
    for genre_name_single in genre_name.split():
      if genre_hash.has_key(genre_name_single):
        genre_hash[genre_name_single] += 1
      else:
        genre_hash[genre_name_single] = 1
  for key in sorted(genre_hash.keys()):
    addDir(key, genre_hash[key])

# Build list of links in a given genre from DOM
def buildLinkList(dom, genre_name_orig):
  entries = dom.getElementsByTagName("entry")

  for entry in entries:

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

    if genre_name.find(genre_name_orig) > -1 :

      listen_url_objects = entry.getElementsByTagName("listen_url")
      for listen_url_object in listen_url_objects:
        listen_url = getText(listen_url_object.childNodes)

      server_name_objects = entry.getElementsByTagName("server_name")
      for server_name_object in server_name_objects:
        server_name = getText(server_name_object.childNodes)

      bitrate_objects = entry.getElementsByTagName("bitrate")
      for bitrate_object in bitrate_objects:
        bitrate = getText(bitrate_object.childNodes)

      addLink(server_name, listen_url, bitrate, 0)

# Do a search in DOM
def doSearch(dom, query):
  entries = dom.getElementsByTagName("entry")

  for entry in entries:

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

    server_name_objects = entry.getElementsByTagName("server_name")
    for server_name_object in server_name_objects:
      server_name = getText(server_name_object.childNodes)

    if ((genre_name.find(query) > -1) or (server_name.find(query) > -1)) :

      listen_url_objects = entry.getElementsByTagName("listen_url")
      for listen_url_object in listen_url_objects:
        listen_url = getText(listen_url_object.childNodes)

      bitrate_objects = entry.getElementsByTagName("bitrate")
      for bitrate_object in bitrate_objects:
        bitrate = getText(bitrate_object.childNodes)

      addLink(server_name, listen_url, bitrate, 0)

# Functions to read and write unix timestamp to database or file
def putTimestamp():
  unix_timestamp = int(time.time())
  timestamp_file_name = getTimestampFileName()
  f = open(timestamp_file_name, 'w')
  f.write(str(unix_timestamp))
  f.close()

def getTimestamp():
  timestamp_file_name = getTimestampFileName()
  try: 
    f = open(timestamp_file_name, 'r')
    unix_timestamp = f.read()
    f.close()
    unix_timestamp = int(unix_timestamp)
  except:
    unix_timestamp = 0
  return unix_timestamp

# Timestamp wrappers
def timestampExpired():
  current_unix_timestamp = int(time.time())
  saved_unix_timestamp = getTimestamp()
  if (current_unix_timestamp - saved_unix_timestamp) > TIMESTAMP_THRESHOLD :
    return 1
  return 0

