# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 🛡️ 稳定性与安全

- **配置解析缓存**：按 `mtime + size` 缓存 YAML 解析结果，热路径不再反复解析整份配置；
  改用 `CSafeLoader`（13KB 配置约 60ms → 8ms）。
- **卡片体积预算**：新增 `streaming.max_card_bytes`（默认 30000，`0` 为不限）。超限时只从尾部
  压缩回答正文并追加中英文省略提示，底栏 / 工具面板 / 思考面板保持不变。
- **超时会话收尾**：看门狗改为 ~60s 定时清扫，清理前先把卡片封成「中断」终态，
  不再出现永远转圈的僵尸卡片；文本兜底标记也加了 TTL 回收。
- **clarify 切卡非阻塞**：`clarify` 结束触发的封旧卡/建新卡改为 fire-and-forget，
  不再在 agent 线程里最多阻塞 50s。
- **频控与元素超限**：230020 改为指数退避 + jitter（1s → 30s）；11310 立即强制拆卡。
- **流式重推优化**：只补发 `streamed_source is None` 的段，去掉每次新增段都全量标脏的 O(n²) 行为。
- **密钥脱敏**：工具面板新增 JSON `"key": "value"`、`sk-` / `ghp_` / `xoxb-` / `AKIA` / `AIza`
  等前缀识别；无 sanitizer 的 MCP 工具结果不再直通；嵌套 JSON 也递归脱敏。
- **图片下载防 SSRF**：只允许 http/https 公网地址（拒绝私网、回环、链路本地、保留段），
  校验 `Content-Type` 并把单图限制在 10MB。
- **Studio CSRF 防护**：校验 `Host` / `Sec-Fetch-Site` / `Origin`，写接口强制
  `Content-Type: application/json`；保存配置时保留原文件权限（`.bak` 固定 600）。
- **Studio 参数校验**：`enabled` / `panel_expanded` 必须布尔，`card_ttl_sec` 1..86400，
  `max_card_bytes` 0..5000000。

### 🎨 渲染一致性

- 中断态 header 由红色改为黄色，与文档和面板边框一致；无回答时的兜底文案按状态区分
  `❌ Error` / `🛑 Stopped` / `Done.`。
- Markdown 切分与截断保持代码围栏闭合；`# 注释` 不再被误判为标题降级。
- 底栏天气 / 一言改为只读缓存，会话开始时后台预热，构建完成态卡片不再同步发网络请求。
- Studio 预览对齐真机（模型名无 `⚕`、`耗时 1.2s`、一言斜体无 `💬`），新增
  `card_ttl_sec` / `max_card_bytes` 控件，版本号改由 `/api/health` 注入。

### 🧪 工程

- 修复裸跑 `pytest` 的 `ModuleNotFoundError`（`pythonpath = ["."]`）。
- 版本号单一来源：`pyproject.toml` 改为 `dynamic = ["version"]`，读取 `hermes_lark_cards.__version__`。
- 新增 GitHub Actions CI（Python 3.11/3.12/3.13，`ruff check` + `pytest`）。
- `install` 后若 `streaming.enabled` 未开启，打印可直接粘贴的配置片段。
- 补齐测试：围栏闭合、字节预算、配置缓存、CSRF/权限、密钥脱敏、SSRF 白名单、
  超时封卡、频控退避等。

---

## [0.3.1] - 2026-11-03

### 🎨 Footer 一言排版优化

- **一言改为斜体、去掉直角引号**：底栏 `hitokoto` 字段不再渲染 `「…」`，改用 Markdown 斜体，
  有出处时输出 `*正文* —— *出处*`，无出处时输出 `*正文*`；接口不可用时的本地兜底句子同样为斜体无引号。
- **Studio 模拟器同步**：1:1 预览中的一言示例改用斜体渲染，与真机卡片保持一致。
- **测试覆盖**：新增 footer 一言斜体且不含引号的断言。

### 🧩 模型品牌图标补全

- 新增 **Devin / SWE-2 / Cognition** 品牌图标（官方三链环 logo，PNG + SVG 双份）。
- `resolve_model_icon` 与自定义资产映射补充 `swe`、`devin`、`cognition` 关键词，
  未命中自定义素材时回退到 `ai-agent_outlined`（purple）标准图标。
- Studio 模型下拉新增 `SWE-2 Max / Devin` 选项。

