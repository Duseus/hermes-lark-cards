# Release Notes — hermes-lark-cards v0.3.1

## 💬 一言换成斜体、卸掉括号，外加 Devin / SWE-2 品牌图标

`v0.3.1` 是一个以打磨细节为主的小版本。底栏「一言」不再被 `「」` 包住，改为 Markdown 斜体呈现，观感更像一句随手写下的旁白；同时补全了 Devin / SWE-2 / Cognition 的品牌图标，模型标识不再落到默认占位符。

---

### ✨ 核心更新亮点

#### 1. 💬 Footer 一言：斜体排版，去掉直角引号
- 底栏 `hitokoto` 字段的输出从 `「正文」—— 出处` 改为 `*正文* —— 出处`。
- 没有出处时只输出 `*正文*`；一言接口不可达时的本地兜底句子同样为斜体、无引号。
- 效果示例：`✅ 已完成 · 耗时 12.5s · ⚕ Claude · 💬 *本自同根生，相煎何太急。* —— 七步诗`

#### 2. 🎴 Studio 模拟器同步
- 1:1 卡片预览中的一言示例改用斜体渲染，与真机卡片完全一致，所见即所得。

#### 3. 🧩 Devin / SWE-2 / Cognition 品牌图标
- 新增官方三链环 logo，内置 PNG（640px）与 SVG 双份素材。
- 模型关键词匹配补充 `swe`、`devin`、`cognition`：
  - 命中自定义素材时上传飞书并走 `custom_icon`；
  - 上传失败或未命中时回退 `ai-agent_outlined`（purple）标准图标。
- Studio 模型下拉新增 `SWE-2 Max / Devin` 选项。

#### 4. 🔧 静态资源版本统一
- 样式与脚本的 cache-busting 版本号统一为 `v0.3.1`，避免浏览器继续使用旧缓存。

---

### 🧪 测试

- 新增断言：footer 一言输出为斜体，且不含 `「` / `」`。
- 新增断言：`swe-2` / `devin` / `cognition` 关键词均解析到 Devin 品牌资产与对应标准图标回退。
- 本地 `tests/test_cardkit.py`、`tests/test_studio.py` 全部通过。

---

### 📦 升级方式

```bash
pip install -U hermes-lark-cards==0.3.1
```

或从源码更新后重启网关：

```bash
git pull && systemctl --user restart hermes-gateway
```

> 若底栏仍未变化，请确认 footer 字段配置中包含 `hitokoto`，并清理浏览器缓存以加载 `?v=0.3.1` 的静态资源。
