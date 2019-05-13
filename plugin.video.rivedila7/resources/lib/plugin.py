# -*- coding: utf-8 -*-
import re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
import urlparse
import html5lib
from bs4 import BeautifulSoup



addon = xbmcaddon.Addon()
language = addon.getLocalizedString
handle = int(sys.argv[1])
url_rivedila7 = "http://www.la7.it/rivedila7/0/la7"
url_rivedila7d = "http://www.la7.it/rivedila7/0/la7d"
url_programmi = "http://www.la7.it/programmi"
url_tutti_programmi = "http://www.la7.it/tutti-i-programmi"
url_tgla7d = "http://tg.la7.it/listing/tgla7d"
url_live = "http://www.la7.it/dirette-tv"
url_base = "http://www.la7.it"    
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'}
titolo_global = ''
thumb_global = ''
plot_global = ''
link_global = ''
pagenum = 0
list_programmi = []
tg_cronache = False
filtro_cronache = 'TG LA7 Cronache'
omnibus_news = False
filtro_omnibus = 'Omnibus News'
thumb_path = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
fanart_path = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'fanart.jpg')


def parameters_string_to_dict(parameters):
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict


def show_root_menu():
    ''' Show the plugin root menu '''
    liStyle = xbmcgui.ListItem('[B]'+language(32002)+'[/B]')
    liStyle.setArt({ 'thumb': os.path.join(thumb_path, 'direttalivela7.jpg'), 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": "diretta_live"},liStyle, folder=False)
    liStyle = xbmcgui.ListItem('[B]'+language(32007)+'[/B]')
    liStyle.setArt({ 'thumb': os.path.join(thumb_path, 'tgmeteo.jpg'), 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": "tg_meteo"},liStyle)    
    liStyle = xbmcgui.ListItem('[B]'+language(32001)+'[/B]')
    liStyle.setArt({ 'thumb': os.path.join(thumb_path, 'rivedila7.jpg'), 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": "rivedi_la7"},liStyle)
    liStyle = xbmcgui.ListItem('[B]'+language(32004)+'[/B]')
    liStyle.setArt({ 'thumb': os.path.join(thumb_path, 'rivedila7d.jpg'), 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": "rivedi_la7d"},liStyle)
    liStyle = xbmcgui.ListItem('[B]'+language(32006)+'[/B]')
    liStyle.setArt({ 'thumb': os.path.join(thumb_path, 'programmila7la7d.jpg'), 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": "tutti_programmi"},liStyle)

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def addDirectoryItem_nodup(parameters, li, title=titolo_global, folder=True):
    if title in list_programmi:
        xbmc.log('Prog Duplicato',xbmc.LOGNOTICE)
    else:
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        #xbmc.log('LIST: '+str(url),xbmc.LOGNOTICE)
        if not folder:
            li.setInfo('video', {})
            li.setProperty('isPlayable', 'true')
        return xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=folder)


def play_video(video,live):
    link_video = ''
    regex1 = "vS = '(.*?)'"
    regex2 = 'm3u8" : "(.*?)"'
    regex3 = 'm3u8: "(.*?)"'
    regex4 = '  <iframe src="(.*?)"'

    req = urllib2.Request(video,headers=headers)
    page=urllib2.urlopen(req)
    html=page.read();
    if live:
        if re.findall(regex1, html):
            link_video = re.findall(regex1, html)[0]
    else:
        if re.findall(regex2, html):
            link_video = re.findall(regex2, html)[0]
        elif re.findall(regex3, html):
            link_video = re.findall(regex3, html)[0]
        elif re.findall(regex4, html):
            iframe = re.findall(regex4, html)[0]
            req2 = urllib2.Request(iframe,headers=headers)
            page2=urllib2.urlopen(req2)
            html2=page2.read();
            if re.findall(regex2, html2):
                link_video = str("http:")+re.findall(regex2, html2)[0]

    listitem =xbmcgui.ListItem(titolo_global)
    listitem.setInfo('video', {'Title': titolo_global})
    if (thumb_global != ""):
        listitem.setArt({ 'thumb': thumb_global})
    listitem.setInfo('video', { 'plot': plot_global })
    if link_video == '':
        xbmc.log('NO VIDEO LINK',xbmc.LOGNOTICE)
        if xbmcgui.Dialog().ok(addon.getAddonInfo('name'), language(32005)):
            exit()
    else:
        listitem.setProperty('inputstreamaddon','inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type','hls')
        listitem.setPath(link_video)
        xbmcplugin.setResolvedUrl(handle, True, listitem)


def rivedi(url, thumb):
    req = urllib2.Request(url,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page,'html5lib')
    giorno=html.find(id="giorni").find_all('div' ,class_='giorno')
    if giorno:
        for div in reversed(giorno):
            dateDay=div.find('div',class_='dateDay')
            dateMonth=div.find('div',class_='dateMonth')
            dateRowWeek=div.find('div',class_='dateRowWeek')
            a=div.a.get('href')
            liStyle = xbmcgui.ListItem(dateRowWeek.contents[0]+" "+dateDay.contents[0]+" "+dateMonth.contents[0])
            liStyle.setArt({ 'thumb': os.path.join(thumb_path, thumb), 'fanart' : fanart_path })
            addDirectoryItem_nodup({"mode": mode,"giorno": a}, liStyle)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)    


def rivedi_giorno():
    req = urllib2.Request(url_base+giorno,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page,'html5lib')
    guida_tv=html.find(id="content_guida_tv").find_all('div' ,class_='disponibile')
    if guida_tv:
        for div in guida_tv:
            nome=div.find('div',class_='titolo clearfix').a.contents[0].encode('utf-8')
            thumb=div.find('img')['src']
            try:
                plot=div.find('div',class_='descrizione').p.contents[0]
            except Exception as e:
                e = sys.exc_info()[0]
                xbmc.log('EXCEP PLOT_R7: '+str(e),xbmc.LOGNOTICE)
                plot=""
            link_url = div.find('div',class_='titolo').a.get('href')
            if "tg.la7.it" in link_url:
                urll=div.find('div',class_='titolo').a.get('href')
            else:
                urll=url_base+div.find('div',class_='titolo').a.get('href')
            #xbmc.log('------LINK------: '+str(urll),xbmc.LOGNOTICE)
            orario=div.find('div',class_='orario').contents[0].encode('utf-8')
            liStyle = xbmcgui.ListItem(orario+" "+nome)
            liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
            liStyle.setInfo('video', { 'plot': plot })
            liStyle.setProperty('isPlayable', 'true')
            url2 = sys.argv[0] + '?' + urllib.urlencode({"mode": mode,"play": urll,"titolo": nome,"thumb":thumb,"plot":plot.encode('utf-8')})
            xbmcplugin.addDirectoryItem(handle=handle, url=url2, listitem=liStyle, isFolder=False)

    xbmcplugin.setContent(handle, 'episodes')
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def programmi_lettera():
    req_p = urllib2.Request(url_programmi,headers=headers) 
    page_p=urllib2.urlopen(req_p)
    html_p=BeautifulSoup(page_p,'html5lib') 
    programmi=html_p.find(id='colSx').find_all('div',class_='element_menu')
    req_tp = urllib2.Request(url_tutti_programmi,headers=headers) 
    page_tp=urllib2.urlopen(req_tp)
    html_tp=BeautifulSoup(page_tp,'html5lib') 
    tutti_programmi=html_tp.find(id='colSx').find_all('div',class_='itemTuttiProgrammi')    

    if programmi or tutti_programmi:
        for dati in programmi:
            titolo=dati.find('span',class_='black_overlay').contents[0].encode('utf-8').strip()
            #xbmc.log('TITLE1: '+str(titolo),xbmc.LOGNOTICE)
            liStyle = xbmcgui.ListItem(titolo)
            url_trovato=dati.a.get('href')
            if url_trovato != '/meteola7':
                if url_trovato == '/facciaafaccia':
                    url_trovato='/faccia-a-faccia'
                link=url_base+url_trovato
                if(len(dati)>0):
                    try:
                        thumb=dati.find('img')['src']
                    except Exception as e:
                        e = sys.exc_info()[0]
                        xbmc.log('EXCEP THUMB1: '+str(e),xbmc.LOGNOTICE)
                        thumb = None
                    if thumb:
                        liStyle.setArt({ 'thumb': thumb})
                    else:
                        xbmc.log('NO THUMB1',xbmc.LOGNOTICE)     
                liStyle.setArt({ 'fanart' : fanart_path })
                addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)
                list_programmi.append(titolo)

        for dati in tutti_programmi:
            titolo=dati.find('span',class_='field-content').a.contents[0].encode('utf-8').strip()
            #xbmc.log('TITLE2: '+str(titolo),xbmc.LOGNOTICE)
            liStyle = xbmcgui.ListItem(titolo)
            url_trovato=dati.find('div',class_='wrapperTestualeProgrammi').a.get('href')
            link=url_base+url_trovato
            img=dati.find('div',class_='wrapperImgProgrammi').find('div',class_='field-content')
            if(len(dati)>0):
                try:
                    thumb=dati.find('img')['src']
                except Exception as e:
                    e = sys.exc_info()[0]
                    xbmc.log('EXCEP THUMB2: '+str(e),xbmc.LOGNOTICE)
                    thumb = None
                if thumb:
                    liStyle.setArt({ 'thumb': thumb})
                else:
                    xbmc.log('NO THUMB2',xbmc.LOGNOTICE)     
            liStyle.setArt({ 'fanart' : fanart_path })
            addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)

        #Prog aggiunti manualmente
        programmi = {
            'Artedì': {
                'url': '/artedi',
                'img': 'http://www.la7.it/sites/default/files/lanci/img/artedi.jpg',
                },
            'Bellezze in Bicicletta': {
                'url': '/bellezzeinbicicletta',
                'img': 'http://www.la7.it/sites/default/files/property/header/home/testata-prova.jpg',
                },
            'Bianco e Nero': {
                'url': '/biancoenero',
                'img': 'http://www.la7.it/sites/default/files/property/header/home/header_home_property_ben.png',
                },
            'Eccezionale Veramente 2016': {
                'url': '/eccezionale-veramente',
                'img': 'http://www.la7.it/sites/default/files/property/header/home/header_property_home_ev.png',
                },
            'Eccezionale Veramente 2017': {
                'url': '/eccezionale-veramente-2017',
                'img': 'http://www.la7.it/sites/default/files/property/header/home/ev_2017_header_home_property.jpg',
                },
            'Italian Fashion Show': {
                'url': '/italia-fashion-show',
                'img': 'http://kdam.iltrovatore.it/p/103/sp/10300/thumbnail/entry_id/0_8j9ei136/version/100000/type/5/width/600/height/360/quality/100/name/0_8j9ei136.jpg'
                },
            "L'ora della salute": {
                'url': '/lora-della-salute',
                'img': 'http://www.la7.it/sites/default/files/property/header/home/ora_della_salute_header_hp_property_0.png',
                },
            'La mala educaxxxion (La7)': {
                'url': '/la-mala-educaxxxion',
                'img': 'http://kdam.iltrovatore.it/p/103/sp/10300/thumbnail/entry_id/0_j0z82ps2/version/100001/type/5/width/600/height/360/quality/100/name/0_j0z82ps2.jpg'
                },
            'Missione Natura': {
                'url': '/missione-natura',
                'img': 'http://kdam.iltrovatore.it/p/103/sp/10300/thumbnail/entry_id/0_qadv09vo/version/100000/type/5/width/600/height/360/quality/100/name/0_qadv09vo.jpg',
                },                 
            'Special Guest': {
                'url': '/specialguest',
                'img': 'http://www.la7.it/sites/default/files/property/header/home/formato%20large_dx.jpg',
                },              
            'Video non catalogati (Doc & Altro)': {
                'url': '/non-classificati',
                'img': '',
                },
            'Video non catalogati (Film & Serie)': {
                'url': '/film',
                'img': '',
                },
        }
        for programma, program_info in programmi.items():
            titolo = programma
            liStyle = xbmcgui.ListItem(titolo)
            url_trovato = program_info['url']
            link = url_base + url_trovato
            thumb = program_info['img']
            liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
            addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)

        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def programmi_lettera_tg_meteo():
    titolo = 'TG La7'
    liStyle = xbmcgui.ListItem(titolo)
    url_trovato = '/tgla7'
    link = url_base + url_trovato
    thumb = os.path.join(thumb_path, 'tgla7.jpg')
    liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)
    
    titolo = 'TG La7d'
    liStyle = xbmcgui.ListItem(titolo)
    link = url_tgla7d
    thumb = os.path.join(thumb_path, 'tgla7d.jpg')
    liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)

    # (rimosso temporaneamente per mancanza di contenuti)
    # titolo = 'TG Cronache'
    # liStyle = xbmcgui.ListItem(titolo)
    # link = 'flag_tg_cronache'
    # thumb = os.path.join(thumb_path, 'tgcronache.jpg')
    # liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
    # addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)
    
    titolo = 'Omnibus News'
    liStyle = xbmcgui.ListItem(titolo)
    link = 'flag_omnibus_news'
    thumb = os.path.join(thumb_path, 'omnibusnews.jpg')
    liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo) 

    titolo = 'Meteo La7'
    liStyle = xbmcgui.ListItem(titolo)
    url_trovato = '/meteola7'
    link = url_base+url_trovato
    thumb = os.path.join(thumb_path, 'meteo.jpg')
    liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
    addDirectoryItem_nodup({"mode": mode,"link": link}, liStyle, titolo)          

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def video_programma():
    global link_global
    global tg_cronache
    global omnibus_news

    if link_global == 'flag_tg_cronache':
        tg_cronache = True
        link_global = url_base+'/tgla7'
    #xbmc.log('-----LINK-----'+str(link_global),xbmc.LOGNOTICE)
    
    if link_global == 'flag_omnibus_news':
        omnibus_news = True
        link_global = url_base+'/omnibus'
    
    if link_global != url_tgla7d:
        req = urllib2.Request(link_global+"/rivedila7",headers=headers)
        try:
            page=urllib2.urlopen(req)
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP URL: '+str(e),xbmc.LOGNOTICE)
            if xbmcgui.Dialog().ok(addon.getAddonInfo('name'), language(32005)):
                exit()
        html=BeautifulSoup(page,'html5lib')

        if pagenum == 0:
            # Video first
            if html.find('div',class_='contenitoreUltimaReplicaLa7'):
                first = html.find('div',class_='contenitoreUltimaReplicaLa7')
            elif html.find('div',class_='contenitoreUltimaReplicaLa7d'):
                first = html.find('div',class_='contenitoreUltimaReplicaLa7d')
            elif html.find('div',class_='contenitoreUltimaReplicaNoLuminosa'):
                first = html.find('div',class_='contenitoreUltimaReplicaNoLuminosa')
            else:
                xbmc.log('NO FIRST VIDEO',xbmc.LOGNOTICE)
                if xbmcgui.Dialog().ok(addon.getAddonInfo('name'), language(32005)):
                    exit()
            titolo = first.find('div',class_='title').text.encode('utf-8')
            
            if tg_cronache == True:
                first_video(first, titolo, titolo.find(filtro_cronache) != -1)
            elif omnibus_news == True:
                first_video(first, titolo, titolo.find(filtro_omnibus) != -1)
            elif link_global == url_base+'/tgla7':
                first_video(first, titolo, titolo.find(filtro_cronache) == -1)
            elif link_global == url_base+'/omnibus':
                first_video(first, titolo, titolo.find(filtro_omnibus) == -1)
            else:
                first_video(first, titolo, True)


            # Video week
            if html.find('li',class_='switchBtn settimana'):
                video_settimana = html.find(id='block-la7it-repliche-la7it-repliche-contenuto-tid').find_all('div',class_='views-row')
                if video_settimana:
                    get_rows_video(video_settimana)

        # Video archive
        if html.find('li',class_='switchBtn archivio'):
            if link_global == url_base+'/chi-sceglie-la-seconda-casa':
                req2 = urllib2.Request(link_global+"/rivedila7",headers=headers)
            else:
                req2 = urllib2.Request(link_global+"/rivedila7/archivio?page="+str(pagenum),headers=headers)
            page2 = urllib2.urlopen(req2)
            html2 = BeautifulSoup(page2,'html5lib')
            video_archivio = html2.find(id='block-la7it-repliche-la7it-repliche-contenuto-tid').find_all('div',class_='views-row')
            if video_archivio:
                get_rows_video(video_archivio)

                if (link_global != url_base+'/tgla7') and (link_global != url_base+'/omnibus'):
                    page=html2.find('li',class_='pager-next')
                    pagenext(page)
    #Tg La7d
    else:
        req = urllib2.Request(url_tgla7d+"?page="+str(pagenum),headers=headers)
        page = urllib2.urlopen(req)
        html=BeautifulSoup(page,'html5lib')
        video_tgla7d = html.find('div',class_='tgla7-category').find_all('article',class_='tgla7-new clearfix')
        if video_tgla7d:
            get_rows_video_tgla7d(video_tgla7d)
            page=html.find('li',class_='next')
            pagenext(page)
            
    xbmcplugin.setContent(handle, 'episodes')
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)



def first_video(first, titolo, filtro):
    if filtro:
        thumb=first.find('div',class_='kaltura-thumb').find('img')['src']
        data='[I] - ('+first.find('div',class_='dataPuntata').text.encode('utf-8')+')[/I]'
        try:
            plot=first.find('div',class_='views-field-field-testo-lancio').find('p').text.encode('utf-8')
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP PLOT1: '+str(e),xbmc.LOGNOTICE)
            plot=""
        link=url_base+first.find('a',class_='clearfix').get('href')
        liStyle = xbmcgui.ListItem(titolo+data)
        liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
        liStyle.setInfo('video', { 'plot': plot })
        addDirectoryItem_nodup({"mode": mode,"play": link,"titolo": titolo+data,"thumb":thumb,"plot":plot}, liStyle, folder=False)


def video_list(div, titolo, filtro):
    if filtro:
        thumb=div.find('div',class_='kaltura-thumb').find('img')['data-src']
        data='[I] - ('+div.find('div',class_='dataPuntata').text.encode('utf-8')+')[/I]'
        plot=div.find('div',class_='views-field-field-testo-lancio').text.encode('utf-8')
        link=url_base+div.find('a',class_='thumbVideo').get('href')
        liStyle = xbmcgui.ListItem(titolo+data)
        liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
        liStyle.setInfo('video', { 'plot': plot })
        addDirectoryItem_nodup({"mode": mode,"play": link,"titolo": titolo+data,"thumb":thumb,"plot":plot}, liStyle, folder=False)


def get_rows_video(video):
    for div in video:
        titolo=div.find('div',class_='title').a.text.encode('utf-8')
        #xbmc.log('TITOLO: '+str(titolo.find(filtro_cronache)),xbmc.LOGNOTICE)
        if tg_cronache == True:
            video_list(div, titolo, titolo.find(filtro_cronache) != -1)
        elif omnibus_news == True:
            video_list(div, titolo, titolo.find(filtro_omnibus) != -1)
        elif link_global == url_base+'/tgla7':
            video_list(div, titolo, titolo.find(filtro_cronache) == -1)
        elif link_global == url_base+'/omnibus':
            video_list(div, titolo, titolo.find(filtro_omnibus) == -1)
        else:
            video_list(div, titolo, True)


def get_rows_video_tgla7d(video):
    for div in video:
        titolo=div.find('div',class_='tgla7-condividi').get('data-title').encode('utf-8').strip()
        thumb_link=div.find('div',class_='tgla7-img').get('style')
        thumb = thumb_link[22:-1]
        #xbmc.log('THUMB: '+str(thumb),xbmc.LOGNOTICE)
        try:
            plot=div.find('div',class_='tgla7-descrizione').text.encode('utf-8').strip()
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP PLOT_TGLA7d: '+str(e),xbmc.LOGNOTICE)
            plot=""
        link=div.find('div',class_='tgla7-condividi').get('data-share')
        liStyle = xbmcgui.ListItem(titolo)
        liStyle.setArt({ 'thumb': thumb, 'fanart' : fanart_path })
        liStyle.setInfo('video', { 'plot': plot })
        addDirectoryItem_nodup({"mode": mode,"play": link,"titolo": titolo,"thumb":thumb,"plot":plot}, liStyle, folder=False)              


def pagenext(pagenb):
            if pagenb:
                liStyle = xbmcgui.ListItem('[B]'+language(32003)+'[/B]')
                liStyle.setArt({ 'fanart' : fanart_path })
                addDirectoryItem_nodup({"mode": mode,"link":link_global,"page":pagenum+1}, liStyle)




# Main             
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
giorno = str(params.get("giorno", ""))
play=str(params.get("play", ""))
titolo_global=str(params.get("titolo", ""))
thumb_global=str(params.get("thumb", ""))
plot_global=str(params.get("plot", ""))
link_global=str(params.get("link", ""))


if params.get("page", "")=="":
    pagenum=0;
else:
    pagenum=int(params.get("page", ""))

if mode=="diretta_live":
    titolo_global=language(32002)
    play_video(url_live,True)    

elif mode=="tg_meteo":
    if play=="":
        if link_global=="":
            programmi_lettera_tg_meteo()
        else:
            video_programma()
    else:
        play_video(play,False)  

elif mode=="rivedi_la7":
    if play=="":
        if giorno=="":
            rivedi(url_rivedila7, 'rivedila7.jpg')
        else:
            rivedi_giorno()
    else:
        play_video(play,False)

elif mode=="rivedi_la7d":
    if play=="":
        if giorno=="":
            rivedi(url_rivedila7d, 'rivedila7d.jpg')
        else:
            rivedi_giorno()
    else:
        play_video(play,False)

elif mode=="tutti_programmi":
    if play=="":
        if link_global=="":
            programmi_lettera()
        else:
            video_programma()
    else:
        play_video(play,False)

else:
    show_root_menu()
    



