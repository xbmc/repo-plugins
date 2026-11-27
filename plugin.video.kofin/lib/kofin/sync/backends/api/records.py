"""The pass's view of a catalogue member and the window its payloads come through."""

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Optional
from collections.abc import Iterable, Iterator

if TYPE_CHECKING:
    from .store import Store


class Record:
    """One member of the desired view.

    ``item`` is the payload, read on first use when the record was built
    without one. A pass reads payloads through a ``PayloadWindow``.
    """

    __slots__ = (
        "item_id",
        "kind",
        "library",
        "parent_id",
        "generation",
        "_item",
        "_loader",
    )

    def __init__(
        self,
        item_id: str,
        kind: str,
        library: str,
        parent_id: str,
        item: Optional[dict[str, Any]],
        generation: int,
        loader: Optional[Callable[[str], dict[str, Any]]] = None,
    ):
        self.item_id = item_id
        self.kind = kind
        self.library = library
        self.parent_id = parent_id
        self.generation = generation
        self._item = item
        self._loader = loader

    @property
    def item(self) -> dict[str, Any]:
        if self._item is not None:
            return self._item
        if self._loader is None:
            return {}
        return self._loader(self.item_id)

    @property
    def loaded(self) -> bool:
        return self._item is not None

    def _key(self) -> tuple[str, str, str, str, int]:
        return (self.item_id, self.kind, self.library, self.parent_id, self.generation)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Record):
            return NotImplemented
        return self._key() == other._key() and self.item == other.item

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return "Record(%r, %r, generation=%r)" % (
            self.item_id,
            self.kind,
            self.generation,
        )


class PayloadWindow:
    """Payloads read on demand, a bounded number held at a time.

    ``walk`` yields records in order and reads each chunk's payloads with
    one query ahead of it, so a pass over thousands of records holds a few
    hundred payloads, never the catalogue.
    """

    CHUNK = 200

    def __init__(self, store: "Store", size: int = 512):
        self.store = store
        self.size = size
        self._held: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.reads = 0

    def __call__(self, item_id: str) -> dict[str, Any]:
        payload = self._held.get(item_id)
        if payload is None:
            self.reads += 1
            payload = self.store.payload(item_id)
            self._keep(item_id, payload)
        else:
            self._held.move_to_end(item_id)
        return payload

    def _keep(self, item_id: str, payload: dict[str, Any]) -> None:
        self._held[item_id] = payload
        while len(self._held) > self.size:
            self._held.popitem(last=False)

    def prefetch(self, item_ids: Iterable[str]) -> None:
        wanted = [i for i in item_ids if i not in self._held]
        if wanted:
            self.reads += 1
            for item_id, payload in self.store.payloads(wanted).items():
                self._keep(item_id, payload)

    def walk(self, records: Iterable[Record]) -> Iterator[Record]:
        pending = list(records)
        for start in range(0, len(pending), self.CHUNK):
            chunk = pending[start : start + self.CHUNK]
            unloaded = [r for r in chunk if not r.loaded]
            for record in unloaded:
                # A lazy record from ``records(payloads=False)`` reads one
                # row at a time; walked, it reads through this window.
                record._loader = self
            self.prefetch(r.item_id for r in unloaded)
            for record in chunk:
                yield record
