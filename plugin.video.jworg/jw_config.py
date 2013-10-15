# -*- coding: UTF-8 -*-

import xbmc
import xbmcgui
import xbmcplugin

import sys
import urlparse
import os

import jw_common

# key is english name, value is the name of the locale IN the locale
locale_2_lang = {
	"Italian"		: "Italiano",
	"Polish"		: "Polski",
	"Dutch"			: "Nederlands",
	"Spanish"		: "Español",
	"German"		: "Deutsch",
	"Portuguese" 	: "Português",
}

const = {
	"Italiano" 	: {
		"lang_code"					: "I",
		"video_path" 				: "http://www.jw.org/it/video",
		
		"bible_index_audio"			: "http://www.jw.org/it/pubblicazioni/bibbia/nwt/libri/",
		"bible_audio_json"  		: "http://www.jw.org/apps/I_TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=I",
		
		"magazine_index"			: "http://www.jw.org/it/pubblicazioni/riviste/",
		'has_simplified_edition'	: False,

		"music_index"				: "http://www.jw.org/it/pubblicazioni/musica-cantici/",
		"dramas_index"				: "http://www.jw.org/it/pubblicazioni/drammi-biblici-audio/",
		"dramatic_reading_index"	: "http://www.jw.org/it/pubblicazioni/brani-biblici-recitati/",
		
		'daily_text_json'			: "http://wol.jw.org/wol/dt/r6/lp-i",
		"date_format"				: "%d/%m/%Y",
		"news_index"				: "http://www.jw.org/it/news/",

 	},
	"English" 	: {
		"lang_code"					: "E",
		"video_path" 				: "http://www.jw.org/en/videos",
		
		"bible_index_audio"			: "http://www.jw.org/en/publications/bible/nwt/books/" ,
		"bible_audio_json"  		: "http://www.jw.org/apps/E_TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=E",
		
		"magazine_index"			: "http://www.jw.org/en/publications/magazines/",
		'has_simplified_edition'	: True,

		"music_index"				: "http://www.jw.org/en/publications/music-songs/",
		"dramas_index"				: "http://www.jw.org/en/publications/audio-bible-dramas/",
		"dramatic_reading_index"	: "http://www.jw.org/en/publications/dramatic-bible-readings/",

		'daily_text_json'			: "http://wol.jw.org/wol/dt/r1/lp-e",
		"date_format"				: "%Y-%m-%d",
		"news_index"				: "http://www.jw.org/en/news/",
	},
	"Polski" 	: {
		"lang_code"					: "P",
		"video_path" 				: "http://www.jw.org/pl/filmy/",
		
		"bible_index_audio"			: "http://www.jw.org/pl/publikacje/biblia/nwt/ksi%C4%99gi-biblijne/" , 
		"bible_audio_json"  		: "http://www.jw.org/apps/TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=P&txtCMSLang=P",
		
		"magazine_index"			: "http://www.jw.org/pl/publikacje/czasopisma/",
		'has_simplified_edition'	: False,

		"music_index"				: "http://www.jw.org/pl/publikacje/muzyka-pie%C5%9Bni/",
		"dramas_index"				: "http://www.jw.org/pl/publikacje/s%C5%82uchowiska-biblijne/",
		"dramatic_reading_index"	: "http://www.jw.org/pl/publikacje/adaptacje-d%C5%BAwi%C4%99kowe-biblii/",
		
		'daily_text_json'			: "http://wol.jw.org/wol/dt/r12/lp-p",
		"date_format"				: "%d-%m-%Y",
		"news_index"				: "http://www.jw.org/pl/wiadomo%C5%9Bci/"
	},	
	"Nederlands" : {
		"lang_code"					: "O",
		"video_path" 				: "http://www.jw.org/nl/videos/",

		"bible_index_audio"			: "http://www.jw.org/nl/publicaties/bijbel/nwt/boeken/" , 
		"bible_audio_json"  		: "http://www.jw.org/apps/TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=O&txtCMSLang=O", #last 2 are letters 'o' not zero
		
		"magazine_index"			: "http://www.jw.org/nl/publicaties/tijdschriften/",
		'has_simplified_edition'	: False,

		"music_index"				: "http://www.jw.org/nl/publicaties/muziek-liederen/",
		"dramas_index"				: "http://www.jw.org/nl/publicaties/audio-bijbel-dramas/",
		"dramatic_reading_index"	: "http://www.jw.org/nl/publicaties/bijbelse-hoorspelen/",
		
		'daily_text_json'			: "http://wol.jw.org/wol/dt/r18/lp-o",
		"date_format"				: "%d-%m-%Y",
		"news_index"				: "http://www.jw.org/nl/nieuws/"
	},	
	"Español" : {
		"lang_code"					: "S",
		"video_path" 				: "http://www.jw.org/es/videos/",

		"bible_index_audio"			: "http://www.jw.org/es/publicaciones/biblia/nwt/libros/" , 
		"bible_audio_json"  		: "http://www.jw.org/apps/TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=S&txtCMSLang=S",

		"magazine_index"			: "http://www.jw.org/es/publicaciones/revistas/",
		'has_simplified_edition'	: True,

		"music_index"				: "http://www.jw.org/es/publicaciones/m%C3%BAsica-c%C3%A1nticos/",
		"dramas_index"				: "http://www.jw.org/es/publicaciones/audio-representaciones-dram%C3%A1ticas/",
		"dramatic_reading_index"	: "http://www.jw.org/es/publicaciones/lecturas-b%C3%ADblicas-dramatizadas/",
		
		'daily_text_json'			: "http://wol.jw.org/wol/dt/r4/lp-s",
		"date_format"				: "%d-%m-%Y",
		"news_index"				: "http://www.jw.org/es/noticias/"
	},	
	"Deutsch" : {
		"lang_code"					: "X",
		"video_path" 				: "http://www.jw.org/de/videos/",

		"bible_index_audio"			: "http://www.jw.org/de/publikationen/bibel/nwt/bibelbuecher/" , 
		"bible_audio_json"  		: "http://www.jw.org/apps/TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=X&txtCMSLang=X",

		"magazine_index"			: "http://www.jw.org/de/publikationen/zeitschriften/",
		'has_simplified_edition'	: False,

		"music_index"				: "http://www.jw.org/de/publikationen/musik-lieder/",
		"dramas_index"				: "http://www.jw.org/de/publikationen/biblische-hoerspiele/",
		"dramatic_reading_index"	: "http://www.jw.org/de/publikationen/dramatische-bibellesungen/",
		
		'daily_text_json'			: "http://wol.jw.org/wol/dt/r10/lp-x",
		"date_format"				: "%d-%m-%Y",
		"news_index"				: "http://www.jw.org/de/aktuelle-meldungen/"
	},		
	"Português" : {
		"lang_code"					: "T",
		"video_path" 				: "http://www.jw.org/pt/videos/",

		"bible_index_audio"			: "http://www.jw.org/pt/publicacoes/biblia/nwt/livros/" , 
		"bible_audio_json"  		: "http://www.jw.org/apps/TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten=T&txtCMSLang=T",

		"magazine_index"			: "http://www.jw.org/pt/publicacoes/revistas/",
		'has_simplified_edition'	: True,

		"music_index"				: "http://www.jw.org/pt/publicacoes/musica-canticos/",
		"dramas_index"				: "http://www.jw.org/pt/publicacoes/dramas-biblicos-em-audio/",
		"dramatic_reading_index"	: "http://www.jw.org/pt/publicacoes/leituras-biblicas-dramatizadas/",
		
		'daily_text_json'			: "http://wol.jw.org/wol/dt/r5/lp-t",
		"date_format"				: "%d-%m-%Y",
		"news_index"				: "http://www.jw.org/pt/noticias/"
	},		
}


