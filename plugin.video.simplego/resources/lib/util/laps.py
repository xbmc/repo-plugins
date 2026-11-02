"""How long each step of one piece of work took, for one log line ("checks 0.05s, roll 0.40s")."""

import time


class Laps:
    """Call it with a step's name when the step is done; str() lists them all."""

    def __init__(self):
        self._at = time.monotonic()
        self.steps = []

    def __call__(self, name):
        """Mark the step since the last mark (or since made) as done."""
        now = time.monotonic()
        self.steps.append((name, now - self._at))
        self._at = now

    def __str__(self):
        return ", ".join("%s %.2fs" % step for step in self.steps)
