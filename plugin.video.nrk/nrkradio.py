from enum import Enum
from typing import Any, Self, override
import nrk
from nrk import deep_get_str, deep_get_dict, deep_get_list


class Type(Enum):
    CHANNEL = "channel"
    PAGE = "page"
    PAGESOVERVIEW = "pagesoverview"
    PODCAST = "podcast"
    PODCASTEPISODE = "podcastepisode"
    SEASON = "season"
    SECTION = "section"
    SERIES = "series"
    STANDALONEPROGRAM = "standaloneprogram"


class PagesOverview(nrk.BasePage):
    def __init__(self):
        response = nrk.get("/radio/pages")
        title: str | None = deep_get_str(response, "title")
        id: str | None = deep_get_str(response, "id")
        super().__init__(id, title, Type.PAGESOVERVIEW, False, "/radio/pages")
        for page in deep_get_list(response, "pages"):
            page_id: str | None = deep_get_str(page, "id")
            self.append_child(Page(page_id, page))


class Page(nrk.BasePage):

    def __init__(self, page_id: str | None, response: Any):
        title: str | None = deep_get_str(response, "title")
        super().__init__(page_id, title, Type.PAGE, False, f"/radio/pages/{page_id}")
        super().add_images(deep_get_list(response, "image", "webImages"))
        for index, item in enumerate(deep_get_list(response, "sections")):
            self.append_child(Section(page_id, str(index), item))

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if len(dirs) != 4 or dirs[1] != "radio" or dirs[2] != "pages":
            raise ValueError("Wrong format of url")
        page_id: str = dirs[3]
        # https://psapi.nrk.no/documentation/redoc/pages-radio/v3.6/#tag/Pages/operation/GetGivenNRKRadioPage
        return cls(page_id, nrk.get(f"/radio/pages/{page_id}"))


class PlugInfo:
    def __init__(
        self,
        id: str | None,
        title: str | None,
        type: Enum,
        is_playable: bool,
        manifest_url: str | None,
        images: list[dict[str, str | int]] | str | None,
    ) -> None:
        self.id: str | None = id
        self.title: str | None = title
        self.type: Enum = type
        self.is_playable: bool = is_playable
        self.manifestUrl: str | None = manifest_url
        self.images: list[dict[str, str | int]] | str | None = images


class BasePlug(nrk.BasePage):

    def __init__(self, response: dict[Any, Any]):
        self.response: dict[Any, Any] = response
        pluginfo: PlugInfo = self._extract()
        super().__init__(
            id=pluginfo.id,
            title=pluginfo.title,
            type=pluginfo.type,
            is_playable=pluginfo.is_playable,
            manifest_url=pluginfo.manifestUrl,
        )
        if pluginfo.images:
            self.add_images(pluginfo.images)

    def _extract(self) -> PlugInfo:
        """Sub-classes override this method to extract the fields they need."""
        raise NotImplementedError


class Section(nrk.Base):

    def __init__(self, page_id, section_id: str, response):

        # response can be full response or just the respective section of the response
        if response.get("sections", None):
            response = deep_get_dict(response, "sections", int(section_id))

        plugs_response = []
        if response.get("included", None):
            title = deep_get_str(response, "included", "title")
            plugs_response = deep_get_list(response, "included", "plugs")
        elif response.get("placeholder", None):
            title = deep_get_str(response, "placeholder", "title")
            plugs_response = deep_get_list(response, "placeholder", "plugs")
        else:
            title: str | None = None
            plugs_response: list[Any] = []
        super().__init__(
            str(section_id),
            title,
            Type.SECTION,
            False,
            f"/pages/{page_id}/{section_id}",
        )
        for item in plugs_response:
            plug: BasePlug = plug_factory(item)
            super().append_child(plug)

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if len(dirs) != 4:
            raise ValueError("Wrong format of url")
        page_id: str = dirs[2]
        section_id: str = dirs[3]
        # Same request as for radio_page() as the request for a section does not work
        # https://psapi.nrk.no/documentation/redoc/pages-radio/v3.6/#tag/Pages/operation/GetGivenNRKRadioPage
        return cls(page_id, section_id, nrk.get("/radio/pages/" + page_id))


class ChannelPlug(BasePlug):
    def _extract(self) -> PlugInfo:
        channel: dict[Any, Any] = deep_get_dict(self.response, "channel")
        channel_title: str | None = deep_get_str(channel, "titles", "title")
        manifest_url = deep_get_str(self.response, "_links", "channel")
        images: list[dict[str, str | int]] = deep_get_list(
            channel, "image", "webImages"
        )
        return PlugInfo(
            None,
            channel_title,
            Type.CHANNEL,
            is_playable=True,
            manifest_url=manifest_url,
            images=images,
        )


