# -*- coding: utf-8 -*-

""" Sapo Videos
    2015 fightnight
"""

import xbmc,xbmcaddon,xbmcgui,xbmcplugin,urllib,urllib2,os,re,sys
import requests,htmlentitydefs,json

####################################################### CONSTANTES #####################################################

versao = '1.0.0'
addon_id = 'plugin.video.sapo'
MainURL = 'http://videos.sapo.pt/'
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:10.0a1) Gecko/20111029 Firefox/10.0a1'
selfAddon = xbmcaddon.Addon(id=addon_id)
pastaperfil = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
ref_data = {'User-Agent': user_agent}

def menu_principal():
      addDir(translate(30002),MainURL,1,'',1)
      addDir(translate(30003),MainURL + 'ajax/destaques?token=' + file_token() + '&nocache=' + get_random() + '&page=1',6,'',1)
      addDir(translate(30004),MainURL + 'ajax/lives?token=' + file_token() + '&nocache=' + get_random() + '&page=1',6,'',1)
      addDir(translate(30005),MainURL + 'categorias.html',3,'',1)
      addDir(translate(30006),MainURL,4,'',1)

def translate(text):
      return selfAddon.getLocalizedString(text).encode('utf-8')

def pesquisa():
      keyb = xbmc.Keyboard('', translate(30001))
      keyb.doModal()
      if (keyb.isConfirmed()):
            search = keyb.getText()
            if search=='': sys.exit(0)
            encode=urllib.quote(search)
            urlfinal='http://videos.sapo.pt/ajax/search?q='+encode+'&type=videos&token='+file_token()+'&nocache='+get_random()+'&page=1'
            request(urlfinal)

def tops():
      get_token=file_token()
      addDir(translate(30007),MainURL + 'ajax/top?token=' + get_token + '&nocache=' + get_random() + '&page=1&order=day',6,'',1)
      addDir(translate(30008),MainURL + 'ajax/top?token=' + get_token + '&nocache=' + get_random() + '&page=1&order=week',6,'',1)
      addDir(translate(30009),MainURL + 'ajax/top?token=' + get_token + '&nocache=' + get_random() + '&page=1&order=month',6,'',1)
      addDir(translate(30010),MainURL + 'ajax/top?token=' + get_token + '&nocache=' + get_random() + '&page=1&order=all',6,'',1)

def categorias():
      link=abrir_url(url)
      categorias=re.compile('small-40" href=".+?id=(.+?)"><img alt="(.+?)" src="(.+?)" />.+?<span class="vid-count">(.+?)</span>').findall(link)
      for end,nome,thumb,nrvideos in categorias:
            addDir('[B]%s[/B] (%s %s)' % (nome,nrvideos,translate(30011)),MainURL + 'ajax/category/'+end+'?token=' + file_token() + '&nocache=' + get_random() + '&page=1&order=releve',6,thumb,1)
           
def file_token():
      token = selfAddon.getSetting('session_id')
      return token

def get_random():
      from random import randint
      random=str(randint(0, 10000))
      return random

def descape(content):
      content = re.sub('&([^;]+);', lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), content)
      return content.encode('utf-8')
           
def request(url):
      ref_data = {'Accept':'text/javascript,text/xml,application/xml,application/xhtml+xml,text/html,application/json;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,*/*;q=0.1','Cookie':'sv_token=%s;' %(file_token()),'User-Agent':user_agent,'X-Ink-Version':'1','X-Requested-With':'XMLHttpRequest'}
      link = json.loads(abrir_url(url,ref_data))
      if link['success']==True:
            for videos in link['data']:
                  pastastream('[B]%s[/B] (%s %s)' % (descape(videos['title']),videos['views'],translate(30012)),MainURL + videos['randname'],5,'http:%s' % (videos['thumb_url']),len(link),plot=descape(videos['synopse']))
            xbmcplugin.setContent(int(sys.argv[1]), 'livetv')
            if "confluence" in xbmc.getSkinDir(): xbmc.executebuiltin('Container.SetViewMode(560)')

