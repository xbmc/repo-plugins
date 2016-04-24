import os
import sys
import xbmc
from xbmc import log
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
import urlparse
import html5lib
from bs4 import BeautifulSoup
import re

addon = xbmcaddon.Addon()
language = addon.getLocalizedString
handle = int(sys.argv[1])
url_rivedi="http://www.la7.it/rivedila7"
#url_tutti_programmi="http://www.la7.it/tutti-i-programmi"
url_live="http://www.la7.it/dirette-tv"
url_base="http://www.la7.it"
headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'}

def parameters_string_to_dict(parameters):
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict
def show_root_menu():
    ''' Show the plugin root menu '''
    liStyle = xbmcgui.ListItem(language(32001))
    addDirectoryItem({"mode": "rivedi_la7"},liStyle)
    liStyle = xbmcgui.ListItem(language(32002))
    addDirectoryItem({"mode": "diretta_live"},liStyle)
    #liStyle = xbmcgui.ListItem("Tutti i programmi")
    #addDirectoryItem({"mode": "tutti_programmi"},liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def addDirectoryItem(parameters, li):
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=True)

def rivedi_la7():
    req = urllib2.Request(url_rivedi,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page,'html5lib')
    giorno=html.find(id="giorni").find_all('div' ,class_='giorno')
    if giorno is not None:
        i=0;
        for div in giorno:
            if(i>0):
                dateDay=div.find('div',class_='dateDay')
                dateMonth=div.find('div',class_='dateMonth')
                dateRowWeek=div.find('div',class_='dateRowWeek')
                a=div.a.get('href')
                liStyle = xbmcgui.ListItem(dateRowWeek.contents[0]+" "+dateDay.contents[0]+" "+dateMonth.contents[0])
                addDirectoryItem({"mode": "rivedi_la7","giorno": a}, liStyle)
            else:
                i=1;
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
def get_video_link(url):
    req = urllib2.Request(url,headers=headers) 
    page=urllib2.urlopen(req)
    html=page.read();
    res=re.findall('src_mp4 : "(.*?)"', html)
    if res:
        return res[0]
def play_video(video):
    if "la7.it" in video:
        link_video=get_video_link(video)
    else:
        link_video=get_video_link(url_base+video)       
    listitem =xbmcgui.ListItem(titolo_global)
    listitem.setInfo('video', {'Title': titolo_global})
    if (thumb_global != ""):
        listitem.setArt({ 'thumb': thumb_global})
    xbmc.Player().play(link_video, listitem)
def rivedi_la7_giorno():
    req = urllib2.Request(url_base+giorno,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page,'html5lib')
    guida_tv=html.find(id="content_guida_tv").find_all('div' ,class_='disponibile')
    if guida_tv is not None:
        for div in guida_tv:
            nome=div.find('div',class_='titolo clearfix').a.contents[0].encode('utf-8')
            thumb=div.find('img')['src']
            plot=div.find('div',class_='descrizione').p.contents[0]
            urll=div.find('div',class_='titolo').a.get('href')
            orario=div.find('div',class_='orario').contents[0].encode('utf-8')
            liStyle = xbmcgui.ListItem(orario+" "+nome)
            liStyle.setArt({ 'thumb': thumb})
            liStyle.setInfo('video', { 'plot': plot })
            url2 = sys.argv[0] + '?' + urllib.urlencode({"mode": "rivedi_la7","play": urll,"titolo": nome,"thumb":thumb})
            xbmcplugin.addDirectoryItem(handle=handle, url=url2,listitem=liStyle, isFolder=False)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
'''def tutti_programmi():
    req = urllib2.Request(url_tutti_programmi,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page)        
    lettere=html.find(id='colSx').find('div',class_='view-content').find_all('h3')
    if lettere is not None:
        i=0;
        for h3 in lettere:
            liStyle = xbmcgui.ListItem(lettere[i].contents[0])
            addDirectoryItem({"mode": "tutti_programmi","lettera": lettere[i].contents[0]}, liStyle)
            i=i+1
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
def programmi_lettera():
    req = urllib2.Request(url_tutti_programmi,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page) 
    programmi=html.find(id='colSx').find_all('div',class_='itemTuttiProgrammi')
    if programmi is not None:
        for span in programmi:
            titolo=span.find('span',class_='field-content').a.contents[0].encode('utf-8')
            if(titolo[0:1]==lettera_global):
                liStyle = xbmcgui.ListItem(titolo)
                link=url_base+span.find('div',class_='wrapperTestualeProgrammi').a.get('href')
                img=span.find('div',class_='wrapperImgProgrammi').find('div',class_='field-content')
                if(len(img)>0):
                    thumb=img.find('img')['src']
                    if thumb is not None:
                        liStyle.setArt({ 'thumb': thumb})
                addDirectoryItem({"mode": "tutti_programmi","link": link}, liStyle)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
def video_programma():
    req = urllib2.Request(link_global,headers=headers) 
    page=urllib2.urlopen(req)
    html=BeautifulSoup(page)         
    video=html.find(id='colSx').find_all('div',class_='item_la7_repliche')
    if video is not None:
        for div in video:
            thumb=div.find('div',class_='kaltura-thumb').find('img')['data-src']
            titolo=div.find('div',class_='views-field views-field-title views-field-title-inPropertyPage').a.contents[0]
            log("link %s"% titolo)'''
    
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
giorno = str(params.get("giorno", ""))
play=str(params.get("play", ""))
titolo_global=str(params.get("titolo", ""))
thumb_global=str(params.get("thumb", ""))
#lettera_global=str(params.get("lettera", ""))
#link_global=str(params.get("link", ""))
if mode=="rivedi_la7":
    if play=="":
        if giorno=="":
            rivedi_la7()
        else:
            rivedi_la7_giorno()
    else:
        play_video(play)
#elif mode=="tutti_programmi":
#    if link_global=="":
#        if lettera_global=="":
#            tutti_programmi()
#        else:
#            programmi_lettera()
#    else:
#        video_programma()
elif mode=="diretta_live":
    titolo_global=language(32002)
    thumb_global=""
    play_video(url_live)
else:
    show_root_menu()
