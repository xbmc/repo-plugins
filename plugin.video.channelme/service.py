# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - background service entry point. Kodi runs this once at startup;
# the continuous queue-management logic lives in resources/lib/service_runner.py.

from resources.lib import service_runner

service_runner.main()
