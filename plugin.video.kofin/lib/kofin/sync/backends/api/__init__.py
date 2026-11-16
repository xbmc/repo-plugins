"""The API backend: its claim on kofin.db, the capability probe, and the
companion folder an earlier build left."""

import os
import shutil
from typing import Any

from kofin.core.log import Logger
from kofin.sync import private

LOG = Logger(__name__)


class APIBackend:
    name = "api"

    def initialize(self) -> None:
        # The plugin process imports this package on every play and never
        # claims the backend, so the catalogue stays out of module scope.
        from kofin.sync.catalogue import claim_backend
        from kofin.sync.private import Database

        with Database() as db:
            claim_backend(db.cursor, self.name)
        forget_companion()

    def capabilities(self) -> dict[str, Any]:
        from .capabilities import inspect

        return inspect()


def forget_companion() -> None:
    """Delete the companion/ folder an earlier build left in addon_data."""
    folder = os.path.join(private.addon_data_path(), "companion")
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)
        LOG.debug("removed the companion add-on's requests")
