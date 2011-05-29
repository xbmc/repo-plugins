# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculasyonkis
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys

try:
    from core import logger
    from core import config
    from core import scrapertools
    from core.item import Item
    from servers import servertools
    from core import DecryptYonkis as Yonkis
    from pelisalacarta import buscador
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools
    from Code.core.item import Item
    from Code.core import DecryptYonkis as Yonkis
    from pelisalacarta import buscador

CHANNELNAME = "peliculasyonkis_generico"
SERVER = {'pymeno2'   :'Megavideo' ,'pymeno3':'Megavideo','pymeno4':'Megavideo','pymeno5':'Megavideo','pymeno6':'Megavideo',
          'svueno'    :'Stagevu'   ,
          'manueno'   :'Movshare'  ,
          'videoweed' :'Videoweed' ,
          'veoh2'     :'Veoh'      ,
          'megaupload':'Megaupload',
          'pfflano'   :'Directo'   ,
          'pya'       :'adnstream' ,
          }
CALIDAD = {'f-1':u'\u2776','f-2':u'\u2777','f-3':u'\u2778','f-4':u'\u0002\u2779\u0002','f-5':u'\u277A'}
DEBUG = True

def isGeneric():
    return True
    
def mainlist(item):
    logger.info("[peliculasyonkis_generico.py] mainlist")
    
    itemlist = []
    itemlist.append( Item ( channel=CHANNELNAME , action="listnovedades"  , title="Estrenos de cartelera" ,url="http://www.peliculasyonkis.com/ultimas-peliculas/cartelera/") )
    itemlist.append( Item ( channel=CHANNELNAME , action="listnovedades"  , title="Estrenos de DVD"       ,url="http://www.peliculasyonkis.com/ultimas-peliculas/estrenos-dvd/"))
    
    itemlist.append( Item ( channel=CHANNELNAME , action="listnovedades"  , title="Ultimas Peliculas Actualizadas"     ,url="http://www.peliculasyonkis.com/ultimas-peliculas/actualizadas/") )
    itemlist.append( Item ( channel=CHANNELNAME , action="listnovedades"  , title="Ultimas Peliculas añadidas a la web",url="http://www.peliculasyonkis.com/ultimas-peliculas/estrenos-web/") )
    
    itemlist.append( Item ( channel=CHANNELNAME , action="listcategorias" , title="Listado por Categorias",url="http://www.peliculasyonkis.com/") )
    itemlist.append( Item ( channel=CHANNELNAME , action="listalfabetico" , title="Listado Alfabético"    ,url="http://www.peliculasyonkis.com/") )
    itemlist.append( Item ( channel=CHANNELNAME , action="listservidor"   , title="Listado por Servidor"  ,url="http://www.peliculasyonkis.com/") )
    itemlist.append( Item ( channel=CHANNELNAME , action="listidiomas"    , title="Listado por Idiomas"   ,url="http://www.peliculasyonkis.com/") )
    
    itemlist.append( Item ( channel=CHANNELNAME , action="buscaporanyo"   , title="Busqueda por Año",url="http://www.peliculasyonkis.com/") )
    itemlist.append( Item ( channel=CHANNELNAME , action="search"         , title="Buscar"          ,url="http://www.peliculasyonkis.com/buscarPelicula.php?s=", category="Buscador_Generico",thumbnail="http://www.mimediacenter.info/xbmc/pelisalacarta/posters/buscador.png") )
    
    return itemlist
    
def listidiomas(item):
    logger.info("[peliculasyonkis_generico.py] listidiomas")
    itemlist=[]
    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)
    
    # Extrae las entradas (carpetas)
    # <li class="page_item"><a href="http://www.peliculasyonkis.com/lista-peliculas/idioma/espanol-espana/0/" title="Español (España)"><img height="16" src="http://simages.seriesyonkis.com/images/f/spanish.png" alt="Audio Español España" style="vertical-align: middle;" />Español (España)</a></li>
    patronvideos  = '<a href="(http\://www.peliculasyonkis.com/lista-peliculas/idioma/[^"]+)"(.*?) src="([^"]+)" (.*?)>([^"]+)</a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    for match in matches:
        scrapedurl = match[0]
        scrapedtitle = match[4]
        scrapedthumbnail = match[2]
        scrapedplot = ""
        itemlist.append( Item ( channel=CHANNELNAME , action="listvideos" , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot ) )

    return itemlist

