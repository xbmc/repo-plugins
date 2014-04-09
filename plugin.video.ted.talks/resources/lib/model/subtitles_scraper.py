'''
Inspired by code of Esteban Ordano

http://estebanordano.com/ted-talks-download-subtitles/
http://estebanordano.com.ar/wp-content/uploads/2010/01/TEDTalkSubtitles.py_.zip
'''
import json
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

def __get_languages__(talk_json):
    '''
    Get languages for a talk, or empty array if we fail.
    '''
    return [l['languageCode'] for l in talk_json['languages']]

def get_subtitles(talk_id, language, logger):
    url = 'http://www.ted.com/talks/subtitles/id/%s/lang/%s' % (talk_id, language)
    subs = json.loads(urllib.urlopen(url).read())
    captions = []
    for caption in subs['captions']:
        captions += [{'start': caption['startTime'], 'duration': caption['duration'], 'content': caption['content']}]
    return captions

def get_subtitles_for_talk(talk_json, accepted_languages, logger):
    '''
    Return subtitles in srt format, or notify the user and return None if there was a problem.
    '''
    talk_id = talk_json['id']
    intro_duration = talk_json['introDuration']

    try:
        languages = __get_languages__(talk_json)

        if len(languages) == 0:
            msg = 'No subtitles found'
            logger(msg, msg)
            return None

        language_matches = [l for l in accepted_languages if l in languages]
        if not language_matches:
            msg = 'No subtitles in: %s' % (",".join(accepted_languages))
            logger(msg, msg)
            return None

        raw_subtitles = get_subtitles(talk_id, language_matches[0], logger)
        if not raw_subtitles:
            return None

        return format_subtitles(raw_subtitles, int(float(intro_duration) * 1000))

    except Exception, e:
        # Must not fail!
        logger('Could not display subtitles: %s' % (e), __friendly_message__)
        return None
