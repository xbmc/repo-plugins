from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

import xbmcvfs

from logger import Logger
from models import ArtworkType, DataSource, MovieDetails, TVShowDetails
from settings_manager import SettingsManager


def write_movie_nfo(
    details: MovieDetails,
    file_path: str,
    settings: SettingsManager,
    logger: Logger,
) -> None:
    """Write movie NFO file next to the video file."""
    try:
        if not settings.enable_nfo_export:
            logger.debug(f"write_movie_nfo: nfo export disabled, skipping kp_id={details.kinopoisk_id}")
            return

        if not file_path:
            logger.info(f"write_movie_nfo: empty file_path, skipping kp_id={details.kinopoisk_id}")
            return

        nfo_path = _get_movie_nfo_path(file_path)

        if not nfo_path:
            logger.info(
                f"write_movie_nfo: directory path detected, skipping nfo export "
                f"kp_id={details.kinopoisk_id} path={file_path}"
            )
            return

        if xbmcvfs.exists(nfo_path) and not settings.nfo_overwrite:
            logger.info(
                f"write_movie_nfo: nfo already exists and overwrite disabled, "
                f"kp_id={details.kinopoisk_id} path={nfo_path}"
            )
            return

        xml_content = _build_movie_xml(details, settings, logger)
        success = _write_nfo_file(xml_content, nfo_path, logger)

        if success:
            logger.info(
                f"write_movie_nfo: success kp_id={details.kinopoisk_id} path={nfo_path}"
            )
        else:
            logger.warning(
                f"write_movie_nfo: failed kp_id={details.kinopoisk_id} path={nfo_path}"
            )
    except Exception as e:
        logger.warning(
            f"write_movie_nfo: unexpected error kp_id={details.kinopoisk_id}: {e}"
        )


def write_tvshow_nfo(
    details: TVShowDetails,
    dir_path: str,
    settings: SettingsManager,
    logger: Logger,
) -> None:
    """Write tvshow NFO file into the show directory."""
    try:
        if not settings.enable_nfo_export:
            logger.debug(f"write_tvshow_nfo: nfo export disabled, skipping kp_id={details.kinopoisk_id}")
            return

        if not dir_path:
            logger.info(f"write_tvshow_nfo: empty dir_path, skipping kp_id={details.kinopoisk_id}")
            return

        nfo_path = _get_tvshow_nfo_path(dir_path)

        if xbmcvfs.exists(nfo_path) and not settings.nfo_overwrite:
            logger.info(
                f"write_tvshow_nfo: nfo already exists and overwrite disabled, "
                f"kp_id={details.kinopoisk_id} path={nfo_path}"
            )
            return

        xml_content = _build_tvshow_xml(details, settings, logger)
        success = _write_nfo_file(xml_content, nfo_path, logger)

        if success:
            logger.info(
                f"write_tvshow_nfo: success kp_id={details.kinopoisk_id} path={nfo_path}"
            )
        else:
            logger.warning(
                f"write_tvshow_nfo: failed kp_id={details.kinopoisk_id} path={nfo_path}"
            )
    except Exception as e:
        logger.warning(
            f"write_tvshow_nfo: unexpected error kp_id={details.kinopoisk_id}: {e}"
        )


def _build_movie_xml(details: MovieDetails, settings=None, logger: Logger | None = None) -> str:
    """Build XML string for a movie NFO."""
    root = ET.Element("movie")
    _build_common_elements(root, details, settings, logger)
    if details.set_name:
        set_elem = ET.SubElement(root, "set")
        ET.SubElement(set_elem, "name").text = details.set_name
    return _prettify_xml(root)


def _build_tvshow_xml(details: TVShowDetails, settings=None, logger: Logger | None = None) -> str:
    """Build XML string for a tvshow NFO."""
    root = ET.Element("tvshow")
    _build_common_elements(root, details, settings, logger)
    return _prettify_xml(root)


