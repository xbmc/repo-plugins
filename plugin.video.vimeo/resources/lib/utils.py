import os
import re
import urllib.parse


def m3u8_without_av1(m3u8, base_url):
    """
    Strip AV1 codec streams from m3u8 master playlist.
    :param m3u8: string
    :param base_url: string
    :return: string
    """
    m3u8_master_without_av1 = ""

    remove_line = False
    for line in m3u8.splitlines():
        av1 = re.search(r"CODECS=\"av01", line)
        url = re.search(r"^\.\./", line)
        url_media = re.search(r"URI=\"(.*\.m3u8.*)\"", line)
        if remove_line:
            remove_line = False
            continue
        elif not av1:
            if url_media:
                url_absolute = urllib.parse.urljoin(base_url, url_media.group(1))
                m3u8_master_without_av1 += line.replace(url_media.group(1), url_absolute)
            elif url:
                m3u8_master_without_av1 += urllib.parse.urljoin(base_url, line)
            else:
                m3u8_master_without_av1 += line

            m3u8_master_without_av1 += os.linesep
            remove_line = False
        else:
            remove_line = True

    return m3u8_master_without_av1


def m3u8_fix_audio(m3u8):
    """
    Vimeo HLS playlists with AV1 streams contain broken audio-links.
    We have to repair those by using the folders from AVC1 streams.
    :param m3u8: string
    :return: string
    """
    m3u8_with_fixed_audio = ""
    audio = {}

    # Collect audio qualities with paths
    collect_path = False
    for line in m3u8.splitlines():
        audio_quality = re.search(r"AUDIO=\"([^\"]*)\"", line)
        if collect_path and audio.get(collect_path) is None:
            audio_path = re.search(r".*/([^/]*)/[^/]*\.m3u8.*", line)
            if audio_path:
                audio[collect_path] = audio_path.group(1)
            collect_path = False
        elif audio_quality:
            collect_path = audio_quality.group(1)

    # Patch audio links
    for line in m3u8.splitlines():
        audio_id = re.search(r"TYPE=AUDIO,GROUP-ID=\"([^\"]*)\"", line)
        audio_path = re.search(r"URI=\".*/([^/]*)/.*\.m3u8.*\"", line)
        if audio_id and audio_path and audio.get(audio_id.group(1)) is not None:
            m3u8_with_fixed_audio += line.replace(audio_path.group(1), audio[audio_id.group(1)])
        else:
            m3u8_with_fixed_audio += line

        m3u8_with_fixed_audio += os.linesep

    return m3u8_with_fixed_audio


def webvtt_to_srt(webvtt):
    srt = ""
    counter = 1

    for line in webvtt.splitlines():
        if line.startswith("WEBVTT"):
            continue
        if counter == 1 and line == "":
            continue

        matches = re.match(r"^(?P<fh>\d{2}:)?(?P<fm>\d{2}):(?P<fs>\d{2}).(?P<fms>\d{3})\s-->\s(?P<th>\d{2}:)?(?P<tm>\d{2}):(?P<ts>\d{2}).(?P<tms>\d{3})", line)  # noqa: E261
        if matches:
            srt += str(counter) + os.linesep
            srt += "{}{}:{},{} --> {}{}:{},{}{}".format(
                matches.group('fh') or "00:",
                matches.group('fm'),
                matches.group('fs'),
                matches.group('fms'),
                matches.group('th') or "00:",
                matches.group('tm'),
                matches.group('ts'),
                matches.group('tms'),
                os.linesep
            )
            counter += 1
        else:
            srt += line + os.linesep

    return srt
