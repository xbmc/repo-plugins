# -*- coding: utf-8 -*-
from ..addon import utils
from ..addon.constants import LIVE_PREVIEW_TEMPLATE


def route(notify=True):
    utils.TextureCacheCleaner().remove_like(LIVE_PREVIEW_TEMPLATE, notify)
