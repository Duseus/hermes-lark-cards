# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