def listservidor(item):
    logger.info("[peliculasyonkis_generico.py] listservidor")
    
    itemlist=[]
    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)
    
    # Extrae las entradas (carpetas)
    # <li class="page_item"><a href="http://www.peliculasyonkis.com/lista-peliculas/servidor/megavideo/0/" title="Megavideo"><img height="16" src="http://simages.peliculasyonkis.com/images/tmegavideo.png" alt="Megavideo" style="vertical-align: middle;" />Megavideo (todas)</a></li>
    patronvideos  = '<a href="(http\://www.peliculasyonkis.com/lista-peliculas/servidor/[^"]+)"(.*?)>([^"]+)</a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    for match in matches:
        scrapedurl = match[0]
        scrapedtitle = match[2]
        if scrapedtitle=="Veoh":
            scrapedthumbnail = "http://simages.peliculasyonkis.com/images/veoh.jpg"
        elif scrapedtitle=="VeohTV":
            scrapedthumbnail = "http://simages.peliculasyonkis.com/images/veohtv.jpg"
        elif scrapedtitle=="Megavideo (con descarga de Megaupload)":
            scrapedthumbnail = "http://www.mimediacenter.info/xbmc/pelisalacarta/posters/megauploadsite.png"
        elif scrapedtitle=="Megavideo (todas)":
            scrapedthumbnail = "http://www.mimediacenter.info/xbmc/pelisalacarta/posters/megavideosite.png"
        elif scrapedtitle=="DivX":
            scrapedthumbnail = "http://simages.peliculasyonkis.com/images/divx.png"
        else:
            scrapedthumbnail = ""
        # procesa el resto
        scrapedplot = ""
        logger.info(match[2])
        
        itemlist.append( Item ( channel=CHANNELNAME , action="listvideos" , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot ) )
    
    return itemlist
def search(item):
    logger.info("[peliculasyonkis_generico.py] search")
    return buscador.listar_busquedas(item)
    
def searchresults(item):
    logger.info("[peliculasyonkis_generico.py] searchresults")
    buscador.salvar_busquedas(item)
    texto = item.url.replace(" ", "+")
    item.url = "http://www.peliculasyonkis.com/buscarPelicula.php?s="+texto
    
    return listvideos(item)
    
def listalfabetico(item):

   itemlist=[]
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="0-9",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasNumeric.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="A",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasA.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="B",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasB.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="C",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasC.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="D",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasD.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="E",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasE.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="F",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasF.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="G",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasG.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="H",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasH.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="I",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasI.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="J",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasJ.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="K",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasK.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="L",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasL.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="M",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasM.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="N",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasN.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="O",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasO.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="P",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasP.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="Q",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasQ.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="R",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasR.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="S",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasS.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="T",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasT.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="U",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasU.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="V",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasV.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="W",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasW.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="X",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasX.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="Y",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasY.php") )
   itemlist.append( Item ( channel=CHANNELNAME ,action="listvideos", title="Z",url="http://www.peliculasyonkis.com/lista-peliculas/listaPeliculasZ.php") )
   
   return itemlist

