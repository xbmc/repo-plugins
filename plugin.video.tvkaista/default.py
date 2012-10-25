#xbmc tvkaista.fi plugin
#
#Copyright (C) 2009-2012  Viljo Viitanen <viljo.viitanen@iki.fi>
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
#5.12.2010 varasto pois, elokuva-haku etusivulle, alpha->www, tekstitys pois
#5.12.2010 lisays ja poisto katselulistalta ja sarjoista - kiitos Markku Lamminluoto!
#7.1.2011 tuki tvkaistan proxyille
#11.8.2011 naytetaan aika aina Suomen ajassa
#13.11.2011 proxytuki pois tarpeettomana, sarjojen sorttaus
#24.11.2012 bugikorjaus, lisatty oma user-agent tvkaistan dokumentaation mukaan
#           fiksumpi virheilmoitus vaarasta kayttajatunnuksesta/salasanasta

import locale
locale.setlocale(locale.LC_ALL, 'C')

import xbmcgui, urllib, urllib2, cookielib , re, os, xbmcplugin, htmlentitydefs, time, xbmcaddon, calendar
tvkaista_addon = xbmcaddon.Addon("plugin.video.tvkaista");

VERSION = "2.2.3"
MYHEADERS = { 'User-Agent': "tvkaista-xbmc version "+VERSION+";" }

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( tvkaista_addon.getAddonInfo('path'), "resources" ) )
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
  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.fi/feed/channels/')+"&mode=1"
  listfolder = xbmcgui.ListItem('Kanavat - tanaan')
  listfolder.setInfo('video', {'Title': "Kanavat"})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.fi/feed/seasonpasses/')+"&mode=1"
  listfolder = xbmcgui.ListItem('Sarjat')
  listfolder.setInfo('video', {'Title': "Sarjat"})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.fi/feed/playlist')+"&mode=2"
  listfolder = xbmcgui.ListItem('Lista')
  listfolder.setInfo('video', {'Title': 'Lista'})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  
  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.fi/feed/search/title/elokuva')+"&mode=2"
  listfolder = xbmcgui.ListItem('Elokuvat')
  listfolder.setInfo('video', {'Title': 'Elokuvat'})
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

#onko gmt-aikaleima kesaajassa
def isdst(tt):
  dates = {
    2011 : [27,30],
    2012 : [25,28],
    2013 : [31,27],
    2014 : [30,26],
    2015 : [29,25],
    2016 : [27,30],
    2017 : [26,29],
    2018 : [25,28],
    2019 : [31,27],
  }
  t=time.gmtime(tt)
  if t[1] > 3 and t[1]<10:
    return True
  if t[1] < 3 or t[1]>10:
    return False
  if t[1] == 3:
    if t[2] < dates[t[0]][0]:
      return False
    if t[2] == dates[t[0]][0]:
      if t[3] == 0:
        return False
    return True
  if t[1] == 10:
    if t[2] < dates[t[0]][1]:
      return True
    if t[2] == dates[t[0]][1]:
      if t[3] == 0:
        return True
    return False

#Listaa feedin sisaltamat ohjelmat
def listprograms(url):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://www.tvkaista.fi", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  #print "listprograms avataan: "+url+'/'+bitrate()+'.rss'
  try:
      if url.endswith('/'):
        needslash=''
      else:
        needslash='/'
      request = urllib2.Request(url+needslash+bitrate()+'.rss', headers=MYHEADERS)
      content = opener.open(request).read()
  except urllib2.HTTPError,e:
    if e.code == 401:
      desc=" (virheellinen kayttajatunnus tai salasana)"
    else:
      desc=""
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem('www-pyynto ei onnistunut '+str(e.code)+desc)
    listfolder.setInfo('video', {'Title': 'www-pyynto ei onnistunut '+str(e.code)+desc})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=0)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return
  dom = minidom.parseString(content)

