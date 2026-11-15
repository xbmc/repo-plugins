# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations


class AddonError(RuntimeError):
    pass


class AccountError(AddonError):
    def __init__(self, resp, message: str | None = None):
        self.response = resp
        if not message:
            message = 'This content is only available to users with a BBC account.'
        super().__init__(message)


class SignInError(AddonError):
    pass


class GeoBlockError(AddonError):
    def __init__(self, resp, message: str | None = None):
        self.response = resp
        if not message:
            message = 'This content is not available in your region.'
        super().__init__(message)
