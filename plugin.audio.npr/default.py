# *
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


import xbmc,xbmcaddon,xbmcplugin,xbmcgui
import csv, urllib, urlparse, os, sys
from xml.etree.ElementTree import ElementTree

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.npr')
__home__ = __settings__.getAddonInfo('path')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__     = "NPR - National Public Radio"
__addonid__       = "plugin.audio.npr"
__author__        = "Stieg"


## {{{ http://code.activestate.com/recipes/577305/ (r1)
__STATES = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}
## end of http://code.activestate.com/recipes/577305/ }}}


def read_in_station_data(path):
  # File format as follows in the CSV file:
  #
  # name|sid|call|icon|city|state|tagline
  data = {}
  with open(path, 'rt') as f:
    reader = csv.DictReader(f, delimiter='|')
    for d in reader:
      data[int(d['sid'])] = d

    return data


def get_station_data(sid = 0):
  ''' Acquire station data for the provided station ID '''
  url = 'http://api.npr.org/stations.php'
  query = {
    'apiKey' : 'MDA4NTkxNTA1MDEzMjI0NDk1MzM0YjliOA001',
    'id'     : sid,
    }

  params = urllib.urlencode(query)
  data = urllib.urlopen(url + "?" + params)

  tree = ElementTree()
  tree.parse(data)

  return tree

def get_station_streams(tree):
  ''' Extract all station streams from etree of NPR station data '''
  streams = {}
  elist = tree.findall('station/url')
  for e in elist:
    url_id = e.get('typeId')
    if  url_id == '10' or url_id == '15':
      title = e.get('title')
      text = e.text
      streams[title] = text

  return streams


def get_station_info(tree):
  ''' Extract general station info from etree of NPR station data '''
  data = {}
  tags = [
    'callLetters',
    'band',
    'name',
    'frequency',
    'marketCity',
    'tagline',
    ]

  for tag in tags:
    e = tree.find('station/' + tag)
    if e is None:
      data[tag] = ''
    else:
      data[tag] = e.text

    return data


def url_query_to_dict(url):
  ''' Returns the URL query args parsed into a dictionary '''
  param = {}
  if url:
    u = urlparse.urlparse(url)
    for q in u.query.split('&'):
      kvp = q.split('=')
      param[kvp[0]] = kvp[1]

  return param


def get_states_with_stations(stations):
  ''' Returns a dict of all available states '''
  states = {}
  for v in stations.itervalues():
    state = v.get('state')
    if state:
      state_full = __STATES.get(state)
      if not state_full:
	state_full = 'Unknown'
      states[state_full] = state

  return states


def get_stations_in_state(stations, state):
  ''' Returns a dictionary of stations in the given state '''
  state_st = {}
  for v in stations.itervalues():
    s = v.get('state')
    if state == s:
      sid = v.get('sid')
      city = v.get('city')
      tag = v.get('tagline')
      if city is None:
	city = 'Unknown'
      if tag is None or tag == 'None':
	tag = ''
      else:
	tag = ' - ' + tag
      name = "%s - %s%s" % (city, v.get('name'), tag)
      state_st[name] = int(sid)

  return state_st


def main():
  stations = read_in_station_data(os.path.join(__home__, 'npr_stations.csv'))
  params = url_query_to_dict(sys.argv[2])
  state = params.get('state')
  stream = params.get('stream')
  sid = params.get('id')

  if stream:
    # Play it.
    print ("Playing stream %s" % stream)
    xbmc.Player().play(stream)
  elif sid:
    # Display all streams for the station
    print("Station #%s selected" % sid)
    sd = get_station_data(sid)
    streams = get_station_streams(sd)
    keys = streams.keys()
    keys.sort()
    for k in keys:
      stream = streams[k]
      u = sys.argv[0] + "?stream=" + stream
      name = "Live Stream - %s" % k
      liz = xbmcgui.ListItem(name)
      xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]),
                                  url = u, listitem = liz,
                                  isFolder = False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

  elif state:
    # Display all stations in the state
    print("State of %s selected" % state)
    state_st = get_stations_in_state(stations, state)
    keys = state_st.keys()
    keys.sort()
    for k in keys:
      sid = state_st[k]
      tni = stations[sid].get('icon')
      u = sys.argv[0] + "?id=" + str(sid)
      liz = xbmcgui.ListItem(k, thumbnailImage = tni)
      xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]),
                                  url = u, listitem = liz,
                                  isFolder = True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  else:
    print("No state selected.")
    states = get_states_with_stations(stations)
    keys = states.keys()
    keys.sort()
    for k in keys:
      u = sys.argv[0] + "?state=" + states[k]
      liz = xbmcgui.ListItem(k)
      xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]),
                                  url = u, listitem = liz,
                                  isFolder = True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# Enter here.
main()
