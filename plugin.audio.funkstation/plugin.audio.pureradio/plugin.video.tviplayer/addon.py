#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: enen92 

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
"""

import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmc,xbmcaddon,xbmcvfs
import os,sys

from resources.common_variables import *
from resources.utilities import *
from resources.directory import *
from resources.webutils import *
from resources.ondemand import *

""" 40002 """
def main_menu():
    addDir(translate(40011) ,'http://tviplayer.iol.pt',40011, os.path.join(artfolder,'porcanal.png'),1)
    addDir(translate(40012) ,'http://tviplayer.iol.pt',40012, os.path.join(artfolder,'portema.png'),1)
    addDir(translate(40013) ,'http://tviplayer.iol.pt',40013, os.path.join(artfolder,'az.png'),1)
    addDir(translate(40014) ,'http://tviplayer.iol.pt',40014, os.path.join(artfolder,'pesquisa.png'),1)


""" 40011 """
def programas_canal_menu(name):
    canais = [['TVI','TVI','logo-TVI.png'],['TVI 24','TVI24','logo-TVI24.png'],['+TVI','MAIS_TVI','logo-MAIS_TVI.png'],['TVI Ficcao','TVI_FICCAO','logo-TVI_FICCAO.png'],['TVI Internacional','TVI_INTERNACIONAL','logo-TVI_INTERNACIONAL.png'],['Exclusivos','TVI_PLAYER','logo-Exclusivo.png']]
    for nome_canal ,codigo_canal,img_canal in canais:
        addDir(nome_canal,getListaProgramasUrl(canal=codigo_canal),15,os.path.join(artfolder,img_canal),len(canais))


""" 40012 """
def programas_categoria_menu(name):
    categorias = [['ARTE_CULTURA','Arte e Cultura'],['CONCURSO','Concurso'],['DESPORTO','Desporto'],['DOCUMENTARIO','Documentário'],['ENTRETENIMENTO','Entretenimento'],['ENTREVISTA_DEBATE','Entrevista/Debate'],['FILME','Filme'],['INFANTIL','Infantil'],['INFORMACAO','Informação'],['MUSICAL','Musical'],['NACIONAL_OUTROS','Nacional - outros'],['NOVELA_INTERNACIONAL','Novela internacional'],['NOVELA_NACIONAL','Novela nacional'],['OUTROS','Outros'],['RELIGIOSO','Religioso'],['SERIE_INTERNACIONAL','Série internacional'],['SERIE_NACIONAL','Série nacional'],['TALK_SHOW','Talk show'],['TECNOLOGIA','Tecnologia'] ]
    for cod_catgegoria ,nome_categoria in categorias:
        addDir(nome_categoria,getListaProgramasUrl(categoria= cod_catgegoria),15,os.path.join(artfolder,'por_tema.png'),len(categorias))


""" 40013 """
def programas_az_menu(name):
    alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    for letter in alphabet:
        addDir('[B]'+ letter +'[/B]',getListaProgramasUrl(letra=letter),15,os.path.join(artfolder,'az.png'),len(alphabet))



"""

Addon navigation is below
 
"""	


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
iconimage=None
plot=None

try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except:
    try:
        mode=params["mode"]
    except: pass
try: iconimage=urllib.unquote_plus(params["iconimage"])
except: pass
try: plot=urllib.unquote_plus(params["plot"])
except: pass

xbmc.log('TVI-KODI-PLAYER Mode: %s   URL: %s  Name: %s  IconImage: %s' % (str(mode), str(url),str(name),str(iconimage)))


if mode==None: main_menu()
elif mode==40002: main_menu()
elif mode==40011: programas_canal_menu(name)
elif mode==40012: programas_categoria_menu(name)
elif mode==40013: programas_az_menu(name)
elif mode==3: list_episodes(name,url,plot)
elif mode==13: list_tv_shows_info(name,url,iconimage,plot)
elif mode==14: list_emissoes(url)
elif mode==15: list_tv_shows(name,url)
elif mode==16: list_episodes(name,url,iconimage,plot)
elif mode==17: get_show_episode_parts(name,url,iconimage)
elif mode==40014: pesquisar()
elif mode==19: resultadosPesquisa(url)




xbmcplugin.endOfDirectory(int(sys.argv[1]))
