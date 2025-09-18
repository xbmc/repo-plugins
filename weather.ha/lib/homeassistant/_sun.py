from dataclasses import dataclass
from enum import Enum


class HomeAssistantSunState(Enum):
    ABOVE_HORIZON = "above_horizon"
    BELOW_HORIZON = "below_horizon"


@dataclass
class HomeAssistantSunInfo:
    state: HomeAssistantSunState
    next_dawn: str
    next_dusk: str
    next_midnight: str
    next_noon: str
    next_rising: str
    next_setting: str
    elevation: float
    azimuth: float
    rising: bool
    friendly_name: str
