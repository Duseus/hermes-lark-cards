/**
 * Studio Application Controller
 */

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
  presets: {},

  async init() {
    this.bindEvents();
    this.setupMobileTabs();
    await this.loadVersion();
    await this.loadPresets();
    await this.loadConfig();
    this.renderFooterChips();
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
        this.syncForm();
      }
    } catch (e) {
      console.warn("loadConfig failed, using defaults:", e);
    }
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
    this.syncForm();
    this.refreshSimulator();
    document.querySelectorAll(".preset-card").forEach(el => {
      el.classList.toggle("active", el.dataset.preset === presetId);
    });
    this.toast(`已应用预设: ${p.name}`);
  },

  syncForm() {
    // Toggles
    document.getElementById("toggleEnabled").checked = !!this.state.enabled;
    document.getElementById("toggleHeader").checked = !!(this.state.header && this.state.header.enabled);
    document.getElementById("inputHeaderTitle").value = (this.state.header && this.state.header.title) || "";
    this.toggleHeaderTitleVisibility(!!(this.state.header && this.state.header.enabled));

    document.getElementById("togglePanelExpanded").checked = !!this.state.panel_expanded;
    document.getElementById("toggleFooter").checked = !!(this.state.footer && this.state.footer.enabled);
    document.getElementById("toggleFooterLabel").checked = !!(this.state.footer && this.state.footer.show_label);

    // Selects
    document.getElementById("selectWidthMode").value = this.state.width_mode || "default";
    document.getElementById("selectBodyTextSize").value = (this.state.body && this.state.body.text_size) || "normal_v2";
    document.getElementById("selectFooterTextSize").value = (this.state.footer && this.state.footer.text_size) || "notation";

    this.renderFooterChips();
  },

  toggleHeaderTitleVisibility(show) {
    const group = document.getElementById("groupHeaderTitle");
    if (group) {
      group.style.display = show ? "flex" : "none";
    }
  },

  renderFooterChips() {
    const container = document.getElementById("footerChipsWrap");
    if (!container) return;
    const allFields = [
      { id: "status", name: "完成状态" },
      { id: "elapsed", name: "运行耗时" },
      { id: "model", name: "模型名称" },
      { id: "tokens", name: "Token 吞吐" },
      { id: "context", name: "上下文进度" },
      { id: "weather", name: "实时天气" },
      { id: "hitokoto", name: "灵感一言" }
    ];

    const active = new Set();
    const fields = (this.state.footer && this.state.footer.fields) || [];
    fields.forEach(row => {
      if (Array.isArray(row)) row.forEach(f => active.add(f));
    });

    container.innerHTML = allFields.map(f => `
      <div class="footer-chip ${active.has(f.id) ? 'active' : ''}" onclick="StudioApp.toggleFooterField('${f.id}')">
        ${active.has(f.id) ? '✓ ' : '+ '}${f.name}
      </div>
    `).join("");
  },

  toggleFooterField(fieldId) {
    if (!this.state.footer) this.state.footer = { fields: [] };
    if (!Array.isArray(this.state.footer.fields)) this.state.footer.fields = [];
    if (this.state.footer.fields.length === 0) this.state.footer.fields.push([]);

    let found = false;
    this.state.footer.fields.forEach(row => {
      const idx = row.indexOf(fieldId);
      if (idx >= 0) {
        row.splice(idx, 1);
        found = true;
      }
    });

    if (!found) {
      this.state.footer.fields[0].push(fieldId);
    }

    this.state.footer.fields = this.state.footer.fields.filter(r => r.length > 0);
    this.renderFooterChips();
    this.refreshSimulator();
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

    document.getElementById("btnSave").addEventListener("click", () => this.saveConfig());
    document.getElementById("btnRestart").addEventListener("click", () => this.restartGateway());
  },

  refreshSimulator() {
    CardSimulator.render(this.state);
  },

  async saveConfig() {
    try {
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
