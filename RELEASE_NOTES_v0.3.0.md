# Release Notes — hermes-lark-cards v0.3.0

## 🎨 可视化配置工作坊 (Visual Card Studio) · 1:1 卡片模拟器与主题预设

`v0.3.0` 带来了期待已久的原生可视化卡片配置后台（**Visual Card Studio**）。参考了 aiduPOP 与 10router 生态的优秀卡片设计，让开发者和用户无需手写 YAML 即可直观定制 Header、Footer 指标字段排布、卡片宽度模式与正文字号，并支持实时 1:1 飞书 CardKit 2.0 原生卡片模拟渲染。

---

### ✨ 核心更新亮点

#### 1. 🖥️ 原生零依赖可视化工作坊 (`hermes-lark-cards studio`)
- 基于 Python 标准库 `http.server` 打造，完全不引入外部 Web 框架，开箱即用。
- 仅需运行 `hermes-lark-cards studio`，自动唤起浏览器即可进行可视化交互配置。
- 具备严格的安全写入保障：
  - 白名单控制：仅修改 UI 涉及的展示字段，绝不触碰或丢失原有网关配置、鉴权凭据与自定义字段。
  - 自动备份机制：每次保存自动将旧配置安全备份至 `~/.hermes/backups/studio_config_baks/`。
  - 仅监听本地 Loopback 接口，防范 CSRF 与 DNS 重绑定。

#### 2. 🎴 1:1 飞书 CardKit 2.0 DOM 级卡片模拟器
- 右侧实时卡片预览引擎支持 **完成态 (Completed)** 与 **流式打字态 (Streaming)** 双模态一键切换。
- 支持过程折叠面板点击展开/收起交互，所见即所得。

#### 3. 📊 交互式指标底栏 (Footer) 自由排布
- 提供直观的字段芯片切换体验（完成状态、运行耗时、模型名称、Token 吞吐、上下文进度、实时天气、灵感一言）。
- 一键开启/关闭字段前缀标签、切换注脚字号 (`notation`) 与标准字号 (`normal_v2`)。

#### 4. 🎨 三套开箱即用视觉预设 (Visual Presets)
- **🏛️ 经典科技 (Classic Tech)**：经典干练、标准版式、全维指标底栏。
- **🫧 泡波轻灵 (Bubble Wave)**：充满卡片模式 (fill)、大标题打字机、轻灵视觉。
- **🍃 极简极速 (Minimalist)**：紧凑模式 (compact)，仅保留耗时与模型，克制纯粹。

#### 5. 🔄 一键网关重启与热重载
- 前端内置 **「重启网关」** 快捷按钮，支持通过 `systemctl --user restart hermes-gateway` 无缝加载最新配置。

---

### 🧪 自动化测试验证
- 补充完整的 Studio API、载荷校验与安全深度合并测试用例（`tests/test_studio.py`）。
- 既有用例全面通过验证。
