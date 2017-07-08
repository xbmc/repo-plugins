from __future__ import print_function

import simplejson

from .recording import Recordings


def test_recordings():
    r = Recordings(SampleJson)
    assert len(r.recordings) == 10
    recordings = r.recordings_sorted("hd", "mp4")
    assert len(recordings) == 6
    preferred = recordings[0]
    assert preferred.hd is True
    assert preferred.format == 'mp4'
    assert len(preferred.languages) == 2

def test_minimal_broken_json():
    r = Recordings(MinimalBrokenJson)
    assert len(r.recordings) == 2
    recordings = r.recordings_sorted("hd", "mp4")
    assert len(recordings) == 2
    preferred = recordings[0]
    assert preferred.hd is True
    assert preferred.format == 'mp4'
    assert len(preferred.languages) == 1

# From https://api.media.ccc.de/public/events/2893
SampleJson = simplejson.loads('''
{
  "conference_url": "https://api.media.ccc.de/public/conferences/78",
  "date": "2015-12-29T17:15:00.000+01:00",
  "description": "Last year I presented research showing how to de-anonymize programmers based on their coding style. This is of immediate concern to open source software developers who would like to remain anonymous. On the other hand, being able to de-anonymize programmers can help in forensic investigations, or in resolving plagiarism claims or copyright disputes. \\n\\nI will report on our new research findings in the past year. We were able to increase the scale and accuracy of our methods dramatically and can now handle 1,600 programmers, reaching 94% de-anonymization accuracy. In ongoing research, we are tackling the much harder problem of de-anonymizing programmers from binaries of compiled code. This can help identify the author of a suspicious executable file and can potentially aid malware forensics. We demonstrate the efficacy of our techniques using a dataset collected from GitHub.",
  "frontend_link": "https://media.ccc.de/v/32c3-7491-de-anonymizing_programmers",
  "guid": "371063d0-da9d-4d9f-bbe9-f5739eba2f30",
  "length": 3572,
  "link": "https://events.ccc.de/congress/2015/Fahrplan/events/7491.html",
  "original_language": "en",
  "persons": [
    "Aylin"
  ],
  "poster_url": "https://static.media.ccc.de/media/congress/2015/7491-hd_preview.jpg",
  "recordings": [
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-de-De-anonymizing_Programmers.mp4",
      "folder": "h264-hd-web",
      "height": 1080,
      "high_quality": true,
      "language": "deu",
      "length": 3572,
      "mime_type": "video/mp4",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/h264-hd-web/32c3-7491-de-De-anonymizing_Programmers.mp4",
      "size": 476,
      "state": "downloaded",
      "updated_at": "2016-02-03T14:12:36.223+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9068",
      "width": 1920
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-de-De-anonymizing_Programmers.mp3",
      "folder": "mp3-translated",
      "height": null,
      "high_quality": true,
      "language": "deu",
      "length": 3563,
      "mime_type": "audio/mpeg",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/mp3-translated/32c3-7491-de-De-anonymizing_Programmers.mp3",
      "size": 54,
      "state": "downloaded",
      "updated_at": "2016-01-03T01:11:15.094+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9555",
      "width": null
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-de-De-anonymizing_Programmers.opus",
      "folder": "opus-translation",
      "height": null,
      "high_quality": true,
      "language": "deu",
      "length": 3563,
      "mime_type": "audio/opus",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/opus-translation/32c3-7491-de-De-anonymizing_Programmers.opus",
      "size": 47,
      "state": "downloaded",
      "updated_at": "2016-01-03T01:10:41.958+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9554",
      "width": null
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-de-De-anonymizing_Programmers_webm-hd.webm",
      "folder": "webm-hd",
      "height": 1080,
      "high_quality": true,
      "language": "eng-deu",
      "length": 3572,
      "mime_type": "video/webm",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/webm-hd/32c3-7491-en-de-De-anonymizing_Programmers_webm-hd.webm",
      "size": 542,
      "state": "downloaded",
      "updated_at": "2016-02-03T21:01:47.627+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9354",
      "width": 1920
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-de-De-anonymizing_Programmers_hd.mp4",
      "folder": "h264-hd",
      "height": 1080,
      "high_quality": true,
      "language": "eng-deu",
      "length": 3572,
      "mime_type": "video/mp4",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/h264-hd/32c3-7491-en-de-De-anonymizing_Programmers_hd.mp4",
      "size": 513,
      "state": "downloaded",
      "updated_at": "2016-02-03T14:12:36.436+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9069",
      "width": 1920
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-De-anonymizing_Programmers.mp4",
      "folder": "h264-hd-web",
      "height": 1080,
      "high_quality": true,
      "language": "eng",
      "length": 3572,
      "mime_type": "video/mp4",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/h264-hd-web/32c3-7491-en-De-anonymizing_Programmers.mp4",
      "size": 476,
      "state": "downloaded",
      "updated_at": "2016-02-03T14:12:36.060+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9067",
      "width": 1920
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-de-De-anonymizing_Programmers_sd.mp4",
      "folder": "h264-sd",
      "height": 576,
      "high_quality": false,
      "language": "eng-deu",
      "length": 3572,
      "mime_type": "video/mp4",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/h264-sd/32c3-7491-en-de-De-anonymizing_Programmers_sd.mp4",
      "size": 220,
      "state": "downloaded",
      "updated_at": "2016-02-03T14:12:45.282+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9147",
      "width": 720
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-De-anonymizing_Programmers.opus",
      "folder": "opus",
      "height": null,
      "high_quality": true,
      "language": "eng",
      "length": 3563,
      "mime_type": "audio/opus",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/opus/32c3-7491-en-De-anonymizing_Programmers.opus",
      "size": 46,
      "state": "downloaded",
      "updated_at": "2016-01-03T01:10:08.859+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9553",
      "width": null
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-De-anonymizing_Programmers.mp3",
      "folder": "mp3",
      "height": null,
      "high_quality": true,
      "language": "eng",
      "length": 3563,
      "mime_type": "audio/mpeg",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/mp3/32c3-7491-en-De-anonymizing_Programmers.mp3",
      "size": 54,
      "state": "downloaded",
      "updated_at": "2016-01-03T01:09:36.344+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9552",
      "width": null
    },
    {
      "conference_url": "https://api.media.ccc.de/public/conferences/78",
      "event_url": "https://api.media.ccc.de/public/events/2893",
      "filename": "32c3-7491-en-de-De-anonymizing_Programmers_webm-sd.webm",
      "folder": "webm-sd",
      "height": 576,
      "high_quality": false,
      "language": "eng-deu",
      "length": 3572,
      "mime_type": "video/webm",
      "recording_url": "http://cdn.media.ccc.de/congress/2015/webm-sd/32c3-7491-en-de-De-anonymizing_Programmers_webm-sd.webm",
      "size": 194,
      "state": "downloaded",
      "updated_at": "2016-02-03T14:13:33.007+01:00",
      "url": "https://api.media.ccc.de/public/recordings/9513",
      "width": 720
    }
  ],
  "release_date": "2015-12-29",
  "slug": "32c3-7491-de-anonymizing_programmers",
  "subtitle": "Large Scale Authorship Attribution from Executable Binaries of Compiled Code and Source Code",
  "tags": [
    "Security"
  ],
  "thumb_url": "https://static.media.ccc.de/media/congress/2015/7491-hd.jpg",
  "title": "De-anonymizing Programmers",
  "updated_at": "2016-02-06T00:02:27.744+01:00",
  "url": "https://api.media.ccc.de/public/events/2893"
}
''')

MinimalBrokenJson = simplejson.loads('''
{
  "recordings": [
    {
      "recording_url": "http://cdn.media.ccc.de/congress/2015/h264-hd-web/32c3-7491-de-De-anonymizing_Programmers.mp4"
    },
    {
      "recording_url": "http://cdn.media.ccc.de/congress/2015/h264-hd/32c3-7491-en-de-De-anonymizing_Programmers_hd.mp4"
    }
  ],
  "title": "De-anonymizing Programmers"
}
''')
