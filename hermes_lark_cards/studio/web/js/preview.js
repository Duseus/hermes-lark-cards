/**
 * 1:1 Feishu CardKit 2.0 DOM Simulator
 */

const CardSimulator = {
  mode: "completed", // 'completed' | 'streaming'
  userToggled: false,
  panelExpanded: false,

  render(state) {
    const cardEl = document.getElementById("simulatorCard");
    if (!cardEl) return;

    const widthMode = state.width_mode || "default";
    const headerCfg = state.header || {};
    const bodyCfg = state.body || {};
    const footerCfg = state.footer || {};
    const isExpanded = this.userToggled ? this.panelExpanded : !!state.panel_expanded;

    // Outer wrap class for width mode
    const wrapEl = document.getElementById("simulatorWrap");
    if (wrapEl) {
      wrapEl.className = `feishu-simulator-wrap width-${widthMode}`;
    }

    // Header section
    let headerHtml = "";
    if (headerCfg.enabled) {
      const headerColor = this.mode === "streaming" ? "blue" : "green";
      let headerText = (headerCfg.title || "").trim();
      if (!headerText) {
        headerText = this.mode === "streaming" ? "💭 Hermes 正在处理…" : "✅ 已完成";
      }
      headerHtml = `
        <div class="feishu-card-header ${headerColor}">
          <span>${this.escapeHtml(headerText)}</span>
        </div>
      `;
    }

    // Body content
    let bodyText = "";
    if (this.mode === "streaming") {
      bodyText = "正在分析系统网络与路由状态，准备为您调用相关诊断工具…<span class=\"card-cursor\"></span>";
    } else {
      bodyText = "我已经分析了系统服务状态，DNS 缓存异常导致了心跳超时。已为您自动完成服务重启并验证联通性。";
    }
    const bodyTextSizeClass = `text-${bodyCfg.text_size || "normal_v2"}`;

    // Collapsible process panel
    const panelHeaderInfo = "DeepSeek-V3 · 💭 1 · 🛠️ 2 · ⏱️ 1.2s";
    const panelHtml = `
      <div class="feishu-collapsible ${isExpanded ? 'expanded' : ''}" id="simCollapsible">
        <div class="feishu-collapsible-header" onclick="CardSimulator.togglePanel()">
          <div class="feishu-collapsible-header-left">
            <span>${isExpanded ? '▼' : '▶'}</span>
            <b>${panelHeaderInfo}</b>
          </div>
          <span style="font-size: 11px; color: #8f959e;">${isExpanded ? '收起' : '展开'}</span>
        </div>
        <div class="feishu-collapsible-content">
          <div class="tool-item"><span class="tool-icon">🛠️</span> <span><b>exec</b>: systemctl restart coredns</span></div>
          <div class="tool-item"><span class="tool-icon">🔍</span> <span><b>read</b>: /etc/resolv.conf</span></div>
        </div>
      </div>
    `;

    // Footer section
    let footerHtml = "";
    if (footerCfg.enabled) {
      const fieldsMatrix = footerCfg.fields || [["status", "elapsed", "model"]];
      const showLabel = !!footerCfg.show_label;
      const linesHtml = fieldsMatrix.map(row => {
        const parts = row.map(field => {
          if (field === "status") return "✅ 已完成";
          if (field === "elapsed") return showLabel ? "耗时: 1.2s" : "1.2s";
          if (field === "model") return "⚕ DeepSeek-V3";
          if (field === "tokens") return "↑ 1.2K ↓ 480";
          if (field === "context") return "15.2K/128K (11%)";
          if (field === "weather") return "☀️ 临平 21.5°C/14.0°C · 湿度 68%";
          if (field === "hitokoto") return "💬 「保持好奇，持续折腾。」";
          return field;
        });
        return `<div class="footer-line">${parts.map(p => `<span>${p}</span>`).join(" · ")}</div>`;
      }).join("");

      if (linesHtml) {
        footerHtml = `
          <div class="feishu-card-footer">
            ${linesHtml}
          </div>
        `;
      }
    }

    cardEl.innerHTML = `
      ${headerHtml}
      <div class="feishu-card-body ${bodyTextSizeClass}">
        <div>${bodyText}</div>
        ${panelHtml}
        ${footerHtml}
      </div>
    `;
  },

  escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },

  togglePanel() {
    this.userToggled = true;
    this.panelExpanded = !this.panelExpanded;
    const el = document.getElementById("simCollapsible");
    if (el) el.classList.toggle("expanded", this.panelExpanded);
  },

  setMode(mode) {
    this.mode = mode;
    this.userToggled = false;
    document.querySelectorAll(".btn-mode").forEach(b => {
      b.classList.toggle("active", b.dataset.mode === mode);
    });
    if (window.StudioApp) {
      window.StudioApp.refreshSimulator();
    }
  }
};