class PodcastEpisodePlug(BasePlug):
    @override
    def _extract(self) -> PlugInfo:
        podcastEpisode: dict[Any, Any] = deep_get_dict(self.response, "podcastEpisode")
        podcast_title: str | None = deep_get_str(
            podcastEpisode, "podcast", "titles", "title"
        )
        episode_title: str | None = deep_get_str(podcastEpisode, "titles", "title")
        if episode_title:
            title: str = f"{podcast_title}: {episode_title}"
        else:
            episode_subtitle: str | None = deep_get_str(
                podcastEpisode, "titles", "subtitle"
            )
            title = f"{podcast_title}: {episode_subtitle}"
        manifest_url: str | None = deep_get_str(
            self.response, "_links", "podcastEpisode"
        )
        images: str | None = deep_get_str(podcastEpisode, "imageUrl")
        return PlugInfo(
            None,
            title,
            Type.PODCASTEPISODE,
            is_playable=True,
            manifest_url=manifest_url,
            images=images,
        )

    @override
    def add_images(self, images: str) -> None:
        self.thumb = images
        self.fanart = images


class StandaloneProgramPlug(BasePlug):
    @override
    def _extract(self) -> PlugInfo:
        standaloneProgram: dict[Any, Any] = deep_get_dict(self.response, "program")
        program_title: str | None = deep_get_str(standaloneProgram, "titles", "title")
        program_subtitle: str | None = deep_get_str(
            standaloneProgram, "titles", "subtitle"
        )
        if program_title:
            title: str = f"{program_title}: {program_subtitle}"
        else:
            title = f"{program_subtitle}"
        manifest_url: str | None = deep_get_str(self.response, "_links", "program")
        images: list[dict[str, str | int]] = deep_get_list(
            standaloneProgram, "image", "webImages"
        )
        return PlugInfo(
            None,
            title,
            Type.STANDALONEPROGRAM,
            is_playable=True,
            manifest_url=manifest_url,
            images=images,
        )


class PodcastPlug(BasePlug):
    @override
    def _extract(self) -> PlugInfo:
        podcast: dict[Any, Any] = deep_get_dict(self.response, "podcast")
        podcast_title: str | None = deep_get_str(podcast, "titles", "title")
        podcast_subtitle: str | None = deep_get_str(podcast, "titles", "subtitle")
        if podcast_title:
            title: str = f"{podcast_title}: {podcast_subtitle}"
        else:
            title = f"{podcast_subtitle}"
        manifest_url: str | None = deep_get_str(self.response, "_links", "podcast")
        images: str | None = deep_get_str(podcast, "imageUrl")
        return PlugInfo(
            None,
            title,
            Type.PODCAST,
            is_playable=False,
            manifest_url=manifest_url,
            images=images,
        )

    @override
    def add_images(self, images: str) -> None:
        self.thumb = images
        self.fanart = images


class EpisodePlug(BasePlug):
    @override
    def _extract(self) -> PlugInfo:
        episode: dict[Any, Any] = deep_get_dict(self.response, "episode")
        series_title: str | None = deep_get_str(episode, "series", "titles", "title")
        episode_title: str | None = deep_get_str(episode, "titles", "title")
        episode_subtitle: str | None = deep_get_str(episode, "titles", "subtitle")
        title: str = f"{series_title}: {episode_title}: {episode_subtitle}"
        manifest_url: str | None = deep_get_str(self.response, "_links", "episode")
        images: list[dict[str, str | int]] = deep_get_list(
            episode, "image", "webImages"
        )
        return PlugInfo(
            None,
            title,
            Type.PODCASTEPISODE,
            is_playable=True,
            manifest_url=manifest_url,
            images=images,
        )


class SeriesPlug(BasePlug):
    def _extract(self):
        series: dict[Any, Any] = deep_get_dict(self.response, "series")
        series_title: str | None = deep_get_str(series, "titles", "title")
        series_subtitle: str | None = deep_get_str(series, "titles", "subtitle")
        if series_title:
            title: str = f"{series_title}: {series_subtitle}"
        else:
            title = f"{series_subtitle}"
        manifest_url: str | None = deep_get_str(self.response, "_links", "series")
        images: list[dict[str, str | int]] = deep_get_list(series, "image", "webImages")
        return PlugInfo(
            None,
            title,
            Type.SERIES,
            is_playable=False,
            manifest_url=manifest_url,
            images=images,
        )


