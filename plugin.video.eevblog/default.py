import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon

__plugin__ =  'EEVblog'
__author__ = 'Clumsy <clumsy@xbmc.org>'
__date__ = '08-27-2010'
__version__ = '0.1.4'
__settings__ = xbmcaddon.Addon(id='plugin.video.eevblog')

# Thanks to some of the other plugin authors, where I borrowed some ideas from !

REMOTE_DBG = False

# append pydev remote debugger
if REMOTE_DBG:
  # Make pydev debugger works for auto reload.
  # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
  try:
    import pysrc.pydevd as pydevd
  # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
    pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
  except ImportError:
    sys.stderr.write("Error: " +
      "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
    sys.exit(1)
    
def open_url(url):
  req = urllib2.Request(url)
  content = urllib2.urlopen(req)
  data = content.read()
  content.close()
  return data

def build_main_directory():
  image = "icon.png"
  listitem = xbmcgui.ListItem(label = "Episode Listing", iconImage = image, thumbnailImage = image)
  u = sys.argv[0] + "?mode=1"
  xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)

def build_episodes_directory():
  url = 'http://www.eevblog.com/episodes/'
  data = open_url(url)
  match = re.compile('<body>(.+?)<div class="sociable">', re.DOTALL).findall(data)
  youtube_url_name = re.compile('<a href ="(.+?)" title="(.+?)">', re.DOTALL).findall(match[0])
  
  for ep_url, name in youtube_url_name:
    listitem = xbmcgui.ListItem(label = name, iconImage = "", thumbnailImage = "")
    #listitem.setInfo( type = "Video", infoLabels = { "Title": name, "Director": __plugin__, "Studio": __plugin__, "Genre": "Video Blog", "Plot": plot[0], "Episode": "" } )
    #u = sys.argv[0] + "?mode=2&name=" + name + "&youtube_video_id="+ urllib.quote_plus(youtube_video_id[0]) + "&plot=" + urllib.quote_plus(clean(plot[0])) + "&genre=" + "VideoBlog" + "&episode=" + urllib.quote_plus("0")
    u = sys.argv[0] + "?mode=2&url=" + ep_url
    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = False)
    xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    
def clean(name):
  remove = [('&amp;','&'), ('&quot;','"'), ('&#039;','\''), ('\r\n',''), ('&apos;','\''), ('.','')]
  for trash, crap in remove:
    name = name.replace(trash,crap)
  return name
      
def play_video(ep_url):
  xbmc.executebuiltin('ActivateWindow(busydialog)')
  ep_data = open_url(ep_url)
  plot = re.compile('<div class="info">.+?<p>(.+?)</p>.', re.DOTALL).findall(ep_data)
  youtube_video_id = re.compile('<param name="movie" value=".*?/v/(.+?)[&\?].').findall(ep_data)
  
  quality = int(__settings__.getSetting('quality'))
  if quality == 0:
    quality=22 # 720
  else:
    quality=35 # 480
  
  video_info_html = open_url('http://www.youtube.com/get_video_info?video_id=' 
                             + youtube_video_id[0] +'&el=vevo')
  fmt_url_map = urllib.unquote_plus(re.findall('&fmt_url_map=([^&]+)', video_info_html)[0]).split(',')
  for url in fmt_url_map:
    if (quality == 22) and url.startswith('22|'):
      video_url = url.split('|')[1]
      break
    elif (url.startswith('35|')
          or url.startswith('34|') or url.startswith('18|')):
      video_url = url.split('|')[1]
      break

  listitem = xbmcgui.ListItem(label = name , iconImage = 'DefaultVideo.png', thumbnailImage = '')
  listitem.setInfo( type = "Video", infoLabels={ "Title": name, "Director": __plugin__, "Studio": __plugin__, "Genre": genre, "Plot": plot, "Episode": int(0)  } )
  xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(str(video_url), listitem)
  xbmc.sleep(200)

def get_params():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
                          
  return param

params = get_params()
url = None
name = None
mode = None
page = 1
plot = None
genre = None
episode = None

try:
  url = urllib.unquote_plus(params["url"])
except:
  pass
try:
  name = urllib.unquote_plus(params["name"])
except:
  pass
try:
  mode = int(params["mode"])
except:
  pass
try:
  page = int(params["page"])
except:
  pass
try:
  plot = urllib.unquote_plus(params["plot"])
except:
  pass
try:
  genre = urllib.unquote_plus(params["genre"])
except:
  pass
try:
  episode = int(params["episode"])
except:
  pass

if mode == None:
  build_main_directory()
elif mode == 1:
  build_episodes_directory()
elif mode == 2:
  play_video(url)

try:
  xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
except:
  pass
try:
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
  pass
