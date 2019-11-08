# -*- coding: utf-8 -*-

'''
 TV3cat Kodi addon
 @author: jqandreu
 @contact: jqsandreu@gmail.com
'''

import os
import sys
import re
import urlparse
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import urllib
import urllib2
import json
import math
import time
from BeautifulSoup import BeautifulSoup
from resources.lib.tv3_strings import TV3Strings
from resources.lib.utils import buildUrl, getHtml, getDataVideo, toSeconds

url_base = 'http://www.ccma.cat'
url_alacarta = 'http://www.ccma.cat/tv3/alacarta/'
url_coleccions = 'http://www.ccma.cat/tv3/alacarta/coleccions/'
url_mesvist = 'http://www.ccma.cat/tv3/alacarta/mes-vist/'
url_datavideos = 'http://dinamics.ccma.cat/pvideo/media.jsp?media=video&version=0s&idint='
url_programes_emisio = 'http://www.ccma.cat/tv3/alacarta/programes'
url_programes_tots = 'http://www.ccma.cat/tv3/alacarta/programes-tots/'
urlZonaZaping = 'http://www.ccma.cat/tv3/alacarta/zona-zaping/'
urlApm = 'http://www.ccma.cat/tv3/alacarta/apm/'
url_directe_tv3 = 'https://directes-tv-es.ccma.cat/es/ngrp:tv3_web/playlist.m3u8'
url_directe_324 = 'https://directes-tv-int.ccma.cat/int/ngrp:324_web/playlist.m3u8'
url_directe_c33s3 = 'https://directes-tv-es.ccma.cat/es/ngrp:c33_web/playlist.m3u8'
url_directe_esport3 = 'https://directes-tv-es.ccma.cat/es/ngrp:es3_web/playlist.m3u8'
#Feeds per a fer streaming des de l'estranger
url_directe_tv3_int = 'https://directes-tv-int.ccma.cat/int/ngrp:tv3_web/playlist.m3u8'
url_directe_324_int = 'https://directes-tv-int.ccma.cat/int/ngrp:324_web/playlist.m3u8'
url_directe_c33s3_int = 'https://directes-tv-int.ccma.cat/int/ngrp:c33_web/playlist.m3u8'
url_directe_esport3_int = 'https://directes-tv-int.ccma.cat/int/ngrp:es3_web/playlist.m3u8'

url_arafem ='http://dinamics.ccma.cat/wsarafem/arafem/tv'


addon = xbmcaddon.Addon()
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
strs = TV3Strings(addon)

def index():
    xbmc.log( "--------------index------------------")
    
    
    addDir(strs.get('avuidestaquem'),"","destaquem","")
    addDir(strs.get('noperdis'), url_coleccions,"noperdis","")
    addDir(strs.get('mesvist'), url_mesvist,"mesvist","")
    addDir(strs.get('coleccions'),"","coleccions","")
    addDir(strs.get('programes'),"","programes","")
    addDir(strs.get('directe'),"","directe","")
    addDir(strs.get('cercar'),"","cercar","")
    
    xbmcplugin.endOfDirectory(addon_handle)
    
    
def listDestaquem():
    xbmc.log("--------------listDestaquem----------")
   
    html_destacats = getHtml(url_alacarta)
    
    if html_destacats:
   
        soup = BeautifulSoup(html_destacats)
        dest = None
        
        
        try:
          
            
            destacats = soup.findAll("article", { "class" : re.compile("M-destacat")})
            
            destacats2 = soup.find("div", {"class" : "container C-nouGrid "}).findAll("div", { "class" : re.compile("swiper-slide")})
            
     
           
            destacats.extend(destacats2)
            
            
            for c in destacats:
                a = c.a["href"]
                code = a[-8:-1]
            
                xbmc.log( "--------CODIS VIDEOS------------")
                xbmc.log( "codi: " + code)
                xbmc.log( "url: " + url_datavideos + code + '&profile=pc')
        
                html_data = getHtml(url_datavideos + code + '&profile=pc')
            
                html_data = html_data.decode("ISO-8859-1")
                data =json.loads(html_data)
            
                if len(data) > 0:
                    addVideo2(data)
        except AttributeError as e:
            xbmc.log("Exception AtributeError Altres items: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError Altres items: " + str(e))
        except Exception as e:
            xbmc.log("Exception Item destacat: " + str(e))
            
    
       
        xbmcplugin.endOfDirectory(addon_handle)
    
