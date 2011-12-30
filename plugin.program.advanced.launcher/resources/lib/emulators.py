# -*- coding: UTF-8 -*-

import os
import re
import urllib

def _get_program_arguments( app ):
    # Based on the app. name, retrieve the default arguments for the app.
    app = app.lower()
    applications = {
        'bsnes': '"%rom%"',
        'chromium': '-kiosk "%rom%"',
        'dosbox': '"%rom%" -fullscreen',
        'epsxe': '-nogui -loadiso "%rom%"',
        'fbas': '-g %romname%',
        'fceux': '"%rom%"',
        'fusion': '"%rom%"',
        'gens': '--fs --quickexit "%rom%"',
        'lxdream': '-f "%rom%"',
        'mame': '"%rom%"',
        'mednafen': '-fs 1 "%rom%"',
        'mess': '-cart "%rom%" -skip_gameinfo -nowindow -nonewui',
        'mupen64plus': '--nogui --noask --noosd --fullscreen "%rom%"',
        'nestopia': '"%rom%"',
        'nullDC': '-config ImageReader:defaultImage="%rom%"',
        'osmose': '-fs "%rom%"',
        'project64': '%rom%',
        'vbam': '--opengl=MODE --fullscreen -f 15 --no-show-speed "%rom%"',
        'visualboyadvance': '"%rom%"',
        'x64': '-fullscreen -autostart "%rom%"',
        'xbmc': 'PlayMedia(%rom%)',
        'yabause': '-a -f -i "%rom%"',
        'zsnes': '-m -s -v 22 "%rom%"',
        'zsnesw': '-m -s -v 41 "%rom%"',
        'explorer.exe': '%rom%',
    }
    for application, arguments in applications.iteritems():
        if (app.find(application) >= 0):
            return arguments
    return '"%rom%"'


def _get_program_extensions( app ):
    # Based on the app. name, retrieve the recognized extension of the app.
    app = app.lower()
    applications = {
        'bsnes': 'zip|smc|sfc',
        'chromium': 'swf',
        'dosbox': 'bat',
        'epsxe': 'iso|bin|cue',
        'fbas': 'zip',
        'fceux': 'nes|zip',
        'fusion': 'zip|bin|sms|gg',
        'gens': 'zip|bin',
        'lxdream': 'cdi|iso|bin',
        'mame': 'zip',
        'mednafen': 'zip|pce|gba|gb|gbc|lnx|ngc|ngp|wsc|ws',
        'mess': 'zip|nes|sms|gg|rom|a78|a52|a26|gb|gbc|gba|int|bin|sg|pce|smc',
        'mupen64plus': 'z64|zip|n64',
        'nestopia': 'nes|zip',
        'nullDC': 'gdi|cdi',
        'osmose': 'zip|sms|gg',
        'project64': 'z64|zip|n64',
        'vbam': 'gba|gb|gbc|zip',
        'visualboyadvance': 'gba|gb|gbc|zip',
        'x64': 'zip|d64|c64',
        'yabause': 'cue',
        'zsnes': 'zip|smc|sfc',
        'explorer.exe': 'lnk',
    }
    for application, extensions in applications.iteritems():
        if (app.find(application) >= 0):
            return extensions
    return ""


def _get_mame_title(filename):
    try:
        f = urllib.urlopen('http://maws.mameworld.info/minimaws/set/'+filename)
        page = f.read().replace('\r\n', '').replace('\n', '')
        title = ''.join(re.findall('<h1 class="section">(.*?) &copy;', page))
	if title != '':
            return title
        else:
            return filename    
    except:
        return filename


def _test_bios_file(filename):
    try:
        f = urllib.urlopen('http://maws.mameworld.info/minimaws/set/'+filename)
        page = f.read().replace('\r\n', '').replace('\n', '').replace('\r', '')
        game_genre = re.findall('genre:</strong> <a href="(.*?)">(.*?)</a></li>', page)
        if ( game_genre[0][1].lower() == 'bios' ):
            return True
    except:
        return False

