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
        self.orig_mime = json['display_mime_type']
        self.hd = json['hd']
        self.url = json['recording_url']
        self.length = json['length']
        self.size = json['size']

    def __repr__(self):
        return repr((self.mime, self.hd))

    def is_video(self):
        return self.mime.startswith('video/')

def user_preference_sorter(prefer_quality, prefer_format):
    def do_sort(obj):
        prio = 100

        if obj.format == prefer_format:
            prio -= 20

        # Bonus & penalty for exact matches, no score for "obj.hd == None"
        if obj.hd == True and prefer_quality == "hd":
            prio -= 20
        elif obj.hd == False and prefer_quality == "sd":
            prio -= 20
        elif obj.hd == True and prefer_quality == "sd":
            prio += 10
        elif obj.hd == False and prefer_quality == "hd":
            prio += 10

        # "web" versions are missing one audio track
        try:
            if obj.orig_mime.endswith('-web'):
                prio -= 5
        except AttributeError:
            pass

        # Prefer "native" over "translated" for now...
        try:
            if obj.translated:
                prio -= 5
        except AttributeError:
            pass

        return prio
    return do_sort
