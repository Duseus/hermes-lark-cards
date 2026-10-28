/**
 * Studio Application Controller with Multi-row Drag & Drop and Detailed Templates
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
  // Drag-and-drop state across rows
  dragData: null, // { sourceRow: number, sourceCol: number, fieldId: string }
  presets: {},
  templates: {},

  async init() {
    this.bindEvents();
    this.setupMobileTabs();
    await this.loadVersion();
    await this.loadPresets();
    await this.loadTemplates();
    await this.loadConfig();
    this.renderFooterRows();
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

  async loadTemplates() {
    try {
      const res = await fetch("/api/templates");
      this.templates = await res.json();
      this.renderTemplates();
    } catch (e) {
      console.warn("loadTemplates failed:", e);
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
    this.renderFooterRows();
    this.refreshSimulator();
    document.querySelectorAll(".preset-card").forEach(el => {
      el.classList.toggle("active", el.dataset.preset === presetId);
    });
    document.querySelectorAll(".template-card").forEach(el => el.classList.remove("active"));
    this.toast(`已应用预设: ${p.name}`);
  },

  // ── Custom Templates with Name, Date, Meta Badge, Delete ──
  renderTemplates() {
    const container = document.getElementById("templateGrid");
    if (!container) return;
    const list = Object.values(this.templates || {});
    if (list.length === 0) {
      container.innerHTML = `<span style="font-size: 12px; color: #94a3b8; padding: 4px 0;">暂无自定义模板，可在下方配置好后点击「⭐ 保存为模板」</span>`;
      return;
    }

    const fieldMap = Object.fromEntries(ALL_FOOTER_FIELDS.map(f => [f.id, f.name]));
    container.innerHTML = list.map(t => {
      const cfg = t.config || {};
      const rows = (cfg.footer && cfg.footer.fields) || [];
      const summaryParts = [];
      rows.forEach(r => {
        if (Array.isArray(r) && r.length) {
          summaryParts.push(r.map(id => fieldMap[id] || id).join(" · "));
        }
      });
      const summary = summaryParts.join(" / ") || "默认卡片";
      const timeStr = t.updated_at || "最近更新";

      return `
        <div class="template-card" data-template="${t.id}" onclick="StudioApp.applyTemplate('${t.id}')">
          <div class="template-info">
            <div class="template-header-line">
              <span class="template-name">${this.escapeHtml(t.name)}</span>
              <span class="template-time">${this.escapeHtml(timeStr)}</span>
            </div>
            <div class="template-meta-badge" title="${this.escapeHtml(summary)}">${this.escapeHtml(summary)}</div>
          </div>
          <div class="template-actions">
            <button class="btn-del-template" title="删除模板" onclick="StudioApp.deleteTemplate('${t.id}', event)">🗑️</button>
          </div>
        </div>
      `;
    }).join("");
  },

  applyTemplate(templateId) {
    const t = this.templates[templateId];
    if (!t || !t.config) return;
    this.state = JSON.parse(JSON.stringify(t.config));
    this.syncForm();
    this.renderFooterRows();
    this.refreshSimulator();
    document.querySelectorAll(".template-card").forEach(el => {
      el.classList.toggle("active", el.dataset.template === templateId);
    });
    document.querySelectorAll(".preset-card").forEach(el => el.classList.remove("active"));
    this.toast(`已应用模板: ${t.name}`);
  },

  openSaveTemplateModal() {
    const modal = document.getElementById("templateModal");
    const input = document.getElementById("inputTemplateName");
    if (modal && input) {
      input.value = "";
      modal.classList.add("open");
      setTimeout(() => input.focus(), 100);
    }
  },

  closeSaveTemplateModal() {
    const modal = document.getElementById("templateModal");
    if (modal) modal.classList.remove("open");
  },

  async confirmSaveTemplate() {
    const input = document.getElementById("inputTemplateName");
    const name = (input ? input.value : "").trim();
    if (!name) {
      this.toast("请输入模板名称");
      return;
    }

    try {
      this.cleanFooterState();
      const res = await fetch("/api/templates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          config: this.state
        })
      });
      const data = await res.json();
      if (data && data.ok) {
        this.templates = data.templates || {};
        this.renderTemplates();
        this.closeSaveTemplateModal();
        this.toast(`🎉 模板「${name}」已成功保存！`);
      } else {
        this.toast(`模板保存失败: ${data.error || '未知错误'}`);
      }
    } catch (e) {
      this.toast(`保存请求失败: ${e.message}`);
    }
  },

  async deleteTemplate(templateId, event) {
    if (event) event.stopPropagation();
    if (!confirm("确定要删除这个自定义模板吗？")) return;

    try {
      const res = await fetch("/api/templates/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: templateId })
      });
      const data = await res.json();
      if (data && data.ok) {
        this.templates = data.templates || {};
        this.renderTemplates();
        this.toast("模板已删除");
      } else {
        this.toast(`删除失败: ${data.error || '未知错误'}`);
      }
    } catch (e) {
      this.toast(`删除请求失败: ${e.message}`);
    }
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

    this.renderFooterRows();
  },

  toggleHeaderTitleVisibility(show) {
    const group = document.getElementById("groupHeaderTitle");
    if (group) {
      group.style.display = show ? "flex" : "none";
    }
  },

  // ── Multi-row Drag & Drop Footer Builder ──
  renderFooterRows() {
    const container = document.getElementById("footerRowsContainer");
    const availWrap = document.getElementById("footerAvailableWrap");
    if (!container) return;

    if (!this.state.footer) this.state.footer = { fields: [] };
    if (!Array.isArray(this.state.footer.fields) || this.state.footer.fields.length === 0) {
      this.state.footer.fields = [["status", "elapsed"]];
    }

    const fieldMap = Object.fromEntries(ALL_FOOTER_FIELDS.map(f => [f.id, f.name]));
    const usedFields = new Set();

    // 1. Render Each Row Card
    container.innerHTML = this.state.footer.fields.map((row, rIdx) => {
      row.forEach(f => usedFields.add(f));
      const chipsHtml = row.map((fieldId, cIdx) => `
        <div class="drag-item" draggable="true" data-row="${rIdx}" data-col="${cIdx}">
          <span class="drag-handle">⠿</span>
          <span>${fieldMap[fieldId] || fieldId}</span>
          <button class="btn-remove" title="移除" onclick="StudioApp.removeFieldFromRow(${rIdx}, ${cIdx}, event)">×</button>
        </div>
      `).join("");

      return `
        <div class="footer-row-box" data-row="${rIdx}">
          <div class="footer-row-header">
            <span class="footer-row-badge">第 ${rIdx + 1} 行</span>
            <div class="footer-row-actions">
              ${rIdx > 0 ? `<button class="btn btn-sm" title="上移行" onclick="StudioApp.moveRow(${rIdx}, -1)">▲</button>` : ''}
              ${rIdx < this.state.footer.fields.length - 1 ? `<button class="btn btn-sm" title="下移行" onclick="StudioApp.moveRow(${rIdx}, 1)">▼</button>` : ''}
              ${this.state.footer.fields.length > 1 ? `<button class="btn btn-sm" style="color: #ef4444;" title="删除整行" onclick="StudioApp.deleteRow(${rIdx})">🗑️</button>` : ''}
            </div>
          </div>
          <div class="footer-row-dropzone" data-row="${rIdx}">
            ${chipsHtml || '<span style="font-size: 12px; color: #94a3b8; pointer-events: none;">(拖动指标到此行，或从下方点击添加)</span>'}
          </div>
        </div>
      `;
    }).join("");

    // Attach row-aware Drag & Drop events
    this.attachRowDragEvents(container);

    // 2. Render Available (unused) fields in palette
    if (availWrap) {
      const unusedFields = ALL_FOOTER_FIELDS.filter(f => !usedFields.has(f.id));
      if (unusedFields.length === 0) {
        availWrap.innerHTML = `<span style="font-size: 12px; color: #94a3b8;">所有指标均已排入底栏</span>`;
      } else {
        availWrap.innerHTML = unusedFields.map(f => `
          <div class="footer-add-chip" onclick="StudioApp.addFieldToLastRow('${f.id}')">
            <span>+ ${f.name}</span>
          </div>
        `).join("");
      }
    }
  },

  attachRowDragEvents(container) {
    const items = container.querySelectorAll(".drag-item");
    const dropzones = container.querySelectorAll(".footer-row-dropzone");

    items.forEach(el => {
      el.addEventListener("dragstart", e => {
        const r = parseInt(el.dataset.row, 10);
        const c = parseInt(el.dataset.col, 10);
        const fieldId = this.state.footer.fields[r][c];
        this.dragData = { sourceRow: r, sourceCol: c, fieldId };
        el.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
      });

      el.addEventListener("dragend", () => {
        el.classList.remove("dragging");
        container.querySelectorAll(".drop-target").forEach(d => d.classList.remove("drop-target"));
        dropzones.forEach(dz => dz.classList.remove("drag-over"));
        this.dragData = null;
      });

      el.addEventListener("dragover", e => {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = "move";
        container.querySelectorAll(".drop-target").forEach(d => d.classList.remove("drop-target"));
        el.classList.add("drop-target");
      });

      el.addEventListener("drop", e => {
        e.preventDefault();
        e.stopPropagation();
        if (!this.dragData) return;

        const targetRow = parseInt(el.dataset.row, 10);
        const targetCol = parseInt(el.dataset.col, 10);
        const { sourceRow, sourceCol } = this.dragData;

        // Move within or across rows
        const item = this.state.footer.fields[sourceRow].splice(sourceCol, 1)[0];
        this.state.footer.fields[targetRow].splice(targetCol, 0, item);

        this.renderFooterRows();
        this.refreshSimulator();
      });
    });

    dropzones.forEach(dz => {
      dz.addEventListener("dragover", e => {
        e.preventDefault();
        dz.classList.add("drag-over");
      });

      dz.addEventListener("dragleave", () => {
        dz.classList.remove("drag-over");
      });

      dz.addEventListener("drop", e => {
        e.preventDefault();
        if (!this.dragData) return;

        const targetRow = parseInt(dz.dataset.row, 10);
        const { sourceRow, sourceCol } = this.dragData;

        // If dropped onto empty space of the row zone
        const item = this.state.footer.fields[sourceRow].splice(sourceCol, 1)[0];
        this.state.footer.fields[targetRow].push(item);

        this.renderFooterRows();
        this.refreshSimulator();
      });
    });
  },

  addNewRow() {
    if (!this.state.footer) this.state.footer = { fields: [] };
    this.state.footer.fields.push([]);
    this.renderFooterRows();
    this.refreshSimulator();
  },

  deleteRow(rIdx) {
    if (!this.state.footer?.fields) return;
    this.state.footer.fields.splice(rIdx, 1);
    if (this.state.footer.fields.length === 0) {
      this.state.footer.fields.push([]);
    }
    this.renderFooterRows();
    this.refreshSimulator();
  },

  moveRow(rIdx, direction) {
    const fields = this.state.footer?.fields;
    if (!fields) return;
    const targetIdx = rIdx + direction;
    if (targetIdx < 0 || targetIdx >= fields.length) return;
    const temp = fields[rIdx];
    fields[rIdx] = fields[targetIdx];
    fields[targetIdx] = temp;
    this.renderFooterRows();
    this.refreshSimulator();
  },

  addFieldToLastRow(fieldId) {
    if (!this.state.footer) this.state.footer = { fields: [] };
    if (!this.state.footer.fields.length) this.state.footer.fields.push([]);
    const lastRow = this.state.footer.fields[this.state.footer.fields.length - 1];
    if (!lastRow.includes(fieldId)) {
      lastRow.push(fieldId);
    }
    this.renderFooterRows();
    this.refreshSimulator();
  },

  removeFieldFromRow(rIdx, cIdx, event) {
    if (event) event.stopPropagation();
    const row = this.state.footer?.fields?.[rIdx];
    if (!row) return;
    row.splice(cIdx, 1);
    this.renderFooterRows();
    this.refreshSimulator();
  },

  cleanFooterState() {
    if (this.state.footer && Array.isArray(this.state.footer.fields)) {
      this.state.footer.fields = this.state.footer.fields.filter(row => row.length > 0);
      if (this.state.footer.fields.length === 0) {
        this.state.footer.fields = [["status", "elapsed"]];
      }
    }
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

    document.getElementById("btnAddFooterRow").addEventListener("click", () => this.addNewRow());
    document.getElementById("btnOpenSaveTemplate").addEventListener("click", () => this.openSaveTemplateModal());
    document.getElementById("btnCancelTemplate").addEventListener("click", () => this.closeSaveTemplateModal());
    document.getElementById("btnConfirmSaveTemplate").addEventListener("click", () => this.confirmSaveTemplate());
    document.getElementById("inputTemplateName").addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.confirmSaveTemplate();
    });

    document.getElementById("btnSave").addEventListener("click", () => this.saveConfig());
    document.getElementById("btnRestart").addEventListener("click", () => this.restartGateway());
  },

  refreshSimulator() {
    CardSimulator.render(this.state);
  },

  async saveConfig() {
    try {
      this.cleanFooterState();
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

  escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
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
