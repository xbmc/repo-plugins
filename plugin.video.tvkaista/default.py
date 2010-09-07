#xbmc alpha tvkaista plugin
#
#Copyright (C) 2009-2010  Viljo Viitanen <viljo.viitanen@iki.fi>
#Copyright (C) 2010       stilester
#Copyright (C) 2008-2009  J. Luukko
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#muutoshistoria:
#19.12.2009 ensimmainen versio
#20.12.2009 aikaeron laskeminen bugasi, korjattu
#5.1.2010 ohjelmien sijainti oli kovakoodattu alpha.tvkaista.fi:n, feedien muuttuessa
#bugasi, korjattu
#10.2.2010 paljon muutoksia, lisatty tekstitystuki, thumbnailit, paivamaaravalikko
#6.9.2010 tuki XBMC Dharma beta 1:lle - kiitos stilester!
#7.9.2010 fiksauksia xbmc:n official repoa varten, linux-locale-ongelma fiksattu

import locale
locale.setlocale(locale.LC_ALL, 'C')

import xbmcgui, urllib, urllib2 , re, os, xbmcplugin, htmlentitydefs, time, xbmcaddon
tvkaista_addon = xbmcaddon.Addon("plugin.video.tvkaista");

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( os.getcwd(), "resources" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

from string import split, replace, find
from xml.dom import minidom

def bitrate():
    if tvkaista_addon.getSetting("bitrate") == "0":
      return "mp4"
    elif tvkaista_addon.getSetting("bitrate") == "2":
      return "h264"
    elif tvkaista_addon.getSetting("bitrate") == "3":
      return "ts"
    else:
      return "flv"

#varmistetaan asetukset
def settings():
  if tvkaista_addon.getSetting("username") != '' and tvkaista_addon.getSetting("password") != '':
    menu()
  else:
    u=sys.argv[0]+"?url=Asetukset&mode=4"
    listfolder = xbmcgui.ListItem('-- Asetuksia ei maaritelty tai niissa on ongelma. Tarkista asetukset. --')
    listfolder.setInfo('video', {'Title': 'Asetuksia ei maaritelty tai niissa on ongelma. Tarkista asetukset.'})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    u=sys.argv[0]+"?url=Asetukset&mode=4"
    listfolder = xbmcgui.ListItem('Asetukset')
    listfolder.setInfo('video', {'Title': 'Asetukset'})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

# paavalikko
def menu():
  u=sys.argv[0]+"?url="+urllib.quote_plus('http://alpha.tvkaista.fi/feed/channels/')+"&mode=1"
  listfolder = xbmcgui.ListItem('Kanavat - tanaan')
  listfolder.setInfo('video', {'Title': "Kanavat"})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://alpha.tvkaista.fi/feed/seasonpasses/')+"&mode=1"
  listfolder = xbmcgui.ListItem('Sarjat')
  listfolder.setInfo('video', {'Title': "Sarjat"})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://alpha.tvkaista.fi/feed/playlist')+"&mode=2"
  listfolder = xbmcgui.ListItem('Lista')
  listfolder.setInfo('video', {'Title': 'Lista'})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://alpha.tvkaista.fi/feed/storage')+"&mode=2"
  listfolder = xbmcgui.ListItem('Varasto')
  listfolder.setInfo('video', {'Title': 'Varasto'})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url=Haku&mode=6"
  listfolder = xbmcgui.ListItem('Haku')
  listfolder.setInfo('video', {'Title': 'Haku'})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url=Asetukset&mode=4"
  listfolder = xbmcgui.ListItem('Asetukset')
  listfolder.setInfo('video', {'Title': 'Asetukset'})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  vko=['Maanantai','Tiistai','Keskiviikko','Torstai','Perjantai','Lauantai','Sunnuntai']
  t=time.time()
  for i in range(1,29):
    tt=time.localtime(t-86400*i)
    title='%s %s' % (vko[tt[6]], (time.strftime("%d.%m",tt)))
    listfolder = xbmcgui.ListItem(title)
    u=sys.argv[0]+"?url=%d/%d/%d/&mode=5" % (tt[0],tt[1],tt[2])
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

# Parsee kaynnistysparametrit kun skriptaa suoritetaan uudelleen
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

#Listaa feedin sisaltamat ohjelmat
def listprograms(url):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://alpha.tvkaista.fi", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  urllib2.install_opener(opener)
  print "listprograms avataan: "+url+'/'+bitrate()+'.rss'
  try:
      content = urllib2.urlopen(url+'/'+bitrate()+'.rss').read()
  except urllib2.HTTPError,e:
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem('www-pyynto ei onnistunut '+str(e.code))
    listfolder.setInfo('video', {'Title': 'www-pyynto ei onnistunut '+str(e.code)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=0)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return
  dom = minidom.parseString(content)
  try:
    #haetaan aikaero GMT->lokaaliaika. Oletetaan, etta xbmc:n/pythonin aika on oikea lokaaliaika...
    otherdate=dom.getElementsByTagName('channel')[0].getElementsByTagName('lastBuildDate')[0].childNodes[0].nodeValue
    timediff=time.time()-time.mktime(time.strptime(otherdate,"%a, %d %b %Y %H:%M:%S +0000"))
  except:
    timediff=0

#  try:
  items = dom.getElementsByTagName('item')
  ret = []
  for i in items:
    ptit=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
#    print "in "+ptit.encode("utf-8")
    try:
      pdes=i.getElementsByTagName('description')[0].childNodes[0].nodeValue
    except:
      pdes=""
    pdat=i.getElementsByTagName('pubDate')[0].childNodes[0].nodeValue
    pcha=i.getElementsByTagName('source')[0].childNodes[0].nodeValue
    try:
      purl=i.getElementsByTagName('enclosure')[0].attributes['url'].value
      pat = re.compile(r"^http://(.*)", re.IGNORECASE).findall(purl)
    except:
      pat=[]
      pat.append("")
      ptit=ptit+" -TALLENNE PUUTTUU-"
    if len(pdes)>80:
      shortdes=pdes[:80]+'...'
    else:
      shortdes=pdes
    t=time.localtime(timediff+time.mktime(time.strptime(pdat,"%a, %d %b %Y %H:%M:%S +0000")))
    urlii = 'http://%s:%s@%s' % (\
            urllib.quote(tvkaista_addon.getSetting("username")), \
            urllib.quote(tvkaista_addon.getSetting("password")), pat[0])
    nimike = '%s | %s >>> %s (%s)' % (time.strftime("%H:%M",t),ptit,shortdes,pcha)

    listitem = xbmcgui.ListItem(label=nimike, iconImage="DefaultVideo.png")
    try:
      if pat[0] != "":
        pid=re.compile(r"/([0-9]+)[.].+$", re.IGNORECASE).findall(pat[0])
        listitem.setThumbnailImage('http://%s:%s@alpha.tvkaista.fi/feed/thumbnails/%s.jpg' % (\
            urllib.quote(tvkaista_addon.getSetting("username")), \
            urllib.quote(tvkaista_addon.getSetting("password")), pid[0]))
    except:
      pass
    listitem.setInfo('video', {'title': nimike, 'plot': pdes, 
                               'date': time.strftime("%d.%m.%Y",t), })
    u=sys.argv[0]+"?url="+urllib.quote_plus(urlii)+"&mode=0&title="+urllib.quote_plus(nimike.encode('latin1'))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=listitem)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
#  except:
#    u=sys.argv[0]
#    listfolder = xbmcgui.ListItem('www-pyynnon sisallon tulkitseminen ei onnistunut')
#    listfolder.setInfo('video', {'Title': 'www-pyynnon sisallon tulkitseminen ei onnistunut'})
#    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  dom.unlink()
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

#haetaan kanavalista, ujutetaan feed-urleihin archive-paivamaara, joka tulee url-parametrina
def listdates(url):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://alpha.tvkaista.fi", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  urllib2.install_opener(opener)
  #print "listfeeds avataan: "+url
  try:
      content = urllib2.urlopen('http://alpha.tvkaista.fi/feed/channels/').read()
  except urllib2.HTTPError,e:
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem('www-pyynto ei onnistunut '+str(e.code))
    listfolder.setInfo('video', {'Title': 'www-pyynto ei onnistunut '+str(e.code)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    return
#  try:
  dom = minidom.parseString(content)
  items = dom.getElementsByTagName('item')
  ret = []
  for i in items:
    ptit=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
    plin=i.getElementsByTagName('link')[0].childNodes[0].nodeValue
    datelink=re.sub(r'/feed/','/feed/archives/'+url,plin)
    #print "plin: " + plin + " datelink: " + datelink
    u=sys.argv[0]+"?url="+urllib.quote_plus(datelink)+"&mode="+"2"
    listfolder = xbmcgui.ListItem(ptit)
    listfolder.setInfo('video', {'Title': ptit})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
#  except:
#    u=sys.argv[0]
#    listfolder = xbmcgui.ListItem('www-pyynnon sisallon tulkitseminen ei onnistunut')
#    listfolder.setInfo('video', {'Title': 'www-pyynnon sisallon tulkitseminen ei onnistunut'})
#    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  dom.unlink()
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

# Listaa feedin sisaltamat feedit
def listfeeds(url):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://alpha.tvkaista.fi", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  urllib2.install_opener(opener)
  #print "listfeeds avataan: "+url
  try:
      content = urllib2.urlopen(url).read()
  except urllib2.HTTPError,e:
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem('www-pyynto ei onnistunut '+str(e.code))
    listfolder.setInfo('video', {'Title': 'www-pyynto ei onnistunut '+str(e.code)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    return
#  try:
  dom = minidom.parseString(content)
  items = dom.getElementsByTagName('item')
  ret = []
  for i in items:
    ptit=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
    plin=i.getElementsByTagName('link')[0].childNodes[0].nodeValue
    u=sys.argv[0]+"?url="+urllib.quote_plus(plin)+"&mode="+"2"
    listfolder = xbmcgui.ListItem(ptit)
    listfolder.setInfo('video', {'Title': ptit})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
#  except:
#    u=sys.argv[0]
#    listfolder = xbmcgui.ListItem('www-pyynnon sisallon tulkitseminen ei onnistunut')
#    listfolder.setInfo('video', {'Title': 'www-pyynnon sisallon tulkitseminen ei onnistunut'})
#    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  dom.unlink()
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

# Antaa kayttajalle virtuaalisen nappaimiston ja listaa hakutulokset
def search():
  keyboard = xbmc.Keyboard()
  keyboard.doModal()
  if (keyboard.isConfirmed() and keyboard.getText() != ''):
    list=tvkaista_addon.getSetting("searches").splitlines()
    try:
      list.remove(keyboard.getText())
    except ValueError:
      pass
    if len(list)>20: list.pop()
    list.insert(0,keyboard.getText())
    tvkaista_addon.setSetting("searches","\n".join(list))
    url = 'http://alpha.tvkaista.fi/feed/search/title/%s' % (urllib.quote_plus(keyboard.getText()))
    listprograms(url)

def play(url,title):
  play=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
  play.clear()
  listitem = xbmcgui.ListItem(title)

  play.add(url,listitem)
  player = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
  player.play(play)
  try:
    s=re.sub(r'/([0-9]+)[^/]+$','/\\1.srt',url)
    print "subtitles "+s
    player.setSubtitles(s)
  except:
      pass
  
def listsearches():
  u=sys.argv[0]+"?url=Haku&mode=3"
  listfolder = xbmcgui.ListItem('Uusi haku')
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://alpha.tvkaista.fi/feed/search/title/elokuva')+"&mode=2"
  listfolder = xbmcgui.ListItem('Haku: elokuva')
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  for i in tvkaista_addon.getSetting("searches").splitlines():
    u=sys.argv[0]+"?url="+urllib.quote_plus('http://alpha.tvkaista.fi/feed/search/title/'+urllib.quote_plus(i))+"&mode=2"
    listfolder = xbmcgui.ListItem('Haku: '+i)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  if(tvkaista_addon.getSetting("searches") != ""):
    u=sys.argv[0]+"?url=Haku&mode=7"
    listfolder = xbmcgui.ListItem('Poista viimeiset haut')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
def delsearches():
  dialog = xbmcgui.Dialog()
  if(dialog.yesno('Tvkaista', 'Poistetaanko viimeiset haut?')):
    tvkaista_addon.setSetting("searches","")
    dialog.ok('Tvkaista', 'Viimeiset haut poistettu.','Viimeiset haut kuitenkin nakyvat listassa','kunnes olet poistunut hakutoiminnosta.')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

params=get_params()
url=None
mode=None
try:
        url=urllib.unquote_plus(params["url"])
        title=urllib.unquote_plus(params["title"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
        settings()
        
elif mode==0:
        play(url,title)
elif mode==1:
        listfeeds(url)
elif mode==2:
        listprograms(url)
elif mode==3:
        search()
elif mode==4:
        tvkaista_addon.openSettings(url=sys.argv[0])
elif mode==5:
        listdates(url)
elif mode==6:
        listsearches()
elif mode==7:
        delsearches()

