import json
from dataclasses import dataclass


@dataclass
class Playback:
    """
    Stores whatever data we can grab about a Kodi Playback so that we can display it nicely in the Switchback list
    """
    file:str = None
    type:str = None  # episode, movie, video, song
    source:str = None  # kodi_library, pvr_live, media_file
    dbid:int = None
    tvshowdbid: int = None
    title:str = None
    thumbnail:str = None
    fanart:str = None
    poster:str = None
    year:int = None
    showtitle:str = None
    season:int = None
    episode:int = None
    resumetime:float = None
    totaltime:float = None
    duration:float = None
    artist:str = None
    album:str = None
    tracknumber:int = None
    channelname: str = None
    channelnumberlabel:str = None
    channelgroup:str = None

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