def listDestaquem2():
    xbmc.log("--------------listDestaquem----------")
    
    titol = ""
    url = ""
    durada = ""
    programa = ""
    img = ""
    data = ""
    resum = ""
   
    html_destacats = getHtml(url_alacarta)
    
    if html_destacats:
    
        soup = BeautifulSoup(html_destacats.decode('utf-8','ignore'))
        
        try:
            destacat = soup.find("section", {"class" : "subitem destacat"})
            titol = destacat.a["title"]
            url = destacat.a["href"]
            durada = toSeconds(destacat.find("time", {"class" : "duration"}).string)
            programa = destacat.find("div", {"class" : "R-titular"}).small.string
            img = destacat.img["src"]
            
            
            addVideo(titol, url, img, durada, programa, data, resum)
            
          
           
        except AttributeError as e:
            xbmc.log("Exception AtributeError Item destacat: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError Item destacat: " + str(e))
        except Exception as e:
            xbmc.log("Exception Item destacat: " + str(e))
            
            
        titol = ""
        url = ""
        durada = ""
        programa = ""
        img = ""
        data = ""
        resum = ""
       
        
        try:
            destacatsPetits = soup.findAll("section", { "class" : "subitem R-petit"})
            xbmc.log("Destacats petits trobats: " + str(len(destacatsPetits)))
            
        except AttributeError as e:
            xbmc.log("Exception AtributeError Altres items: " + str(e))
            
        except KeyError as e:
            xbmc.log("Exception KeyError Altres items: " + str(e))
            
        except Exception as e:
            xbmc.log("Exception Item destacat: " + str(e))
           
            
            
        for d in destacatsPetits:
            
            try:     
            
                titol = d.a["title"]
                url = d.a["href"]
                durada = toSeconds(d.find("time", {"class" : "duration"}).string)
                programa = d.find("div", {"class" : "R-titular"}).small.string
                img = d.img["src"]
                
               
                addVideo(titol, url, img, durada, programa, data, resum)
            
            except AttributeError as e:
                xbmc.log("Exception AtributeError Altres items: " + str(e))
               
            except KeyError as e:
                xbmc.log("Exception KeyError Altres items: " + str(e))
                
            except Exception as e:
                xbmc.log("Exception Item destacat: " + str(e))
                
           
        
       
        xbmcplugin.endOfDirectory(addon_handle)
        
        

def listNoPerdis():
    xbmc.log("--------------listNoPerdis----------")
    
    link = getHtml(url_coleccions)
    
    if link:
 
        soup = BeautifulSoup(link)
        
        try: 
            links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo"})
            
            if not links:
                links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo "})
                
            if not links:
                links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo  "})
        
            for i in links:
                a = i.a["href"]
                code = a[-8:-1]
                
                link = getHtml(url_datavideos + code + '&profile=pc')
                
                link = link.decode("ISO-8859-1")
                data =json.loads(link)
                
                if len(data) > 0:
                    addVideo2(data)
        except AttributeError as e:
            xbmc.log("Exception AtributeError NoPerdis: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError NoPerdis: " + str(e))
        except Exception as e:
            xbmc.log("Exception Item destacat: " + str(e))
        
       
        xbmcplugin.endOfDirectory(addon_handle)   
    
    
    
