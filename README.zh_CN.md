# 中国天气插件 · zip 安装包交付说明（v1.0.2）

- **插件 ID**：`plugin.weather.china`
- **版本**：1.0.2
- **最低 Kodi 版本**：Kodi 19 Matrix（`xbmc.python 3.0.0`），兼容 Nexus / Omega / Piers
- **安装包**：`release/plugin.weather.china-1.0.2.zip`（51 个文件，约 159 KB）
- **安装方式**：Kodi → 设置 → 插件 → 从 zip 文件安装
- **许可**：GPL-3.0

zip 内顶层目录为 `plugin.weather.china/`，`addon.xml` 位于该目录根部，符合 Kodi「从 zip 安装」的硬性要求。

---

## 一、功能范围

| 功能 | 说明 |
|---|---|
| 实时天气 | 温度、体感、现象、湿度、气压、降水、风向/风力/风速、能见度、AQI、PM2.5、日出日落、更新时间 |
| 多日预报 | 3 / 5 / 7 天可设；每天含高低温、白天/夜间现象与图标、风向风力、降水量 |
| 中文城市搜索与切换 | 内置 2529 个 NMC 气象站点 + 3230 个 weather.com.cn 城市码；支持中文子串、拼音首字母 |
| 气象预警 | 本地 + 全国预警；解析寒潮/暴雨等预警类型与蓝/黄/橙/红等级，按等级着色、排序、去重、过滤 |
| 生活指数 | 中国天气网 30 项生活指数 |
| 天气源集成 | 同时注册 `xbmc.python.pluginsource` 与 `xbmc.python.weather`，出现在「设置 → 服务 → 天气」天气源列表 |
| 皮肤集成 | 后台服务写入 `Window(12600)` 的 `Current.*` / `DayN.*` / `Weather.Alert*` 属性 |
| 本地化 | 全中文 UTF-8 界面，`en_GB` + `zh_CN` 双语 strings.po，界面文本零硬编码 |
| 健壮性 | 双数据源（nmc.cn 主 / weather.com.cn 备）自动降级、文件缓存、断网用过期缓存 |

数据源为公开接口，无需注册、无需 API Key。运行时零第三方依赖，仅用 Python 3 标准库 + Kodi 内置模块。

---

## 二、需要新增或修改的文件

相对于官方 `matrix` 分支，本插件为**纯新增**：仅增加 `plugin.weather.china/` 目录（52 个运行时文件），无删除、无修改任何现有文件。

运行时文件清单（`plugin.weather.china/`）：

| 路径 | 作用 |
|---|---|
| `addon.xml` | 插件元数据、扩展点、版本、依赖声明 |
| `default.py` | 插件 / 天气服务共用入口，按 `sys.argv[0]` 判别模式 |
| `service.py` | 后台服务入口，刷新皮肤 Window Properties |
| `icon.png` / `fanart.jpg` | 256×256 图标 / 1280×720 背景图 |
| `LICENSE.txt` / `changelog.txt` | GPL-3.0 许可 / 版本变更记录 |
| `resources/settings.xml` | 城市、单位、预报天数、数据源等设置项 |
| `resources/lib/*.py` | 核心逻辑（weather、nmc、weathercn、alerts、citydb、net、ui、config、icons、background、windowprops、weatherprovider） |
| `resources/data/*.json` | 城市索引（NMC 站点 / weather.com.cn 城市码）、天气现象映射 |
| `resources/language/resource.language.*/strings.po` | 中英双语字符串（139 条） |
| `resources/media/*.png` | 天气现象与预警等级图标 |

打包产物（本交付新增，**不属于** Kodi 官方仓库运行时文件）：

| 路径 | 作用 |
|---|---|
| `release/plugin.weather.china-1.0.2.zip` | 可直接安装的分发包 |
| `release/README.zh_CN.md` | 本交付说明文档 |

> 说明：`docs/`、`tests/`、`tools/`、`assets/` 为开发与测试文件，保留在独立源码仓库 `RenJunJie2003/kodi-weather-china`，**不进入**官方 `repo-plugins` 仓库。

---

## 三、配置与运行说明

### 安装

1. 从 `release/` 下载 `plugin.weather.china-1.0.2.zip`，拷贝到 Kodi 设备可访问的位置。
2. Kodi → ⚙ 设置 → 插件 → **从 zip 文件安装** → 选择该 zip。
3. 安装后可在「我的插件 → 中国天气 China Weather」打开主界面。

### 作为天气源（推荐）

1. Kodi → 设置 → 服务 → 天气 → **选择天气插件** → 选「中国天气」。
2. 点 **地点 1**（可选地点 2/3）→ 输入中文城市名（如「石家庄」）→ 从搜索结果选中。
   - 若「地点」按钮未弹出搜索框：在设置页「或手动输入城市名」编辑框直接填中文城市名即可，插件会自动解析站点码；覆盖安装后重启一次 Kodi。
3. 天气部件每 30 分钟自动刷新；后台服务每 15 分钟刷新皮肤属性。

### 主要设置项

| 设置项 | 默认值 | 说明 |
|---|---|---|
| 城市名称 `city_name` | 北京 | 插件菜单当前城市 |
| NMC 站点码 `nmc_code` | Wqsps | 主数据源站点编码，由城市搜索自动写入 |
| 中国天气网城市码 `wcn_code` | 101010100 | 备用数据源编码 |
| 温度单位 `temp_unit` | 摄氏度 | 摄氏 / 华氏 |
| 预报天数 `forecast_days` | 7 | 3 / 5 / 7 |
| 主数据源 `primary_source` | auto | auto / nmc / wcn |
| 地点 1/2/3 | 空 | 天气服务的三个城市位 |

### 常见问题

- **找不到天气源**：确认插件已安装并重启 Kodi；`xbmc.python.weather` 扩展点已注册。
- **无数据**：检查网络；插件会在主源失败时自动切换备用源，断网时使用 24 小时内的过期缓存。
- **中文乱码**：全链路 UTF-8，界面语言随 Kodi 系统语言；如需英文将 Kodi 语言设为 English。

---

## 四、验证结果

- `kodi-addon-checker` 0.0.36（`--branch matrix --PR`）：0 ERROR
- 55 项离线自测通过；真实接口端到端测试通过
- zip 顶层结构校验通过：`plugin.weather.china/addon.xml` 位于根部，关键文件齐全
- GPL-3.0 许可、路径全小写、UNIX 换行无 BOM、无预编译文件

---

## 五、注意

`xbmc/repo-plugins` 官方仓库只接受**解压后的运行时目录**、且要求**单 commit**。本交付的 `release/*.zip` 与说明文档属于发布辅助产物，放在 fork 分支仅供下载测试；正式提交 PR #4898 时应仅保留 `plugin.weather.china/` 运行时目录，发布包建议改放源码仓库的 GitHub Release。
