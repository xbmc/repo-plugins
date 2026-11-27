"""The one spelling of a reference checksum."""

from typing import Any, Optional


def reference_checksum(etag: Any) -> Optional[str]:
    # A missing Etag must remain unverifiable, never become a reusable match.
    return "%s|plugin" % etag if etag else None
