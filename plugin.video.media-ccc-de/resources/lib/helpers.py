from __future__ import print_function

def recording_list(json, quality, format):
    recs = [Recording(elem) for elem in json]
    print("Requested quality %s and format %s" % (quality, format))
    for rec in recs:
        rec.set_priority(quality, format)
    want = sorted(filter(lambda rec: rec.is_video(), recs), key=lambda rec: rec.priority)
    print(want)
    return want

class Recording(object):
    def __init__(self, json):
        self.mime = json['display_mime_type']
        self.orig_mime = json['display_mime_type']
        self.hd = json['hd']
        self.url = json['recording_url']
        self.length = json['length']
        self.size = json['size']
        self.priority = 100

    def __repr__(self):
        return repr((self.mime, self.hd, self.priority))

    def is_video(self):
        return self.mime.startswith('video/')

    def set_priority(self, prefer_quality, prefer_format):
        format = self.mime.split('/')[1]
        prio = 100

        if format == prefer_format:
            prio -= 20

        # Bonus & penalty for exact matches, no score for "self.hd == None"
        if self.hd == True and prefer_quality == "hd":
            prio -= 20
        elif self.hd == False and prefer_quality == "sd":
            prio -= 20
        elif self.hd == True and prefer_quality == "sd":
            prio += 10
        elif self.hd == False and prefer_quality == "hd":
            prio += 10

        # "web" versions are missing one audio track
        if self.orig_mime.endswith('-web'):
            prio -= 5

        self.priority = prio
