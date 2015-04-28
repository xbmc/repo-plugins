#Youtube channels
#
#
#
#
#
#Husham Memar
import re
import os
import sys
import urllib2
import buggalo
import xbmcgui
import xbmcaddon
import xbmcplugin

BASE_URL = 'http://iwaztv.com/?p=20'
PLAY_VIDEO_PATH = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
PLAYLIST_PATH = 'plugin://plugin.video.youtube/user/stampylonghead/'
PLAYLIST_PATH2 = 'plugin://plugin.video.youtube/user/stampylongnose/'
PLAYLIST_PATH3 = 'plugin://plugin.video.youtube/user/HushamMemarGames/'
PLAYLIST_PATH4 = 'plugin://plugin.video.youtube/user/PewDiePie/'
PLAYLIST_PATH5 = 'plugin://plugin.video.youtube/user/TheMasterOv/'
PLAYLIST_PATH6 = 'plugin://plugin.video.youtube/user/SSundee/'
PLAYLIST_PATH7 = 'plugin://plugin.video.youtube/user/Vikkstar123HD/'
PLAYLIST_PATH8 = 'plugin://plugin.video.youtube/user/Vikkstar123/'
PLAYLIST_PATH9 = 'plugin://plugin.video.youtube/user/TBNRfrags/'
PLAYLIST_PATH10 = 'plugin://plugin.video.youtube/user/TBNRkenworth/'
PLAYLIST_PATH11 = 'plugin://plugin.video.youtube/channel/UCxNMYToYIBPYV829BJcmUQg/'
PLAYLIST_PATH12 = 'plugin://plugin.video.youtube/channel/UCHRTfR2r0Ss3UjFyw7gSA-A/'
PLAYLIST_PATH13 = 'plugin://plugin.video.youtube/channel/UC7p-adWThwCeIQiQ6Hw505g/'
PLAYLIST_PATH14 = 'plugin://plugin.video.youtube/user/JeromeASF/'
PLAYLIST_PATH15 = 'plugin://plugin.video.youtube/user/MoreAliA/'
PLAYLIST_PATH16 = 'plugin://plugin.video.youtube/channel/UCpGdL9Sn3Q5YWUH2DVUW1Ug/'
PLAYLIST_PATH17 = 'plugin://plugin.video.youtube/user/GamingWithJen/'
PLAYLIST_PATH18 = 'plugin://plugin.video.youtube/user/MrWoofless/'
PLAYLIST_PATH19 = 'plugin://plugin.video.youtube/channel/UC9GXn5Y56nNDUNigTS2Ib4Q/'
PLAYLIST_PATH20 = 'plugin://plugin.video.youtube/user/TheBajanCanadian/'
PLAYLIST_PATH21 = 'plugin://plugin.video.youtube/user/BrenyBeast/'
PLAYLIST_PATH22 = 'plugin://plugin.video.youtube/user/HuskyMUDKIPZ/'
PLAYLIST_PATH23 = 'plugin://plugin.video.youtube/user/TheAtlanticCraft/'
PLAYLIST_PATH24 = 'plugin://plugin.video.youtube/user/TheDiamondMinecart/'
PLAYLIST_PATH25 = 'plugin://plugin.video.youtube/user/CreepersEdge/'
PLAYLIST_PATH26 = 'plugin://plugin.video.youtube/user/CraftBattleDuty/'
PLAYLIST_PATH27 = 'plugin://plugin.video.youtube/user/FearADubh/'
PLAYLIST_PATH28 = 'plugin://plugin.video.youtube/user/iBallisticSquid/'
PLAYLIST_PATH29 = 'plugin://plugin.video.youtube/user/DeadloxMC/'
PLAYLIST_PATH30 = 'plugin://plugin.video.youtube/user/LittleLizardGaming/'
PLAYLIST_PATH31 = 'plugin://plugin.video.youtube/user/prestonplayz/'
PLAYLIST_PATH32 = 'plugin://plugin.video.youtube/user/MisterCrainer/'

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    HANDLE = int(sys.argv[1])

    try:
        u = urllib2.urlopen(BASE_URL)
        html = u.read()
        u.close()


        m = re.search('//www.youtube.com/embed/([^"]+)"', html, re.DOTALL)
        if m:
            item = xbmcgui.ListItem('stampylonghead',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/stampycat%20pic.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH, item, True)
            item = xbmcgui.ListItem('stampylongnose',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/stampycat%20pic.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH2, item, True)
            item = xbmcgui.ListItem('Memar Games Channel',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/memar%20games.JPG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH3, item, True)
            item = xbmcgui.ListItem('PewDiePie',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/pewdiepie.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH4, item, True)
            item = xbmcgui.ListItem('TheMasterOv',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/themasterov.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH5, item, True)
            item = xbmcgui.ListItem('SSundee',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/ssundee.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH6, item, True)
            item = xbmcgui.ListItem('Vikkstar123HD',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/vikkstarhd.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH7, item, True)
            item = xbmcgui.ListItem('Vikkstar123',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/vikkstar.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH8, item, True)
            item = xbmcgui.ListItem('TBNRfrags/',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/tbnrfrags.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH9, item, True)
            item = xbmcgui.ListItem('TBNRkenworth',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/tbnrkenworth.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH10, item, True)
            item = xbmcgui.ListItem('PlayClashOfClans',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/playclashofclans.JPG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH11, item, True)
            item = xbmcgui.ListItem('ryguyrocky',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/ryguyrocky.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH12, item, True)
            item = xbmcgui.ListItem('Bayanidood',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/Bayanidood.JPG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH13, item, True)
            item = xbmcgui.ListItem('JeromeASF',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/Jerome.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH14, item, True)
            item = xbmcgui.ListItem('MoreAliA',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/more%20alia.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH15, item, True)
            item = xbmcgui.ListItem('PopularMMOs',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/pop.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH16, item, True)
            item = xbmcgui.ListItem('GamingWithJen',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/gamingwithjen.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH17, item, True)
            item = xbmcgui.ListItem('MrWoofless',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/mrwoofless.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH18, item, True)
            item = xbmcgui.ListItem('WillMcHD',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/mrwilliamo.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH19, item, True)
            item = xbmcgui.ListItem('TheBajanCanadian',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/banjancanadian.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH20, item, True)
            item = xbmcgui.ListItem('BrenyBeast',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/brenybeast.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH21, item, True)
            item = xbmcgui.ListItem('HuskyMUDKIPZ',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/huskymudkipz.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH22, item, True)
            item = xbmcgui.ListItem('TheAtlanticCraft',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/theatlanticcraft.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH23, item, True)
            item = xbmcgui.ListItem('TheDiamondMinecart',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/dantdm.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH24, item, True)
            item = xbmcgui.ListItem('CreepersEdge',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/creepersedge.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH25, item, True)
            item = xbmcgui.ListItem('CraftBattleDuty',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/lachlan.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH26, item, True)
            item = xbmcgui.ListItem('FearADubh',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/ashduhb.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH27, item, True)
            item = xbmcgui.ListItem('iBallisticSquid',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/ibillisticsquid.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH28, item, True)
            item = xbmcgui.ListItem('DeadloxMC',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/deadlox.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH29, item, True)
            item = xbmcgui.ListItem('LittleLizardGaming',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/littlelizardgaming.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH30, item, True)
            item = xbmcgui.ListItem('prestonplayz',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/preston.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH31, item, True)
            item = xbmcgui.ListItem('MisterCrainer',
                                    ADDON.getLocalizedString(30001),
                                    iconImage='https://raw.githubusercontent.com/hmemar/husham.com/master/repo/Haydar%20Games/Images/mistercrainer.PNG')
            xbmcplugin.addDirectoryItem(HANDLE, PLAYLIST_PATH32, item, True)
            
			
        xbmcplugin.endOfDirectory(HANDLE)
    except:
        buggalo.onExceptionRaised()
