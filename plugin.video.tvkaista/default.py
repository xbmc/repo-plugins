#xbmc tvkaista.com plugin
# This Python file uses the following encoding: utf-8
#
#Copyright (C) 2009-2014  Viljo Viitanen <viljo.viitanen@iki.fi>
#Copyright (C) 2014       grinsted
#Copyright (C) 2014       sampov2
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
#24.10.2012 bugikorjaus, lisatty oma user-agent tvkaistan dokumentaation mukaan
#           fiksumpi virheilmoitus vaarasta kayttajatunnuksesta/salasanasta
#7.4.2013 Version 4.0.0. Add "search similar named" to context menu.
#         Add proper umlauts. Change code documentation to English.
#8.4.2013 Add support for new tvkaista 1M mpeg4 stream
#15.9.2013 Version 4.0.1, bugfix with username+password quoting
#31.3.2014 Version 4.0.2, change from tvkaista.fi to tvkaista.com
#26.6.2014 Changed search to searching both title and description all the time.
#27.6.2014 Version 4.1.0, Changed hardcoded strings to translated ones

#tvkaista api documentation is at https://code.google.com/p/tvkaista-api/

import locale
locale.setlocale(locale.LC_ALL, 'C')

import xbmcgui, urllib, urllib2, cookielib , re, os, xbmcplugin, htmlentitydefs, time, xbmcaddon, calendar
tvkaista_addon = xbmcaddon.Addon("plugin.video.tvkaista");
language = tvkaista_addon.getLocalizedString

VERSION = "4.1.0"
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
      return "mpeg4"

