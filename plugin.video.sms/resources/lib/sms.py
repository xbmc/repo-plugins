"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

# ReplayGain mapping
replaygain = {0:0, 1:2, 2:1}

class ClientProfile:
    
    def __init__(self, client, format, formats, codecs, mchCodecs, videoQuality, audioQuality, maxBitrate, maxSampleRate, replaygain, directPlay):
        self.client = client
        self.format = format
        self.formats = formats
        self.codecs = codecs
        self.mchCodecs = mchCodecs
        self.videoQuality = videoQuality
        self.audioQuality = audioQuality
        self.maxBitrate = maxBitrate
        self.maxSampleRate = maxSampleRate
        self.replaygain = replaygain
        self.directPlay = directPlay