def listnovedades(item):
   logger.info("[peliculasyonkis_generico.py] listnovedades")

   # Descarga la página
   data = scrapertools.cachePage(item.url)
   #logger.info(data)
   itemlist=[]
   # Extrae las entradas (carpetas)
   '''
   <td align='center'>
   <center><span style='font-size: 0.7em'>
   <a href="http://www.peliculasyonkis.com/pelicula/otra-vez-tu-you-again-2010-/" title="Otra vez tu (You again) (2010 )">
   <img width='100' height='144' src='http://simages.peliculasyonkis.com/thumbs/otra-vez-tu-you-again-2010-.jpg' alt='Otra vez tu (You again) (2010 )'/><br />Otra vez tu (You again) (2010 )</a></span><br />
   <img height="30" src="http://simages.seriesyonkis.com/images/f/latino.png" alt="Audio Latino" style="vertical-align: middle;" /><img height="30" src="http://simages.peliculasyonkis.com/images/tdescargar2.png" title="Tiene Descarga Directa" style="vertical-align: middle;"/></center></td>
   '''
   patronvideos  = '<td align=\'center\'>'
   patronvideos += '<center><span style=\'font-size: 0.7em\'>'
   patronvideos += '<a href="([^"]+)" title="([^"]+)">'
   patronvideos += '<img.*?src=\'([^\']+)\'[^>]+>.*?'
   patronvideos += '<img.*?src="(http://s.staticyonkis.com[^"]+)"'
   matches = re.compile(patronvideos,re.DOTALL).findall(data)
   scrapertools.printMatches(matches)

   for match in matches:
      # Titulo
      try:
         scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
      except:
         scrapedtitle = match[1]

      # URL
      scrapedurl = match[0]

      # Thumbnail
      scrapedthumbnail = match[2]

      # procesa el resto
      scrapedplot = ""

      # Depuracion
      if (DEBUG):
         logger.info("scrapedtitle="+scrapedtitle)
         logger.info("scrapedurl="+scrapedurl)
         logger.info("scrapedthumbnail="+scrapedthumbnail)

      itemlist.append( Item ( channel=CHANNELNAME , action="detail" , server="Megavideo" , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot ) )
      
   return itemlist

def listcategorias(item):
   logger.info("[peliculasyonkis_generico.py] listcategorias")
   itemlist=[]
   # Descarga la página
   data = scrapertools.cachePage(item.url)
   #logger.info(data)

   # Extrae las entradas (carpetas)
   patronvideos  = '<li class="page_item"><a href="(http\://www.peliculasyonkis.com/genero/[^"]+)"[^>]+>([^<]+)</a></li>'
   matches = re.compile(patronvideos,re.DOTALL).findall(data)
   scrapertools.printMatches(matches)

   for match in matches:
      # Titulo
      try:
         scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
      except:
         scrapedtitle = match[1]

      # URL
      scrapedurl = match[0]
      
      # Thumbnail
      scrapedthumbnail = match[0]
      
      # procesa el resto
      scrapedplot = ""

      # Depuracion
      if (DEBUG):
         logger.info("scrapedtitle="+scrapedtitle)
         logger.info("scrapedurl="+scrapedurl)
         logger.info("scrapedthumbnail="+scrapedthumbnail)

      # Añade al listado de XBMC
      itemlist.append( Item ( channel=CHANNELNAME , action="listvideos" , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot ) )

   return itemlist
   
def buscaporanyo(item):
    logger.info("[peliculasyonkis_generico.py] buscaporanyo")
    itemlist = []
    for i in range(111):
        scrapedtitle=str(2011-i)
        scrapedurl="http://www.peliculasyonkis.com/estreno/"+scrapedtitle+"/"+scrapedtitle+"/0/"
        itemlist.append( Item ( channel=CHANNELNAME , action="listvideos" , title=scrapedtitle , url=scrapedurl , thumbnail="" , plot="" ) )
    return itemlist

