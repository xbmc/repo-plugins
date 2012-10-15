'''
Inspired by code of Esteban Ordano

http://estebanordano.com/ted-talks-download-subtitles/
http://estebanordano.com.ar/wp-content/uploads/2010/01/TEDTalkSubtitles.py_.zip
'''
import simplejson
import urllib
import re

__friendly_message__ = 'Error showing subtitles'
__talkIdKey__ = 'talkId'
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

def get_languages(soup):
    '''
    Get languages for a talk, or empty array if we fail.
    '''
    select_tag = soup.find('select', id='languageCode')
    if not select_tag:
        return []
    options = select_tag.findAll('option')
    return [v for v in [o['value'].encode('ascii') for o in options] if v]

def get_flashvars(soup):
    '''
    Get flashVars for a talk.
    Blow up if we can't find it or if we fail to parse.
    returns dict of values, no guarantees are made about which values are present.
    '''
    input_tag = soup.find('script', type='text/javascript', text=re.compile('var flashVars'))
    if not input_tag:
        raise Exception('Could not find flashVars container')

    flashvar_re = re.compile('var flashVars = \{([^}]+)\}', re.MULTILINE)
    flashvar_match = flashvar_re.search(input_tag.string)

    if not flashvar_match:
        raise Exception('Could not get flashVars')

    talkId_re = re.compile('"%s":(\d+)' % (__talkIdKey__))
    introDuration_re = re.compile('"%s":(\d+)' % (__introDurationKey__))
    flashvars = urllib.unquote(flashvar_match.group(1).encode('ascii'))

    talkId_match = talkId_re.search(flashvars)
    if not talkId_match:
        raise Exception('Could not get talk ID')

    introDuration_match = introDuration_re.search(flashvars)
    if not introDuration_match:
        raise Exception('Could not get intro duration')

    return {__talkIdKey__ : talkId_match.group(1), __introDurationKey__ : introDuration_match.group(1)}

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

def get_subtitles_for_talk(talk_soup, accepted_languages, logger):
    '''
    Return subtitles in srt format, or notify the user and return None if there was a problem.
    '''
    try:
        flashvars = get_flashvars(talk_soup)
    except Exception, e:
        logger('Could not display subtitles: %s' % (e), __friendly_message__)
        return None

    if __talkIdKey__ not in flashvars:
        logger('Could not determine talk ID for subtitles.', __friendly_message__)
        return None
    if __introDurationKey__ not in flashvars:
        logger('Could not determine intro duration for subtitles.', __friendly_message__)
        return None

    try:
        languages = get_languages(talk_soup)
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

    raw_subtitles = get_subtitles(flashvars[__talkIdKey__], matches[0])
    return format_subtitles(raw_subtitles, int(flashvars[__introDurationKey__]) * 1000)