def plug_factory(response: dict[str, Any]) -> BasePlug:
    """Return an appropriate Plug instance based on response['type']."""
    type_map: dict[
        str,
        type[ChannelPlug]
        | type[PodcastEpisodePlug]
        | type[StandaloneProgramPlug]
        | type[PodcastPlug]
        | type[EpisodePlug]
        | type[SeriesPlug],
    ] = {
        "channel": ChannelPlug,
        "podcastEpisode": PodcastEpisodePlug,
        "standaloneProgram": StandaloneProgramPlug,
        "podcast": PodcastPlug,
        "episode": EpisodePlug,
        "series": SeriesPlug,
    }
    plug_type = deep_get_str(response, "type")
    if not plug_type:
        raise ValueError("No type found in plug")
    plug_class: (
        type[ChannelPlug]
        | type[PodcastEpisodePlug]
        | type[StandaloneProgramPlug]
        | type[PodcastPlug]
        | type[EpisodePlug]
        | type[SeriesPlug]
        | None
    ) = type_map.get(plug_type)
    if not plug_class:
        raise ValueError(f"Unsupported plug type: {plug_type}")

    return plug_class(response)


class PodcastEpisode(nrk.Base):

    def __init__(
        self,
        title: str | None,
        podcast_series_id: str | None,
        podcast_episode_id: str | None,
        images: list[dict[str, str | int]],
    ):

        super().__init__(
            podcast_episode_id,
            title,
            Type.PODCASTEPISODE,
            True,
            f"/playback/manifest/podcast/{podcast_series_id}/{podcast_episode_id}",
        )
        self.add_images(images)

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if (
            len(dirs) == 6
            and dirs[1] == "playback"
            and dirs[2] == "manifest"
            and dirs[3] == "podcast"
        ):
            # manifest url from a season
            podcast_series_id: str = dirs[4]
            podcast_episode_id: str = dirs[5]
        elif len(dirs) == 5 and dirs[1] == "podcasts" and dirs[3] == "episodes":
            # url from an PodcastEpisodePlug, the path is actually not valid
            # but we can still use it to extract the relevant IDs
            podcast_series_id: str = dirs[2]
            podcast_episode_id: str = dirs[4]
        else:
            raise ValueError("Wrong format of url")
        response = nrk.get(
            f"/playback/metadata/podcast/{podcast_series_id}/{podcast_episode_id}"
        )
        podcastepisode_title: str | None = deep_get_str(
            response, "preplay", "titles", "title"
        )
        podcastepisode_subtitle: str | None = deep_get_str(
            response, "preplay", "titles", "subtitle"
        )
        images: list[dict[str, str | int]] = deep_get_list(
            response, "preplay", "poster", "images"
        )
        return cls(
            f"{podcastepisode_title}: {podcastepisode_subtitle}",
            podcast_series_id,
            podcast_episode_id,
            images,
        )

    @nrk.Base.media_url.getter
    def media_url(self) -> str | None:
        manifest_url: str | None = self.manifest_url
        if not super().media_url and manifest_url:
            response = nrk.get(manifest_url)
            self.media_url = deep_get_str(response, "playable", "assets", 0, "url")
        return super().media_url


class StandaloneProgram(nrk.Base):

    def __init__(self, title: str | None, program_id: str | None, images):

        super().__init__(
            program_id,
            title,
            Type.STANDALONEPROGRAM,
            True,
            f"/playback/manifest/program/{program_id}",
        )
        self.add_images(images)

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if (
            len(dirs) == 5
            and dirs[1] == "playback"
            and dirs[2] == "manifest"
            and dirs[3] == "program"
        ):
            # manifest url from a season
            program_id: str = dirs[4]
        elif len(dirs) == 3 and dirs[1] == "programs":
            # manifest url from a plug
            program_id: str = dirs[2]
        else:
            raise ValueError("Wrong format of url")
        return cls(None, program_id, [])

    @nrk.Base.media_url.getter
    def media_url(self) -> str | None:
        manifest_url: str | None = self.manifest_url
        if not super().media_url and manifest_url:
            response = nrk.get(manifest_url)
            self.media_url = deep_get_str(response, "playable", "assets", 0, "url")
        return super().media_url


