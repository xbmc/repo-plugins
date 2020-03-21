# -*- coding: utf-8 -*-

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Mobile Safari/537.36",
    "Referer": "https://www.rtp.pt/play/direto/",
}

RTP_CHANNELS = [
    {   "id": "rtp1",
        "name" : "RTP 1",
        "streams": [
            {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtp1HD.smil/playlist.m3u8"},
            {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtp1.smil/manifest.mpd", "tk": "https://www.rtp.pt/play/direto/rtp1", "license": "https://widevine-proxy.drm.technology/proxy"}
        ]
    },
    {   "id": "rtp2",
        "name" : "RTP 2",
        "streams": [
            {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtp2.smil/playlist.m3u8"},
        ]
    },
    {   "id": "rtp3",
        "name" : "RTP 3",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/livetvhlsDVR/rtpndvr.smil/playlist.m3u8?DVR"},
             {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtpn.smil/manifest.mpd?DVR", "tk": "https://www.rtp.pt/play/direto/rtp3", "license": "https://widevine-proxy.drm.technology/proxy" }
        ]
    },
    {   "id": "rtpinternacional",
        "name" : "RTP Internacional",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpi.smil/playlist.m3u8"},
             {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtpi.smil/manifest.mpd", "tk": "https://www.rtp.pt/play/direto/rtpinternacional", "license": "https://widevine-proxy.drm.technology/proxy" }
        ]
    },
    {   "id": "rtpmemoria",
        "name" : "RTP Memória",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpmem.smil/playlist.m3u8"},
             {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtpmem.smil/manifest.mpd", "tk": "https://www.rtp.pt/play/direto/rtpmemoria", "license": "https://widevine-proxy.drm.technology/proxy" }
        ]
    },
    {   "id": "rtpmadeira",
        "name" : "RTP Madeira",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpmadeira.smil/playlist.m3u8"},
             {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtpmadeira.smil/manifest.mpd", "tk": "https://www.rtp.pt/play/direto/rtpmadeira", "license": "https://widevine-proxy.drm.technology/proxy" }
        ]
    },
    {   "id": "rtpacores",
        "name" : "RTP Açores",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpacores.smil/playlist.m3u8"},
             {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtpacores.smil/manifest.mpd", "tk": "https://www.rtp.pt/play/direto/rtpacores", "license": "https://widevine-proxy.drm.technology/proxy" }
        ]
    },
    {   "id": "rtpafrica",
        "name" : "RTP África",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpafrica.smil/playlist.m3u8"},
             {"type":"dashwv", "url": "https://streaming-live.rtp.pt/liverepeater/rtpafrica.smil/manifest.mpd", "tk": "https://www.rtp.pt/play/direto/rtpafrica", "license": "https://widevine-proxy.drm.technology/proxy" }
        ]
    },
]