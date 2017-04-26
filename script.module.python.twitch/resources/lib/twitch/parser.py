# -*- encoding: utf-8 -*-
import re
from twitch import keys
from twitch.logging import log

_m3u_pattern = re.compile(
    r'#EXT-X-MEDIA:TYPE=VIDEO.*'
    r'GROUP-ID="(?P<group_id>[^"]*)",'
    r'NAME="(?P<group_name>[^"]*)"[,=\w]*\n'
    r'#EXT-X-STREAM-INF:.*'
    r'BANDWIDTH=(?P<bandwidth>[0-9]+).*\n('
    r'?P<url>http.*)')

_clip_embed_pattern = re.compile(r'quality_options:\s*(?P<qualities>\[[^\]]+?\])')

_error_pattern = re.compile(r'.*<tr><td><b>error</b></td><td>(?P<message>.+?)</td></tr>.*', re.IGNORECASE)


def m3u8(f):
    def m3u8_wrapper(*args, **kwargs):
        results = f(*args, **kwargs)
        if keys.ERROR in results:
            if isinstance(results, dict):
                return results
            else:
                error = re.search(_error_pattern, results)
                if error:
                    return {'error': 'Error', 'message': error.group('message'), 'status': 404}
        return m3u8_to_list(results)

    return m3u8_wrapper


def clip_embed(f):
    def clip_embed_wrapper(*args, **kwargs):
        return clip_embed_to_list(f(*args, **kwargs))

    return clip_embed_wrapper


def m3u8_to_dict(string):
    log.debug('m3u8_to_dict called for:\n{0}'.format(string))
    d = dict()
    matches = re.finditer(_m3u_pattern, string)
    for m in matches:
        name = 'Audio Only' if m.group('group_name') == 'audio_only' else m.group('group_name')
        name = 'Source' if m.group('group_id') == 'chunked' else name
        d[m.group('group_id')] = {
            'id': m.group('group_id'),
            'name': name,
            'url': m.group('url'),
            'bandwidth': int(m.group('bandwidth'))
        }
    log.debug('m3u8_to_dict result:\n{0}'.format(d))
    return d


def m3u8_to_list(string):
    log.debug('m3u8_to_list called for:\n{0}'.format(string))
    l = list()
    matches = re.finditer(_m3u_pattern, string)
    for m in matches:
        name = 'Audio Only' if m.group('group_name') == 'audio_only' else m.group('group_name')
        name = 'Source' if m.group('group_id') == 'chunked' else name
        l.append({
            'id': m.group('group_id'),
            'name': name,
            'url': m.group('url'),
            'bandwidth': int(m.group('bandwidth'))
        })

    log.debug('m3u8_to_list result:\n{0}'.format(l))
    return l


def clip_embed_to_list(string):
    log.debug('clip_embed_to_list called for:\n{0}'.format(string))
    match = re.search(_clip_embed_pattern, string)
    l = list()
    if match:
        match = eval(match.group('qualities'))
        l = [{
                 'id': item['quality'],
                 'name': item['quality'],
                 'url': item['source'],
                 'bandwidth': -1
             } for item in match]
        if l:
            l.insert(0, {
                'id': 'Source',
                'name': 'Source',
                'url': l[0]['url'],
                'bandwidth': -1
            })

    log.debug('clip_embed_to_list result:\n{0}'.format(l))
    return l
