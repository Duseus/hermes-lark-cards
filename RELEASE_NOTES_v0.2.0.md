# Release Notes — hermes-lark-cards v0.2.0

## 🎴 视觉大升级：模型品牌图标、状态感知边框与精致胶囊面板

`v0.2.0` 是 `hermes-lark-cards` 的首个重要视觉与体验升级版本，全面拥抱飞书 CardKit 2.0 原生标准图标库与交互设计，为模型调用与执行过程赋予极高辨识度的质感。

---

### ✨ 核心更新亮点

#### 1. 🐋 模型品牌专属指示图标 (Model Brand Standard Icons)
- 无需外部图床或图片上传，直接对接飞书官方矢量标准图标库（`standard_icon`）。
- 折叠面板右侧自适应根据所调用的模型名称匹配专属品牌图标：
  - **DeepSeek** (`deepseek*`) → 🐋 蓝鲸图标 (`whale_outlined`, `color: "blue"`)
  - **Claude** (`claude*`) → ✳️ 智能星火 (`sparks_outlined`, `color: "orange"`)
  - **OpenAI / GPT / o1 / o3** (`gpt*`, `openai*`, `o1*`, `o3*`) → 🌐 神经网络 (`connect_outlined`, `color: "green"`)
  - **Gemini** (`gemini*`) → ✨ 四角星芒 (`star-shine_outlined`, `color: "blue"`)
  - **Qwen 通义千问** (`qwen*`) → ⚡ 灵动闪电 (`lightning_outlined`, `color: "purple"`)
  - **Kimi** (`kimi*`) → 纸飞机 (`send_outlined`, `color: "blue"`)
  - **GLM / 智谱** (`glm*`) → 思维导图 (`mind-mapping_outlined`, `color: "blue"`)
  - 未匹配模型平滑回落为精致下三角小箭头 (`down-small-ccm_outlined`)。

#### 2. 🟢 动态状态边框色彩感知 (Status Border Color)
- 过程折叠面板外边框自适应当前会话的最终执行状态：
  - **正常完成 (`Completed`)**：呈现清新绿框（`border: {"color": "green", "corner_radius": "5px"}`）。
  - **用户打断 (`Aborted / Stopped`)**：呈现警示黄框（`border: {"color": "yellow", "corner_radius": "5px"}`）。
  - **执行异常 (`Error`)**：呈现醒目红框（`border: {"color": "red", "corner_radius": "5px"}`）。

#### 3. 💊 精致胶囊面板标题栏
- 过程折叠面板 Header 统一采用格式化指标流：
  `<Model> · 💭 <思考轮数> · 🛠️ <工具调用数> · ⏱️ <耗时>`
  示例：`DeepSeek-V4.1-Flash · 💭 0 · 🛠️ 17 · ⏱️ 2m4s`。

---

### 🧪 自动化测试验证
- 单元测试与端到端集成用例全数通过（**755 passed**）。
- 兼容 Python 3.11+、CardKit 2.0 与飞书桌面/移动端最新版本。

---

**Full Changelog**: https://github.com/Duseus/hermes-lark-cards/compare/v0.1.0...v0.2.0