#  try:
  items = dom.getElementsByTagName('item')
  ret = []
  myusername=urllib.quote(tvkaista_addon.getSetting("username"))
  mypassword=urllib.quote(tvkaista_addon.getSetting("password"))
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
    tt=calendar.timegm(time.strptime(pdat,"%a, %d %b %Y %H:%M:%S +0000"))
    if (isdst(tt)):
      timediff=10800
    else:
      timediff=7200
    t=time.gmtime(tt+timediff)

    urlii = 'http://%s:%s@%s' % (\
            myusername, mypassword, pat[0])
    nimike = '%s | %s >>> %s (%s)' % (time.strftime("%H:%M",t),ptit,shortdes,pcha)

    listitem = xbmcgui.ListItem(label=nimike, iconImage="DefaultVideo.png")
    try:
      if pat[0] != "":
        pid=re.compile(r"/([0-9]+)[.].+$", re.IGNORECASE).findall(pat[0])
        listitem.setThumbnailImage('http://%s:%s@www.tvkaista.fi/feed/thumbnails/%s.jpg' % (\
            myusername, mypassword, pid[0]))
        if url.find('/feed/playlist') > 0:
          label='Poista Listalta'
          mode=9
        else:
          label='Lisaa Listalle'
          mode=8
        if url.find('/feed/seasonpasses/') > 0:
          se = re.compile(r"/feed/seasonpasses/([0-9]+)", re.IGNORECASE).findall(url)
          label2='Poista Sarjoista'
          mode2=11
          id2=se[0]
        else:
          label2='Lisaa Sarjoihin'
          mode2=10
          id2=pid[0]
        listitem.addContextMenuItems([
            ('Ohjelman tiedot','XBMC.Action(Info)',),
            (label,"XBMC.RunPlugin(%s?mode=%d&url=%s)"%(sys.argv[0],mode,pid[0] ),),
            (label2,"XBMC.RunPlugin(%s?mode=%d&url=%s)"%(sys.argv[0],mode2,id2 ),
            )], True )
    except:
      pass
    listitem.setInfo('video', {'title': nimike, 'plot': pdes, 
                               'date': time.strftime("%d.%m.%Y",t), })
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=urlii,listitem=listitem)
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
  passman.add_password(None, "http://www.tvkaista.fi", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  #print "listdates avataan: "+url
  try:
      request = urllib2.Request('http://www.tvkaista.fi/feed/channels/', headers=MYHEADERS)
      content = opener.open(request).read()
  except urllib2.HTTPError,e:
    if e.code == 401:
      desc=" (virheellinen kayttajatunnus tai salasana)"
    else:
      desc=""
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem('www-pyynto ei onnistunut '+str(e.code)+desc)
    listfolder.setInfo('video', {'Title': 'www-pyynto ei onnistunut '+str(e.code)+desc})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
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
  passman.add_password(None, "http://www.tvkaista.fi", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  #print "listfeeds avataan: "+url
  try:
      request = urllib2.Request(url, headers=MYHEADERS)
      content = opener.open(request).read()
  except urllib2.HTTPError,e:
    if e.code == 401:
      desc=" (virheellinen kayttajatunnus tai salasana)"
    else:
      desc=""
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem('www-pyynto ei onnistunut '+str(e.code)+desc)
    listfolder.setInfo('video', {'Title': 'www-pyynto ei onnistunut '+str(e.code)+desc})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return
#  try:
  dom = minidom.parseString(content)
  items = dom.getElementsByTagName('item')
  if "/feed/seasonpasses" in url:
    items.sort(key=lambda i: i.getElementsByTagName('title')[0].childNodes[0].nodeValue)
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
    url = 'http://www.tvkaista.fi/feed/search/title/%s' % (urllib.quote_plus(keyboard.getText()))
    listprograms(url)

def listsearches():
  u=sys.argv[0]+"?url=Haku&mode=3"
  listfolder = xbmcgui.ListItem('Uusi haku')
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  for i in tvkaista_addon.getSetting("searches").splitlines():
    u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.fi/feed/search/title/'+urllib.quote_plus(i))+"&mode=2"
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
    dialog.ok('Tvkaista', 'Viimeiset haut poistettu.')

def addremove(action,id):
  opts = {'action': 'login', 'username': tvkaista_addon.getSetting("username"), \
          'password': tvkaista_addon.getSetting("password"), 'rememberme':'on'}
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  request = urllib2.Request('http://www.tvkaista.fi/login/', headers=MYHEADERS)
  r = opener.open(request, urllib.urlencode(opts))
  dialog = xbmcgui.Dialog()
  try:
    if action==1:
      request = urllib2.Request("http://www.tvkaista.fi/recordings/?action=addtoplaylist&id=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', 'Ohjelma lisatty listalle.')
    elif action==2:
      request = urllib2.Request("http://www.tvkaista.fi/recordings/?action=removefromplaylist&id=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', 'Ohjelma poistettu listalta.')
    elif action==3:
      request = urllib2.Request("http://www.tvkaista.fi/recordings/?action=addseasonpass&id=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', 'Ohjelma lisatty sarjoihin')
    elif action==4:
      request = urllib2.Request("http://www.tvkaista.fi/recordings/?action=removeseasonpass&spid=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', 'Ohjelma poistettu sarjoista.')
    else:
      dialog.ok('Tvkaista', 'Ohjelmavirhe!')
  except Error:
      dialog.ok('Tvkaista', 'Toiminto ei onnistunut!')

#main program

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
elif mode==8:
        addremove(1,url)
elif mode==9:
        addremove(2,url)
elif mode==10:
        addremove(3,url)
elif mode==11:
        addremove(4,url)

