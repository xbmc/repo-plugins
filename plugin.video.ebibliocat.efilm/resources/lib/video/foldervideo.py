from dataclasses import dataclass


@dataclass
class FolderVideo:
    name: str
    url: str
    mode: str
    iconImage: str = ""
    thumbnailImage: str = ""
