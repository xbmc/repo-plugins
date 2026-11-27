"""Jellyfin device profile, ported from pvr.kofin's BuildDeviceProfile.

A bitrate cap leaves direct play available: for VOD the server applies the
cap in its direct-play decision, per item.

``forceDirectPlay`` is scoped to video. It suppresses every video-side
constraint (HDR, width, streaming bitrate), but music delivery belongs to
``musicTranscode`` and its own cap, so forcing direct play for video does not
silently uncap music.

The same scoping holds the other way: ``forceRemux`` and ``forceTranscode``
withdraw the *video* DirectPlayProfile, never the audio one. A profile with no
audio DirectPlayProfile makes the server re-encode every song no matter what
the music settings say.

Force remux is HLS + codec-copy: the video transcoding legs list every
HLS-legal allowed codec, copy stays on, and the bitrate / channel caps are
ignored so StreamBuilder does not refuse a listed E-AC3 copy and then try
to encode it. Force transcode names the preferred encode target only and
denies both copies. Transcode wins when both are set. Music PlaybackInfo is
not this path.
"""

from typing import Any, Optional

from kofin.core import settings

JsonDict = dict[str, Any]

UNLIMITED_BITRATE = 1_000_000_000

ALL_HDR_TYPES = [
    "HDR10",
    "HLG",
    "HDR10Plus",
    "DOVI",
    "DOVIWithHDR10",
    "DOVIWithHLG",
    "DOVIWithSDR",
    "DOVIWithEL",
    "DOVIWithHDR10Plus",
    "DOVIWithELHDR10Plus",
]
VP9_HDR_TYPES = ["HDR10", "HLG", "HDR10Plus"]

SUBTITLE_FORMATS = ["srt", "ass", "sub", "ssa", "smi", "pgssub", "dvdsub", "pgs"]
# The same list without the image formats. Offering only these is how a
# burn-in is requested — see _subtitle_profiles.
TEXT_SUBTITLE_FORMATS = ["srt", "ass", "sub", "ssa", "smi"]


DEFAULT_VIDEO_CODECS = [
    "h264",
    "h264_10bit",
    "hevc",
    "hevc_rext",
    "av1",
    "mpeg2video",
    "vp9",
    "vc1",
]
DEFAULT_AUDIO_CODECS = ["aac", "mp2", "mp3", "ac3", "eac3", "opus", "flac", "dts"]

# The video codecs ffmpeg muxes into mp4, for the download transcoding
# profile's stream-copy list (build_download). No vc1: its mp4 mapping is
# poorly supported, and a compliant vc1 source downloads as the original.
MP4_COPY_CODECS = ("h264", "hevc", "av1", "vp9", "mpeg2video")

# What counts as an acceptable *music file* for the download decision: lossy
# codecs only, so FLAC/ALAC/WAV answer SupportsDirectPlay=false and convert
# whatever the bitrate cap says — "lossless always converts" is the music
# toggle's core promise. Distinct from DEFAULT_AUDIO_CODECS, which describes
# what the *device decodes* (flac included) for video-embedded audio and
# streaming.
LOSSY_AUDIO_CODECS = ("aac", "mp3", "opus", "vorbis", "wma", "mp2", "ac3", "eac3")

# HLS will copy only these. A remux TranscodingProfile that lists anything
# else either gets it stripped (no fallback restored) or, if the source
# matches, pinned as the encode target.
HLS_TS_AUDIO = ("aac", "ac3", "eac3", "mp3")
HLS_MP4_AUDIO = ("aac", "ac3", "eac3", "mp3", "alac", "flac", "opus", "dts", "truehd")
HLS_TS_VIDEO = ("h264", "hevc", "vp9")


