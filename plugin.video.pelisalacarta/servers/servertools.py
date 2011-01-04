# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Utilidades para detectar vídeos de los diferentes conectores
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re
import scrapertools
import config
import logger

logger.info("[servertools.py] init")

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
    logger.info("1k) Megaupload...")
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

    # Megavideo - Vídeos sin título
    logger.info("2) Megavideo sin titulo...")
    patronvideos  = '<param name="movie" value="http://wwwstatic.megavideo.com/mv_player.swf\?v=([^"]+)">'
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

    logger.info("0) YouTube...")
    patronvideos  = '"http://www.youtube.com/v/([^"]+)"'
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
    
    return devuelve

def findurl(code,server):
    mediaurl = "ERROR"
    server = server.lower() #Para hacer el procedimiento case insensitive

    if server == "megavideo":
        import megavideo
        mediaurl = megavideo.Megavideo(code)

    if server == "megaupload":
        import megaupload
        mediaurl = megaupload.getvideo(code)
        
    if server == "vreel":
        import vreel
        mediaurl = vreel.Vreel(code)

    if server == "stagevu":
        import stagevu
        mediaurl = stagevu.Stagevu(code)
    
    if server == "tu.tv":
        import tutv
        mediaurl = tutv.Tutv(code)
    
    if server == "movshare":
        import movshare
        mediaurl = movshare.getvideo(code)
    
    if server == "veoh":
        import veoh
        mediaurl = veoh.getvideo(code)
    
    if server == "directo":
        mediaurl = code
        
    if server == "metadivx":
        import metadivx
        mediaurl = metadivx.geturl(code)

    if server == "divxden":
        import divxden
        mediaurl = divxden.geturl(code)

    if server == "divxlink":
        import divxlink
        mediaurl = divxlink.geturl(code)

    if server == "videoweed":
        import videoweed
        mediaurl = videoweed.geturl(code)
    
    if server == "youtube":
        import youtube
        mediaurl = youtube.geturl(code)
    
    if server == "zshare":
        import zshare
        mediaurl = zshare.geturl(code)

    if server == "4shared":
        import fourshared
        mediaurl = fourshared.geturl(code)
    
    if server == "cinshare":
        import cinshare
        mediaurl = cinshare.geturl(code)
        
    if server == "facebook":
        mediaurl = code
        
    if server == "xml":
        import xmltoplaylist
        mediaurl = xmltoplaylist.geturl(code)

    if server == "vimeo":
        import vimeo
        mediaurl = vimeo.geturl(code)
        
    return mediaurl

def getmegavideolow(code):
    import megavideo
    return megavideo.getlowurl(code)

def getmegavideohigh(code):
    import megavideo
    return megavideo.gethighurl(code)

def getmegauploadhigh(code):
    import megaupload
    return megaupload.gethighurl(code)

def getmegauploadlow(code):
    import megaupload
    return megaupload.getlowurl(code)
