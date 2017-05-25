# -*- coding: utf-8 -*-
from base64 import b64decode
from hashlib import md5
from resources.lib.kodion import Context as __Context

DEFAULT_SWITCH = 1

__context = __Context()
__settings = __context.get_settings()

_own_key = __settings.get_string('youtube.api.key', '').strip()
_own_id = __settings.get_string('youtube.api.id', '').replace('.apps.googleusercontent.com', '').strip()
_own_secret = __settings.get_string('youtube.api.secret', '').strip()

__settings.set_string('youtube.api.key', _own_key)
__settings.set_string('youtube.api.id', _own_id)
__settings.set_string('youtube.api.secret', _own_secret)


def _has_own_keys():
    return False if not _own_key or \
                    not _own_id or \
                    not _own_secret or \
                    not __settings.get_bool('youtube.api.enable', False) else True


has_own_keys = _has_own_keys()


def __get_key_switch():
    switch = __settings.get_string('youtube.api.key.switch', str(DEFAULT_SWITCH))
    use_switch = __settings.get_string('youtube.api.key.switch.use', '')
    if not use_switch and switch:
        switch = 'own' if has_own_keys else str(DEFAULT_SWITCH)
        __settings.set_string('youtube.api.key.switch', switch)
        __settings.set_string('youtube.api.key.switch.use', switch)
        return switch
    elif use_switch != switch:
        __settings.set_string('youtube.api.key.switch.use', switch)
        return switch
    else:
        return use_switch


key_sets = {
    'youtube-tv': {
        'id': 'ODYxNTU2NzA4NDU0LWQ2ZGxtM2xoMDVpZGQ4bnBlazE4azZiZThiYTNvYzY4',
        'key': 'QUl6YVN5QWQtWUVPcVp6OW5YVnpHdG4zS1d6WUxiTGFhamhxSURB',
        'secret': 'U2JvVmhvRzlzMHJOYWZpeENTR0dLWEFU'
    },
    'own': {
        'key': _own_key,
        'id': _own_id,
        'secret': _own_secret
    },
    'provided': {
        'switch': __get_key_switch(),
        '0': {  # youtube-plugin-for-kodi-2
            'id': 'NDMwNTcyNzE0ODgyLTlqcDdjYzVvMmZkZGdhZGM2bWM4anB1a2JmYjlsczdv',
            'key': 'QUl6YVN5REIxVGU4MElUejdYR3ZXVGRzazhVMjVlVHY5WWlDS2Zz',
            'secret': 'ekE5d2lqLWZsSXRZMzVrSHBsN3NmZWt4'
        },
        '1': {  # youtube-plugin-for-kodi
            'id': 'Mjk0ODk5MDY0NDg4LWE4a2MxazFqZDAwa2FtcXJlMHZkMm5mdHVpaWZyZjZh',
            'key': 'QUl6YVN5Q1p3UXVvc0ZKYlF6bnFucXBxcFlsYUpXVk1uMTZ3QnZz',
            'secret': 'S1RrQktJTk41dmY0T3dqMU5ZeVhMemJl',
        },
        '2': {  # youtube-plugin-for-kodi-3
            'id': 'NjM5NjIwMzY5MzYxLWJvYW9qNDM1dDJncDRybjNyNHFyNm52aW8yOXAwZnJi',
            'key': 'QUl6YVN5QVA0eFJteU5KcndXcTFwNm5KUy1Wd25yY2dIWGxZT3Fr',
            'secret': 'V1luZGxUQWxLaU1lZjhRT2N5UENkZ1dF'
        },
        '3': {  # youtube-plugin-for-kodi-4
            'id': 'NTMxNTEzODY4MDE5LWk1aGJoMDh1aWY4OWhrM2tzNnRmOGR1aTlndWl0dWVn',
            'key': 'QUl6YVN5REJBRzB0ZXRrblVralo4b3QzRW95MEltUXFYNzRXWU1n',
            'secret': 'VHpsZ2lkZXlNdmhCcFdiZTAyWi0xQzVy'
        },
        '4': {  # youtube-plugin-for-kodi-5
            'id': 'NzYxMjUyMTUxMDQ3LXN1ZGNpMjMyNzBhZjM2cWdpcDg0ZHYxaWM3dXZkYzhi',
            'key': 'QUl6YVN5RFo1ZXk0T1JueGpHQTI1RkRCRGFteVVJakRTLTZKRUhR',
            'secret': 'VzNad0psdko0U2VRaEkza0tqbFhBRFk3'
        },
        '5': {  # youtube-plugin-for-kodi-6
            'id': 'ODY1MTkxMjg0NTM0LXNzMDlvbzBhMDg1c3BmNHVvbnAzcmdmb2hqc2hzNGUy',
            'key': 'QUl6YVN5QXc2VWtjREJpVk14ZXZxaGs3WE9la1BRU3dSaWNKaThR',
            'secret': 'Q1IxOGd6VWlNTi1XRVNVdGc0dE1LNWdz'
        }
    }
}


def get_current_switch():
    return 'own' if has_own_keys else key_sets['provided']['switch']


def get_last_switch():
    return __settings.get_string('youtube.api.last.switch', '')


def set_last_switch(value):
    __settings.set_string('youtube.api.last.switch', value)


def get_key_set_hash(value):
    m = md5()
    if value == 'own':
        m.update('%s%s%s' % (key_sets[value]['key'], key_sets[value]['id'], key_sets[value]['secret']))
    else:
        m.update('%s%s%s' % \
                 (key_sets['provided'][value]['key'], key_sets['provided'][value]['id'],
                  key_sets['provided'][value]['secret']))
    return m.hexdigest()


def set_last_hash(value):
    __settings.set_string('youtube.api.last.hash', get_key_set_hash(value))


def get_last_hash():
    return __settings.get_string('youtube.api.last.hash', '')


def _resolve_old_login():
    __context.log_debug('API key set changed: Signing out')
    __context.execute('RunPlugin(%s)' % __context.create_uri(['sign', 'out']))


# make sure we have a valid switch, if not use default
if not has_own_keys:
    if not key_sets['provided'].get(key_sets['provided']['switch'], None):
        __settings.set_string('youtube.api.key.switch', str(DEFAULT_SWITCH))
        key_sets['provided']['switch'] = __get_key_switch()


def check_for_key_changes():
    last_switch = get_last_switch()
    current_switch = get_current_switch()
    __context.log_debug('Using API key set: %s' % current_switch)
    last_set_hash = get_last_hash()
    current_set_hash = get_key_set_hash(current_switch)
    if (last_switch != current_switch) or (last_set_hash != current_set_hash):
        __context.log_warning('Switching API key set from %s to %s' % (last_switch, current_switch))
        set_last_switch(current_switch)
        set_last_hash(current_switch)
        _resolve_old_login()
        return True
    return False


api = {
    'key':
        key_sets['own']['key']
        if has_own_keys
        else
        b64decode(key_sets['provided'][key_sets['provided']['switch']]['key']),
    'id':
        '%s.apps.googleusercontent.com' %
        (key_sets['own']['id']
         if has_own_keys
         else
         b64decode(key_sets['provided'][key_sets['provided']['switch']]['id'])),
    'secret':
        key_sets['own']['secret']
        if has_own_keys
        else
        b64decode(key_sets['provided'][key_sets['provided']['switch']]['secret'])
}

youtube_tv = {
    'key': b64decode(key_sets['youtube-tv']['key']),
    'id': '%s.apps.googleusercontent.com' % b64decode(key_sets['youtube-tv']['id']),
    'secret': b64decode(key_sets['youtube-tv']['secret'])
}

keys_changed = check_for_key_changes()
