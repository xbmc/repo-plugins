# -*- coding: utf-8 -*-

import json
import time
import xbmcvfs

class Cache:

    def __init__(self, plugin):
        self.plugin = plugin
        self.file = self.plugin.file_path('cache_{0}.json')

    def delete_cache(self, name):
        if xbmcvfs.exists(self.file):
            st = xbmcvfs.Stat(self.file)
            current = round(time.time())
            access = st.st_atime()
            at = (current - access) / 3600
            at = str(at).split('.')[0]
            size = st.st_size()
            s = int(size) / 1024
            t = 24*5
            if 'lastfm' in name:
                t = 24*30
            if int(at) > t or s > 1024:
                xbmcvfs.delete(self.file)

    def load_json(self, name, lastfm):
        if lastfm == 'tag':
            name = 'lastfm_tag'
        elif lastfm:
            name = 'lastfm_similar'
        self.file = self.file.format(name)
        self.delete_cache(name)
        return get_json_data(self.file)

    def save_value(self, name, string, value, lastfm=False):
        if name == 'local':
            return
        json_data = self.load_json(name, lastfm)
        if json_data:
            if json_data.get(name):
                json_data[name][string] = value
            else:
                json_data[name] = {
                    string: value
                }
        else:
            json_data = {
                name: {
                    string: value
                }
            }
        save_json_data(self.file, json_data)

    def get_value(self, name, string, lastfm=False):
        if name == 'local':
            return
        json_data = self.load_json(name, lastfm)
        name = self.plugin.utfdec(name)
        string = self.plugin.utfdec(string)
        value = json_data.get(name, {}).get(string, None)
        return value

class Artist_List:

    def __init__(self, plugin):
        self.plugin = plugin
        self.file = self.plugin.file_path('artist_list.json')

    def get_artist_list(self):
        return get_json_data(self.file)

    def add_to_artist_list(self, artist, thumb):
        entries = self.get_artist_list()
        new_entry = {
            'artist': artist,
            'thumb': thumb
        }
        if entries:
            for entry in entries:
                if self.plugin.utfenc(entry['artist']) == artist:
                    return
            entries.insert(0,new_entry)
            save_json_data(self.file, entries)
        else:
            save_json_data(self.file, [new_entry])

    def remove_from_artist_list(self, artist):
        json_data = self.get_artist_list()
        for i in xrange(len(json_data)):
            if self.plugin.utfenc(json_data[i]['artist']) == artist:
                json_data.pop(i)
                break
        save_json_data(self.file, json_data)

class Hide_List:

    def __init__(self, plugin):
        self.plugin = plugin
        self.file = self.plugin.file_path('ignore_list.json')

    def get_hide_list(self):
        return get_json_data(self.file)

    def add_to_hide_list(self, site, id_):
        entries = self.get_hide_list()
        new_entry = {
            'site': site,
            'id': id_
        }
        if entries:
            for entry in entries:
                if entry['id'] == id_ and entry['site'] == site:
                    return
            entries.insert(0, new_entry)
            save_json_data(self.file, entries)
        else:
            save_json_data(self.file, [new_entry])

    def remove_from_hide_list(self, site, id_):
        json_data = self.get_hide_list()
        for i in xrange(len(json_data)):
            if json_data[i]['id'] == id_ and json_data[i]['site'] == site_:
                json_data.pop(i)
                break
        save_json_data(self.file, json_data)

class Resume:

    def __init__(self, plugin):
        self.plugin = plugin
        self.file = self.plugin.file_path('resume.json')

    def get_resume_point(self):
        return get_json_data(self.file)

    def save_resume_point(self, resume_point):
        save_json_data(self.file, resume_point)

    def get_start_artist(self):
        start_artist = None
        resume_point = self.get_resume_point()
        if resume_point:
            start_artist = self.plugin.utfenc(resume_point['start_artist'])
        return start_artist

def get_json_data(file):
    json_data = {}
    if xbmcvfs.exists(file):
        f = xbmcvfs.File(file, 'r')
        json_data = json.load(f)
        f.close()
    return json_data

def save_json_data(file, data):
    f = xbmcvfs.File(file, 'w')
    json.dump(data, f)
    f.close()