def listvideos(item):
   logger.info("[peliculasyonkis_generico.py] listvideos")
   itemlist=[]
   # Descarga la página
   data = scrapertools.cachePage(item.url)
   #logger.info(data)

   # Extrae las entradas (carpetas)
   patronvideos  = "<a href='([^']+)'>Siguiente &gt;&gt;</a>"
   matches = re.compile(patronvideos,re.DOTALL).findall(data)
   scrapertools.printMatches(matches)

   for match in matches:
      # Titulo
      scrapedtitle = "#Siguiente"

      # URL
      scrapedurl = match
      
      # Thumbnail
      scrapedthumbnail = ""
      
      # procesa el resto
      scrapedplot = ""

      # Depuracion
      if (DEBUG):
         logger.info("scrapedtitle="+scrapedtitle)
         logger.info("scrapedurl="+scrapedurl)
         logger.info("scrapedthumbnail="+scrapedthumbnail)

      # Añade al listado de XBMC
      itemlist.append( Item ( channel=CHANNELNAME , action="listvideos" ,  title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot ) )

   # Extrae las entradas (carpetas)
   patronvideos  = '<li>[^<]+<a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)"[^>]+>.*?<span[^>]+>(.*?)</span>'
   matches = re.compile(patronvideos,re.DOTALL).findall(data)
   scrapertools.printMatches(matches)

   for match in matches:
      # Titulo
      try:
         scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
      except:
         scrapedtitle = match[1]

      # URL
      scrapedurl = match[0]
      
      # Thumbnail
      scrapedthumbnail = match[2]
      
      # procesa el resto
      try:
         scrapedplot = unicode( match[3], "utf-8" ).encode("iso-8859-1")
      except:
         scrapedplot = match[3]
      
      scrapedplot = scrapedplot.replace("\r"," ")
      scrapedplot = scrapedplot.replace("\n"," ")
      scrapedplot = scrapedplot.replace("&quot;","'")
      scrapedplot = scrapedplot.replace("<br />","|")
      patronhtml = re.compile( '<img[^>]+>' )
      scrapedplot = patronhtml.sub( "", scrapedplot )
      patronhtml = re.compile( 'Uploader:[^\|]+\|' )
      scrapedplot = patronhtml.sub( "", scrapedplot )
      patronhtml = re.compile( 'Idioma:[^\|]+\|' )
      scrapedplot = patronhtml.sub( "", scrapedplot )
      patronhtml = re.compile( 'Tiene descarga directa:[^\|]+\|' )
      scrapedplot = patronhtml.sub( "", scrapedplot )
      patronhtml = re.compile( '\W*\|\W*' )
      scrapedplot = patronhtml.sub( "|", scrapedplot )
      patronhtml = re.compile( '\|Descripci.n:' )
      scrapedplot = patronhtml.sub( "\n\n", scrapedplot )
      
      scrapedplot = scrapedplot.replace("|b>Servidor:</b|","")
      scrapedplot = re.sub('<[^>]+>',"",scrapedplot)
      scrapedplot = scrapedplot.replace("b>","\n")
      # Depuracion
      if (DEBUG):
         logger.info("scrapedtitle="+scrapedtitle)
         logger.info("scrapedurl="+scrapedurl)
         logger.info("scrapedthumbnail="+scrapedthumbnail)

      # Añade al listado de XBMC
      itemlist.append( Item ( channel=CHANNELNAME , action="detail" , server="Megavideo" , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot ) )

   return itemlist

def detailfolder(item):
   logger.info("[peliculasyonkis_generico.py] detail")

   itemlist=[]
   itemlist.append( Item ( channel=CHANNELNAME , action="detail" , server="Megavideo" , title=item.title , url=item.url , thumbnail=item.thumbnail , plot=item.plot ) )
   #xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "Megavideo" , title , url , thumbnail , plot )

   # Label (top-right)...
   #~ xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
   #~ xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
   #~ xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
   return itemlist

def detail(item):
    logger.info("[peliculasyonkis_generico.py] detail")

   
    listafinal = []
    itemlist=[] # Lista de videos
    listapartes=[] # Lista para las partes
    title = item.title
    thumbnail = item.thumbnail
    plot = item.plot

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    patronvideos  = 'href="http://www.peliculasyonkis.com/player/visor_([^\.]+).php.*?'
    patronvideos += 'id=([^"]+)".*?'
    patronvideos += 'alt="([^"]+)"'
    patronvideos += '(.*?)</tr>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    patronvideos1  = 'http://www.peliculasyonkis.com/go/(d)/(.+?)".*?alt="([^"]+)"'
    patronvideos1 += "(.+?)<br /></span></div></td>"
    matches1 = re.compile(patronvideos1,re.DOTALL).findall(data)
    if (len(matches1) > 0):
        for j in matches1:
            matches.append(j)
            
    if len(matches)>0:
        #scrapertools.printMatches(matches)
        logger.info("MATCHES %d" % len(matches))
        itemlist = ChoiceOneVideo(matches,title)

    return itemlist

