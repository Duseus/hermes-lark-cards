/**
 * Studio Application Controller with HTML5 Drag-and-Drop Sequence Canvas
 */

const ALL_FOOTER_FIELDS = [
  { id: "status", name: "完成状态" },
  { id: "elapsed", name: "运行耗时" },
  { id: "model", name: "模型名称" },
  { id: "tokens", name: "Token 吞吐" },
  { id: "context", name: "上下文进度" },
  { id: "weather", name: "实时天气" },
  { id: "hitokoto", name: "灵感一言" }
];

window.StudioApp = {
  state: {
    enabled: true,
    width_mode: "default",
    panel_expanded: false,
    header: { enabled: false, title: "" },
    body: { text_size: "normal_v2" },
    footer: {
      enabled: true,
      text_size: "notation",
      show_label: false,
      fields: [
        ["status", "elapsed", "model"],
        ["tokens", "context"],
        ["weather"],
        ["hitokoto"]
      ]
    }
  },
  // Flattened token sequence for Drag-and-Drop: e.g. ["status", "elapsed", "model", "__BREAK__", "weather"]
  sequence: [],
  dragSourceIndex: null,
  presets: {},

  async init() {
    this.bindEvents();
    this.setupMobileTabs();
    await this.loadVersion();
    await this.loadPresets();
    await this.loadConfig();
    this.buildSequenceFromState();
    this.renderFooterCanvas();
    this.refreshSimulator();
  },

  setupMobileTabs() {
    const tabConfig = document.getElementById("tabConfig");
    const tabPreview = document.getElementById("tabPreview");
    if (!tabConfig || !tabPreview) return;

    tabConfig.addEventListener("click", () => {
      document.body.classList.remove("show-preview");
      tabConfig.classList.add("active");
      tabPreview.classList.remove("active");
    });

    tabPreview.addEventListener("click", () => {
      document.body.classList.add("show-preview");
      tabPreview.classList.add("active");
      tabConfig.classList.remove("active");
      this.refreshSimulator();
    });
  },

  async loadVersion() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (data && data.version) {
        document.getElementById("versionBadge").textContent = `v${data.version}`;
      }
    } catch (e) {
      console.warn("loadVersion failed:", e);
    }
  },

  async loadPresets() {
    try {
      const res = await fetch("/api/presets");
      this.presets = await res.json();
      this.renderPresets();
    } catch (e) {
      console.warn("loadPresets failed:", e);
    }
  },

  async loadConfig() {
    try {
      const res = await fetch("/api/config");
      const data = await res.json();
      if (data && data.config) {
        this.state = { ...this.state, ...data.config };
        this.buildSequenceFromState();
        this.syncForm();
      }
    } catch (e) {
      console.warn("loadConfig failed, using defaults:", e);
      this.buildSequenceFromState();
    }
  },

  // Convert 2D fields array [["a", "b"], ["c"]] into sequence ["a", "b", "__BREAK__", "c"]
  buildSequenceFromState() {
    const raw = (this.state.footer && this.state.footer.fields) || [];
    const seq = [];
    raw.forEach((row, rIdx) => {
      if (rIdx > 0) seq.push("__BREAK__");
      if (Array.isArray(row)) {
        row.forEach(item => {
          if (item) seq.push(item);
        });
      }
    });
    this.sequence = seq;
  },

  // Convert sequence back into 2D fields array
  syncStateFromSequence() {
    const fields = [];
    let currentRow = [];
    this.sequence.forEach(token => {
      if (token === "__BREAK__") {
        if (currentRow.length > 0) {
          fields.push(currentRow);
          currentRow = [];
        }
      } else {
        currentRow.push(token);
      }
    });
    if (currentRow.length > 0) {
      fields.push(currentRow);
    }
    if (!this.state.footer) this.state.footer = {};
    this.state.footer.fields = fields.length > 0 ? fields : [["status", "elapsed"]];
    this.refreshSimulator();
  },

  renderPresets() {
    const container = document.getElementById("presetGrid");
    if (!container) return;
    container.innerHTML = Object.values(this.presets).map(p => `
      <div class="preset-card" data-preset="${p.id}" onclick="StudioApp.applyPreset('${p.id}')">
        <div class="preset-name">${p.name}</div>
      </div>
    `).join("");
  },

  applyPreset(presetId) {
    const p = this.presets[presetId];
    if (!p) return;
    this.state = JSON.parse(JSON.stringify(p.config));
    this.buildSequenceFromState();
    this.syncForm();
    this.renderFooterCanvas();
    this.refreshSimulator();
    document.querySelectorAll(".preset-card").forEach(el => {
      el.classList.toggle("active", el.dataset.preset === presetId);
    });
    this.toast(`已应用预设: ${p.name}`);
  },

  syncForm() {
    document.getElementById("toggleEnabled").checked = !!this.state.enabled;
    document.getElementById("toggleHeader").checked = !!(this.state.header && this.state.header.enabled);
    document.getElementById("inputHeaderTitle").value = (this.state.header && this.state.header.title) || "";
    this.toggleHeaderTitleVisibility(!!(this.state.header && this.state.header.enabled));

    document.getElementById("togglePanelExpanded").checked = !!this.state.panel_expanded;
    document.getElementById("toggleFooter").checked = !!(this.state.footer && this.state.footer.enabled);
    document.getElementById("toggleFooterLabel").checked = !!(this.state.footer && this.state.footer.show_label);

    document.getElementById("selectWidthMode").value = this.state.width_mode || "default";
    document.getElementById("selectBodyTextSize").value = (this.state.body && this.state.body.text_size) || "normal_v2";
    document.getElementById("selectFooterTextSize").value = (this.state.footer && this.state.footer.text_size) || "notation";

    this.renderFooterCanvas();
  },

  toggleHeaderTitleVisibility(show) {
    const group = document.getElementById("groupHeaderTitle");
    if (group) {
      group.style.display = show ? "flex" : "none";
    }
  },

  // ── Render Drag-and-Drop Canvas & Palette ──
  renderFooterCanvas() {
    const canvas = document.getElementById("footerCanvas");
    const availWrap = document.getElementById("footerAvailableWrap");
    if (!canvas) return;

    const fieldMap = Object.fromEntries(ALL_FOOTER_FIELDS.map(f => [f.id, f.name]));
    const usedFields = new Set();

    // 1. Render items in sequence
    canvas.innerHTML = this.sequence.map((token, idx) => {
      if (token === "__BREAK__") {
        return `
          <div class="drag-item break-tag" draggable="true" data-index="${idx}">
            <span>↵ 换行符</span>
            <button class="btn-remove" title="删除换行" onclick="StudioApp.removeSequenceItem(${idx}, event)">×</button>
          </div>
        `;
      }
      usedFields.add(token);
      return `
        <div class="drag-item field-tag" draggable="true" data-index="${idx}">
          <span class="drag-handle">⠿</span>
          <span>${fieldMap[token] || token}</span>
          <button class="btn-remove" title="移除" onclick="StudioApp.removeSequenceItem(${idx}, event)">×</button>
        </div>
      `;
    }).join("");

    if (this.sequence.length === 0) {
      canvas.innerHTML = `<span style="font-size: 12px; color: #94a3b8; pointer-events: none;">(画板为空，请从下方点击或拖入指标/换行符)</span>`;
    }

    // Attach HTML5 Drag and Drop listeners to items
    this.attachDragEvents(canvas);

    // 2. Render Available (unused) fields in palette
    if (availWrap) {
      const unusedFields = ALL_FOOTER_FIELDS.filter(f => !usedFields.has(f.id));
      if (unusedFields.length === 0) {
        availWrap.innerHTML = `<span style="font-size: 12px; color: #94a3b8;">所有指标均已排入底栏</span>`;
      } else {
        availWrap.innerHTML = unusedFields.map(f => `
          <div class="footer-add-chip" onclick="StudioApp.addToken('${f.id}')">
            <span>+ ${f.name}</span>
          </div>
        `).join("");
      }
    }
  },

  attachDragEvents(canvas) {
    const items = canvas.querySelectorAll(".drag-item");

    items.forEach(el => {
      el.addEventListener("dragstart", e => {
        this.dragSourceIndex = parseInt(el.dataset.index, 10);
        el.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
      });

      el.addEventListener("dragend", () => {
        el.classList.remove("dragging");
        items.forEach(i => i.classList.remove("drop-target"));
        canvas.classList.remove("drag-over");
      });

      el.addEventListener("dragover", e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        items.forEach(i => i.classList.remove("drop-target"));
        el.classList.add("drop-target");
      });

      el.addEventListener("drop", e => {
        e.preventDefault();
        e.stopPropagation();
        const targetIdx = parseInt(el.dataset.index, 10);
        if (this.dragSourceIndex !== null && this.dragSourceIndex !== targetIdx) {
          this.reorderSequence(this.dragSourceIndex, targetIdx);
        }
      });
    });

    canvas.addEventListener("dragover", e => {
      e.preventDefault();
      canvas.classList.add("drag-over");
    });

    canvas.addEventListener("dragleave", () => {
      canvas.classList.remove("drag-over");
    });
  },

  reorderSequence(fromIdx, toIdx) {
    if (fromIdx < 0 || fromIdx >= this.sequence.length) return;
    if (toIdx < 0 || toIdx >= this.sequence.length) return;

    const item = this.sequence.splice(fromIdx, 1)[0];
    this.sequence.splice(toIdx, 0, item);

    this.renderFooterCanvas();
    this.syncStateFromSequence();
  },

  addToken(token) {
    this.sequence.push(token);
    this.renderFooterCanvas();
    this.syncStateFromSequence();
  },

  addBreakToken() {
    // Avoid double consecutive breaks or leading break
    if (this.sequence.length === 0 || this.sequence[this.sequence.length - 1] === "__BREAK__") {
      this.toast("已在行末，无需重复添加换行符");
      return;
    }
    this.sequence.push("__BREAK__");
    this.renderFooterCanvas();
    this.syncStateFromSequence();
  },

  removeSequenceItem(idx, event) {
    if (event) event.stopPropagation();
    if (idx < 0 || idx >= this.sequence.length) return;
    this.sequence.splice(idx, 1);
    this.renderFooterCanvas();
    this.syncStateFromSequence();
  },

  bindEvents() {
    document.getElementById("toggleEnabled").addEventListener("change", e => {
      this.state.enabled = e.target.checked;
      this.refreshSimulator();
    });
    document.getElementById("toggleHeader").addEventListener("change", e => {
      if (!this.state.header) this.state.header = {};
      this.state.header.enabled = e.target.checked;
      this.toggleHeaderTitleVisibility(e.target.checked);
      this.refreshSimulator();
    });
    document.getElementById("inputHeaderTitle").addEventListener("input", e => {
      if (!this.state.header) this.state.header = {};
      this.state.header.title = e.target.value;
      this.refreshSimulator();
    });

    document.getElementById("togglePanelExpanded").addEventListener("change", e => {
      this.state.panel_expanded = e.target.checked;
      this.refreshSimulator();
    });
    document.getElementById("toggleFooter").addEventListener("change", e => {
      if (!this.state.footer) this.state.footer = {};
      this.state.footer.enabled = e.target.checked;
      this.refreshSimulator();
    });
    document.getElementById("toggleFooterLabel").addEventListener("change", e => {
      if (!this.state.footer) this.state.footer = {};
      this.state.footer.show_label = e.target.checked;
      this.refreshSimulator();
    });
    document.getElementById("selectWidthMode").addEventListener("change", e => {
      this.state.width_mode = e.target.value;
      this.refreshSimulator();
    });
    document.getElementById("selectBodyTextSize").addEventListener("change", e => {
      if (!this.state.body) this.state.body = {};
      this.state.body.text_size = e.target.value;
      this.refreshSimulator();
    });
    document.getElementById("selectFooterTextSize").addEventListener("change", e => {
      if (!this.state.footer) this.state.footer = {};
      this.state.footer.text_size = e.target.value;
      this.refreshSimulator();
    });

    document.getElementById("btnAddBreak").addEventListener("click", () => this.addBreakToken());
    document.getElementById("btnSave").addEventListener("click", () => this.saveConfig());
    document.getElementById("btnRestart").addEventListener("click", () => this.restartGateway());
  },

  refreshSimulator() {
    CardSimulator.render(this.state);
  },

  async saveConfig() {
    try {
      this.syncStateFromSequence();
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.state)
      });
      const data = await res.json();
      if (data && data.ok) {
        this.toast("🎉 配置已成功保存！");
      } else {
        this.toast(`保存失败: ${data.error || '未知错误'}`);
      }
    } catch (e) {
      this.toast(`保存请求失败: ${e.message}`);
    }
  },

  async restartGateway() {
    try {
      this.toast("正在重启 Hermes Gateway...");
      const res = await fetch("/api/restart", { method: "POST" });
      const data = await res.json();
      if (data && data.ok) {
        this.toast(data.message || "Hermes Gateway 重启完成");
      } else {
        this.toast(`重启失败: ${data.error || '未知错误'}`);
      }
    } catch (e) {
      this.toast(`重启请求异常: ${e.message}`);
    }
  },

  toast(msg) {
    const el = document.getElementById("toastMsg");
    if (!el) return;
    el.textContent = msg;
    el.style.display = "block";
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      el.style.display = "none";
    }, 3000);
  }
};

window.addEventListener("DOMContentLoaded", () => {
  StudioApp.init();
});
