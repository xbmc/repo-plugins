"""Pure metadata helpers: no Kodi modules, settings reads, networking or storage."""

from dataclasses import dataclass
from typing import Any, Optional
from collections.abc import Mapping


@dataclass(frozen=True)
class MediaItem:
    item_id: str
    kind: str
    payload: dict[str, Any]

    @classmethod
    def from_dto(cls, item: Mapping[str, Any], kind: str = "") -> "MediaItem":
        identity = item.get("Id")
        media = item.get("Type") or kind
        if (
            not isinstance(identity, str)
            or not identity
            or not isinstance(media, str)
            or not media
        ):
            raise ValueError("media needs a non-empty server ID and type")
        payload = dict(item)
        payload["Type"] = media
        return cls(identity, media, payload)


class Metadata:
    def __init__(self, item: Mapping[str, Any]) -> None:
        self.item = item

    def media_streams(self, video: Any, audio: Any, subtitles: Any) -> dict[str, Any]:
        return {"video": video or [], "audio": audio or [], "subtitle": subtitles or []}

    def video_streams(
        self, tracks: list[dict[str, Any]], container: Optional[str] = None
    ) -> list[dict[str, Any]]:

        if container:
            container = container.split(",")[0]

        for track in tracks:

            if "DvProfile" in track:
                track["hdrtype"] = "dolbyvision"
            elif track.get("VideoRangeType", "") in ["HDR10", "HDR10Plus"]:
                track["hdrtype"] = "hdr10"
            elif "HLG" in track.get("VideoRangeType", ""):
                track["hdrtype"] = "hlg"

            track.update(
                {
                    "hdrtype": track.get("hdrtype", "").lower(),
                    "codec": track.get("Codec", "").lower(),
                    "profile": track.get("Profile", "").lower(),
                    "height": track.get("Height"),
                    "width": track.get("Width"),
                    "3d": self.item.get("Video3DFormat"),
                    "aspect": 1.85,
                }
            )

            if "msmpeg4" in track["codec"]:
                track["codec"] = "divx"

            elif "mpeg4" in track["codec"] and (
                "simple profile" in track["profile"] or not track["profile"]
            ):
                track["codec"] = "xvid"

            elif "h264" in track["codec"] and container in ("mp4", "mov", "m4v"):
                track["codec"] = "avc1"

            try:
                width, height = self.item.get(
                    "AspectRatio", track.get("AspectRatio", "0")
                ).split(":")
                track["aspect"] = round(float(width) / float(height), 6)
            except (ValueError, ZeroDivisionError):

                if track["width"] and track["height"]:
                    track["aspect"] = round(float(track["width"] / track["height"]), 6)

            track["duration"] = self.get_runtime()

        return tracks

    def audio_streams(self, tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:

        for track in tracks:

            track.update(
                {
                    "codec": track.get("Codec", "").lower(),
                    "profile": track.get("Profile", "").lower(),
                    "channels": track.get("Channels"),
                    "language": track.get("Language"),
                }
            )

            if "dts-hd ma" in track["profile"]:
                track["codec"] = "dtshd_ma"

            elif "dts-hd hra" in track["profile"]:
                track["codec"] = "dtshd_hra"

        return tracks

    def get_runtime(self) -> Any:

        try:
            runtime = self.item["RunTimeTicks"] / 10000000.0

        except KeyError:
            runtime = self.item.get("CumulativeRunTimeTicks", 0) / 10000000.0

        return runtime


def streams_and_runtime(item: Mapping[str, Any]) -> tuple[dict[str, Any], float]:
    """``(streams, runtime_seconds)`` from a Jellyfin DTO.

    Prefers ``MediaSources[0]`` streams and falls back to top-level
    ``MediaStreams``. When the payload has a runtime but no video track, a
    stub video row is synthesised so Kodi still gets ``iVideoDuration``
    (without it the extras UI falls back to the film's length). Track dicts
    are copied so the caller's DTO is not mutated.
    """
    sources = item.get("MediaSources") or []
    if sources:
        source = sources[0]
        raw = source.get("MediaStreams") or []
        container = source.get("Container") or item.get("Container")
        ticks = source.get("RunTimeTicks")
        if ticks is None:
            ticks = item.get("RunTimeTicks") or item.get("CumulativeRunTimeTicks") or 0
    else:
        raw = item.get("MediaStreams") or []
        container = item.get("Container")
        ticks = item.get("RunTimeTicks") or item.get("CumulativeRunTimeTicks") or 0

    runtime = round(float(ticks or 0) / 10000000.0, 6)
    # Only stamp keys with real values: video_streams does
    # item.get("AspectRatio", fallback).split(":") and a present-but-None
    # AspectRatio would raise.
    shaped = {"RunTimeTicks": ticks or 0}
    if item.get("Video3DFormat") is not None:
        shaped["Video3DFormat"] = item["Video3DFormat"]
    if item.get("AspectRatio"):
        shaped["AspectRatio"] = item["AspectRatio"]
    helper = Metadata(shaped)
    video = [dict(s) for s in raw if s.get("Type") == "Video"]
    audio = [dict(s) for s in raw if s.get("Type") == "Audio"]
    subs = [s.get("Language") for s in raw if s.get("Type") == "Subtitle"]
    video = helper.video_streams(video, container)
    audio = helper.audio_streams(audio)
    if runtime and not video:
        video = [
            {
                "codec": "",
                "profile": "",
                "aspect": None,
                "width": None,
                "height": None,
                "3d": None,
                "hdrtype": "",
                "duration": runtime,
            }
        ]
    return helper.media_streams(video, audio, subs), runtime


def ratings(obj: Mapping[str, Any]) -> dict[str, tuple[Any, Any]]:
    """Ordered ``{rating_type: (rating, votes)}`` for Kodi's ratings.

    The community rating is always present as ``default``, even as ``None``.
    The critic rating (Jellyfin's ``CriticRating``, the OMDb plugin's Rotten
    Tomatoes tomatometer) is a percentage, scaled onto Kodi's 0-10 scale --
    78 becomes 7.8 -- so star ratings and rating sorts agree.
    """
    rows = {"default": (obj.get("Rating"), obj.get("Votes"))}
    critic = obj.get("CriticRating")

    if critic is not None:
        rows["critic"] = (round(float(critic) / 10.0, 2), None)

    return rows


PROVIDER_PRIORITY = ("imdb", "tvdb", "tmdb")
