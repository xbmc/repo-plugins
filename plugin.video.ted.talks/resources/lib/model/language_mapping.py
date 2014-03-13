'''
Maps between ISO-639-1 language codes and full language names.
'''

import os

def get_language_code(language):
    '''
    This is ludicrous but I can't find XBMC APIs to do it for me :(
    APIs coming in Gotham...
    List taken from http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    '''
    language = language.lower()
    
    file_path = os.path.join(os.path.dirname(__file__), "ISO-639-2_utf-8.txt")
    f = open(file_path, 'r')
    try:
        for line in f:
            split = line.split('|')
            if split[2]:
                for l in split[3].split(';'):
                    if language.startswith(l.strip().lower()):
                        return split[2]
    finally:
        f.close()
    
    return None
