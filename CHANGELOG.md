# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.1] - 2026-11-03

### 🎨 Footer 一言排版优化

- **一言改为斜体、去掉直角引号**：底栏 `hitokoto` 字段不再渲染 `「…」`，改用 Markdown 斜体，
  有出处时输出 `*正文* —— 出处`，无出处时输出 `*正文*`；接口不可用时的本地兜底句子同样为斜体无引号。
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

---

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