class Season(nrk.Base):  # can be podcast or series season

    def __init__(self, title: str | None, url: str | None, images: list[dict[str, str | int]]):
        super().__init__(
            None, title, is_playable=False, type=Type.SEASON, manifest_url=url
        )
        self.add_images(images)

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if (
            len(dirs) != 7
            or dirs[1] != "radio"
            or dirs[2] != "catalog"
            or (dirs[3] != "podcast" and dirs[3] != "series")
            or dirs[5] != "seasons"
        ):
            raise ValueError("Wrong format of url")
        podcast_series_id: str = dirs[4]
        podcast_season_id: str = dirs[6]
        response = nrk.get(url)
        title: str | None = deep_get_str(response, "titles", "title")
        images: list[dict[str,str|int]] = deep_get_list(response, "image")
        return cls(title, url, images)

    @property
    @override
    def children(self) -> list[nrk.Base]:
        if self.manifest_url and not super().children:
            response: dict[str, Any] = nrk.get(path=f"{self.manifest_url}")
            series_type: str | None = deep_get_str(response, "type")
            page = 1
            pageSize = 50
            while True:
                response: dict[str, Any] = nrk.get(
                    path=f"{self.manifest_url}/episodes",
                    params=f"&page={page}&pageSize={pageSize}&sort=desc",
                )
                episodes: list[dict[str, Any]] = deep_get_list(
                    response, "_embedded", "episodes"
                )
                for episode in episodes:
                    title: str | None = deep_get_str(episode, "titles", "title")
                    series_id: str | None = deep_get_str(
                        episode, "_links", "series", "name"
                    )
                    episode_id: str | None = deep_get_str(episode, "episodeId")
                    images: list[dict[str, str | int]] = deep_get_list(episode, "image")

                    if series_type == "podcast":
                        self.append_child(PodcastEpisode(title, series_id, episode_id, images))
                    elif series_type == "series":
                        self.append_child(StandaloneProgram(title, episode_id, images))
                    else:
                        raise ValueError("Invalid series type detected")
                if len(episodes) < pageSize:
                    break
                page += 1
        return super().children


class Podcast(nrk.Base):

    def __init__(self, podcast_series_id: str, response):
        seasons: list[dict[str, str]] = deep_get_list(response, "_links", "seasons")
        title: str | None = deep_get_str(response, "series", "titles", "title")
        super().__init__(
            podcast_series_id,
            title,
            Type.PODCAST,
            False,
            f"/radio/catalog/podcast/{podcast_series_id}",
        )
        super().add_images(deep_get_list(response, "series", "image"))
        for season in seasons:
            season_title: str | None = deep_get_str(season, "title")
            season_url: str | None = deep_get_str(season, "href")
            super().append_child(Season(season_title, season_url, []))

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if len(dirs) != 3 or dirs[1] != "podcasts":
            raise ValueError("Wrong format of url")
        podcast_series_id: str = dirs[2]
        return cls(
            podcast_series_id, nrk.get(f"/radio/catalog/podcast/{podcast_series_id}")
        )


class Channel(nrk.Base):

    def __init__(self, channel_id):
        super().__init__(
            channel_id,
            None,
            Type.CHANNEL,
            True,
            f"/playback/manifest/channel/{channel_id}",
        )
        if self.manifest_url:
            response = nrk.get(self.manifest_url)
            self.media_url = deep_get_str(response, "playable", "assets", 0, "url")

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if len(dirs) != 3 or dirs[1] != "mediaelement":
            raise ValueError("Wrong format of url")
        channel_id: str = dirs[2]
        return cls(channel_id)


class Series(nrk.Base):

    def __init__(self, series_id: str, response):
        seasons: list[dict[str, str]] = deep_get_list(response, "_links", "seasons")
        title: str | None = deep_get_str(response, "series", "titles", "title")

        super().__init__(
            series_id, title, Type.SERIES, False, f"/radio/catalog/series/{series_id}"
        )
        for season in seasons:
            season_title: str | None = deep_get_str(season, "title")
            season_url: str | None = deep_get_str(season, "href")
            super().append_child(Season(season_title, season_url, []))

    @classmethod
    def from_url(cls, url: str) -> Self:
        dirs: list[str] = url.split("/")
        if len(dirs) != 3 or dirs[1] != "series":
            raise ValueError("Wrong format of url")
        series_id: str = dirs[2]
        return cls(series_id, nrk.get(f"/radio/catalog/series/{series_id}"))


def map_type_to_class(
    type_string: str,
) -> (
    type[Channel]
    | type[Page]
    | type[Podcast]
    | type[PodcastEpisode]
    | type[Season]
    | type[Section]
    | type[Series]
    | type[StandaloneProgram]
):
    type_map: dict[
        Type,
        type[Channel]
        | type[Page]
        | type[Podcast]
        | type[PodcastEpisode]
        | type[Season]
        | type[Section]
        | type[Series]
        | type[StandaloneProgram],
    ] = {
        Type.CHANNEL: Channel,
        Type.PAGE: Page,
        Type.PODCAST: Podcast,
        Type.PODCASTEPISODE: PodcastEpisode,
        Type.SEASON: Season,
        Type.SECTION: Section,
        Type.SERIES: Series,
        Type.STANDALONEPROGRAM: StandaloneProgram,
    }
    try:
        item_type = Type(type_string)
    except ValueError:
        raise ValueError(f"No type found for: {type_string}")

    item_class: (
        type[Channel]
        | type[Page]
        | type[Podcast]
        | type[PodcastEpisode]
        | type[Season]
        | type[Section]
        | type[Series]
        | type[StandaloneProgram]
        | None
    ) = type_map.get(item_type)

    if not item_class:
        raise ValueError(f"No class found for: {type_string}")

    return item_class
