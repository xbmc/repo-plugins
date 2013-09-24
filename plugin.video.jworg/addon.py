# -*- coding: UTF-8 -*-

# for utf-8 see http://www.python.org/dev/peps/pep-0263/

import xbmcplugin

import jw_config
import jw_video
import jw_audio_bible
import jw_audio_music

"""
START
"""

language     = xbmcplugin.getSetting(jw_config.pluginPid, "language")
print "JWORG language: " + language
if language == "":
	language = jw_config.t(30009)
	print "JWORG forced language: " + language

# call arguments
params 		 = jw_config.plugin_params

content_type = "video"
try:
	content_type = params["content_type"][0]
except:
	pass

mode = None
try:	
	mode = params["mode"][0]
except:
	pass

start = None
try:
	start = params["start"][0]        
except:
    pass


# Call router
if content_type == "video" and mode is None :
	jw_video.showVideoFilter(language)

if content_type == "video" and mode == "open_video_page" and start is not None:
	video_filter = params["video_filter"][0]	#Note: video_filter can be 'none', and it's a valid filter for jw.org !
	jw_video.showVideoIndex(language, start, video_filter)

if content_type == "video" and mode == "open_json_video":
	json_url = params["json_url"][0]
	jw_video.showVideoJsonUrl(language, json_url)

if content_type == "audio" and mode is None :
	jw_audio_bible.showAudioTypeIndex()

if content_type == "audio" and mode == "open_bible_index" :
	jw_audio_bible.showAudioBibleIndex(language)

if content_type == "audio" and mode == "open_bible_book_index"  :
	book_num = params["book_num"][0]
	jw_audio_bible.showAudioBibleBookJson(language, book_num)

if content_type == "audio" and mode == "open_music_index"  and start is not None: 
	jw_audio_music.showMusicIndex(language, start);

if content_type == "audio" and mode == "open_music_json" : 
	json_url = params["json_url"][0]
	jw_audio_music.showMusicJsonUrl(language, json_url);