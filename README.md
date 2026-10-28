<div align="center">

# 🎴 hermes-lark-cards

**Hermes Agent Gateway 飞书 / Lark 流式卡片插件：CardKit v2.0 实时打字机流式输出 · 思考与工具折叠面板 · 统一指标底栏 · 零侵入 AST Hook 注入**

[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.11-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Hermes](https://img.shields.io/badge/Hermes-%E2%89%A5%200.20.0-2463eb)](https://github.com/NousResearch/hermes-agent)
[![Feishu](https://img.shields.io/badge/Feishu-CardKit%202.0-00d6b9)](https://open.feishu.cn)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[快速开始](#-快速开始) · [卡片效果](#-卡片效果) · [核心特性](#-核心特性) · [配置说明](#%EF%B8%8F-配置说明) · [命令行工具](#%EF%B8%8F-命令行工具) · [工作原理](#-工作原理) · [致敬与相关项目](#-致敬与相关项目)

</div>

---

## 📖 简介

`hermes-lark-cards` 是为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) Gateway 量身打造的飞书（Lark）**流式交互卡片插件**。

通过基于 Python AST（抽象语法树）的零侵入 Hook 注入机制，在完全不修改 Hermes 核心代码的前提下，将 Agent 的每一次输出升级为飞书 CardKit v2.0 原生流式卡片——边想边输出，打字机实时上屏，工具调用和耗时清晰折叠，会话结束时统一汇总运行耗时、Token 用量、上下文窗口占比、实时天气与灵感一言。

---

## 🎨 卡片效果

```
┌────────────────────────────────────────────────────────┐
│  💭 Hermes 正在处理…                           (蓝色)  │
│                                                        │
│  我已经分析了系统服务状态，DNS 缓存异常导致了心跳超时。 │
│  现在为你生成修复脚本并验证联通性。                    │
│                                                        │
│  ▶ 🧠 思考过程 (展开查看)                              │
│      先检查 systemd 服务的重启日志...                  │
│                                                        │
│  ▶ 🛠️ 工具调用 · 3 步 · 1.2s                          │
│      Run command (352 ms)                              │
│      bash /opt/scripts/check_health.sh                 │
│      Read file (25 ms)                                 │
│      /etc/resolv.conf                                  │
│  ──────────────────────────────────────────────────    │
│  ✅ 已完成 · 4.8s · ⚕DeepSeek-V3                       │
│  ↑ 1.2K ↓ 480 · 15.2K/128K (11%)                       │
│  ☀️ 临平 21.5°C/14.0°C · 湿度 68%                      │
│  💬 「保持好奇，持续折腾。」                           │
└────────────────────────────────────────────────────────┘
```

- **三色状态感知**：蓝色（流式生成中）、绿色（成功完成）、红色（异常或被打断 `/stop`）。
- **打字机实时流式**：高频小步缓冲刷字（~15ms 节流节奏），告别传统全量等待的漫长空白。
- **可折叠过程面板**：思考链与工具调用步骤（状态、耗时、调用参数与结果）按轮次收拢，界面清爽。
- **长文本与防爆保护**：自适应拆卡机制与 30KB / 200 元素硬上限截断保护，杜绝飞书卡片渲染崩溃。

---

## ✨ 核心特性

1. **CardKit v2.0 原生流式与品牌图标 (Brand Icons)**
   - 使用飞书开放平台最新的 `cardkit.v1` 批量更新与流式卡片 API。
   - 折叠面板右侧自适应呈现模型专属图标（DeepSeek 蓝鲸 🐋 `whale_outlined`、Claude 橙色星火 ✳️、OpenAI 绿色网络 🌐 等）。
   - 动态状态边框色彩：正常完成绿框（`green`）、任务中断黄框（`yellow`）、执行出错红框（`red`）。
   - 消息撤回/删除主动识别，防止无效 API 请求循环。
2. **零侵入 AST Hook 注入**
   - 通过分析 Hermes 网关调度流（`run_inbound.py`、`run_turn.py`、`run_turn_runner.py`、`cron/scheduler_delivery.py`），安全挂载 Hook 点。
   - 一键注入与还原，系统升级或卸载时完整回滚，原生文件零污染。
3. **多模型与峰谷价感知**
   - 自动识别当前执行模型，支持高峰/低谷电费别名映射与定价标注。
   - 智能匹配模型上下文窗口（`resolve_context_window`），精确计算 Context 百分比。
4. **多维状态指标底栏**
   - 会话总耗时、输入/输出 Token 统计、上下文占用进度。
   - 集成 Open-Meteo 免 Key 实时天气与 Hitokoto 精选一言，提供有温度的交互。
5. **双语自适应（i18n）**
   - 内置中英双语标签字典，跟随飞书客户端界面语言无缝切换。

---

## 🚀 快速开始

### 1. 安装

在 Hermes 所在的 Python 环境中安装：

```bash
cd hermes-lark-cards
pip install -e .
```

或使用 `pip` 直接安装：

```bash
pip install hermes-lark-cards
```

### 2. 注入 Hook

执行补丁注入命令，将流式卡片 Hook 挂载到 Hermes 网关：

```bash
hermes-lark-cards install
```

查看挂载状态：

```bash
hermes-lark-cards status
```

输出示例：

```text
Patched: yes
Target:  /root/.hermes/hermes-agent/gateway/run.py
Layout:  split gateway modules
  run_inbound.py: normalize, start
  run_turn.py: answer, tool, reasoning
  run_turn_runner.py: complete, followup_complete
  cron/scheduler_delivery.py: cron_delivery
Config streaming.enabled: True
Feishu credentials: configured
```

### 3. 重启 Hermes 网关

```bash
systemctl restart hermes-gateway
# 或使用你的进程管理工具重新启动 Hermes
```

---

## ⚙️ 配置说明

在 Hermes 根目录下的 `config.yaml`（通常位于 `~/.hermes/config.yaml`）中配置：

```yaml
hermes_lark_cards:
  streaming:
    enabled: true              # 是否启用流式卡片（默认: true）
    width_mode: "fill"         # 卡片宽度模式: default | fill
    header_enabled: false      # 是否展示卡片大标题（默认 false，直接正文打字）
    body_text_size: "normal_v2"# 正文字号: normal_v2 | heading
    show_tool_use: true        # 是否在卡片内展示工具调用过程面板
    panel_expanded: false      # 终态时工具面板是否默认展开

  footer:
    enabled: true              # 是否展示统一底栏
    text_size: "notation"      # 底栏字号
    fields:                    # 底栏行与字段排布
      - ["status", "elapsed", "model"]
      - ["tokens", "context"]
      - ["weather"]
      - ["hitokoto"]

  # 天气配置（可选）
  weather:
    place: "临平"
    latitude: 30.42
    longitude: 120.30
```

---

## 🛠️ 命令行工具

`hermes-lark-cards` 提供了完整的运维与诊断 CLI：

| 命令 | 说明 |
|---|---|
| `hermes-lark-cards studio` | 启动可视化卡片工作坊（Visual Card Studio），浏览器直观配置版式并实时模拟卡片效果 |
| `hermes-lark-cards install` | 将 AST 钩子安全注入到 Hermes Gateway 与 Cron 调度模块 |
| `hermes-lark-cards uninstall` | 移除 AST 钩子并恢复原始文件 |
| `hermes-lark-cards restore` | 从 `.bak` 备份文件中硬恢复网关源码 |
| `hermes-lark-cards status` | 查看当前注入状态、补丁完整度及飞书凭证配置 |
| `hermes-lark-cards verify` | 静态检查 Hermes 安装目录与源码兼容性（不修改任何文件） |

---

## 🏗️ 工作原理

```
[ 用户在飞书发送消息 ]
         │
         ▼
┌─────────────────────────┐
│  Hermes Gateway 进程    │
│  ┌───────────────────┐  │
│  │ run_inbound.py    │──┼─► [HOOK: NORMALIZE / START]
│  └───────────────────┘  │           │
│  ┌───────────────────┐  │           ▼
│  │ run_turn.py       │──┼─► [HOOK: TOOL / REASONING / ANSWER]
│  └───────────────────┘  │           │
│  ┌───────────────────┐  │           ▼
│  │ run_turn_runner.py│──┼─► [HOOK: COMPLETE / INTERRUPT]
│  └───────────────────┘  │           │
└─────────────────────────┘           ▼
                         ┌─────────────────────────────┐
                         │ hermes_lark_cards Controller│
                         │ ├─ 流式队列与节流 (Flush)   │
                         │ ├─ 段落状态管理 (Segments)  │
                         │ ├─ 防爆截断与拆卡安全引擎   │
                         │ └─ 指标统计与卡片构建       │
                         └──────────────┬──────────────┘
                                        │ (CardKit v2.0 REST API)
                                        ▼
                         ┌─────────────────────────────┐
                         │    飞书客户端实时呈现       │
                         └─────────────────────────────┘
```

---

## 🙏 致敬与相关项目

本项目融合了社区优秀流式卡片与网关实践：

- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — 强大且高度可扩展的开源 Agent 网关框架
- [Cheerwhy/hermes-lark-streaming](https://github.com/Cheerwhy/hermes-lark-streaming) — 奠定了 Hermes CardKit 2.0 基础流式会话控制与 AST 补丁体系
- [techysy/hermes-fry-cards](https://github.com/techysy/hermes-fry-cards) — 薯条卡片（fry-cards）系列带来的精美版式、Markdown 防爆引擎与通知槽位设计
- [Duseus/claw-lark-cards](https://github.com/Duseus/claw-lark-cards) — OpenClaw 通道流式卡片、实时工具追踪与统一底栏体系
- [Duseus/opensquilla-lark-streaming](https://github.com/Duseus/opensquilla-lark-streaming) — 统一指标系统、天气与一言组件实现

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。
