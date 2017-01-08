# -*- coding: utf-8 -*-
import urllib, os, sys

import channel


menu = {'rtbfTV': {'name': 'TV Channels', 'icon': 'rtbf-all.png','module': 'rtbf','action': 'show_tv'},
            'rtbfRadio': {'name': 'Radio Channels', 'icon': 'radios.png','module': 'rtbf','action': 'show_radio'},
            'rtbfAll': {'name': 'All Shows', 'icon': 'rtbf.png','module': 'rtbf','action': 'show_program'},
            'rtbfCat': {'name': 'By Categories', 'icon': 'rtbf.png','module': 'rtbf','action': 'show_categories'},
            'rtbfLive': {'name': 'Directs', 'icon': 'rtbf.png','module': 'rtbf','action': 'show_lives'}
            }

def show_menu():
   for menu_id, ch in menu.iteritems():
        if channel.in_xbmc:
            icon = xbmc.translatePath(os.path.join(channel.home, 'resources/' + ch['icon']))
            channel.addDir(ch['name'], icon, channel_id=menu_id, action=ch['action'])
        else:
             xbmc.log(str(ch['name'])+' '+menu_id+' show_program',xbmc.LOGDEBUG)
    
            

     
def get_params():
    param = {}
    if len(sys.argv) < 3:
        return {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        xbmc.log(str(cleanedparams),xbmc.LOGDEBUG)
        pairsofparams = cleanedparams.split('&')
        xbmc.log(str(pairsofparams),xbmc.LOGDEBUG)
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                try:
                    param[splitparams[0]] = urllib.unquote_plus(splitparams[1])
                except:
                    pass
    return param
xbmc.log("===============================",xbmc.LOGDEBUG)
xbmc.log("  RTBF Auvio",xbmc.LOGDEBUG)
xbmc.log("===============================",xbmc.LOGDEBUG)


params = get_params()

channel_id = params.get('channel_id')
xbmc.log('channel_id:'+ channel_id,xbmc.LOGDEBUG)
if params.get('action', False) is False:
    show_menu()
elif channel_id:
    try:
	context = menu[channel_id]
    except:
    	try:
    	   context = channel.channelsTV[channel_id]
    	except:
           try:
    	      context = channel.channelsRadio[channel_id]
           except:
    	      context = channel.categories[channel_id]
    context.update(params)
    import sys
    channel_module_name = 'rtbf'
    __import__(channel_module_name)
    sys.modules[channel_module_name].Channel(context)

if channel.in_xbmc:
    channel.xbmcplugin.endOfDirectory(int(sys.argv[1]))				
