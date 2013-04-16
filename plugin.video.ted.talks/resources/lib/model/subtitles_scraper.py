'''
Inspired by code of Esteban Ordano

http://estebanordano.com/ted-talks-download-subtitles/
http://estebanordano.com.ar/wp-content/uploads/2010/01/TEDTalkSubtitles.py_.zip
'''
import simplejson
import urllib
import re
# Custom xbmc thing for fast parsing. Can't rely on lxml being available as of 2012-03.
import CommonFunctions as xbmc_common

__friendly_message__ = 'Error showing subtitles'
__talkIdKey__ = 'id'
__introDurationKey__ = 'introDuration'

def format_time(time):
    millis = time % 1000
    seconds = (time / 1000) % 60
    minutes = (time / 60000) % 60
    hours = (time / 3600000)
    return '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, millis)

def format_subtitles(subtitles, introDuration):
    result = ''
    for idx, sub in enumerate(subtitles):
        start = introDuration + sub['start']
        end = start + sub['duration']
        result += '%d\n%s --> %s\n%s\n\n' % (idx + 1, format_time(start), format_time(end), sub['content'])
    return result

def get_languages(talk_html):
    '''
    Get languages for a talk, or empty array if we fail.
    '''
    select_tag = xbmc_common.parseDOM(talk_html, 'select', attrs={'id':'languageCode'})
    if not select_tag:
        return []
    options = xbmc_common.parseDOM(select_tag, 'option', ret='value')
    return [o for o in options if o]

def get_flashvars(talk_html):
    '''
    Get flashVars for a talk.
    Blow up if we can't find it or if we fail to parse.
    returns dict of values, no guarantees are made about which values are present.
    '''
    talkDetails_re = re.compile('var talkDetails = (\{.*\})');
    talkDetails_match = None
    for script in xbmc_common.parseDOM(talk_html, 'script', attrs={'type':'text/javascript'}):
        if not talkDetails_match:
            talkDetails_match = talkDetails_re.search(script)

    if not talkDetails_match:
        raise Exception('Could not find the talkDetails container')

    talkId_re = re.compile('"%s":(\d+)' % (__talkIdKey__))
    talkId_match = talkId_re.search(talkDetails_match.group(1))
    if not talkId_match:
        print talkDetails_match.group(1)
        raise Exception('Could not get talk ID')

    talkDetails = urllib.unquote(talkDetails_match.group(1).encode('ascii'))
    introDuration_re = re.compile('"%s":(\d+)' % (__introDurationKey__))
    introDuration_match = introDuration_re.search(talkDetails)
    if not introDuration_match:
        raise Exception('Could not get intro duration')

    return talkId_match.group(1), introDuration_match.group(1)

def get_subtitles(talk_id, language):
    url = 'http://www.ted.com/talks/subtitles/id/%s/lang/%s' % (talk_id, language)
    return get_subtitles_for_url(url)

def get_subtitles_for_url(url):
    s = urllib.urlopen(url)
    try:
        json = simplejson.load(s)
    finally:
        s.close()

    captions = []
    for caption in json['captions']:
        captions += [{'start': caption['startTime'], 'duration': caption['duration'], 'content': caption['content']}]
    return captions

def get_subtitles_for_talk(talk_html, accepted_languages, logger):
    '''
    Return subtitles in srt format, or notify the user and return None if there was a problem.
    '''
    try:
        talk_id, intro_duration = get_flashvars(talk_html)
    except Exception, e:
        logger('Could not display subtitles: %s' % (e), __friendly_message__)
        return None

    try:
        languages = get_languages(talk_html)
    except Exception, e:
        logger('Could not display subtitles: %s' % (e), __friendly_message__)
        return None
    if len(languages) == 0:
        msg = 'No subtitles found'
        logger(msg, msg)
        return None
    matches = [l for l in accepted_languages if l in languages]
    if not matches:
        msg = 'No subtitles in: %s' % (",".join(accepted_languages))
        logger(msg, msg)
        return None

    raw_subtitles = get_subtitles(talk_id, matches[0])
    return format_subtitles(raw_subtitles, int(intro_duration) * 1000)