### 🔧 其他

- 静态资源版本号统一为 `v0.3.1`，避免浏览器命中旧缓存。

---

## [0.3.0] - 2026-10-27

### ✨ 可视化卡片配置工作坊 (Visual Card Studio)

- **原生零依赖 Visual Card Studio (`hermes-lark-cards studio`)**：
  - 基于 Python 标准库打造本地可视化配置服务，支持一键浏览器启动。
  - 安全白名单写入与自动备份保护机制，杜绝配置污染与凭证丢失。
- **1:1 飞书 CardKit 2.0 原生卡片模拟器**：
  - 实时响应表单调整，支持流式打字态与完成态卡片双模态切换。
- **Header 与 Footer 交互式配置**：
  - 支持大标题切换、卡片宽度模式（default / compact / fill）与正文字号调节。
  - Footer 指标芯片交互排布，支持状态、耗时、模型、Token、上下文、天气与一言自由组合。
- **内置三大主题预设**：
  - 经典科技 (Classic Tech)、泡波轻灵 (Bubble Wave)、极简极速 (Minimalist)。

## [0.2.1] - 2026-10-26

### ✨ 高清全彩品牌图标与双层缓存 (HD Brand Icons & Dual-layer Cache)

- **官方高清全彩品牌图标接入 (`custom_icon`)**：
  - 支持 Google Gemini 官方四色渐变星芒高精图标，以及 Claude、DeepSeek、OpenAI、Qwen 通义千问、Kimi、智谱 GLM 等官方高清品牌素材。
  - 卡片构建器（`_collapsible_panel` 与 `build_complete_card`）支持动态指定 `icon_img_key`，渲染飞书 CardKit 2.0 原生 `custom_icon` 节点。
- **智能内存与磁盘双层缓存**：
  - 首次调用新模型时自动上传内置高清素材至飞书图片服务，并写入本地持久化缓存（`~/.hermes/card_icons_cache.json`）。
  - 后续直接复用 `img_key`，无额外网络调用与上传延迟；离线或无权限时无缝平滑回退至标准矢量图标（`standard_icon`）。
- **图片直传增强**：
  - `FeishuClient` 新增 `upload_image_bytes(data: bytes)`，支持原生内存二进制图片安全上传。

---

## [0.2.0] - 2026-10-26

### ✨ 新特性与视觉优化 (Visual & Brand Updates)

- **模型品牌专属图标 (Model Brand Icon)**：
  - 工具与过程折叠面板右侧指示图标自适应匹配模型品牌专属飞书标准图标 (`standard_icon`)。
  - 支持 DeepSeek（🐋 `whale_outlined` 蓝色小鲸鱼）、Claude（✳️ `sparks_outlined` 橙色星火）、OpenAI / GPT（🌐 `connect_outlined` 绿色网络）、Gemini（✨ `star-shine_outlined` 蓝色四角星）、Qwen 通义千问（⚡ `lightning_outlined` 紫色闪电）、Kimi、GLM 等主流模型。
- **动态状态边框 (Status Border Color)**：
  - 折叠面板外框自适应感知会话执行结果状态：正常完成呈现护眼清新绿框 (`green`)，执行中断呈现醒目黄框 (`yellow`)，发生异常呈现警告红框 (`red`)。
- **精致胶囊面板标题栏**：
  - 过程折叠面板 Header 统一采用模型与指标流格式：`<Model> · 💭 <思考轮数> · 🛠️ <工具调用数> · ⏱️ <耗时>`，例如 `DeepSeek-V4.1-Flash · 💭 0 · 🛠️ 17 · ⏱️ 2m4s`。

---

## [0.1.0] - 2026-10-26

### 🚀 初始版本发布 (Initial Release)

- **CardKit v2.0 原生流式卡片**：支持实时打字机流式输出、推理思考过程和工具执行过程展示。
- **状态感知色彩体系**：处理中（蓝）、成功完成（绿）、异常或被中断（红）。
- **零侵入 AST Hook 机制**：支持自动化安装、卸载、状态查询与兼容性验证，无缝对接 Hermes Gateway 各分发模块。
- **统一指标底栏**：整合会话耗时、Token 吞吐、上下文占用百分比、实时天气以及文学一言。
- **安全与防爆防护**：自动拆卡与长文本分块，确保不突破飞书 30KB 与 200 元素限制。