def choiceOnePart(item, opciones):
    logger.info("[peliculasyonkis_generico.py] ChoiceOneVideo")

    Nro = 0
    matches = item.url.split("|")
    logger.info("Elige bien %02d " % len(matches))
    for url in matches:
        logger.info(" URL " + url)
        Nro = Nro + 1
        titulo = item.title  + "Parte %s " % Nro
        opciones.append(Item (channel=CHANNELNAME, title=titulo, server=item.server, url=url.strip(), action=item.action, folder=False))
   
    return opciones
   
def ChoiceOneVideo(matches,title):
    logger.info("[peliculasyonkis_generico.py] ChoiceOneVideo")
   
    opciones = []
    Nro = 0
    fmt=duracion=id=""
   
    for server,codigo,audio,data in matches:
        logger.info("SERVER="+server)
        try:
            ql= ""
            if server in SERVER:
                servidor = SERVER[server]
                player = server
                id = codigo
                Server = servidor
            else:
                if server == "d":
                    player = "megaupload"
                    id = "http://www.peliculasyonkis.com/go/%s/%s" % (server,codigo)
                    
                    servidor = "Descarga"
                    Server = "megaupload"
                elif server == "mv":
                    player = "pymeno2"
                    id = "http://www.peliculasyonkis.com/go/%s/%s" % (server,codigo)
                    
                    servidor = "Megavideo"
                    Server = "megavideo"
                else:
                    servidor = "desconocido ("+server+")"
                    logger.info("[peliculasyonkis.py] SERVIDOR DESCONOCIDO ["+server+"]")
                    player=Server = server
            logger.info("SERVER="+servidor)
            Nro = Nro + 1
            regexp = re.compile(r"title='([^']+)'")
            match = regexp.search(data)
            if match is not None:
                fmt = match.group(1)
                fmt = fmt.replace("Calidad","").strip()
            regexp = re.compile(r"Duraci\xc3\xb3n:([^<]+)<")
            match = regexp.search(data)
            if match is not None:
                duracion = match.group(1).replace(".",":")
                if len(duracion.strip())>0:
                    duracion = duracion + " minutos"
            audio = audio.replace("Subt\xc3\xadtulos en Espa\xc3\xb1ol","Subtitulado")
            audio = audio.replace("Audio","").strip()
            data2 =  re.sub("<[^>]+>",">",data)
            data2 = data2.replace(">>>","").replace(">>","<")
            data2 = re.sub("[0-9:.]+","",data2)
            logger.info(data2)
            Video_info = ""
            regexp = re.compile(r"<(.+?)<")
            match = regexp.search(data2)
            if match is not None:
               
                Video_info = match.group(1)
                logger.info(Video_info)
                Video_info = "-%s" %Video_info.replace("Duraci\xc3\xb3n","").strip()
            else:
                regexp = re.compile(r">(.+?)<")
                match = regexp.search(data2)
                if match is not None:
               
                    Video_info = match.group(1)
                    logger.info(Video_info)
                    Video_info = "-%s" %Video_info.replace("Duraci\xc3\xb3n","").strip()               
            #opciones.append("%02d) [%s] - [%s] %s (%s%s)" % (Nro , audio,servidor,duracion,fmt,Video_info))
            title = "%02d) [%s] - [%s] %s (%s%s)" % (Nro , audio,servidor,duracion,fmt,Video_info)
           
            logger.info("Codigo " + id)
            if '&al=' in id:
                codigos = id.split('&al=')         
                url = Decrypt_Server(codigos[0],server)
                logger.info("url="+url)
                if "|" in url:
                    logger.info("partes")
                    itemPartes = Item (title=title, url=url, server=servidor, action="play",folder=False)
                    opciones = choiceOnePart(itemPartes, opciones)
                    #opciones.append(listaPartes)
            else:
                logger.info("1link")
                if "http" in id:
                    
                    opciones.append(Item (channel=CHANNELNAME, title=title, server=player, url=id, action="play2",folder=False) )
                else:
                    url = Decrypt_Server(id,player)
                    if "|" in url:
                        logger.info("1link con dos partes")
                        itemPartes = Item (title=title, url=url, server=Server, action="play",folder=False)
                        opciones = choiceOnePart(itemPartes, opciones)
                    else:                   
                        opciones.append(Item (channel=CHANNELNAME, title=title, server=Server, url=url, action="play",folder=False) )

        except urllib2.URLError,e:
            logger.info("[peliculasyonkis_generico.py] error:%s (%s)" % (e.code,server))
           
    return opciones