def listNoPerdis2(url):
    xbmc.log("--------------listNoPerdis----------")
    
    
    titol = ""
    urlVideo = ""
    durada = ""
    programa = ""
    img = ""
    data = ""
    resum = ""
    
    link = getHtml(url)
    
    if link:
 
        soup = BeautifulSoup(link.decode('utf-8','ignore'))
        
        try: 
            links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo"})
            
            
        except AttributeError as e:
            xbmc.log("Exception AtributeError NoPerdis: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError NoPerdis: " + str(e))
        except Exception as e:
            xbmc.log("Exception Item destacat: " + str(e))  
            
              
        for d in links:
            
            try:
            
                titol = d.find("div", {"class" : "titol"}).a.string.strip()
                urlVideo = d.a["href"]
                durada = toSeconds(d.find("time", {"class" : "duration"}).string)
                programa = d.find("div", {"class" : "infoNoticia"}).small.string
                img = d.img["src"]
                
                xbmc.log("DestPe - titol: " + titol.encode("utf-8"))
                xbmc.log("Url: " + url)
                xbmc.log("Img: " + img  )
                
                addVideo(titol, urlVideo, img, durada, programa, data, resum)
                
            except AttributeError as e:
                xbmc.log("Exception AtributeError NoPerdis: " + str(e))
            except KeyError as e:
                xbmc.log("Exception KeyError NoPerdis: " + str(e))
            except Exception as e:
                xbmc.log("Exception Item destacat: " + str(e))
            
       
        
        xbmcplugin.endOfDirectory(addon_handle) 
        


def listMesVist():
    xbmc.log("--------------listMesVist----------")
   
    link = getHtml(url_mesvist)
    
    if link:
  
        soup = BeautifulSoup(link)
        
        try: 
            links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo"})
            
            if not links:
                links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo "})
                
            if not links:
                links = soup.findAll("li", {"class" : "sensePunt R-elementLlistat  C-llistatVideo  "})
            
            for i in links:
                a = i.a["href"]
                code = a[-8:-1]
                
                link = getHtml(url_datavideos + code + '&profile=pc')
                
                link = link.decode("ISO-8859-1")
                data =json.loads(link)
                
                if len(data) > 0:
                    addVideo2(data)
        except AttributeError as e:
            xbmc.log("Exception AtributeError listMesVist: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError listMesVist: " + str(e))
        except Exception as e:
            xbmc.log("Exception listMesVist: " + str(e))
            
      
        xbmcplugin.endOfDirectory(addon_handle)
    
    
    
def listColeccions():
    xbmc.log("--------------listColeccions----------")
    
    link = getHtml(url_coleccions)
    
    if link:
    
        soup = BeautifulSoup(link)
        
        try: 
            
            colecc = soup.findAll("a", {"class" : "media-object"})
            xbmc.log("Col·leccions - elements trobats: " + str(len(colecc)))
            
            for a in colecc:
               
                url = a["href"]
                url = url_base + url
                t = a["title"]
                titol = t.encode("utf-8")
                xbmc.log("Col·leccions -t: " + titol)
                img = a.img["src"]
              
                addDir(titol ,url,'listvideos', img)
                
        except AttributeError as e:
            xbmc.log("Exception AtributeError listColeccions: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError listColeccions: " + str(e))
        except Exception as e:
            xbmc.log("Exception listColeccions: " + str(e))
        
            
        xbmcplugin.endOfDirectory(addon_handle) 
    
def dirSections():
   
    addDir(strs.get('series'),"/series/","sections","")
    addDir(strs.get('informatius'),"/informatius/","sections","")
    addDir(strs.get('entreteniment'),"/entreteniment/","sections","")
    addDir(strs.get('esports'),"/esports/","sections","")
    addDir(strs.get('documentals'),"/documentals/","sections","")
    addDir(strs.get('divulgacio'),"/divulgacio/","sections","")
    addDir(strs.get('cultura'),"/cultura/","sections","")
    addDir(strs.get('musica'),"/musica/","sections","")
    addDir(strs.get('emissio'),"","dirAZemisio","")
    addDir(strs.get('tots'),"","dirAZtots","")
    
   
    xbmcplugin.endOfDirectory(addon_handle)
    
