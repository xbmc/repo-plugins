import xbmcplugin

def getUserSettingAltPlayer(arg):
    uap = xbmcplugin.getSetting(arg,'useAltPlayer')
    v = False
    if(uap == "0"):
        v = True
    if(uap == "1"):
        v = False
    return v

def getUserSettingOSX(arg):
    osx = xbmcplugin.getSetting(arg,'isOSX')
    v = False
    if(osx == "0"):
        v = True
    if(osx == "1"):
        v = False
    return v

def getUserSettingCaUser(arg):
    cau = xbmcplugin.getSetting(arg,'caUser')
    v = False
    if(cau == "0"):
        v = True
    if(cau == "1"):
        v = False
    return v

def getUserSettingExpandEpisodes(arg):
    ee = xbmcplugin.getSetting(arg,'expandEpisodes')
    v = False
    if(ee == "0"):
        v = True
    if(ee == "1"):
        v = False
    return v


def getUserSettingDebug(arg):
    deb = xbmcplugin.getSetting(arg,'debug')
    v = False
    if(deb == "0"):
        v = True
    if(deb == "1"):
        v = False
    return v

def getUserSettingVerboseUserInfo(arg):
    vui = xbmcplugin.getSetting(arg,'verboseuser')
    v = False
    if(vui == "0"):
        v = True
    if(vui == "1"):
        v = False
    return v

def getUserSettingAppendYear(arg):
    ay = xbmcplugin.getSetting(arg,'appendYear')
    v = False
    if(ay == "0"):
        v = True
    if(ay == "1"):
        v = False
    return v

def getUserSettingYearLimit(arg):
    ylim = xbmcplugin.getSetting(arg, 'yearLimit')
    return str(ylim)

def getUserSettingShowRatingInTitle(arg):
    ay = xbmcplugin.getSetting(arg,'showRatingInTitle')
    v = False
    if(ay == "0"):
        v = True
    if(ay == "1"):
        v = False
    return v

def getUserSettingPosterQuality(arg):
    pqs = xbmcplugin.getSetting(arg,'pQuality')
    v = ""
    if(pqs == "0"):
        v = "ghd"
    if(pqs == "1"):
        v =  "large"
    if(pqs == "2"):
        v =  "medium"
    if(pqs == "3"):
        v =  "small"
    return v

def getUserSettingRatingLimit(arg):
    maxr = xbmcplugin.getSetting(arg,'mrLimit')
    v = ""
    if(maxr == "0"):
        v = "10000"
    elif(maxr == "1"):
        v =  "1000"
    elif(maxr == "2"):
        v =  "130"
    elif(maxr == "3"):
        v =  "110"
    elif(maxr == "4"):
        v =  "100"
    elif(maxr == "5"):
        v =  "90"
    elif(maxr == "6"):
        v =  "80"
    elif(maxr == "7"):
        v =  "75"
    elif(maxr == "8"):
        v =  "60"
    elif(maxr == "9"):
        v =  "50"
    elif(maxr == "10"):
        v =  "40"
    elif(maxr == "11"):
        v =  "20"
    elif(maxr == "12"):
        v =  "10"
    return v

def getUserSettingGenreDisplay(arg, sgGenre):
    vui = xbmcplugin.getSetting(arg, str(sgGenre))
    v = False
    if(vui == "0"):
        v = True
    if(vui == "1"):
        v = False
    return v

def getUserSettingMaxIQRetreve(arg):
    maxr = xbmcplugin.getSetting(arg,'maxIqR')
    v = ""
    if(maxr == "0"):
        v = "10"
    if(maxr == "1"):
        v =  "25"
    if(maxr == "2"):
        v =  "50"
    if(maxr == "3"):
        v =  "75"
    if(maxr == "4"):
        v =  "100"
    if(maxr == "5"):
        v =  "200"
    if(maxr == "6"):
        v =  "300"
    if(maxr == "7"):
        v =  "400"
    if(maxr == "8"):
        v =  "500"
    return v
