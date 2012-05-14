'''
Inspired by code of Esteban Ordano

http://estebanordano.com/ted-talks-download-subtitles/
http://estebanordano.com.ar/wp-content/uploads/2010/01/TEDTalkSubtitles.py_.zip
'''
import simplejson
import urllib
import re

__friendly_message__ = 'Error showing subtitles'

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

def get_languages(languages):
    '''
    languages Escaped languages param from flashVars
    '''
    language_code_re = re.compile('"LanguageCode":"(\w+)"')
    matches = filter(None, [language_code_re.search(param) for param in urllib.unquote(languages).split(',')])
    return [m.group(1) for m in matches]

def get_flashvars(soup):
    '''
    Get flashVars for a talk.
    Blow up if we can't find it or if we fail to parse.
    returns dict of values, no guarantees are made about which values are present.
    '''
    flashvars_re = re.compile('flashVars = {([^}]+)}')
    flash_script = soup.find('script', text=flashvars_re)
    if not flash_script:
        raise Exception('Could not find flashVars')
    flashvars = flashvars_re.search(flash_script.string).group(1)
    flashvar_re = re.compile('^\s*(\w+):"?(.+?)"?,?$')
    matches = filter(None, [flashvar_re.match(l) for l in flashvars.split('\n')])
    return dict([(m.group(1).encode('ascii'), m.group(2).encode('ascii')) for m in matches])

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

    if 'languages' in flashvars:
        languages = get_languages(flashvars['languages'])
        if len(languages) == 0:
            msg = 'No subtitles found'
            logger(msg, msg)
            return None
        matches = [l for l in languages if l in accepted_languages]
        if not matches:
            msg = 'No subtitles in: %s' % (",".join(accepted_languages))
            logger(msg, msg)
            return None
    else:
        # If we don't find 'languages' in flashvars, may as well take a punt anyway.
        logger('Could not find languages in flashvars.')
        matches = accepted_languages

    if 'ti' not in flashvars:
        logger('Could not determine talk ID for subtitles.', __friendly_message__)
        return None
    if 'introDuration' not in flashvars:
        logger('Could not determine intro duration for subtitles.', __friendly_message__)
        return None

    raw_subtitles = get_subtitles(flashvars['ti'], matches[0])
    return format_subtitles(raw_subtitles, int(flashvars['introDuration']))