def listSections(url):
    xbmc.log("--------------listSections----------")
    
    link = getHtml(url_programes_emisio + url)
    
    if link: 
        soup = BeautifulSoup(link)
        
        try: 
            #Grups programes de cada lletra
            links = soup.findAll("ul", {"class" : "R-abcProgrames"})
            
            for i in links:
                xbmc.log("------------------Grup programes per lletra------------------")
                ls = i.findAll("li")
                
                for li in ls:
                    url = li.a["href"]
                    t = str(li.a.string)
                    titol = re.sub('^[\n\r\s]+', '', t)
                    
                 
                    #test url
                    urlProg = url_base + url
                    if urlProg == urlApm or urlProg == urlZonaZaping:
                            url_final = urlProg + 'clips/'
                            
                    else:
                        match = re.compile('(http://www.ccma.cat/tv3/alacarta/.+?/fitxa-programa/)(\d+/)').findall(urlProg)
                        if len(match) != 0:
                            url1 = match[0][0]
                            urlcode = match[0][1]
                            url_final = url1 + 'ultims-programes/' + urlcode
                        else:
                            url_final = urlProg + 'ultims-programes/'
                            
                    xbmc.log ("url final: " + str(url_final))
                
                    addDir(titol ,url_final,'listvideos', "")
                
        except AttributeError as e:
            xbmc.log("Exception AtributeError listSections: " + str(e))
        except KeyError as e:
            xbmc.log("Exception KeyError listSections: " + str(e))
        except Exception as e:
            xbmc.log("Exception listSections: " + str(e))
        
            
        xbmcplugin.endOfDirectory(addon_handle) 
    
def listDirecte():
    xbmc.log("--------------listDirecte----------")
    
    thumb_tv3 = os.path.join(addon_path, 'resources', 'media', 'tv3_thumbnail.png')
    thumb_324 = os.path.join(addon_path, 'resources', 'media', '324_thumbnail.png')
    thumb_c33s3 = os.path.join(addon_path, 'resources', 'media', 'c33-super3_thumbnail.png')
    thumb_esp3 = os.path.join(addon_path, 'resources', 'media', 'esports3_thumbnail.png')
    
    #info channels
    data = getDataVideo(url_arafem)
    
    if data:
        c = data.get('canal',None)
        
        
        if c:
        
            arafemtv3 = ''
            arafem33 = ''
            arafemesp3 = ''
            arafem324 = ''
            arafemtv3_sinop = ''
            arafem33_sinop = ''
            arafemesp3_sinop = ''
            arafem324_sinop = ''
            
            i = 0
            while i < 5:
                nameChannel = c[i].get('ara_fem',{}).get('codi_canal',None)
                
                if nameChannel == 'tv3':
                    arafemtv3 = c[i].get('ara_fem',{}).get('titol_programa',None)
                    arafemtv3_sinop = c[i].get('ara_fem',{}).get('sinopsi',None)
                if nameChannel == 'cs3' or nameChannel == '33d':
                    arafem33 = c[i].get('ara_fem',{}).get('titol_programa',None)
                    arafem33_sinop = c[i].get('ara_fem',{}).get('sinopsi',None)
                if nameChannel == 'esport3':
                    arafemesp3 = c[i].get('ara_fem',{}).get('titol_programa',None)
                    arafemesp3_sinop = c[i].get('ara_fem',{}).get('sinopsi',None)
                if nameChannel == '324':
                    arafem324 = c[i].get('ara_fem',{}).get('titol_programa',None)
                    arafem324_sinop = c[i].get('ara_fem',{}).get('sinopsi',None)
                    
                i = i + 1
               
        infolabelstv3 = {}
        infolabels324 = {}
        infolabels33 = {}
        infolabelsesp3 = {}
        
        if arafemtv3:
            infolabelstv3['title'] = arafemtv3
            infotv3 = '[B]' + arafemtv3 + '[/B]' + '[CR]'
        if arafemtv3_sinop:
            if type(arafemtv3) is int or type(arafemtv3) is float:
                arafemtv3 = str(arafemtv3)
            infotv3 = infotv3 + arafemtv3_sinop
            
        infolabelstv3['plot'] = infotv3
            
        if arafem33:
            infolabels33['title'] = arafem33
            info33 = '[B]' + arafem33 + '[/B]' + '[CR]' 
        if arafem33_sinop:
            if type(arafem33) is int or type(arafem33) is float:
                arafem33 = str(arafem33)
            info33 = info33 + arafem33_sinop
            
        infolabels33['plot'] = info33
            
        if arafemesp3:
            infolabelsesp3['title'] = arafemesp3
            infoesp3 = '[B]' + arafemesp3 + '[/B]' + '[CR]'
        if arafemesp3_sinop:
            if type(arafemesp3) is int or type(arafemesp3) is float:
                arafemesp3 = str(arafemesp3)
            infoesp3 = infoesp3  + arafemesp3_sinop
            
        infolabelsesp3['plot'] = infoesp3
            
        if arafem324:
            infolabels324['title'] = arafem324
            info324 = '[B]' + arafem324 + '[/B]' + '[CR]' 
        if arafem324_sinop:
            if type(arafem324) is int or type(arafem324) is float:
                arafem324 = str(arafem324)
            info324 = info324 + arafem324_sinop
            
        infolabels324['plot'] = info324
            
        
 
    listTV3 = xbmcgui.ListItem(strs.get('tv3'), iconImage=thumb_tv3,  thumbnailImage=thumb_tv3)
    listTV3.setProperty('isPlayable','true')
    listTV3.setInfo('video', infolabelstv3)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_tv3,listitem=listTV3)
    
    list324 = xbmcgui.ListItem(strs.get('canal324'), iconImage=thumb_324,  thumbnailImage=thumb_324)
    list324.setProperty('isPlayable','true')
    list324.setInfo('video', infolabels324)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_324,listitem=list324)
    
    listC33S3 = xbmcgui.ListItem(strs.get('c33super3'), iconImage=thumb_c33s3,  thumbnailImage=thumb_c33s3)
    listC33S3.setProperty('isPlayable','true')
    listC33S3.setInfo('video', infolabels33)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_c33s3,listitem=listC33S3)
    
    listEsport3 = xbmcgui.ListItem(strs.get('esport3'), iconImage=thumb_esp3,  thumbnailImage=thumb_esp3)
    listEsport3.setProperty('isPlayable','true')
    listEsport3.setInfo('video', infolabelsesp3)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_esport3,listitem=listEsport3)

    listTV3 = xbmcgui.ListItem(strs.get('tv3_int'), iconImage=thumb_tv3,  thumbnailImage=thumb_tv3)
    listTV3.setProperty('isPlayable','true')
    listTV3.setInfo('video', infolabelstv3)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_tv3_int,listitem=listTV3)
    
    list324 = xbmcgui.ListItem(strs.get('canal324_int'), iconImage=thumb_324,  thumbnailImage=thumb_324)
    list324.setProperty('isPlayable','true')
    list324.setInfo('video', infolabels324)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_324_int,listitem=list324)
    
    listC33S3 = xbmcgui.ListItem(strs.get('c33super3_int'), iconImage=thumb_c33s3,  thumbnailImage=thumb_c33s3)
    listC33S3.setProperty('isPlayable','true')
    listC33S3.setInfo('video', infolabels33)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_c33s3_int,listitem=listC33S3)
    
    listEsport3 = xbmcgui.ListItem(strs.get('esport3_int'), iconImage=thumb_esp3,  thumbnailImage=thumb_esp3)
    listEsport3.setProperty('isPlayable','true')
    listEsport3.setInfo('video', infolabelsesp3)
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=url_directe_esport3_int,listitem=listEsport3)
        
    xbmcplugin.endOfDirectory(addon_handle) 
    
