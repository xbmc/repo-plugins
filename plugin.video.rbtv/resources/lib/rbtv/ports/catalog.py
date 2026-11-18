from __future__ import annotations

from typing import Protocol

from rbtv.domain.episode import EpisodePage
from rbtv.domain.show import Show


class Catalog(Protocol):
    def all_shows(self) -> list[Show]: ...

    def episodes_of_show(self, show_id: int, offset: int = 0) -> EpisodePage: ...


class RefreshableCatalog(Catalog, Protocol):
    def invalidate(self) -> None: ...
