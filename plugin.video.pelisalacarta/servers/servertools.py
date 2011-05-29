# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Utilidades para detectar vídeos de los diferentes conectores
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re

try:
    from core import scrapertools
    from core import config
    from core import logger
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools

def findvideos(data):
    logger.info("[servertools.py] findvideos")
    encontrados = set()
    devuelve = []
    
    #Megavideo con partes para cinetube
    logger.info ("0) Megavideo con partes para cinetube")
    patronvideos = 'id.+?http://www.megavideo.com..v.(.+?)".+?(parte\d+)'
    #id="http://www.megavideo.com/?v=CN7DWZ8S"><a href="#parte1">Parte 1 de 2</a></li>
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        titulo = "[Megavideo " + match[1] + "]"
        url = match[0]
        if url not in encontrados:
            logger.info(" url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info(" url duplicada="+url)

    # Megavideo - Vídeos con título
    logger.info("1) Megavideo con titulo...")
    patronvideos  = '<div align="center">([^<]+)<.*?<param name="movie" value="http://www.megavideo.com/v/([A-Z0-9a-z]{8})[^"]+"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = match[0].strip()
        if titulo == "":
            titulo = "[Megavideo]"
        url = match[1]
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megavideo - Vídeos con título
    logger.info("1b) Megavideo con titulo...")
    patronvideos  = '<a href\="http\:\/\/www.megavideo.com/\?v\=([A-Z0-9a-z]{8})".*?>([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = match[1].strip()
        if titulo == "":
            titulo = "[Megavideo]"
        url = match[0]
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("1c) Megavideo sin titulo...")
    #http://www.megavideo.com/?v=OYGXMZBM
    patronvideos  = 'http\:\/\/www.megavideo.com/\?v\=([A-Z0-9a-z]{8})"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        titulo = ""
        if titulo == "":
            titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("1d) Megavideo sin titulo...")
    #http://www.megavideo.com/?v=OYGXMZBM
    patronvideos  = 'http\:\/\/www.megavideo.com/\?v\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        titulo = ""
        if titulo == "":
            titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megaupload con título
    logger.info("1k1) Megaupload...")
    patronvideos  = '<a.*?href="http://www.megaupload.com/\?d=([A-Z0-9a-z]{8})".*?>(.*?)</a>'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        titulo = scrapertools.htmlclean(match[1].strip())+" - [Megaupload]"
        url = match[0]
        if url not in encontrados:
            logger.info("  titulo="+titulo)
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megaupload' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
    
    #2/12/2010 Megaupload
    logger.info("1k) Megaupload (...")
    patronvideos  = 'http\://www.megaupload.com/(?:es/)?\?.*?d\=([A-Z0-9a-z]{8})(?:[^>]*>([^<]+)</a>)?'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        if match[1]<>"":
            titulo = match[1].strip()+" - [Megaupload]"
        else:
            titulo = "[Megaupload]"
        url = match[0]
        if url not in encontrados:
            logger.info("  titulo="+titulo)
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megaupload' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
    
    # Código especial cinetube
    #xrxa("BLYT2ZC9=d?/moc.daolpuagem.www//:ptth")
    logger.info("1k) Megaupload reverse")
    patronvideos  = 'xrxa\("([A-Z0-9a-z]{8})=d\?/moc.daolpuagem.www//\:ptth"\)'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        titulo = "[Megaupload]"
        url = match[::-1]
        if url not in encontrados:
            logger.info("  titulo="+titulo)
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megaupload' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megavideo - Vídeos sin título
    logger.info("2) Megavideo sin titulo...")
    patronvideos  = '<param name="movie" value="http://wwwstatic.megavideo.com/mv_player.swf\?v=([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Megavideo]"
        if "&" in match:
            url = match.split("&")[0]
        else:
            url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)


    # Megavideo - Vídeos sin título
    logger.info("3) Megavideo formato islapeliculas") #http://www.megavideo.com/mv_player.swf?image=imagenes/mBa.jpg&amp;v=RV4GBJYS
    patronvideos  = "www.megavideo.com.*?mv_player.swf.*?v(?:=|%3D)(\w{8})"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)


    # Vreel - Vídeos con título
    logger.info( "3) Vreel con título...")
    patronvideos  = '<div align="center"><b>([^<]+)</b>.*?<a href\="(http://beta.vreel.net[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = match[0].strip()
        if titulo == "":
            titulo = "[Vreel]"
        url = match[1]
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Vreel' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Vreel - Vídeos con título
    logger.info("4) Vreel con titulo...")
    patronvideos  = '<div align="center">([^<]+)<.*?<a href\="(http://beta.vreel.net[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = match[0].strip()
        if titulo == "":
            titulo = "[Vreel]"
        url = match[1]
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Vreel' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # STAGEVU
    logger.info("7) Stagevu sin título...")
    patronvideos  = '"(http://stagevu.com[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Stagevu]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Stagevu' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # TU.TV
    logger.info("8) Tu.tv sin título...")
    patronvideos  = '<param name="movie" value="(http://tu.tv[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[tu.tv]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'tu.tv' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # TU.TV
    logger.info("9) Tu.tv sin título...")
    #<param name="movie" value="http://www.tu.tv/tutvweb.swf?kpt=aHR0cDovL3d3dy50dS50di92aWRlb3Njb2RpL24vYS9uYXppcy11bi1hdmlzby1kZS1sYS1oaXN0b3JpYS0xLTYtbGEtbC5mbHY=&xtp=669149_VIDEO"
    patronvideos  = '<param name="movie" value="(http://www.tu.tv[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[tu.tv]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'tu.tv' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("9b) Tu.tv sin título...")
    #<embed src="http://tu.tv/tutvweb.swf?kpt=aHR0cDovL3d3dy50dS50di92aW
    patronvideos  = '<embed src="(http://tu.tv/[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[tu.tv]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'tu.tv' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megavideo - Vídeos sin título
    logger.info("10 ) Megavideo sin titulo...")

    patronvideos  = '"http://www.megavideo.com/v/([A-Z0-9a-z]{8})[^"]+"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megavideo - Vídeos sin título
    logger.info("11) Megavideo sin titulo...")
    patronvideos  = '"http://www.megavideo.com/v/([A-Z0-9a-z]{8})[^"]+"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # STAGEVU
    '''
    logger.info("12) Stagevu...")
    patronvideos  = '(http://stagevu.com[^<]+)<'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "Ver el vídeo en Stagevu"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Stagevu' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
    '''
        
    # Vreel - Vídeos sin título
    logger.info("13) Vreel sin titulo...")
    patronvideos  = '(http://beta.vreel.net[^<]+)<'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Vreel]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Vreel' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megavideo - Vídeos con título
    logger.info("14) Megavideo con titulo...")
    patronvideos  = '<a href="http://www.megavideo.com/\?v\=([^"]+)".*?>(.*?)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = match[1].strip()
        if titulo == "":
            titulo = "[Megavideo]"
        url = match[0]
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # Megavideo - Vídeos con título
    logger.info("14b) Megavideo con titulo...")
    patronvideos  = '<param name="movie" value=".*?v\=([A-Z0-9]{8})" />'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Stagevu...")
    patronvideos  = '"http://stagevu.com.*?uid\=([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = "[Stagevu]"
        url = "http://stagevu.com/video/"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Stagevu' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Stagevu...")
    patronvideos  = "'http://stagevu.com.*?uid\=([^']+)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Stagevu]"
        url = "http://stagevu.com/video/"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Stagevu' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Megavideo... formato d=XXXXXXX")
    patronvideos  = 'http://www.megavideo.com/.*?\&d\=([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Megavideo... formato watchanimeon")
    patronvideos  = 'src="http://wwwstatic.megavideo.com/mv_player.swf.*?\&v\=([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megavideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Megaupload... formato megavideo con d=XXXXXXX")
    patronvideos  = 'http://www.megavideo.com/\?d\=([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Megavideo]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Megaupload' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Movshare...")
    patronvideos  = '"(http://www.movshare.net/video/[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = "[Movshare]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'movshare' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Movshare...")
    patronvideos  = "'(http://www.movshare.net/embed/[^']+)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    
    for match in matches:
        titulo = "[Movshare]"
        url = match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'movshare' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Veoh...")
    patronvideos  = '"http://www.veoh.com/.*?permalinkId=([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Veoh]"
        if match.count("&")>0:
            primera = match.find("&")
            url = match[:primera]
        else:
            url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'veoh' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Directo - myspace")
    patronvideos  = 'flashvars="file=(http://[^\.]+.myspacecdn[^\&]+)&'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Directo]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Directo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Directo - myspace")
    patronvideos  = '(http://[^\.]+\.myspacecdn.*?\.flv)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Directo]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Directo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Directo - ning")
    patronvideos  = '(http://api.ning.com.*?\.flv)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Directo]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Directo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Videoweed...")
    patronvideos  = '(http://www.videoweed.com/file/*?\.flv)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Videoweed]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'videoweed' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("1) Videoweed formato islapeliculas") #http://embed.videoweed.com/embed.php?v=h56ts9bh1vat8
    patronvideos  = "(http://embed.videoweed.*?)&"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Videoweed]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'videoweed' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) YouTube...")
    patronvideos  = 'http://www.youtube(?:-nocookie)?\.com/(?:(?:(?:v/|embed/))|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?v=))?([0-9A-Za-z_-]{11})?'#'"http://www.youtube.com/v/([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[YouTube]"
        url = match
        
        if url!='':
            if url not in encontrados:
                logger.info("  url="+url)
                devuelve.append( [ titulo , url , 'youtube' ] )
                encontrados.add(url)
            else:
                logger.info("  url duplicada="+url)
    
    logger.info(") YouTube formato buenaisla")  #www.youtube.com%2Fwatch%3Fv%3DKXpGe0ds5r4
    patronvideos  = 'www.youtube.*?v(?:=|%3D)([0-9A-Za-z_-]{11})'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[YouTube]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'youtube' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    #http://video.ak.facebook.com/cfs-ak-ash2/33066/239/133241463372257_27745.mp4
    logger.info("0) Facebook...")
    patronvideos  = '(http://video.ak.facebook.com/.*?\.mp4)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Facebook]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'directo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("0) Facebook para buenaisla...") #http%3A%2F%2Fwww.facebook.com%2Fv%2F139377799432141_23545.mp4
    patronvideos  = "www.facebook.com(?:/|%2F)v(?:/|%2F)(.*?)(?:&|%26)"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Facebook]"
        url = "http://www.facebook.com/video/external_video.php?v="+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'facebook' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)		

    #http://www.4shared.com/embed/392975628/ff297d3f
    logger.info("0) 4shared...")
    patronvideos  = '"(http://www.4shared.com.*?)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[4shared]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , '4shared' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    #http://www.4shared.com/embed/392975628/ff297d3f
    logger.info("0) 4shared...")
    patronvideos  = "'(http://www.4shared.com.*?)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[4shared]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , '4shared' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    #file=http://es.video.netlogstatic.com//v/oo/004/398/4398830.flv&
    #http://es.video.netlogstatic.com//v/oo/004/398/4398830.flv
    logger.info("0) netlogicstat...")
    patronvideos  = "file\=(http\:\/\/es.video.netlogstatic[^\&]+)\&"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[Directo]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'Directo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("videobb...")
    patronvideos  = "(http\:\/\/videobb.com\/e\/[a-zA-Z0-9]+)"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[videobb]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'videobb' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("videobb...")
    patronvideos  = "(http\:\/\/(?:www\.)?videobb.com\/(?:(?:e/)|(?:(?:video/|f/)))?[a-zA-Z0-9]{12})"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #print data
    for match in matches:
        titulo = "[videobb]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'videobb' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("videozer...")
    patronvideos  = "(http\:\/\/(?:www\.)?videozer.com\/(?:(?:e/|flash/)|(?:(?:video/|f/)))?[a-zA-Z0-9]{4,8})"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #print data
    for match in matches:
        titulo = "[videozer]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'videozer' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
    
    logger.info ("vk...")
    #vk tipo "http://vk.com/video_ext.php?oid=70712020&amp;id=159787030&amp;hash=88899d94685174af&amp;hd=3"
    patronvideos = '<iframe src="(http://[^\/]+\/video_ext.php[^"]+)"'
    matches = re.compile(patronvideos).findall(data)

    for match in matches:
        titulo = "[vk]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'vk' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("VKserver...")
    patronvideos  = '(http\:\/\/vk.+?\/video_ext\.php[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #print data
    for match in matches:
        titulo = "[VKserver]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'vk' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
            
    logger.info ("0) Enlace estricto a userporn")
    #userporn tipo "http://www.userporn.com/f/szIwlZD8ewaH.swf"
    patronvideos = 'userporn.com\/f\/([A-Z0-9a-z]{12}).swf'
    matches = re.compile(patronvideos).findall(data)

    for match in matches:
        titulo = "[userporn]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'userporn' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
           
    logger.info ("1) Enlace estricto a userporn")
    #userporn tipo "http://www.userporn.com/video/ZIeb370iuHE4"
    patronvideos = 'userporn.com\/video\/([A-Z0-9a-z]{12})'
    matches = re.compile(patronvideos).findall(data)

    for match in matches:
        titulo = "[userporn]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'userporn' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
           
    logger.info ("2) Enlace estricto a userporn")
    #userporn tipo "http://www.userporn.com/e/LLqVzhw5ft7T"
    patronvideos = 'userporn.com\/e\/([A-Z0-9a-z]{12})'
    matches = re.compile(patronvideos).findall(data)

    for match in matches:
        titulo = "[userporn]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'userporn' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    logger.info("userporn...")
    patronvideos  = "(http\:\/\/(?:www\.)?userporn.com\/(?:(?:e/|flash/)|(?:(?:video/|f/)))?[a-zA-Z0-9]{0,12})"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #print data
    for match in matches:
        titulo = "[Userporn]"
        url = match

        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'userporn' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
			
    logger.info("0) Videos animeid...") #http%3A%2F%2Fmangaid.com%2Ff.php%3Fh3eqiGdkh3akY2GaZJ6KpqyDaWmJ%23.mp4
    patronvideos  = "file=http.*?mangaid.com(.*?)&amp;backcolor="
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    cont = 0
    for match in matches:
        cont = cont + 1 
        titulo = " Parte %s [Directo]" % (cont)
        url = "http://mangaid.com"+match
        url = url.replace('%2F','/').replace('%3F','?').replace('%23','#')
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'directo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)	
            
    return devuelve
    
