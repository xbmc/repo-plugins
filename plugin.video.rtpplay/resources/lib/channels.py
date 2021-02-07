# -*- coding: utf-8 -*-

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36",
    "Referer": "https://www.rtp.pt/",
}

RTP_CHANNELS = [
    {   "id": "rtp1",
        "name" : "RTP 1",
        "streams": [
            {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtp1HD.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
    {   "id": "rtp2",
        "name" : "RTP 2",
        "streams": [
            {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtp2.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
    {   "id": "rtp3",
        "name" : "RTP 3",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/livetvhlsDVR/rtpndvr.smil/playlist.m3u8?DVR"}
        ]
    },
    {   "id": "rtpinternacional",
        "name" : "RTP Internacional",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpi.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
    {   "id": "rtpmemoria",
        "name" : "RTP Memória",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpmem.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
    {   "id": "rtpmadeira",
        "name" : "RTP Madeira",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpmadeira.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
    {   "id": "rtpacores",
        "name" : "RTP Açores",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpacores.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
    {   "id": "rtpafrica",
        "name" : "RTP África",
        "streams": [
             {"type":"hls", "url": "https://streaming-live.rtp.pt/liverepeater/smil:rtpafrica.smil/playlist.m3u8?pxt_rtp"}
        ]
    },
]