# -*- coding: utf-8 -*-

'''
 TV3cat Kodi addon
 @author: jqandreu
 @contact: jqsandreu@gmail.com
'''


import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui




class UI:
    
    def __init__(self, url):
        
        
    def addDir(name, url, mode,iconimage):
        u = build_url({'mode':mode,'name':name,'url':url})
        liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={"title":name})
        liz.setArt({'fanart' : iconimage})
        ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=True)
        return ok

        
    def addLink(self, data):
        ok = True
       
        linkvideo = None
        media = data.get('media',{})
        
        if type(media) is list and len(media) > 0:
            media_dict = media[0]
            linkvideo = media_dict.get('url', None)
        else:
            linkvideo = media.get('url', None)
            
        if linkvideo <> None:
            titol = data.get('informacio',{}).get('titol', None)
            image = data.get('imatges',{}).get('url', None)
            descripcio = data.get('informacio',{}).get('descripcio', None)
            programa = data.get('informacio',{}).get('programa', None)
            capitol = data.get('informacio',{}).get('capitol', None)
            tematica = data.get('informacio',{}).get('tematica',{}).get('text', None)
            data_emisio = data.get('informacio',{}).get('data_emissio',{}).get('text', None)
            milisec = data.get('informacio',{}).get('durada', {}).get('milisegons', None)
            durada = ""
            
            if milisec <> None:
                durada = milisec/1000
            
            liz = xbmcgui.ListItem(titol, iconImage="DefaultVideo.png", thumbnailImage=image)
            
            if descripcio == None:
                descripcio = '' 
            else:
                descripcio = descripcio.replace('<br />', '')
                
            header = ""
            if programa <> None:
                if type(programa) is int or type(programa) is float:
                    programa = str(programa)
                header = '[B]' + programa + '[/B]' + '[CR]'
                
               
            infolabels = {}
            
               
            if data_emisio <> None:
                dt = data_emisio[0:10]
                year = data_emisio[6:10]
                infolabels['aired'] = dt
                infolabels['year'] = year
                header = header + dt + '[CR]'
                
            descripcio = header + descripcio
            
            if titol <> None:
                infolabels['title'] = titol
                xbmc.log('Titol: ' + titol.encode("utf-8"))
                
            if capitol <> None:
                infolabels['episode'] = capitol
                xbmc.log('Capitol: ' + str(capitol))
                
            if descripcio <> None:
                infolabels['plot'] = descripcio
              
            if tematica <> None:
                infolabels['genre'] = tematica
            
                
              
            liz.setInfo('video', infolabels)
            liz.addStreamInfo('video',{'duration':durada})
            liz.setProperty('isPlayable','true')
            ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=linkvideo,listitem=liz)
            
        else:
            ok = None
        return ok
        
    def playVideo(self):


class DestaquemAction:
    
    
    
class MesVistAction:
    
    
class NoperdisAction:
    

class ColeccionsAction:
    
    
class SearchAction:
    
class ProgramesAction:
