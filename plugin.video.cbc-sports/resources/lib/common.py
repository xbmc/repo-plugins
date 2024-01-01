from datetime import datetime, timedelta as td
import time
import xbmcgui, xbmcaddon, xbmcplugin, xbmc


def timeConvert(orgtime):				#  Verify CBC Sports time format


    try:
        if len(orgtime) == 20 and orgtime[2] == '/' and orgtime[5] == '/' and orgtime[13] == ':':
            retime = orgtime
        elif orgtime[13] != ':' and len(orgtime) == 19:
            retime = retime[:13] + ':' + retime[13:]
        elif orgtime[2] != '/' and len(orgtime) == 19:
            retime = retime[:2] + '/' + retime[2:]
        elif orgtime[5] != '/' and len(orgtime) == 19:
            retime = retime[:5] + '/' + retime[5:]
        else:
            retime = 'invalid'

        if int(orgtime[11:13]) > 23:
            retime = 'invalid'     

        return(retime)
    except:
        return('invalid')  


def logging_level(cbclog):	
	if cbclog == 1:
	    xbmc.log('CBC Sports addon logging level is Normal.', xbmc.LOGINFO)
	if cbclog == 2:
	    xbmc.log('CBC Sports addon logging level is Detailed.', xbmc.LOGINFO)


def hnightUrl(name, response, cbclog):

    target = '<li><a href="http://cbc.ca/1.'

    i = 0
    mifound = 0
    findpos = 0
    count = response.count(target)

    stitlepos = name.find('Canada: ')
    etitlepos = name.find('[COLOR blue]', stitlepos)
    ptitle = name[stitlepos+8:etitlepos]
    hntarget = ptitle.split(' ')[0]
    if cbclog >= 1:
        xbmc.log('CBC Sports hnightUrl hntarget: ' + hntarget, xbmc.LOGINFO)
        xbmc.log('CBC Sports hnightUrl ptitle: ' + ptitle, xbmc.LOGINFO)
    

    while i < count and mifound == 0:
        findpos = response.find(target, findpos)
        if findpos > 0:
            mediaidpos = response.find('1.',findpos) 
            mediaid = response[mediaidpos:mediaidpos+9]
            findpos = response.find('<strong>', findpos)
            stoppos = response.find('</strong>', findpos)       
            responsep = response[findpos+8:stoppos]
            if cbclog >= 1:
                xbmc.log('CBC Sports hnightUrl name: ' + name, xbmc.LOGINFO)
                xbmc.log('CBC Sports hnightUrl response: ' +  responsep, xbmc.LOGINFO)
                xbmc.log('CBC Sports hnightUrl mediaId: ' + mediaid, xbmc.LOGINFO)
            if hntarget in responsep:
                if cbclog >= 1:
                    xbmc.log('CBC Sports hnightUrl found: '  + mediaid, xbmc.LOGINFO)
                mifound = 1
                return(mediaid)
        i += 1
    return('0')
        



