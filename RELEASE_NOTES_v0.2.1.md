# Release Notes — hermes-lark-cards v0.2.1

## 🌟 官方高清全彩品牌图标接入、CardKit 2.0 原生 `custom_icon` 与双层零延迟缓存

`v0.2.1` 为 `hermes-lark-cards` 带来了顶级的品牌质感提升。针对飞书默认标准图标样式单一的问题，全面接入各大主流大模型官方高清全彩品牌 Logo，并通过 CardKit 2.0 原生 `custom_icon` 与智能双层缓存架构，实现高精还原与极致性能兼得。

---

### ✨ 核心更新亮点

#### 1. 🌈 官方高清品牌矢量/PNG 图标支持 (`custom_icon`)
- 全面收录 Google Gemini 官方四色渐变星芒图标（蓝绿红黄），彻底告别单色粗线条。
- 同步内置 Claude、DeepSeek、OpenAI / GPT、通义千问 (Qwen)、Kimi、智谱 GLM 等主流模型官方全彩高清素材（640×640）。
- 折叠面板 Header 深度兼容 CardKit 2.0 `custom_icon` 规范（通过 `img_key` 渲染），质感媲美官方原生客户端。

#### 2. ⚡ 内存 + 本地磁盘双层智能缓存系统
- **零额外网络耗时**：首次调用某模型时，后台自动读取内置素材上传飞书图片服务，并将飞书返回的 `img_key` 持久化存储在 `~/.hermes/card_icons_cache.json`。
- **即时复用**：后续所有会话直接从内存或本地磁盘命中缓存，无需重复上传，渲染零延迟。
- **无缝优雅回退**：离线或飞书 API 未就绪时，自动回退到 `v0.2.0` 的内置 `standard_icon` 矢量图标库，保障 100% 运行可靠性。

#### 3. 🛡️ 底层通信与数据传输增强
- `FeishuClient` 新增 `upload_image_bytes(data: bytes)`，支持原生内存二进制图片安全上传，避免中间文件写入。
- 完善包构建配置，内置静态品牌资源自动随 Python wheel 及源码分发包分发。

---

### 🧪 自动化测试验证
- 单元测试与端到端集成用例全数通过（**761 passed, 1 skipped**）。
- 覆盖品牌 Token 解析、本地素材定位、飞书直传、双层缓存命中及异常回退全链路。

---

**Full Changelog**: https://github.com/Duseus/hermes-lark-cards/compare/v0.2.0...v0.2.1
