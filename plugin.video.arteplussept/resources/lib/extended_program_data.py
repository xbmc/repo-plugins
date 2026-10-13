"""Lazy cache for optional Arte program metadata and playback progress."""
import hashlib
import time

# pylint: disable=import-error
import requests

from resources.lib import api, user


class ExtendedProgramData:
    """Load and update program data indexed by Arte program id."""

    STORAGE_KEY = 'extended_program_data'

    def __init__(self, plugin, settings, token=None, ttl_seconds=300,
                 ttl_from='creation'):
        if ttl_from not in ('creation', 'last_edit'):
            raise ValueError("ttl_from must be 'creation' or 'last_edit'")
        self.plugin = plugin
        self.settings = settings
        self.token = token
        self.ttl_seconds = ttl_seconds
        self.ttl_from = ttl_from
        scope = f'{settings.username}:{settings.language}'
        self.scope = hashlib.sha256(scope.encode('utf-8')).hexdigest()
        self.storage = plugin.get_storage(self.STORAGE_KEY)

    def get(self, program_id):
        """Return cached program data, refreshing the history lazily if stale."""
        entry = self._load()
        return dict(entry.get('programs', {}).get(program_id, {}))

    def get_all(self):
        """Return all cached program data after at most one lazy refresh."""
        entry = self._load()
        return {
            program_id: dict(program_data)
            for program_id, program_data in entry.get('programs', {}).items()
        }

    def clear(self):
        """Invalidate this account and language snapshot."""
        self.storage.pop(self.scope, None)

    def update_program(self, program_id, timecode, duration=None):
        """Write a successfully synchronized position into the local cache."""
        if not program_id:
            return
        entry = dict(self.storage.get(self.scope, {}))
        programs = dict(entry.get('programs', {}))
        program_data = dict(programs.get(program_id, {}))
        try:
            timecode = max(0, int(float(timecode)))
        except (TypeError, ValueError, OverflowError):
            return

        progress = program_data.get('progress', 0.0)
        if isinstance(duration, (int, float)) and duration > 0:
            progress = min(1.0, timecode / duration)
        program_data.update({
            'programId': program_id,
            'last_viewed_time': timecode,
            'progress': progress,
            'lastviewed': {
                'is': True,
                'timecode': timecode,
                'progress': progress,
            },
        })
        programs[program_id] = program_data
        now = int(time.time())
        entry.update({
            'created_at': entry.get('created_at', now),
            'last_edit_at': now,
            'snapshot_loaded': entry.get('snapshot_loaded', False),
            'programs': programs,
        })
        self.storage[self.scope] = entry

    def _load(self):
        entry = self.storage.get(self.scope, {})
        timestamp_key = 'created_at' if self.ttl_from == 'creation' else 'last_edit_at'
        timestamp = entry.get(timestamp_key)
        if (timestamp is not None and entry.get('snapshot_loaded') is True
                and time.time() - timestamp < self.ttl_seconds):
            return entry

        token = self.token or user.get_cached_token(
            self.plugin, self.settings.username, True
        )
        if not token:
            return {'programs': {}}

        try:
            rows = api.get_last_viewed_all(self.settings.language, token)
        except (requests.exceptions.RequestException, TypeError, ValueError):
            return entry if entry else {'programs': {}}
        if rows is None:
            return entry if entry else {'programs': {}}

        programs = {}
        for row in rows:
            program_id = row.get('programId')
            if not program_id:
                continue
            program_data = dict(row)
            last_viewed = row.get('lastviewed') or {}
            if last_viewed.get('is'):
                program_data['last_viewed_time'] = last_viewed.get('timecode')
                program_data['progress'] = last_viewed.get('progress')
            programs[program_id] = program_data

        now = int(time.time())
        entry = {
            'created_at': now,
            'last_edit_at': now,
            'snapshot_loaded': True,
            'programs': programs,
        }
        self.storage[self.scope] = entry
        return entry


def enrich_program_data(program_data, extended_data):
    """Merge cached fields without replacing authoritative current data."""
    enriched = dict(program_data)
    for key, value in extended_data.items():
        # Empty cache values cannot add useful information to the response.
        if value is None:
            continue
        if key == 'lastviewed':
            # Preserve active page history, but replace missing or inactive
            # history when the cache has an active resume point.
            current_last_viewed = enriched.get(key)
            current_is_active = (
                isinstance(current_last_viewed, dict)
                and current_last_viewed.get('is') is True
            )
            cached_is_active = (
                isinstance(value, dict) and value.get('is') is True
            )
            if not current_last_viewed or (cached_is_active and not current_is_active):
                enriched[key] = value
        elif enriched.get(key) in (None, ''):
            # For all other fields, the cache only fills missing page data.
            enriched[key] = value
        else:
            # A non-empty value from the current response takes precedence.
            continue
    return enriched
