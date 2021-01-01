import json, requests
from BeautifulSoup import BeautifulSoup as BS

BASE_URL="https://www.newyankee.com/watch/"
session = requests.session()


def get_first_select_options(dom):
    options_list = dom.findAll('select')[0].findAll('option')[1:]
    options_objs = [[x.text,dict(x.attrs)] for x in options_list]
    active_options = [x for x in options_objs if "disabled" not in x[1]]
    keypairs = [[x[0],x[1]['value']] for x in active_options] 
    return keypairs

def get_second_select_options(dom):
    options_list = dom.findAll('select')[1].findAll('option')[1:]
    options_objs = [[x.text,dict(x.attrs)] for x in options_list]
    keypairs = [[x[0],x[1]['value']] for x in options_objs]
    return keypairs

def extract_m3u8(video_js_uri):
    resp_text = session.get(video_js_uri).text
    m3u8_id   = [x for x in resp_text.split('sources: ')[1].split('mmVideo')[0].splitlines() if x.__contains__('id:')][0].split('\'')[1]
    m3u8_json = "https://content.uplynk.com/preplay/" + m3u8_id + ".json?v=2"
    m3u8_dict = json.loads(session.get(m3u8_json).text)
    m3u8_uri  = m3u8_dict["playURL"]
    return m3u8_uri

def get_season_list():
    resp_text = session.get(BASE_URL).text
    dom = BS(resp_text)
    return get_first_select_options(dom)

def get_episode_list(season):
    resp_text = session.post(BASE_URL, data={'nyw_season':season}).text
    dom = BS(resp_text)
    return get_second_select_options(dom)

def get_episode(season, episode):
    resp_text = session.post(BASE_URL, data={'nyw_season':season, 'nyw_episode':episode}).text
    video_js_pos = resp_text.find('https://player.zype.com')
    video_js_uri = resp_text[video_js_pos:].split('">')[0]
    return extract_m3u8(video_js_uri)

