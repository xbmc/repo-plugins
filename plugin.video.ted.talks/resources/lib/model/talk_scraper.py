# Custom xbmc thing for fast parsing. Can't rely on lxml being available as of 2012-03.
import CommonFunctions as xbmc_common
import httplib
import urlparse
import json
import re
import xbmc

from ted_talks_const import ADDON, DATE, VERSION

def get(html, video_quality='320kbps'):
    """Extract talk details from talk html
       @param video_quality string in form '\d+kbps' that should match one of the provided TED bitrates.
    """
    init_scripts = [script for script in xbmc_common.parseDOM(html, 'script') if '"talkPage.init"' in script]
    if init_scripts:
        init_json = json.loads(re.compile(r'q[(]"talkPage.init",(.+)[)]').search(init_scripts[0]).group(1))
        talk_json = init_json['__INITIAL_DATA__']['talks'][0]
        title = talk_json['player_talks'][0]['title']

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
            xbmc.LOGDEBUG)

        speaker = talk_json['player_talks'][0]['speaker']

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "speaker", str(speaker)),
            xbmc.LOGDEBUG)

        resources = talk_json['player_talks'][0]['resources']

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "resources", str(json.dumps(resources))),
            xbmc.LOGDEBUG)

        url = resources['h264'][0]['file']
        pos_of_question_mark = str(url).find('?')
        if pos_of_question_mark >= 0:
            url = str(url)[0:pos_of_question_mark]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "url", str(url)),
            xbmc.LOGDEBUG)

        plot = talk_json['description']

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "plot", str(plot)),
            xbmc.LOGDEBUG)
        if not video_quality == '320kbps':
            url_custom = url.replace("-320k.mp4", "-%sk.mp4" % (video_quality.split('k')[0]))

            # Test resource exists
            url_custom_parsed = urlparse.urlparse(url_custom)
            h = httplib.HTTPConnection(url_custom_parsed.netloc)
            h.request('HEAD', url_custom_parsed.path)
            response = h.getresponse()
            h.close()
            if response.status / 100 < 4:
                url = url_custom

        return url, title, speaker, plot, talk_json
    else:
        raise Exception('Could not parse HTML:\n%s' % (html))