def _build_common_elements(
    parent: ET.Element,
    details: "MovieDetails | TVShowDetails",
    settings=None,
    logger: Logger | None = None,
) -> None:
    """Populate shared NFO elements onto parent from details."""
    ET.SubElement(parent, "title").text = details.title_ru

    if details.title_original:
        ET.SubElement(parent, "originaltitle").text = details.title_original

    if details.year > 0:
        ET.SubElement(parent, "year").text = str(details.year)

    if details.plot:
        ET.SubElement(parent, "plot").text = details.plot

    if details.plot_outline:
        ET.SubElement(parent, "outline").text = details.plot_outline
        if logger:
            logger.info("_build_common_elements: wrote <outline>")

    if details.premiere_date:
        ET.SubElement(parent, "premiered").text = details.premiere_date
        if logger:
            logger.info(f"_build_common_elements: wrote <premiered>={details.premiere_date}")

    if details.tagline:
        ET.SubElement(parent, "tagline").text = details.tagline

    if details.runtime > 0:
        ET.SubElement(parent, "runtime").text = str(details.runtime)

    if details.mpaa:
        ET.SubElement(parent, "mpaa").text = details.mpaa

    if details.kinopoisk_id > 0:
        uid = ET.SubElement(parent, "uniqueid")
        uid.set("type", "kinopoisk")
        uid.set("default", "true")
        uid.text = str(details.kinopoisk_id)

    if details.imdb_id:
        uid = ET.SubElement(parent, "uniqueid")
        uid.set("type", "imdb")
        uid.text = details.imdb_id

    if details.ratings:
        ratings_elem = ET.SubElement(parent, "ratings")
        for r in details.ratings:
            if r.source in (DataSource.KINOPOISK, DataSource.IMDB):
                max_val = "10"
            else:
                max_val = "100"

            rating_elem = ET.SubElement(ratings_elem, "rating")
            rating_elem.set("name", r.source.value)
            rating_elem.set("max", max_val)
            if r.source == DataSource.KINOPOISK:
                rating_elem.set("default", "true")

            ET.SubElement(rating_elem, "value").text = str(r.value)
            ET.SubElement(rating_elem, "votes").text = str(r.votes)

    for genre in details.genres:
        ET.SubElement(parent, "genre").text = genre

    for country in details.countries:
        ET.SubElement(parent, "country").text = country

    for studio in details.studios:
        ET.SubElement(parent, "studio").text = studio

    for tag in details.tags:
        ET.SubElement(parent, "tag").text = tag

    actor_lang = settings.actor_name_language if settings else "ru"

    for person in details.directors:
        ET.SubElement(parent, "director").text = person.display_name(actor_lang)

    for person in details.writers:
        ET.SubElement(parent, "credits").text = person.display_name(actor_lang)

    for person in details.cast:
        actor_elem = ET.SubElement(parent, "actor")
        ET.SubElement(actor_elem, "name").text = person.display_name(actor_lang)
        if person.role:
            ET.SubElement(actor_elem, "role").text = person.role
        if person.photo_url:
            ET.SubElement(actor_elem, "thumb").text = person.photo_url
        ET.SubElement(actor_elem, "order").text = str(person.order)

    for artwork in details.artwork:
        if artwork.artwork_type == ArtworkType.POSTER:
            thumb = ET.SubElement(parent, "thumb")
            thumb.set("aspect", "poster")
            thumb.text = artwork.url
        elif artwork.artwork_type == ArtworkType.FANART:
            thumb = ET.SubElement(parent, "thumb")
            thumb.set("aspect", "fanart")
            thumb.text = artwork.url

    if details.trailer_url:
        ET.SubElement(parent, "trailer").text = details.trailer_url

    if details.original_language:
        ET.SubElement(parent, "language").text = details.original_language

    if hasattr(details, 'status') and details.status:
        ET.SubElement(parent, "status").text = details.status
        if logger:
            logger.info(f"_build_common_elements: wrote <status>={details.status}")


def _prettify_xml(element: ET.Element) -> str:
    """Return indented XML string with custom declaration."""
    rough_string = ET.tostring(element, encoding="unicode")
    dom = parseString(rough_string)
    pretty = dom.toprettyxml(indent="  ", encoding=None)
    lines = pretty.split("\n")
    lines[0] = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    result = "\n".join(line for line in lines if line.strip())
    return result + "\n"


def _write_nfo_file(xml_content: str, nfo_path: str, logger: Logger) -> bool:
    """Write xml_content to nfo_path via xbmcvfs; return True on success."""
    try:
        f = xbmcvfs.File(nfo_path, 'w')
        success = f.write(xml_content)
        f.close()
        if success:
            logger.info(f"_write_nfo_file: written {nfo_path}")
        else:
            logger.warning(f"_write_nfo_file: write returned false for {nfo_path}")
        return bool(success)
    except Exception as e:
        logger.warning(f"_write_nfo_file: failed to write {nfo_path}: {e}")
        return False


def _get_movie_nfo_path(video_file_path: str) -> str:
    """Return NFO path by replacing video file extension with .nfo.

    Returns empty string if the path has no extension (i.e. it is a directory),
    which happens when Kodi passes a folder path instead of a file path during
    library scanning via xbmc.getInfoLabel("ListItem.FileNameAndPath").
    """
    root, ext = os.path.splitext(video_file_path)
    if not ext:
        return ""
    return root + ".nfo"


def _get_tvshow_nfo_path(path: str) -> str:
    """Return tvshow.nfo path for a directory or file path."""
    if path.endswith("/") or path.endswith("\\"):
        return path + "tvshow.nfo"
    _, ext = os.path.splitext(path)
    if ext:
        return os.path.dirname(path) + "/tvshow.nfo"
    return path + "/tvshow.nfo"