def abrir_url(url,referencia=False):
      if referencia==False: conteudo=requests.get(url).text.encode('latin-1','ignore')
      else: conteudo=requests.get(url,headers=referencia).text.encode('latin-1','ignore')
      return conteudo
            
def captura(name,url):
      link=abrir_url(url)
      thumb=re.compile('<meta property="og:image" content="(.+?)"/>').findall(link)[0]
      username=re.compile("var usermrec='(.+?)'").findall(link)[0]
      if re.search('rtmp://',link):
            chname=url.replace('http://videos.sapo.pt/','')
            filepath=re.compile('/live/(.+?)&').findall(link)[0]
            host=abrir_url('http://videos.sapo.pt/hosts_stream.html')
            hostip=re.compile('<host>(.+?)</host>').findall(host)[0]
            if re.search('playersrc="',link):
                  jslink=re.compile('playersrc="(.+?)"').findall(link)[0]
                  jslink=jslink.split('.js')
                  swf=jslink[0]
                  swf=swf.replace('Video','flash/videojs.swf')
            else: swf='http://imgs.sapo.pt/sapovideo/swf/flvplayer-sapo.swf?v11'
            finalurl='rtmp://' + hostip + '/live' + ' playPath=' + filepath  + ' swfUrl='+swf+' live=true pageUrl=http://videos.sapo.pt/'+chname
      else:
            try:
                  endereco=re.compile('file=(.+?)&').findall(link)[0]
            except:
                  link=abrir_url(url + '/rss2')
                  video=re.compile('<media:content url="(.+?)/pic/').findall(link)[0]
                  endereco = video + '/mov'
            finalurl=redirect(endereco)
      comecarvideo(name,finalurl,username,thumb)


def comecarvideo(titulo,url,username,thumb):
      playlist = xbmc.PlayList(1)
      playlist.clear()
      listitem = xbmcgui.ListItem(titulo, iconImage="DefaultVideo.png", thumbnailImage=thumb)            
      listitem.setInfo("Video", {"Title":titulo, "TVShowTitle": username[0]})
      listitem.setProperty('mimetype', 'video/x-msvideo')
      listitem.setProperty('IsPlayable', 'true')
      playlist.add(url, listitem)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]),True,listitem)
      xbmcPlayer = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
      xbmcPlayer.play(playlist)

################################################## PASTAS ################################################################

def pastastream(name,url,mode,iconimage,total,plot=''):
      u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
      ok=True; liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
      liz.setInfo( type="Video", infoLabels={ "Title": name,"overlay":6 ,"plot":plot} )
      ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False,totalItems=total)
      cm = []
      cm.append(('',''))
      liz.addContextMenuItems(cm, replaceItems=True)                      
      return ok

def addDir(name,url,mode,iconimage,total):
      u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
      ok=True; liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
      liz.setInfo( type="Video", infoLabels={ "Title": name } )
      ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=total)
      return ok

def redirect(url):
      req = urllib2.Request(url)
      req.add_header('User-Agent', user_agent)
      response = urllib2.urlopen(req)
      gurl=response.geturl()
      return gurl

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

params=get_params()
url=None
name=None
mode=None
try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except: pass

if mode==None or url==None or len(url)<1:
      print "Versao Instalada: v" + versao
      
      ## Session Token ID ##
      key=requests.get(MainURL,headers=ref_data)
      token=re.compile('sv_token=(.+?);').findall(key.headers['set-cookie'])[0]
      selfAddon.setSetting('session_id',value=token)
      ######################

      menu_principal()
elif mode==1: tops()
elif mode==2: canais()
elif mode==3: categorias()
elif mode==4: pesquisa()
elif mode==5: captura(name,url)
elif mode==6: request(url)

#plugin://plugin.video.sapo/?mode=5&url=http://videos.sapo.pt/qAUkoLFQegUKv0jDDs33&name=Nomedovideo
  
xbmcplugin.endOfDirectory(int(sys.argv[1]))