def dirAZ_emisio():
    xbmc.log("--------------dirAZ_emisio----------")
  
    addDir("A-C","#A-C","listAZemisio","")
    addDir("D-E","D-E","listAZemisio","")
    addDir("F-I","F-I","listAZemisio","")
    addDir("J-L","J-L","listAZemisio","")
    addDir("M-P","M-P","listAZemisio","")
    addDir("Q-S","Q-S","listAZemisio","")
    addDir("T-V","T-V","listAZemisio","")
    addDir("X-Z","X-Z","listAZemisio","")
    
    xbmcplugin.endOfDirectory(addon_handle)
    
def dirAZ_tots():
    xbmc.log("--------------dirAZ_tots----------")

    addDir("A-C","#A-C","listAZtots","")
    addDir("D-E","D-E","listAZtots","")
    addDir("F-I","F-I","listAZtots","")
    addDir("J-L","J-L","listAZtots","")
    addDir("M-P","M-P","listAZtots","")
    addDir("Q-S","Q-S","listAZtots","")
    addDir("T-V","T-V","listAZtots","")
    addDir("X-Z","X-Z","listAZtots","")
    
    xbmcplugin.endOfDirectory(addon_handle)
    
def listProgramesAZ(url, letters):
    xbmc.log("--------------listProgramesAZ----------")
  
    html = getHtml(url)
    
    if html: 
   
   
        soup = BeautifulSoup(html.decode('utf-8','ignore'))
        
        elements = soup.findAll("ul", {"class" : "R-abcProgrames"})
        
       
        li = None
        
        if len(elements) > 0:
            
            if letters == "#A-C":
                
                li = elements[0:4]
                
            elif letters == "D-E":
                
                li = elements[4:6]
                
            elif letters == "F-I":
                
                li = elements[6:10]
                
            elif letters == "J-L":
                
                li = elements[10:13]
                
            elif letters == "M-P":
                
                li = elements[13:17]
            
            elif letters == "Q-S":
                
                li = elements[17:20]
                
            elif letters == "T-V":
                
                li = elements[20:23]
                
            elif letters == "X-Z":
                
                li = elements[23:]
                
            if li != None and len(li) > 0:
                
                
                for l in li:
                    
                    links = l.findAll("li")
                    
                    if len(links) > 0:
                        
                        for i in links:
                            
                            url = i.a["href"]
                            titol = i.a.string.strip().encode("utf-8")
                            
                            #test url
                            urlProg = url_base + url
                            if urlProg == urlApm or urlProg == urlZonaZaping:
                                    url_final = urlProg + 'clips/'
                                    
                            else:
                                match = re.compile('(http://www.ccma.cat/tv3/alacarta/.+?/fitxa-programa/)(\d+/)').findall(urlProg)
                                if len(match) != 0:
                                    url1 = match[0][0]
                                    urlcode = match[0][1]
                                    url_final = url1 + 'ultims-programes/' + urlcode
                                else:
                                    url_final = urlProg + 'ultims-programes/'
                            
                            
                            
                            addDir(titol,url_final,'listvideos', "")
                
        
            
        xbmcplugin.endOfDirectory(addon_handle) 
    
