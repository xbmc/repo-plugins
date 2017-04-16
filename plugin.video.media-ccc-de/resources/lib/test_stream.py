# -*- coding: utf-8 -*-

from __future__ import print_function

import simplejson

from .stream import Streams


def test_conferences():
    s = Streams(SampleJson)
    assert len(s.conferences) == 1
    assert s.conferences[0].slug == "eh17"
    assert s.conferences[0].name == "Easterhegg 2017"


def test_rooms():
    s = Streams(SampleJson)
    c = s.conferences[0]
    assert len(c.rooms) == 3
    assert c.rooms[0].slug == "vortragssaal"
    assert c.rooms[0].display == u"Für die Glupscher: Vortragssaal"


def test_streams():
    s = Streams(SampleJson)
    c = s.conferences[0]
    r = c.rooms[0]
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
        "conference": "Easterhegg 2017",
        "slug": "eh17",
        "author": "Easterhegg, you know!",
        "description": "Ist das Zufall oder kann das weg?",
        "keywords": "Easterhegg, Ostern, Hack, CCC, Zufall, Mühlheim, Video, Streaming, Live, Livestream",
        "startsAt": "2017-04-14T11:30:00+0000",
        "endsAt": "2017-04-17T14:30:00+0000",
        "groups": [
            {
                "group": "Für die Glupscher",
                "rooms": [
                    {
                        "slug": "vortragssaal",
                        "schedulename": "Vortragssaal",
                        "thumb": "http://streaming.media.ccc.de/thumbs/s6.png",
                        "link": "http://streaming.media.ccc.de/eh17/vortragssaal",
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
                                        "tech": "1920x1080, VP8+Vorbis in WebM, 3.5 MBit/s",
                                        "url": "http://cdn.c3voc.de/s6_native_hd.webm"
                                    },
                                    "hls": {
                                        "display": "HLS",
                                        "tech": "1920x1080, h264+AAC im MPEG-TS-Container via HTTP, 3 MBit/s",
                                        "url": "http://cdn.c3voc.de/hls/s6_native_hd.m3u8"
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
                                        "tech": "1024x576, VP8+Vorbis in WebM, 1 MBit/s",
                                        "url": "http://cdn.c3voc.de/s6_native_sd.webm"
                                    },
                                    "hls": {
                                        "display": "HLS",
                                        "tech": "1024x576, h264+AAC im MPEG-TS-Container via HTTP, 800 kBit/s",
                                        "url": "http://cdn.c3voc.de/hls/s6_native_sd.m3u8"
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
                                        "url": "http://cdn.c3voc.de/s6_native.mp3"
                                    },
                                    "opus": {
                                        "display": "Opus",
                                        "tech": "Opus-Audio, 64 kBit/s",
                                        "url": "http://cdn.c3voc.de/s6_native.opus"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "slug": "grosses-kolleg",
                        "schedulename": "Großes Kolleg",
                        "thumb": "http://streaming.media.ccc.de/thumbs/s4.png",
                        "link": "http://streaming.media.ccc.de/eh17/grosses-kolleg",
                        "display": "Großes Kolleg",
                        "streams": [
                            {
                                "slug": "hd-native",
                                "display": "Großes Kolleg FullHD Video",
                                "type": "video",
                                "isTranslated": false,
                                "videoSize": [
                                    1920,
                                    1080
                                ],
                                "urls": {
                                    "webm": {
                                        "display": "WebM",
                                        "tech": "1920x1080, VP8+Vorbis in WebM, 3.5 MBit/s",
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
                                "display": "Großes Kolleg SD Video",
                                "type": "video",
                                "isTranslated": false,
                                "videoSize": [
                                    1024,
                                    576
                                ],
                                "urls": {
                                    "webm": {
                                        "display": "WebM",
                                        "tech": "1024x576, VP8+Vorbis in WebM, 1 MBit/s",
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
                                "display": "Großes Kolleg Audio",
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
                    }
                ]
            },
            {
                "group": "Auf die Lauscher",
                "rooms": [
                    {
                        "slug": "lounge",
                        "schedulename": "Lounge",
                        "thumb": "http://streaming.media.ccc.de/thumbs/lounge.png",
                        "link": "http://streaming.media.ccc.de/eh17/lounge",
                        "display": "Lounge",
                        "streams": [
                            {
                                "slug": "music-native",
                                "display": "Lounge Radio",
                                "type": "music",
                                "isTranslated": false,
                                "videoSize": null,
                                "urls": {
                                    "mp3": {
                                        "display": "MP3",
                                        "tech": "MP3-Audio, 192 kBit/s",
                                        "url": "http://cdn.c3voc.de/lounge.mp3"
                                    },
                                    "opus": {
                                        "display": "Opus",
                                        "tech": "Opus-Audio, 96 kBit/s",
                                        "url": "http://cdn.c3voc.de/lounge.opus"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
]
''')
