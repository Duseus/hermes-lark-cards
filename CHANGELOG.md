# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-26

### 🚀 初始版本发布 (Initial Release)

- **CardKit v2.0 原生流式卡片**：支持实时打字机流式输出、推理思考过程和工具执行过程展示。
- **状态感知色彩体系**：处理中（蓝）、成功完成（绿）、异常或被中断（红）。
- **零侵入 AST Hook 机制**：支持自动化安装、卸载、状态查询与兼容性验证，无缝对接 Hermes Gateway 各分发模块。
- **统一指标底栏**：整合会话耗时、Token 吞吐、上下文占用百分比、实时天气以及文学一言。
- **安全与防爆防护**：自动拆卡与长文本分块，确保不突破飞书 30KB 与 200 元素限制。