def play2(item):

    opciones = []
    if item.server in SERVER:
        servidor = SERVER[item.server]
        url = Decrypt_Server(item.url,item.server)
        if url == "":
            from core import xbmctools
            xbmctools.alertUnsopportedServer()
            servidor = "unknown"
            return []
    else:
        servidor = "desconocido ("+item.server+")"
        logger.info("[peliculasyonkis.py] SERVIDOR DESCONOCIDO ["+item.server+"]")
        url = ""
    if "|" in url:
        
        logger.info("1link con dos partes")
        itemPartes = Item (title=title, url=url, server=servidor, action="play",folder=False)
        opciones = choiceOnePart(itemPartes, opciones)
        
    else:
        #opciones.append(Item (channel=CHANNELNAME, title=item.title, server=servidor, url=url, action="play",folder=False) )
        from core import xbmctools
        xbmctools.playvideo(CHANNELNAME,servidor,url,item.category,item.title,item.thumbnail,item.plot,subtitle=item.subtitle)
    return opciones
def getId(url):
    logger.info("[peliculasyonkis.py] getId")
    #print url
    movielink = url
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        opener = urllib2.build_opener(SmartRedirectHandler())
        response = opener.open(req)
    except ImportError, inst:    
        status,location=inst
        logger.info(str(status) + " " + location)    
        movielink = location
    #print movielink

    try:
        id = re.compile(r'id=([A-Z0-9%]{0,})').findall(movielink)[0]
    except:
        id = ""
    
    return id
def Decrypt_Server(id_encoded,servidor):
    id = id_encoded
    DEC = Yonkis.DecryptYonkis()
    logger.info("Recibimos " + servidor + " y " + id_encoded)
    if "http" in id:
        id = getId(id_encoded)
    if   'pymeno2'   == servidor: idd=DEC.decryptID(DEC.charting(DEC.unescape(id)))   
    elif 'pymeno3'   == servidor: idd=DEC.decryptID(DEC.charting(DEC.unescape(id)))   
    elif 'pymeno4'   == servidor: idd=DEC.decryptID(DEC.charting(DEC.unescape(id)))   
    elif 'pymeno5'   == servidor: idd=DEC.decryptID_series(DEC.unescape(id))         
    elif 'pymeno6'   == servidor: idd=DEC.decryptID_series(DEC.unescape(id))     
    elif 'svueno'    == servidor:
        idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
        if ":" in idd:
            ids = idd.split(":")
            idd = "http://stagevu.com/video/%s|http://stagevu.com/video/%s" %(ids[0].strip(),ids[1].strip())
            
        else:
            idd = "http://stagevu.com/video/%s" %idd
    elif 'manueno'   == servidor:
        idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
        if len(idd)>50:
            
            idd = idd.replace("\n","|")
       
    elif 'videoweed' == servidor:
        idd= DEC.decryptID(DEC.charting(DEC.unescape(id)))
        if ":" in idd:
            ids = idd.split(":")
            idd = "http://www.videoweed.com/file/%s|http://www.videoweed.com/file/%s" %(ids[0].strip(),ids[1].strip())       
        else:
            idd = "http://www.videoweed.com/file/%s" %idd
    elif 'veoh2'     == servidor: idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
    elif 'megaupload'== servidor:
        idd=DEC.ccM(DEC.unescape(id))
        if ":" in idd:
            idd = idd.replace(":","|")
       
    elif 'pfflano'   == servidor:
        idd=DEC.decryptALT(DEC.charting(DEC.unescape(id)))
        logger.info(idd)
        idd = idd.replace("\n","|")
        
        return idd
       
    elif 'pya'  == servidor:
        return id
    else:
        return ""
   
    return idd
   
   
   
   
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        raise ImportError(302,headers.getheader("Location"))
   