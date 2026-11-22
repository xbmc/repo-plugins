# -*- coding: utf-8 -*-
"""
lib/background.py — 后台服务主循环（由根目录 service.py 调用）。

按「后台刷新间隔」定时抓取当前城市天气并写入 Kodi 皮肤天气属性。
完全异常安全：任一步失败只写日志，不影响 Kodi 运行；
Kodi 关机/退出时通过 Monitor.waitForAbort 立即退出循环。

若不需要皮肤集成，可在插件设置里关闭「写入皮肤天气属性」。
"""
from __future__ import unicode_literals

import xbmc

from . import config


def run():
    config.log("background service started", config.LOGINFO)
    monitor = xbmc.Monitor()
    # 启动后先等 20 秒，避开 Kodi 启动时的网络/皮肤初始化高峰
    if monitor.waitForAbort(20):
        return

    while not monitor.abortRequested():
        try:
            if config.get_bool("skin_props", True):
                from . import windowprops
                from .weather import WeatherService
                result = WeatherService().fetch_all()
                if result.get("ok"):
                    windowprops.publish(result)
                    # 同时写 Kodi 天气窗口(12600)：即使 RunScript 地点配置
                    # 未被调用，皮肤天气 infolabel 也能拿到数据。
                    windowprops.publish_weather(result)
                    config.debug("skin properties published for %s" %
                                 (result.get("location") or {}).get("name", ""))
                else:
                    config.debug("background fetch failed: %s" %
                                 (result.get("errors") or []))
        except Exception as exc:  # noqa: BLE001
            config.warn("background refresh error: %s" % exc)

        interval = config.get_int("refresh_interval", 15, 1, 240) * 60
        if monitor.waitForAbort(interval):
            break
    config.log("background service stopped", config.LOGINFO)
