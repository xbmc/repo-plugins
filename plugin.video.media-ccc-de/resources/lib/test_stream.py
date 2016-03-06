from __future__ import print_function

import simplejson

from .stream import Streams


def test_rooms():
    s = Streams(SampleJson)
    assert len(s.rooms) == 2
    assert s.rooms[0].slug == "vortragssaal"
    assert s.rooms[0].display == "Vortragssaal"


def test_streams():
    s = Streams(SampleJson)
    r = s.rooms[0]
    assert len(r.streams) == 6
    streams = r.streams_sorted("hd", "mp4")
    assert len(streams) == 4
    preferred = streams[0]
    assert preferred.hd is True
    assert preferred.format == 'mp4'
    assert preferred.translated is False


SampleJson = simplejson.loads('''
[
  {
    "group": "",
    "rooms": [
      {
        "slug": "vortragssaal",
        "display": "Vortragssaal",
        "streams": [
          {
            "slug": "hd-native",
            "display": "Vortragssaal FullHD Video",
            "type": "video",
            "isTranslated": false,
            "videoSize": [
              1920,
              1080
            ],
            "urls": {
              "webm": {
                "display": "WebM",
                "tech": "1920x1080, VP8+Vorbis in WebM, 2.8 MBit/s",
                "url": "http://cdn.c3voc.de/s4_native_hd.webm"
              },
              "hls": {
                "display": "HLS",
                "tech": "1920x1080, h264+AAC im MPEG-TS-Container via HTTP, 3 MBit/s",
                "url": "http://cdn.c3voc.de/hls/s4_native_hd.m3u8"
              }
            }
          },
          {
            "slug": "sd-native",
            "display": "Vortragssaal SD Video",
            "type": "video",
            "isTranslated": false,
            "videoSize": [
              1024,
              576
            ],
            "urls": {
              "webm": {
                "display": "WebM",
                "tech": "1024x576, VP8+Vorbis in WebM, 800 kBit/s",
                "url": "http://cdn.c3voc.de/s4_native_sd.webm"
              },
              "hls": {
                "display": "HLS",
                "tech": "1024x576, h264+AAC im MPEG-TS-Container via HTTP, 800 kBit/s",
                "url": "http://cdn.c3voc.de/hls/s4_native_sd.m3u8"
              }
            }
          },
          {
            "slug": "audio-native",
            "display": "Vortragssaal Audio",
            "type": "audio",
            "isTranslated": false,
            "videoSize": null,
            "urls": {
              "mp3": {
                "display": "MP3",
                "tech": "MP3-Audio, 96 kBit/s",
                "url": "http://cdn.c3voc.de/s4_native.mp3"
              },
              "opus": {
                "display": "Opus",
                "tech": "Opus-Audio, 64 kBit/s",
                "url": "http://cdn.c3voc.de/s4_native.opus"
              }
            }
          }
        ]
      },
      {
        "slug": "tagungsraum-1",
        "display": "Tagungsraum 1",
        "streams": [
          {
            "slug": "sd-native",
            "display": "Tagungsraum 1 SD Video",
            "type": "video",
            "isTranslated": false,
            "videoSize": [
              1024,
              576
            ],
            "urls": {
              "webm": {
                "display": "WebM",
                "tech": "1024x576, VP8+Vorbis in WebM, 800 kBit/s",
                "url": "http://cdn.c3voc.de/s2_native_sd.webm"
              },
              "hls": {
                "display": "HLS",
                "tech": "1024x576, h264+AAC im MPEG-TS-Container via HTTP, 800 kBit/s",
                "url": "http://cdn.c3voc.de/hls/s2_native_sd.m3u8"
              }
            }
          },
          {
            "slug": "audio-native",
            "display": "Tagungsraum 1 Audio",
            "type": "audio",
            "isTranslated": false,
            "videoSize": null,
            "urls": {
              "mp3": {
                "display": "MP3",
                "tech": "MP3-Audio, 96 kBit/s",
                "url": "http://cdn.c3voc.de/s2_native.mp3"
              },
              "opus": {
                "display": "Opus",
                "tech": "Opus-Audio, 64 kBit/s",
                "url": "http://cdn.c3voc.de/s2_native.opus"
              }
            }
          }
        ]
      }
    ]
  }
]
''')