#display settings if username and password are not set
def settings():
  if tvkaista_addon.getSetting("username") != '' and tvkaista_addon.getSetting("password") != '':
    menu()
  else:
    u=sys.argv[0]+"?url=Asetukset&mode=4"
    listfolder = xbmcgui.ListItem('-- '+language(30201)+' --') #Asetuksia ei määritelty tai niissa on ongelma. Tarkista asetukset.
    listfolder.setInfo('video', {'Title': language(30201)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    u=sys.argv[0]+"?url=Asetukset&mode=4"
    listfolder = xbmcgui.ListItem(language(30101)) #asetukset
    listfolder.setInfo('video', {'Title': language(30101)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

# paavalikko
def menu():
  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.com/feed/channels/')+"&mode=1"
  listfolder = xbmcgui.ListItem(language(30102)) #'Kanavat - tänään'
  listfolder.setInfo('video', {'Title': language(30102)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.com/feed/seasonpasses/')+"&mode=1"
  listfolder = xbmcgui.ListItem(language(30103)) #sarjat
  listfolder.setInfo('video', {'Title': language(30103)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.com/feed/playlist')+"&mode=2"
  listfolder = xbmcgui.ListItem(language(30104)) #lista
  listfolder.setInfo('video', {'Title': language(30104)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.com/feed/search/title/elokuva')+"&mode=2"
  listfolder = xbmcgui.ListItem(language(30105)) #elokuvat
  listfolder.setInfo('video', {'Title': language(30105)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url=Haku&mode=6"
  listfolder = xbmcgui.ListItem(language(30106)) #haku
  listfolder.setInfo('video', {'Title': language(6)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?url=Asetukset&mode=4"
  listfolder = xbmcgui.ListItem(language(30101)) #asetukset
  listfolder.setInfo('video', {'Title': language(30101)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  vko=language(30107).split(',') #"maanantai,tiistai,..."
  t=time.time()
  for i in range(1,29):
    tt=time.localtime(t-86400*i)
    title='%s %s' % (vko[tt[6]], (time.strftime("%d.%m",tt)))
    listfolder = xbmcgui.ListItem(title)
    u=sys.argv[0]+"?url=%d/%d/%d/&mode=5" % (tt[0],tt[1],tt[2])
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

# parse parameters when plugin is run
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

#is gmt timestamp in Finnish DST
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

#list the programs in a feed
def listprograms(url):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://www.tvkaista.com", tvkaista_addon.getSetting("username"), \
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
      desc=" ("+language(30202)+")" #virheellinen käyttäjätunnus tai salasana)"
    else:
      desc=""
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem(language(30203)+' '+str(e.code)+desc) #www-pyyntö ei onnistunut
    listfolder.setInfo('video', {'Title': language(30203)+' '+str(e.code)+desc})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=0)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return
  dom = minidom.parseString(content)

#  try:
  items = dom.getElementsByTagName('item')
  ret = []
  myusername=urllib.quote_plus(tvkaista_addon.getSetting("username"))
  mypassword=urllib.quote_plus(tvkaista_addon.getSetting("password"))
  for i in items:
    try:
      ptit=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
    except:
      ptit="?"
    #print "in "+ptit.encode("utf-8")
    try:
      pdes=i.getElementsByTagName('description')[0].childNodes[0].nodeValue
    except:
      pdes=""
    pdat=i.getElementsByTagName('pubDate')[0].childNodes[0].nodeValue
    pcha=i.getElementsByTagName('source')[0].childNodes[0].nodeValue
    try:
      purl=i.getElementsByTagName('enclosure')[0].attributes['url'].value
      #print "   purl: "+purl.encode("utf-8")
      pat = re.compile(r"^http://(.*)", re.IGNORECASE).findall(purl)
    except:
      pat=[]
      pat.append("")
      ptit=ptit+" "+language(30204) #-TALLENNE PUUTTUU-
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
#        listitem.setThumbnailImage('http://%s:%s@www.tvkaista.com/feed/thumbnails/%s.jpg' % (\
#            myusername, mypassword, pid[0]))
        listitem.setThumbnailImage('http://%s:%s@www.tvkaista.com/resources/recordings/screengrabs/%s.jpg' % (\
            myusername, mypassword, pid[0]))
        if url.find('/feed/playlist') > 0:
          label=language(30109) #'Poista Listalta'
          mode=9
        else:
          label=language(30108) #'Lisää Listalle'
          mode=8
        if url.find('/feed/seasonpasses/') > 0:
          se = re.compile(r"/feed/seasonpasses/([0-9]+)", re.IGNORECASE).findall(url)
          label2=language(30111) #'Poista Sarjoista'
          mode2=11
          id2=se[0]
        else:
          label2=language(30110) #'Lisää Sarjoihin'
          mode2=10
          id2=pid[0]
        menuitems=[
            (language(30116),'XBMC.Action(Info)',), #Ohjelman tiedot
            (label,"XBMC.RunPlugin(%s?mode=%d&url=%s)"%(sys.argv[0],mode,pid[0] ),),
            (label2,"XBMC.RunPlugin(%s?mode=%d&url=%s)"%(sys.argv[0],mode2,id2 ),),
        ]
        if url.find('/feed/search') == -1 and url.find('/feed/seasonpasses/') == -1:
          search=ptit.split(':')[0].encode('utf-8')
          #double encoding cos it gets decoded twice.
          menuitems.append((language(30117),'XBMC.Container.Update(%s?mode=%d&url=%s)'% #Etsi samannimisiä
            (sys.argv[0],2,'http://www.tvkaista.com/feed/search/title/'+urllib.quote_plus(urllib.quote_plus(search)) ),))
        listitem.addContextMenuItems(menuitems, True )
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

#get channel list, add archive date in the fetched url.
#note: the date parameter really is called url when specifying the plugin url parameters. See mode 5 in main.
def listdates(date):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://www.tvkaista.com", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  #print "listdates avataan: "+date
  try:
      request = urllib2.Request('http://www.tvkaista.com/feed/channels/', headers=MYHEADERS)
      content = opener.open(request).read()
  except urllib2.HTTPError,e:
    if e.code == 401:
      desc=" ("+language(30202)+")" #virheellinen käyttäjätunnus tai salasana
    else:
      desc=""
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem(' '+language(30203)+str(e.code)+desc) #www-pyyntö ei onnistunut
    listfolder.setInfo('video', {'Title': language(30203)+' '+str(e.code)+desc})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return
#  try:
  dom = minidom.parseString(content)
  items = dom.getElementsByTagName('item')
  ret = []
  for i in items:
    try:
      ptit=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
    except:
      ptit="?"
    plin=i.getElementsByTagName('link')[0].childNodes[0].nodeValue
    datelink=re.sub(r'/feed/','/feed/archives/'+date,plin)
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

# list feeds contained in a feed
def listfeeds(url):
  passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
  passman.add_password(None, "http://www.tvkaista.com", tvkaista_addon.getSetting("username"), \
                         tvkaista_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman))
  #print "listfeeds avataan: "+url
  try:
      request = urllib2.Request(url, headers=MYHEADERS)
      content = opener.open(request).read()
  except urllib2.HTTPError,e:
    if e.code == 401:
      desc=" ("+language(30202)+")" #virheellinen käyttäjätunnus tai salasana
    else:
      desc=""
    u=sys.argv[0]
    listfolder = xbmcgui.ListItem(language(30203)+' '+str(e.code)+desc)  #www-pyyntö ei onnistunut
    listfolder.setInfo('video', {'Title': language(30203)+' '+str(e.code)+desc})
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
    try:
      ptit=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
    except:
      ptit="?"
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

# displays the virtual keyboard and lists search results
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
    url = 'http://www.tvkaista.com/feed/search/either/%s' % (urllib.quote_plus(keyboard.getText()))
    listprograms(url)

#list searches that are stored in plugin settings
def listsearches():
  u=sys.argv[0]+"?url=Haku&mode=3"
  listfolder = xbmcgui.ListItem(language(30118)) #'Uusi haku'
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  for i in tvkaista_addon.getSetting("searches").splitlines():
    u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.tvkaista.com/feed/search/either/'+urllib.quote_plus(i))+"&mode=2"
    listfolder = xbmcgui.ListItem(language(30106)+': '+i) #haku
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  if(tvkaista_addon.getSetting("searches") != ""):
    u=sys.argv[0]+"?url=Haku&mode=7"
    listfolder = xbmcgui.ListItem(language(30119)) #'Poista viimeiset haut'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

#delete stored searches
def delsearches():
  dialog = xbmcgui.Dialog()
  if(dialog.yesno('Tvkaista', language(30120))): #'Poistetaanko viimeiset haut?'
    tvkaista_addon.setSetting("searches","")
    dialog.ok('Tvkaista', language(30121)) #'Viimeiset haut poistettu.'

#adds/removes programs to/from playlist and seasonpasses
#TODO: convert to tvkaista supported api instead of the current hack
def addremove(action,id):
  opts = {'action': 'login', 'username': tvkaista_addon.getSetting("username"), \
          'password': tvkaista_addon.getSetting("password"), 'rememberme':'on'}
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  request = urllib2.Request('http://www.tvkaista.com/login/', headers=MYHEADERS)
  r = opener.open(request, urllib.urlencode(opts))
  dialog = xbmcgui.Dialog()
  try:
    if action==1:
      request = urllib2.Request("http://www.tvkaista.com/recordings/?action=addtoplaylist&id=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', language(30112)) #'Ohjelma lisätty listalle.'
    elif action==2:
      request = urllib2.Request("http://www.tvkaista.com/recordings/?action=removefromplaylist&id=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', language(30113)) #'Ohjelma poistettu listalta.'
    elif action==3:
      request = urllib2.Request("http://www.tvkaista.com/recordings/?action=addseasonpass&id=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', language(30114)) #Ohjelma lisätty sarjoihin
    elif action==4:
      request = urllib2.Request("http://www.tvkaista.com/recordings/?action=removeseasonpass&spid=%s"%id, headers=MYHEADERS)
      r = opener.open(request)
      dialog.ok('Tvkaista', language(30115)) #'Ohjelma poistettu sarjoista.'
    else:
      dialog.ok('Tvkaista', language(30205)) #'Ohjelmavirhe!'
  except Error:
      dialog.ok('Tvkaista', language(30206)) #'Toiminto ei onnistunut!'

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
