from dataclasses import dataclass
from typing import Type, Union

_Setting_Type = Union[bool, int, float, str]


@dataclass
class KodiPluginSetting:
    setting_id: str
    setting_type: Type[_Setting_Type]