def listVideos(url, cercar, program):
    xbmc.log("--------------listVideos----------")
    
    xbmc.log('listVideos--Url listvideos: ' + url)
    
    link = getHtml(url)
    
    
    if link:
   
        soup = BeautifulSoup(link.decode('utf-8','ignore'))
        links = None
        try:
            links = soup.findAll("div", {"class" : "F-itemContenidorIntern C-destacatVideo"})
            
            if not links:
                links = soup.findAll("li", {"class" : "F-llistat-item"})
                
            #Col·leccions
            if not links:
                links = soup.findAll("div", {"class" : "F-itemContenidorIntern C-destacatVideo"})
                
            #Col·leccions 2
            if not links:
                links = soup.findAll("article", {"class" : "M-destacat  C-destacatVideo T-alacartaTema C-3linies   "})
                
            #Zona Zapping
            if not links:
                links = soup.findAll("article", {"class" : "M-destacat  C-destacatVideo T-alacartaTema C-3linies "})
            
           
        except AttributeError as e:
            xbmc.log("listVideos--getLinks--Exception AtributeError listVideos: " + str(e))
        except KeyError as e:
            xbmc.log("listVideos--getLinks--Exception KeyError  listVideos: " + str(e))
        except Exception as e:
            xbmc.log("listVideos--getLinks--Exception listVideos: " + str(e))
        
        
        
        if links: 
            
        
            for l in links:
            
                try:     
                
                    titElement = l.find("h3", {"class" : "titol"})
                    xbmc.log("lisVideos--bucle addVideo--Titol: %s" % (str(titElement)))
                    
                    if titElement:
                        titol = titElement.a.string
                        
                    
                    else: #Coleccions
                        titol = l.a["title"]
                        
                    urlvideo = l.a["href"]
                    
                    
                    durElement = l.find("time", {"class" : "duration"})
                    if durElement:
                        durada = toSeconds(durElement["datetime"])
                    else:
                        durada = None
                        
                    img = "https:" + l.img["src"]
                    
                    datElement = l.find("time", {"class" : "data"})
                    if datElement :
                        data = datElement.string
                    else:
                        data = None
                    
                    
                    resElement = l.find("p", {"class" : "entradeta"})
                    if resElement :
                        resum = resElement.string
                    else:
                        resum = None
                      
                    
                    #Search
                    if cercar: 
                        prElement = l.find("span", {"class" : "programa"})
                         
                        if prElement:
                            program = prElement.string.encode("utf-8")
                    
                    
                    addVideo(titol, urlvideo, img, durada, program, data, resum)
                
                except AttributeError as e:
                    xbmc.log("listVideos--bucle addVideo--Exception AtributeError: " + str(e))
                   
                except KeyError as e:
                    xbmc.log("listVideos--bucle addVideo--Exception KeyError: " + str(e))
                    
                except Exception as e:
                    xbmc.log("listVideos--bucle addVideo--Exception: " + str(e))
                    
            else:
                xbmc.log("No s'ha trobat cap video")
        
        
        
           ###############################################################################
                   
            #Pagination
            match = re.compile('<p class="numeracio">P\xc3\xa0gina (\d+) de (\d+)</p>').findall(link)
            if len(match) != 0:
                actualPage = int(match[0][0])
                totalPages = int(match[0][1])
                
                if actualPage < totalPages:
                    ntPage = str(actualPage + 1)
                    nextPage = '&pagina=' + ntPage
                    if cercar:
                        if actualPage == 1:
                            url_next = url + nextPage
                        else:
                            url_next = re.sub('&pagina=[\d]+', nextPage, url)
                        addDir(strs.get('seguent'), url_next, "listvideoscercar","", program)
                    else:
                        url_next = url + '?text=&profile=&items_pagina=15' + nextPage
                        addDir(strs.get('seguent'), url_next, "listvideos", "", program)
                    
            xbmcplugin.endOfDirectory(addon_handle)
            
