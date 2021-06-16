import html5lib
import json
import requests


def get_talk(html, logger):
    '''Extract talk details from talk html
    '''

    init_scripts = html5lib.parse(html, namespaceHTMLElements=False).findall(".//script[@data-spec='q']")
    init_scripts = [script.text for script in init_scripts if '"talkPage.init"' in script.text]

    if not init_scripts:
        raise Exception('Could not parse HTML.')

    # let's do this some other way
    init_scripts_start_pos = str(init_scripts).find('{')
    init_scripts = str(init_scripts)[init_scripts_start_pos:]
    init_scripts = init_scripts + '}'

    # let's remove some json breaking invalid characters
    init_scripts = init_scripts.replace('\\n\\t', '')
    init_scripts = init_scripts.replace("\\n})']", '')
    init_scripts = init_scripts.replace('\\\\"', '')
    init_scripts = init_scripts.replace('\\', '')
    init_scripts = init_scripts[:-4]

    init_json = json.loads(str(init_scripts), strict=False)
    talk_json = init_json['__INITIAL_DATA__']['talks'][0]
    player_talks_json = talk_json['player_talks'][0]
    
    title = player_talks_json['title']
    speaker = player_talks_json['speaker']
    plot = talk_json['description']

    m3u8_url = player_talks_json['resources']['hls']['stream']

    return m3u8_url, title, speaker, plot, talk_json
