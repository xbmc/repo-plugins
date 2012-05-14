'''
Maps between ISO-639-1 language codes and full language names.
'''

import os

def get_language_code(language):
    '''
    This is ludicrous but I can't find XBMC APIs to do it for me :(
    List taken from http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    '''
    file_path = os.path.join(os.path.dirname(__file__), "ISO-639-2_utf-8.txt")
    f = open(file_path, 'r')
    try:
        code_to_language = {}
        for line in f:
            split = line.split('|')
            if split[2]:
                code_to_language[split[2]] = split[3]
    finally:
        f.close()
    matches = [k for k, v in code_to_language.iteritems() if language.lower().startswith(v.lower())]
    if matches:
        return matches[0]
    else:
        return None
