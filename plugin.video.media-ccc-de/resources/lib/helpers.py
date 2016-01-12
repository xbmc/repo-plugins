from __future__ import print_function

def recording_list(json, quality, format):
    recs = [Recording(elem) for elem in json]
    print("Requested quality %s and format %s" % (quality, format))
    want = sorted(filter(lambda rec: rec.is_video(), recs), key = user_preference_sorter(quality, format))
    print(want)
    return want

class Recording(object):
    def __init__(self, json):
        self.mime = json['display_mime_type']
        self.format = self.mime.split('/')[1]
        self.orig_mime = json['mime_type']
        self.hd = json['hd']
        self.url = json['recording_url']
        self.length = json['length']
        self.size = json['size']
        lang = json['language']
        if lang:
            self.languages = lang.split('-')
        else:
            self.languages = ('unk',)

    def __repr__(self):
        return "Recording<F:%s,M:%s,HD:%s,LANG:%s>" % (self.format, self.orig_mime, self.hd, self.languages)

    def is_video(self):
        return self.mime.startswith('video/')

def user_preference_sorter(prefer_quality, prefer_format):
    def do_sort(obj):
        prio = 0

        if obj.format == prefer_format:
            prio += 20

        # Bonus & penalty for exact matches, no score for "obj.hd == None"
        if obj.hd == True and prefer_quality == "hd":
            prio += 20
        elif obj.hd == False and prefer_quality == "sd":
            prio += 20
        elif obj.hd == True and prefer_quality == "sd":
            prio -= 10
        elif obj.hd == False and prefer_quality == "hd":
            prio -= 10

        # "web" versions are missing one audio track
        # (legacy, but not all conferences have proper language tags yet)
        try:
            if obj.orig_mime.endswith('-web'):
                prio -= 5
        except AttributeError:
            pass

        # Prefer versions with "more" audio tracks
        try:
            translations = len(obj.languages) - 1
            prio += translations
        except AttributeError:
            pass

        # Prefer "native" over "translated" for now (streaming)...
        try:
            if obj.translated:
                prio += 5
        except AttributeError:
            pass

        return -prio
    return do_sort