def search():
    xbmc.log("--------------search----------")
    
    keyboard = xbmc.Keyboard('', strs.get('cercar'))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        url = "http://www.ccma.cat/tv3/alacarta/cercador/?items_pagina=15&profile=videos&text="+search_string
        listVideos(url, True, "")
        
            
    
def addDir(name, url, mode,iconimage,program=None):
    
    if program:
        
        p = program
        
    else:
        
        p = name
        
        
    u = buildUrl({'mode':mode,'name':p,'url':url}, base_url)
    liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"title":name})
    liz.setArt({'fanart' : iconimage})
    
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=True)
    return ok
    




def addVideo(titol, url, img, durada, programa, data, resum):
    xbmc.log("-------------------addVideo------------------------------")
    
    
    li = xbmcgui.ListItem(titol, iconImage="DefaultVideo.png", thumbnailImage=img)
    u = buildUrl({'mode':'playVideo','name':"",'url':url}, base_url)
    
    infolabels = {}
    
    if titol != None:
        infolabels['title'] = titol
        
        
    infolabels['plot'] = ""
    
    if programa :
        programa =  '[B]' + programa.decode("utf-8") + '[/B]' + '[CR]'
        infolabels['plot'] =  programa
        
    if data :
        
        data = data + '[CR]'
        infolabels['plot'] =  infolabels['plot'] + data
        
        year = data[6:10]
        infolabels['year'] = year
        
    if resum :
        infolabels['plot'] = infolabels['plot']  + resum
    
    
    li.setInfo('video', infolabels)
    li.addStreamInfo('video',{'duration':durada})
    li.setProperty('isPlayable','true')
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=li)
    