plugin_name 	= sys.argv[0]   # plugin://plugin.video.jworg/
pluginPid   	= int(sys.argv[1])
plugin_params 	= urlparse.parse_qs((sys.argv[2])[1:])
skin_used 		= xbmc.getSkinDir()
dir_media		= os.path.dirname(__file__) + os.sep + "resources" + os.sep + "media" + os.sep

try: 
	emulating = xbmcgui.Emulating
except: 
	emulating = False

try:
	import StorageServer
except:
	from resources.lib import storageserverdummy as StorageServer
	 
cache 			= StorageServer.StorageServer(plugin_name, 24)  # 2 hour cache
audio_sorting 	= str(int(xbmcplugin.getSetting(pluginPid, "audio_sorting")) + 1)
video_sorting 	= str(int(xbmcplugin.getSetting(pluginPid, "video_sorting")) + 1)

# if language is set, it used a localized language name, like "Italiano" or "Polski"
language		= xbmcplugin.getSetting(pluginPid, "language")

# if not set, language will be read from system, where it uses english language name
# if it's one of supported language, I got localized name to adhere to addon language setting 
# availables values ( Italiano, English, Polski, ... )

if language == "":
	actual_locale = xbmc.getLanguage()
	if actual_locale in locale_2_lang :
		language = locale_2_lang[actual_locale]
	else :
		language = "English"
