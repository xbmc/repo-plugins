import sys, os
import urllib, cgi, struct, time
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# plugin constants
__plugin__     = "reLive"
__author__     = 'BuZz [buzz@exotica.org.uk] / http://www.exotica.org.uk'
__svn_url__    = "http://xbmc-addons.googlecode.com/svn/trunk/plugins/music/relive"
__version__    = "0.8"

__settings__ = xbmcaddon.Addon('plugin.audio.relive')
__language__ = __settings__.getLocalizedString

RELIVE_STATIONS = 'http://stations.re-live.se/getstations/'

class AppURLopener(urllib.FancyURLopener):
    version = 'reLive/6 (' + os.name + ') reLive XBMC/' + __version__

urllib._urlopener = AppURLopener()

handle = int(sys.argv[1])

def get_params(defaults):
  new_params = defaults
  params = cgi.parse_qs(sys.argv[2][1:])
  for key, value in params.iteritems():
    new_params[key] = urllib.unquote_plus(params[key][0])
  return new_params

def show_stations():
  livestreams = os.path.join(__settings__.getAddonInfo('path'), 'livestreams')

  li = xbmcgui.ListItem( __language__(30000) )
  ok = xbmcplugin.addDirectoryItem(handle, livestreams, listitem = li, isFolder = True)

  response = urllib.urlopen(RELIVE_STATIONS)
  pack_len, pack_type, prot_ver, num_stations = struct.unpack('<HBBL', response.read(8))

  for i in range(0, num_stations):
    pack_len, pack_type, station_id, port = struct.unpack('<HBLH', response.read(9))
    station_name = get_struct_text(response)
    domain_name = get_struct_text(response)
    path_name = get_struct_text(response)
    
    station_info = 'http://' + domain_name + path_name
    url = sys.argv[0] + '?' + urllib.urlencode( { 'mode': 'streams', 'station': station_info } )

    li = xbmcgui.ListItem(label = station_name)
    ok = xbmcplugin.addDirectoryItem(handle, url, listitem = li, isFolder = True)

  response.close
  xbmcplugin.endOfDirectory(handle = handle, succeeded = True)

# get the streams associated with a specific station
def get_station_info(station):
  response = urllib.urlopen(station + 'getstationinfo/')
  pack_len, pack_type, prot_ver = struct.unpack('<HBB', response.read(4))
  station_name = get_struct_text(response)
  
  # v5 introduced the website field
  if prot_ver > 4:
    station_website = get_struct_text(response)

  num_streams, = struct.unpack('<L', response.read(4))

  for i in range(0, num_streams):
    pack_len, pack_type = struct.unpack('<HB', response.read(3))
    stream_id, stream_date, stream_len, stream_size, stream_fmt, stream_crc, stream_has_chat, stream_chat_crc \
      = struct.unpack('<LLLLBLBL', response.read(26))
    stream_name = get_struct_text(response)
    host_name = get_struct_text(response)
    info = get_struct_text(response)

    url = sys.argv[0] + '?'
    url += urllib.urlencode( { \
      'mode': 'tracks', \
      'station': station, \
      'name': station_name, \
      'title': stream_name, \
      'streamid': stream_id, \
      'size': stream_size, \
      'length':  stream_len } )
    stream_date_fmt = time.strftime('%d.%m.%Y', time.gmtime(stream_date))
    li = xbmcgui.ListItem( label = '[' + stream_date_fmt + '] ' + stream_name )
    li.setInfo( 'music', { 'date': stream_date_fmt, 'title': stream_name } )
    ok = xbmcplugin.addDirectoryItem(handle, url, listitem = li, isFolder = True)

  response.close
  xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.endOfDirectory(handle, succeeded = True)

# get the information for individual parts of a stream
def get_stream_info(station, station_name, stream_id, stream_name, stream_size, stream_len ):

  response = urllib.urlopen(station + 'getstreaminfo/?streamid=%d' % stream_id )
  pack_len, pack_type, prot_ver = struct.unpack('<HBB', response.read(4))
  num_tracks, = struct.unpack('<L', response.read(4))

  for i in range(0, num_tracks):
    pack_len, pack_type = struct.unpack('<HB', response.read(3))
    track_offset, track_id, track_type, track_has_info = struct.unpack('<LLBB', response.read(10))
    artist_name = get_struct_text(response)
    track_name = get_struct_text(response)

    track_offset_bytes = track_offset*(stream_size/stream_len)
    stream_url = station + 'getstreamdata/?'
    stream_url += urllib.urlencode( { 'streamid': stream_id, 'start': track_offset_bytes, 'length': stream_size } )

    url = sys.argv[0] + '?'
    url += urllib.urlencode( { 'mode': 'play', 'title': stream_name, 'artist': station_name, 'url': stream_url } )
    label = str(i + 1) + '. ' + track_name + " - " + artist_name + ' - ' + stream_name
    li = xbmcgui.ListItem( label )
    li.setInfo( 'music', { 'title': label, 'artist': artist_name, 'album': stream_name, 'genre': station_name, 'tracknumber': i + 1 } )
    ok = xbmcplugin.addDirectoryItem(handle, url, listitem = li, isFolder = False)

  response.close
  xbmcplugin.endOfDirectory(handle, succeeded = True)

# get a string from the API in the format length of text (word), text
def get_struct_text(response):
  name_len = struct.unpack('<H', response.read(2))
  name, = struct.unpack("<%ds" % name_len, response.read(name_len[0]))
  return name

def play_stream(url, title, info):
  listitem = xbmcgui.ListItem(title)
  listitem.setInfo ( 'music', info )
  player = xbmc.Player(xbmc.PLAYER_CORE_MPLAYER)
  player.play(url, listitem)

params = get_params( { 'mode': 'stations', 'station': '' } )
mode = params['mode']
station = params["station"]

if mode == 'stations':
  show_stations()
  
elif mode == 'streams':
  get_station_info(station)

elif mode == 'tracks':
  stream_id = int(params['streamid'])
  station_name = params['name']
  stream_name = params['title']
  stream_size = int(params['size'])
  stream_len = int(params['length'])
  get_stream_info(station, station_name, stream_id, stream_name, stream_size, stream_len )

elif mode == 'play':
  title = params['title']
  artist = params['artist']
  url = params['url']
  play_stream(url, title, { 'title': title, 'artist': artist })