def addVideo2(data):
    ok = True
   
    linkvideo = None
    media = data.get('media',{})
    
    if type(media) is list and len(media) > 0:
        media_dict = media[0]
        linkvideo = media_dict.get('url', None)
    else:
        linkvideo = media.get('url', None)
        
    if linkvideo != None:
        if type(linkvideo) is list and len(linkvideo) > 0:
            linkvideo_item = linkvideo[0]
            video = linkvideo_item.get('file', None)
            
        titol = data.get('informacio',{}).get('titol', None)
        image = data.get('imatges',{}).get('url', None)
        descripcio = data.get('informacio',{}).get('descripcio', None)
        programa = data.get('informacio',{}).get('programa', None)
        capitol = data.get('informacio',{}).get('capitol', None)
        tematica = data.get('informacio',{}).get('tematica',{}).get('text', None)
        data_emisio = data.get('informacio',{}).get('data_emissio',{}).get('text', None)
        milisec = data.get('informacio',{}).get('durada', {}).get('milisegons', None)
        durada = ""
        
        if milisec != None:
            durada = milisec/1000
        
        liz = xbmcgui.ListItem(titol, iconImage="DefaultVideo.png", thumbnailImage=image)
        
        if descripcio == None:
            descripcio = '' 
        else:
            descripcio = descripcio.replace('<br />', '')
            
        header = ""
        if programa != None:
            if type(programa) is int or type(programa) is float:
                programa = str(programa)
            header = '[B]' + programa + '[/B]' + '[CR]'
            
           
        infolabels = {}
        
           
        if data_emisio != None:
            dt = data_emisio[0:10]
            year = data_emisio[6:10]
            infolabels['aired'] = dt
            infolabels['year'] = year
            header = header + dt + '[CR]'
            
        descripcio = header + descripcio
        
        if titol != None:
            infolabels['title'] = titol
            xbmc.log('Titol: ' + titol.encode("utf-8"))
            
        if capitol != None:
            infolabels['episode'] = capitol
            xbmc.log('Capitol: ' + str(capitol))
            
        if descripcio != None:
            infolabels['plot'] = descripcio
          
        if tematica != None:
            infolabels['genre'] = tematica
        
            
          
        liz.setInfo('video', infolabels)
        liz.addStreamInfo('video',{'duration':durada})
        liz.setProperty('isPlayable','true')
        ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=video,listitem=liz)
        
    else:
        ok = None
    return ok
    
        
    
def playVideo(url):    
    
    xbmc.log("---------------playVideo--------------------")
    
    code = url[-8:-1]
  
    html_data = getHtml(url_datavideos + code + '&profile=pc')
    
    
    if html_data:
        
        html_data = html_data.decode("ISO-8859-1")
        data =json.loads(html_data)
            
        urlvideo = None
        
        if len(data) > 0:
            
            
            media = data.get('media',{})
        
            if type(media) is list and len(media) > 0:
                media_dict = media[0]
                urlvideo = media_dict.get('url', None)
            else:
                urlvideo = media.get('url', None)
                
            if urlvideo:
                if type(urlvideo) is list and len(urlvideo) > 0:
                    urlvideo_item = urlvideo[0]
                    video = urlvideo_item.get('file', None)
                    
                else:
                    video = url
                
                xbmc.log("Play video - url:  " + video)
                
                item = xbmcgui.ListItem(path=video)
                xbmcplugin.setResolvedUrl(addon_handle, True, item)
               
    
    
    
###############################################################################################   
###############################################################################################            
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')

mode = args.get('mode', None)
url = args.get('url', [''])
name = args.get('name', None)
if (name != None) and (len(name) > 0):
    name = name[0].replace("\n", "")
program = args.get('program', None)
  

    
if mode==None:
   
    index()
        
elif mode[0]=='destaquem':
  
    listDestaquem()
    
elif mode[0]=='noperdis':
   
    listNoPerdis()
    
elif mode[0]=='mesvist':

     listMesVist()

elif mode[0]=='programes':

    dirSections()    

elif mode[0]=='sections':

    listSections(url[0])  

elif mode[0]=='listvideos':
   
    listVideos(url[0], None, name)
    
elif mode[0]=='listvideoscercar':
   
    listVideos(url[0], True, "")
    

elif mode[0]=='dirAZemisio':
   
    dirAZ_emisio()  

elif mode[0]=='dirAZtots':
   
    dirAZ_tots()       

elif mode[0]=='listAZemisio':
   
    listProgramesAZ(url_programes_emisio,url[0])
    
elif mode[0]=='listAZtots':
   
    listProgramesAZ(url_programes_tots, url[0])     
    
elif mode[0]=='directe':
   
    listDirecte() 

elif mode[0]=='cercar':
   
    search()   

elif mode[0]=='coleccions':
   
    listColeccions()
    
elif mode[0]=='playVideo':
   
    playVideo(url[0])         
    
    