def audio_bitrate_bps(audio_cap_kbps: int, budget_bps: int) -> int:
    """The audio allowance for a transcode confined to ``budget_bps``.

    The budget is split rather than a fixed share reserved, because a
    reservation above a small budget pushes VideoBitrate negative, which the
    server rejects. The share is min(setting, budget/10).
    """
    cap = max(audio_cap_kbps, 0) * 1000
    if budget_bps <= 0 or budget_bps >= UNLIMITED_BITRATE:
        return cap
    return min(cap, budget_bps // 10)


class ProfileConfig:
    """The transcoding settings snapshot a profile is built from."""

    def __init__(
        self,
        force_direct_play: bool = False,
        force_remux: bool = False,
        force_transcode: bool = False,
        video_codecs: Optional[list[str]] = None,
        audio_codecs: Optional[list[str]] = None,
        hdr_types: Optional[list[str]] = None,
        preferred_video: str = "h264",
        preferred_audio: str = "aac",
        max_channels: int = 6,
        max_bitrate_mbps: float = 0,
        max_width: int = 0,
        audio_bitrate_kbps: int = 384,
        music_codec: str = "opus",
        music_bitrate_kbps: int = 128,
        music_max_bitrate_kbps: int = 0,
    ) -> None:
        self.force_direct_play = force_direct_play
        self.force_remux = force_remux
        self.force_transcode = force_transcode
        self.video_codecs = list(
            DEFAULT_VIDEO_CODECS if video_codecs is None else video_codecs
        )
        self.audio_codecs = list(
            DEFAULT_AUDIO_CODECS if audio_codecs is None else audio_codecs
        )
        self.hdr_types = list(ALL_HDR_TYPES if hdr_types is None else hdr_types)
        self.preferred_video = preferred_video
        self.preferred_audio = preferred_audio
        self.max_channels = max_channels
        self.max_bitrate_mbps = max_bitrate_mbps
        self.max_width = max_width
        self.audio_bitrate_kbps = audio_bitrate_kbps
        self.music_codec = music_codec
        self.music_bitrate_kbps = music_bitrate_kbps
        self.music_max_bitrate_kbps = music_max_bitrate_kbps

    @classmethod
    def _device(cls) -> dict[str, Any]:
        """What the device plays, the same whether it streams or downloads:
        the transcode tab's codec lists, HDR types, preferred targets,
        channels and audio bitrate."""
        return dict(
            video_codecs=settings.get_list("directPlayVideoCodecs"),
            audio_codecs=settings.get_list("directPlayAudioCodecs"),
            hdr_types=settings.get_list("allowedHdrTypes"),
            preferred_video=settings.get_str("preferredVideoCodec") or "h264",
            preferred_audio=settings.get_str("preferredAudioCodec") or "aac",
            max_channels=settings.get_int("maxAudioChannels") or 6,
            audio_bitrate_kbps=settings.get_int("audioBitrate") or 384,
        )

    @classmethod
    def from_settings(cls) -> "ProfileConfig":
        return cls(
            **cls._device(),
            force_direct_play=settings.get_bool("forceDirectPlay"),
            force_remux=settings.get_bool("forceRemux"),
            force_transcode=settings.get_bool("forceTranscode"),
            max_bitrate_mbps=settings.get_float("maxStreamingBitrate"),
            max_width=settings.get_int("maxResolution"),
            music_codec=settings.get_str("musicTranscodeCodec") or "opus",
            music_bitrate_kbps=settings.get_int("musicTranscodeBitrate") or 128,
            # ``musicTranscode`` owns the whole music group: with it off the
            # cap must not apply, or a value left behind from an earlier
            # session would still force transcodes on the paths that do reach
            # PlaybackInfo (browsing the server directly). The transcoding
            # profile itself stays either way — it is the server's fallback
            # when a container cannot be direct played at all.
            music_max_bitrate_kbps=(
                settings.get_int("musicMaxBitrate")
                if settings.get_bool("musicTranscode")
                else 0
            ),
        )

    @classmethod
    def for_downloads(cls) -> "ProfileConfig":
        """The snapshot the *download* decision is built from.

        Device compatibility — codec lists, HDR types, preferred targets —
        comes from the transcode tab, because the device is the same device;
        the caps are downloads-own, because streaming limits describe
        streaming (a box that streams 4K over the LAN may still want 720p
        downloads). Force flags stay False by construction: whether the
        decision runs at all is ``downloadsTranscode``/
        ``downloadsMusicTranscode``, gated by the caller, and a forced answer
        would defeat the only-when-necessary contract.
        """
        return cls(
            **cls._device(),
            max_bitrate_mbps=settings.get_float("downloadsMaxBitrate"),
            max_width=settings.get_int("downloadsMaxResolution"),
            music_codec=settings.get_str("downloadsMusicCodec") or "opus",
            music_bitrate_kbps=settings.get_int("downloadsMusicBitrate") or 128,
            music_max_bitrate_kbps=settings.get_int("downloadsMusicMaxBitrate"),
        )


def build(
    config: ProfileConfig,
    bitrate_override_mbps: float = 0,
    force_transcode: bool = False,
    burn_subtitles: bool = False,
) -> JsonDict:
    """The DeviceProfile JSON for PlaybackInfo requests.

    ``bitrate_override_mbps``/``force_transcode`` implement the transcode
    context item: a forced transcode at a chosen bitrate for this play only.
    The override may be fractional (0.5/0.75 Mbit/s) or 0, which means
    Maximum streaming bitrate: the context item's default, read even under
    force direct play, and unlimited only when that setting is.

    ``burn_subtitles`` withdraws the image formats from SubtitleProfiles for
    this play only, which is what makes the server answer ``Encode`` for a
    PGS/DVDSUB track instead of ``External``. It is the single case where kofin
    asks for burn-in: an image subtitle chosen on a transcode, where the
    stream carries no subtitles and the ``.sup`` the External delivery would
    serve is neither small enough to fetch nor something Kodi can render.
    """
    force_xcode = force_transcode or config.force_transcode
    remux_copy = config.force_remux and not force_xcode
    force_direct = config.force_direct_play and not force_xcode
    bitrate_mbps = bitrate_override_mbps or config.max_bitrate_mbps
    if force_direct or remux_copy or bitrate_mbps <= 0:
        max_bitrate = UNLIMITED_BITRATE
    else:
        max_bitrate = int(bitrate_mbps * 1_000_000)

    audio_codecs = _preferred_first(config.audio_codecs, config.preferred_audio)
    video_codecs = _direct_video_codecs(config)

    return _envelope(
        config,
        max_bitrate,
        _transcoding_profiles(
            config,
            audio_codecs,
            video_codecs,
            max_bitrate,
            remux_copy=remux_copy,
            force_xcode=force_xcode,
        ),
        _direct_play_profiles(
            config, audio_codecs, video_codecs, force_direct, force_transcode
        ),
        force_direct,
        burn_subtitles,
    )


def _envelope(
    config: ProfileConfig,
    max_bitrate: int,
    transcoding: list[JsonDict],
    direct: list[JsonDict],
    force_direct: bool,
    burn_subtitles: bool,
) -> JsonDict:
    """The DeviceProfile shell :func:`build` and :func:`build_download`
    share: the envelope fields, the codec profiles — which derive
    their own capability tokens from ``config`` — and the subtitle list."""
    return {
        "Name": "Kodi",
        "MaxStreamingBitrate": max_bitrate,
        "MaxStaticBitrate": max_bitrate,
        "MusicStreamingTranscodingBitrate": config.music_bitrate_kbps * 1000,
        "TimelineOffsetSeconds": 5,
        "TranscodingProfiles": transcoding,
        "DirectPlayProfiles": direct,
        "CodecProfiles": _codec_profiles(config, force_direct),
        "SubtitleProfiles": _subtitle_profiles(burn_subtitles),
    }


def _subtitle_profiles(burn_subtitles: bool) -> list[JsonDict]:
    """Declaring a format here is what keeps the server from burning it in.

    With the image formats present the server answers ``External`` for every
    subtitle, embedded PGS included, so withdrawing them is an explicit
    request for ``Encode``; the text formats stay either way so a text
    subtitle chosen alongside is still delivered as a file.
    """
    formats = TEXT_SUBTITLE_FORMATS if burn_subtitles else SUBTITLE_FORMATS
    return [
        {"Format": fmt, "Method": method}
        for fmt in formats
        for method in ("Embed", "External")
    ]


def _preferred_first(codecs: list[str], preferred: str) -> list[str]:
    ordered = [preferred]
    ordered.extend(codec for codec in codecs if codec != preferred)
    return ordered


def _hls_copy_list(allowed: list[str], preferred: str, legal: tuple) -> list[str]:
    """Preferred first when HLS-legal, then the rest of ``allowed`` that HLS can mux."""
    legal_set = set(legal)
    lead = (
        preferred
        if preferred in legal_set
        else next((codec for codec in allowed if codec in legal_set), None)
    )
    if lead is None:
        return []
    return [lead] + [codec for codec in allowed if codec in legal_set and codec != lead]


def _direct_video_codecs(config: ProfileConfig) -> list[str]:
    """The direct-play codec names, with the capability tokens (h264_10bit,
    hevc_rext) folded into their base codecs and the configured order kept."""
    tokens = set(config.video_codecs)
    codecs: list[str] = []
    if "h264" in tokens or "h264_10bit" in tokens:
        codecs.append("h264")
    if "hevc" in tokens or "hevc_rext" in tokens:
        codecs.append("hevc")
    for token in config.video_codecs:
        if token not in ("h264", "h264_10bit", "hevc", "hevc_rext"):
            codecs.append(token)
    return codecs


def build_download(config: ProfileConfig) -> JsonDict:
    """The DeviceProfile for the conditional download decision.

    Same device statement as :func:`build` — direct-play lists, codec and
    HDR conditions, the width cap — with the caps read from the downloads
    settings (``ProfileConfig.for_downloads``) and two deviations:

    * The video transcoding profile is a single progressive leg:
      ``Protocol: "http"`` (a file, not a playlist), ``Container: "mp4"``.
      Its codec list is every mp4-muxable direct-play codec, so the
      server's own stream-copy logic keeps a compliant video track and
      re-encodes only what violates a limit.
    * The audio DirectPlayProfile is the lossy list, not the open one:
      ``SupportsDirectPlay`` is the whole decision for a music download, and
      an open profile would answer "keep the FLAC". The bitrate cap rides
      the Audio codec profile as in :func:`build` (``music_max_bitrate_kbps``).
    """
    if config.max_bitrate_mbps <= 0:
        max_bitrate = UNLIMITED_BITRATE
    else:
        max_bitrate = int(config.max_bitrate_mbps * 1_000_000)

    audio_codecs = _preferred_first(config.audio_codecs, config.preferred_audio)
    video_codecs = _direct_video_codecs(config)

    return _envelope(
        config,
        max_bitrate,
        _download_transcoding_profiles(config, audio_codecs, video_codecs, max_bitrate),
        _download_direct_play_profiles(config, audio_codecs, video_codecs),
        False,
        False,
    )


def _music_transcoding_profile(config: ProfileConfig) -> JsonDict:
    return {
        "Type": "Audio",
        "Container": config.music_codec,
        "AudioCodec": config.music_codec,
        "Context": "Streaming",
        "Protocol": "http",
        "MaxAudioChannels": "2",
    }


def _download_transcoding_profiles(
    config: ProfileConfig,
    audio_codecs: list[str],
    video_codecs: list[str],
    max_bitrate: int,
) -> list[JsonDict]:
    lead = (
        config.preferred_video if config.preferred_video in MP4_COPY_CODECS else "h264"
    )
    # The encode target is the first entry the server's ffmpeg can encode
    # (StreamingHelpers picks FirstOrDefault(CanEncodeToVideoCodec)); the
    # rest of the list is order-blind stream-copy membership. So the tail
    # ranks by efficiency — hevc before h264 — rather than keeping the
    # direct-play list's display order: on a stripped ffmpeg without the
    # preferred encoder (stock jellyfin-ffmpeg carries all three), the
    # fallback should cost quality-per-byte, not compatibility. Only codecs
    # the device direct-plays may appear at all: every entry is a codec the
    # finished file may carry.
    copy_codecs = [lead]
    copy_codecs.extend(
        codec for codec in ("hevc", "h264") if codec != lead and codec in video_codecs
    )
    copy_codecs.extend(
        codec
        for codec in video_codecs
        if codec not in copy_codecs and codec in MP4_COPY_CODECS
    )
    video: JsonDict = {
        "Type": "Video",
        "Container": "mp4",
        "VideoCodec": ",".join(copy_codecs),
        "AudioCodec": ",".join(audio_codecs),
        "Context": "Streaming",
        "Protocol": "http",
        "MaxAudioChannels": str(config.max_channels),
    }
    conditions = _audio_bitrate_conditions(config, max_bitrate)
    if conditions is not None:
        video["Conditions"] = conditions
    music = _music_transcoding_profile(config)
    return [video, music]


def _download_direct_play_profiles(
    config: ProfileConfig, audio_codecs: list[str], video_codecs: list[str]
) -> list[JsonDict]:
    profiles: list[JsonDict] = []
    if video_codecs:
        profiles.append(_video_direct_play_profile(config, audio_codecs, video_codecs))
    profiles.append({"Type": "Audio", "AudioCodec": ",".join(LOSSY_AUDIO_CODECS)})
    return profiles


def _transcoding_profiles(
    config: ProfileConfig,
    audio_codecs: list[str],
    video_codecs: list[str],
    max_bitrate: int,
    remux_copy: bool = False,
    force_xcode: bool = False,
) -> list[JsonDict]:
    # TS codec list: everything except av1 (which can't ride MPEG-TS and gets
    # its own fMP4 profile, when the device decodes av1 at all — see below).
    # The lead codec is the forced-transcode target: hevc when av1 is
    # preferred, otherwise the preferred codec.
    hevc_in_list = "hevc" in video_codecs
    ts_lead = (
        "hevc"
        if config.preferred_video == "av1" and hevc_in_list
        else config.preferred_video
    )
    ts_codecs = [ts_lead]
    ts_codecs.extend(
        codec for codec in video_codecs if codec != ts_lead and codec != "av1"
    )
    if ts_lead == "av1":  # preferred av1 but no hevc available
        ts_codecs = [codec for codec in ts_codecs if codec != "av1"] or ["h264"]

    ts_audio = audio_codecs
    mp4_audio = audio_codecs
    if remux_copy:
        ts_preferred = (
            "aac" if config.preferred_audio == "opus" else config.preferred_audio
        )
        ts_audio = _hls_copy_list(audio_codecs, ts_preferred, HLS_TS_AUDIO) or [
            ts_preferred if ts_preferred != "opus" else "aac"
        ]
        mp4_audio = _hls_copy_list(
            audio_codecs, config.preferred_audio, HLS_MP4_AUDIO
        ) or [config.preferred_audio]
        ts_codecs = _hls_copy_list(ts_codecs, ts_lead, HLS_TS_VIDEO) or ts_codecs
    elif force_xcode:
        ts_audio = [
            "aac" if config.preferred_audio == "opus" else config.preferred_audio
        ]
        mp4_audio = [config.preferred_audio]

    common = {
        "Type": "Video",
        "Context": "Streaming",
        "Protocol": "hls",
        "MinSegments": "1",
        "BreakOnNonKeyFrames": True,
    }
    if not remux_copy:
        common["MaxAudioChannels"] = str(config.max_channels)
        conditions = _audio_bitrate_conditions(config, max_bitrate)
        if conditions is not None:
            common["Conditions"] = conditions
    ts: JsonDict = dict(
        common,
        Container="ts",
        VideoCodec=",".join(ts_codecs),
        AudioCodec=",".join(ts_audio),
    )

    music = _music_transcoding_profile(config)

    # The fMP4 leg exists to carry av1, so it is offered only when the device
    # decodes av1 (preferring a codec implies decoding it). Jellyfin's
    # StreamBuilder ranks the transcoding profiles rather than taking the
    # first that matches, and one whose VideoCodec list holds the source codec
    # ranks top so it can stream-copy, so ordering cannot withdraw av1.
    if "av1" not in video_codecs and config.preferred_video != "av1":
        return [ts, music]

    fmp4: JsonDict = dict(
        common,
        Container="mp4",
        VideoCodec="av1",
        AudioCodec=",".join(mp4_audio),
    )
    video_profiles = [fmp4, ts] if config.preferred_video == "av1" else [ts, fmp4]
    return video_profiles + [music]


def _audio_bitrate_conditions(
    config: ProfileConfig, max_bitrate: int
) -> Optional[list[JsonDict]]:
    """Output constraint for transcodes only — never a direct-play gate.
    Capped against the streaming budget so the profile agrees with the
    split ``plugin/play.py`` writes into the transcoding URL; None when
    no cap applies."""
    audio_bps = audio_bitrate_bps(config.audio_bitrate_kbps, max_bitrate)
    if audio_bps <= 0:
        return None
    return [
        {
            "Condition": "LessThanEqual",
            "Property": "AudioBitrate",
            "Value": str(audio_bps),
            "IsRequired": False,
        }
    ]


def _direct_play_profiles(
    config: ProfileConfig,
    audio_codecs: list[str],
    video_codecs: list[str],
    force_direct: bool,
    force_transcode: bool,
) -> list[JsonDict]:
    if force_direct:
        return [
            {"Type": "Video", "Container": "", "VideoCodec": "", "AudioCodec": ""},
            {"Type": "Audio"},
        ]
    if force_transcode:
        # This play only, and the user asked for it by name (the transcode
        # context item), so it takes the audio entry with it.
        return []

    audio = [{"Type": "Audio"}]

    if config.force_remux or config.force_transcode or not video_codecs:
        return audio

    return [_video_direct_play_profile(config, audio_codecs, video_codecs)] + audio


def _video_direct_play_profile(
    config: ProfileConfig, audio_codecs: list[str], video_codecs: list[str]
) -> JsonDict:
    """No Container constraint on purpose: a stream and a downloaded file
    both go through demuxers that read anything ffmpeg does, so a container
    must never be what forces a transcode. Preferring a codec implies the
    device decodes it."""
    direct_video = list(video_codecs)
    if config.preferred_video not in direct_video:
        direct_video.append(config.preferred_video)
    return {
        "Type": "Video",
        "VideoCodec": ",".join(direct_video),
        "AudioCodec": ",".join(audio_codecs),
    }


def _codec_profiles(config: ProfileConfig, force_direct: bool) -> list[JsonDict]:
    tokens = set(config.video_codecs)
    h264 = "h264" in tokens
    h264_10bit = "h264_10bit" in tokens
    hevc = "hevc" in tokens
    hevc_rext = "hevc_rext" in tokens
    profiles: list[JsonDict] = []

    if h264 and not h264_10bit:
        profiles.append(_codec_condition("h264", "LessThanEqual", "VideoBitDepth", "8"))
    if hevc and not hevc_rext:
        profiles.append(
            _codec_condition("hevc", "EqualsAny", "VideoProfile", "main|main 10")
        )

    if not force_direct:
        selected = [hdr for hdr in config.hdr_types if hdr in ALL_HDR_TYPES]
        profiles.extend(
            _hdr_profile(codec, capability, can_dovi, selected)
            for codec, capability, can_dovi, present in (
                ("hevc", ALL_HDR_TYPES, True, hevc or hevc_rext),
                ("av1", ALL_HDR_TYPES, True, "av1" in tokens),
                ("vp9", VP9_HDR_TYPES, False, "vp9" in tokens),
            )
            if present and set(capability) - set(selected)
        )

        if config.max_width > 0:
            profiles.append(
                {
                    "Type": "Video",
                    "Conditions": [
                        {
                            "Condition": "LessThanEqual",
                            "Property": "Width",
                            "Value": str(config.max_width),
                            "IsRequired": False,
                        }
                    ],
                }
            )

    # Outside the force-direct-play block on purpose: that toggle is scoped to
    # video.
    if config.music_max_bitrate_kbps > 0:
        profiles.append(
            {
                "Type": "Audio",
                "Conditions": [
                    {
                        "Condition": "LessThanEqual",
                        "Property": "AudioBitrate",
                        "Value": str(config.music_max_bitrate_kbps * 1000),
                        "IsRequired": False,
                    }
                ],
            }
        )

    return profiles


def _codec_condition(codec: str, condition: str, prop: str, value: str) -> JsonDict:
    return {
        "Type": "Video",
        "Codec": codec,
        "Conditions": [{"Condition": condition, "Property": prop, "Value": value}],
    }


def _hdr_profile(
    codec: str, capability: list[str], can_dovi: bool, selected: list[str]
) -> JsonDict:
    # SDR is always allowed and must lead; iterate the canonical order for a
    # deterministic value string.
    value = "SDR"
    for hdr_type in ALL_HDR_TYPES:
        if hdr_type in capability and hdr_type in selected:
            value += "|" + hdr_type
    if can_dovi and "HDR10" in selected:
        value += "|DOVIInvalid"  # invalid DV is served as its HDR10 base layer
    profile = _codec_condition(codec, "EqualsAny", "VideoRangeType", value)
    profile["Conditions"][0]["IsRequired"] = False
    return profile