def findurl(code,server):
    mediaurl = "ERROR"
    server = server.lower() #Para hacer el procedimiento case insensitive

    if server == "megavideo":
        import megavideo
        mediaurl = megavideo.Megavideo(code)

    elif server == "megaupload":
        import megaupload
        mediaurl = megaupload.gethighurl(code)
        
    elif server == "directo":
        mediaurl = code

    elif server == "4shared":
        import fourshared
        mediaurl = fourshared.geturl(code)
        
    elif server == "xml":
        import xmltoplaylist
        mediaurl = xmltoplaylist.geturl(code)

    else:
        try:
            exec "import "+server+" as serverconnector"
            mediaurl = serverconnector.geturl(code)
        except:
            mediaurl = "ERROR"
            import sys
            for line in sys.exc_info():
                logger.error( "%s" % line )
        
    return mediaurl

def getmegavideolow(code, password=None):
    import megavideo
    if password is not None:
	    return megavideo.getlowurl(code,password)
    else:
        return megavideo.getlowurl(code,password)

def getmegavideohigh(code):
    import megavideo
    return megavideo.gethighurl(code)

def getmegauploadhigh(code, password=None):
    import megaupload
    if password is not None:
	    return megaupload.gethighurl(code,password)
    else:
        return megaupload.gethighurl(code)
	
def getmegauploadlow(code, password=None):
    import megaupload
    if password is not None:
	    return megaupload.getlowurl(code,password)
    else:
        return megaupload.getlowurl(code)