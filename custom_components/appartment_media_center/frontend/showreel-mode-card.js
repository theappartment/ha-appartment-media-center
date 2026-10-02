// Showreel Mode Card 1.1.0 — standalone Lovelace module, no build required.
const DEFAULT_MODES = [
  { label: "Automatico", option: "Automatico", description: "Ultimo showreel scelto in attesa. AirPlay quando ti colleghi." },
  { label: "Showreel video", option: "Showreel video", description: "Video in loop. AirPlay sempre disponibile." },
  { label: "Showreel foto", option: "Showreel foto", description: "Gli shooting in loop. AirPlay sempre disponibile." },
  { label: "Schermo nero", option: "Schermo nero", description: "Standby silenzioso. AirPlay sempre disponibile." },
  { label: "Riunione", option: "Riunione", description: "Una schermata di benvenuto, pronta per condividere con AirPlay." },
];

class ShowreelModeCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._request = null;
    this._error = "";
  }

  setConfig(config) {
    if (!config || typeof config.entity !== "string" || !/^select\.[a-z0-9_]+$/.test(config.entity)) {
      throw new Error("Configura entity con un'entità select.*, ad esempio select.modalita_schermo.");
    }
    const modes = config.modes ?? DEFAULT_MODES;
    if (!Array.isArray(modes) || modes.length < 1 || modes.length > 8) {
      throw new Error("modes deve contenere da una a otto modalità.");
    }
    const normalized = modes.map((mode, index) => {
      if (!mode || typeof mode.option !== "string" || !mode.option.trim()) {
        throw new Error(`modes[${index}].option deve essere una stringa non vuota.`);
      }
      for (const key of ["label", "description"]) {
        if (mode[key] !== undefined && typeof mode[key] !== "string") {
          throw new Error(`modes[${index}].${key} deve essere una stringa.`);
        }
      }
      return { ...DEFAULT_MODES[index], ...mode, label: mode.label ?? DEFAULT_MODES[index]?.label ?? mode.option, description: mode.description ?? DEFAULT_MODES[index]?.description ?? "" };
    });
    if (new Set(normalized.map((mode) => mode.option)).size !== normalized.length) {
      throw new Error("Ogni modalità deve avere un valore option diverso.");
    }
    this._config = { entity: config.entity, modes: normalized, show_controls: config.show_controls !== false };
    this._request = null;
    this._error = "";
    this._build();
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  getCardSize() {
    return Math.ceil((this.getBoundingClientRect().height || 560) / 50);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _build() {
    // Only static markup goes through innerHTML. YAML/state strings use textContent.
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; container-type: inline-size; }
        * { box-sizing: border-box; }
        ha-card { display: block; background: #151717; color: #e8e9e8;
          border: 0; border-radius: 12px; box-shadow: none; padding: 16px; }
        .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
        button { appearance: none; width: 100%; min-width: 0; min-height: 238px;
          display: flex; flex-direction: column; position: relative; text-align: left;
          padding: 26px; border: 1px solid #3a3d3c; border-radius: 8px;
          background: #151717; color: #e8e9e8; cursor: pointer; font: inherit;
          transition: background-color 160ms ease, border-color 160ms ease; }
        .top { display: flex; justify-content: space-between; align-items: flex-start;
          width: 100%; gap: 16px; margin-bottom: 36px; }
        .number { font-size: 17px; line-height: 1.4; color: #a6aba7; }
        svg { width: 30px; height: 30px; flex-shrink: 0; }
        .label { display: block; font-size: 25px; font-weight: 500;
          line-height: 1.2; letter-spacing: -.7px; overflow-wrap: anywhere; }
        .description { display: block; margin-top: 18px; font-size: 17px;
          line-height: 1.5; color: #a6aba7; overflow-wrap: anywhere; }
        button[aria-pressed="true"] { background: #d5f18a; border-color: #d5f18a; color: #253016; }
        button[aria-pressed="true"] .number,
        button[aria-pressed="true"] .description { color: #4c5b31; }
        @media (hover: hover) { button:hover:not(:disabled) { border-color: #d5f18a; } }
        button:focus-visible { outline: 3px solid #fff; outline-offset: 4px; }
        button:disabled { cursor: not-allowed; }
        button.unavailable { opacity: .48; }
        .status { margin: 14px 0 0; font-size: 14px; line-height: 1.5; color: #d5d9d5; }
        .status:empty { display: none; }
        @container (min-width: 560px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        @container (min-width: 1100px) {
          .grid { grid-template-columns: repeat(var(--mode-count, 5), minmax(0, 1fr)); gap: 20px; }
          button { min-height: 280px; padding: 30px; }
        }
        @container (min-width: 1600px) {
          ha-card { padding: 28px; }
          button { min-height: 330px; padding: 36px; }
          .label { font-size: 32px; } .description { font-size: 22px; }
          .number { font-size: 21px; } .top { margin-bottom: 48px; }
        }
        @media (prefers-reduced-motion: reduce) { button { transition: none; } }
        [hidden] { display: none !important; }
        .overview { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px; }
        .badge { padding: 7px 11px; border-radius: 20px; border: 1px solid #3a3d3c; font-size: 13px; }
        .controls { margin-top: 22px; display: grid; grid-template-columns: 1fr; gap: 16px; }
        .control-panel { border: 1px solid #3a3d3c; border-radius: 8px; padding: 20px; min-width: 0; }
        .control-panel h3 { font-size: 17px; font-weight: 500; margin: 0 0 16px; }
        .controls button { min-height: 44px; padding: 10px 14px; display: inline-flex;
          flex-direction: row; align-items: center; justify-content: center; width: auto;
          font-size: 14px; border-radius: 6px; }
        .controls button:disabled { opacity: .45; }
        .controls .row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
        .controls label { display: block; font-size: 14px; color: #a6aba7; margin-bottom: 8px; }
        input { font: inherit; min-width: 0; accent-color: #d5f18a; }
        input[type="text"] { width: 100%; background: #202322; color: #e8e9e8;
          padding: 12px; border: 1px solid #51564e; border-radius: 6px; }
        input[type="range"] { flex: 1; width: 100%; min-height: 36px; }
        .controls p { font-size: 13px; line-height: 1.5; color: #a6aba7; margin: 12px 0; overflow-wrap: anywhere; }
        .controls a { color: #d5f18a; font-size: 14px; display: inline-block; padding: 10px 0; }
        .title-row { margin-top: 10px; }
        .job-summary, .device-errors { white-space: pre-line; }
        @container (min-width: 800px) { .controls { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        @container (min-width: 1600px) { .label { font-size: 28px; } .grid button { padding: 28px; } }
      </style>
      <ha-card>
        <div class="overview" hidden aria-label="Stato media center">
          <span class="badge content-summary"></span><span class="badge airplay-summary"></span>
          <span class="badge readiness-summary"></span>
        </div>
        <div class="grid" role="group" aria-label="Modalità schermo"></div>
        <div class="controls" hidden>
          <section class="control-panel"><h3>Riunione</h3>
            <label for="meeting-title">Messaggio di benvenuto</label>
            <input id="meeting-title" type="text" maxlength="160" placeholder="Benvenuti">
            <div class="row title-row"><button type="button" data-control="meeting_title">Salva titolo</button>
              <button type="button" data-control="release_screen">Libera schermo</button></div>
            <p>Libera schermo interrompe la condivisione in corso e torna a Riunione.</p>
          </section>
          <section class="control-panel"><h3>Audio</h3>
            <label for="volume">Volume <output id="volume-value"></output></label>
            <div class="row"><input id="volume" type="range" min="0" max="100" step="1">
              <button type="button" data-control="muted" aria-pressed="false">Muto</button></div>
            <p>In Schermo nero, senza AirPlay o presentazioni, l’audio resta silenziato.</p>
          </section>
          <section class="control-panel"><h3>Presentazione</h3>
            <p class="presentation-summary"></p>
            <div class="row"><button type="button" data-control="previous_page">← Precedente</button>
              <button type="button" data-control="next_page">Successiva →</button>
              <button type="button" data-control="close_presentation">Chiudi presentazione</button></div>
            <a class="panel-link" target="_blank" rel="noopener noreferrer" hidden>Apri pannello · PDF, Slides e immagini ↗</a>
          </section>
          <section class="control-panel"><h3>Contenuti e stato</h3>
            <div class="row"><button type="button" data-control="refresh_showreel">Aggiorna video</button>
              <button type="button" data-control="refresh_photos">Aggiorna foto</button>
              <button type="button" data-control="sync_content">Sincronizza contenuti</button></div>
            <div class="row"><button type="button" data-control="dismiss_keyring_prompt">Chiudi richiesta portachiavi</button></div>
            <p class="job-summary" role="status" aria-live="polite"></p>
            <p class="device-errors"></p>
          </section>
        </div>
        <p class="status" role="status" aria-live="polite" aria-atomic="true"></p>
      </ha-card>`;
    const grid = this.shadowRoot.querySelector(".grid");
    grid.style.setProperty("--mode-count", Math.min(this._config.modes.length, 5));
    this._buttons = this._config.modes.map((mode, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.innerHTML = `<span class="top"><span class="number"></span>
        <svg viewBox="0 0 32 32" fill="none" aria-hidden="true" focusable="false">
          <path d="M3 29 29 3M19 3h10v10" stroke="currentColor" stroke-width="1.8" />
        </svg></span><span class="label"></span><span class="description"></span>`;
      button.querySelector(".number").textContent = `${String(index + 1).padStart(2, "0")} /`;
      button.querySelector(".label").textContent = mode.label;
      button.querySelector(".description").textContent = mode.description;
      button.addEventListener("click", () => this._select(index));
      grid.append(button);
      return button;
    });
    this._status = this.shadowRoot.querySelector(".status");
    this.shadowRoot.querySelectorAll("[data-control]").forEach(button => {
      button.addEventListener("click", () => this._control(button.dataset.control));
    });
    const volume = this.shadowRoot.querySelector("#volume");
    volume.addEventListener("input", () => { this.shadowRoot.querySelector("#volume-value").textContent = `${volume.value}%`; });
    volume.addEventListener("change", () => this._control("volume"));
  }

  _update() {
    if (!this._config || !this._buttons) return;
    const entity = this._hass?.states?.[this._config.entity];
    const unavailable = !entity || ["unknown", "unavailable"].includes(entity.state);
    const options = Array.isArray(entity?.attributes?.options) ? entity.attributes.options : [];
    const missing = this._config.modes.filter((mode) => !options.includes(mode.option));
    this._buttons.forEach((button, index) => {
      const mode = this._config.modes[index];
      const invalid = unavailable || !options.includes(mode.option);
      button.setAttribute("aria-pressed", String(!unavailable && entity.state === mode.option));
      button.disabled = invalid || !!this._request;
      button.classList.toggle("unavailable", invalid);
      button.title = invalid ? "Entità non disponibile oppure opzione assente nel select" : mode.label;
    });
    this.shadowRoot.querySelector(".grid").setAttribute("aria-busy", String(!!this._request));
    let message = "";
    if (!this._hass) message = "Connessione a Home Assistant…";
    else if (!entity) message = `Entità non trovata: ${this._config.entity}`;
    else if (unavailable) message = "Entità non disponibile.";
    else if (missing.length) message = `Opzioni assenti nel select: ${missing.map((mode) => mode.option).join(", ")}. Controlla il YAML.`;
    else if (!this._config.modes.some((mode) => mode.option === entity.state)) message = `Modalità corrente non mappata: ${entity.state}`;
    this._updateControls(entity, unavailable);
    this._status.textContent = this._error || (this._request ? "Invio comando…" : message);
  }

  _updateControls(entity, unavailable) {
    const root = this.shadowRoot;
    const attrs = entity?.attributes || {};
    const controls = attrs.control_entities || {};
    const visible = this._config.show_controls && Object.keys(controls).length > 0;
    root.querySelector(".controls").hidden = !visible;
    root.querySelector(".overview").hidden = !visible;
    if (!visible) return;
    const labels = { auto: "Automatico", showreel: "Video", photos: "Foto", black: "Schermo nero",
      meeting: "Riunione", custom: "Immagine", pdf: "PDF", slides: "Slides", video: "AirPlay video",
      audio: "AirPlay audio", idle: "Disponibile", pairing: "Connessione", starting: "Avvio" };
    root.querySelector(".content-summary").textContent = unavailable ? "Dispositivo non disponibile" : `Sullo schermo: ${labels[attrs.actual_content] || attrs.actual_content || "—"}`;
    root.querySelector(".airplay-summary").textContent = `AirPlay: ${unavailable ? "—" : (labels[attrs.airplay] || attrs.airplay || "—")}`;
    root.querySelector(".readiness-summary").textContent = unavailable ? "Stato non aggiornato" : (attrs.browser_ready && attrs.receiver_ready ? "Player e ricevitore pronti" : "Controlla player / ricevitore");
    const controlState = key => this._hass?.states?.[controls[key]];
    const disabled = key => unavailable || !!this._request || !controlState(key) || controlState(key).state === "unavailable";
    root.querySelectorAll("[data-control]").forEach(button => { button.disabled = disabled(button.dataset.control); });
    const volume = root.querySelector("#volume");
    volume.disabled = disabled("volume") || !Number.isFinite(Number(controlState("volume")?.state));
    if (root.activeElement !== volume) volume.value = Number(controlState("volume")?.state) || 0;
    root.querySelector("#volume-value").textContent = volume.disabled ? "—" : `${volume.value}%`;
    root.querySelector('[data-control="muted"]').setAttribute("aria-pressed", String(controlState("muted")?.state === "on"));
    const title = root.querySelector("#meeting-title");
    title.disabled = disabled("meeting_title");
    if (root.activeElement !== title) {
      const value = controlState("meeting_title")?.state;
      title.value = value && !["unknown", "unavailable"].includes(value) ? value : "";
    }
    const presentation = attrs.presentation;
    root.querySelector(".presentation-summary").textContent = presentation
      ? `${presentation.name || presentation.title || presentation.kind || "Presentazione"}${presentation.page ? ` · Pagina ${presentation.page}` : ""}`
      : "Nessuna presentazione aperta. Apri un PDF o Google Slides dal pannello.";
    const link = root.querySelector(".panel-link");
    link.hidden = true;
    try {
      const url = new URL(attrs.panel_url);
      if (url.protocol === "https:" && !url.username && !url.password) { link.href = url.href; link.hidden = false; }
    } catch { /* A standalone select may not provide a panel URL. */ }
    const jobs = Array.isArray(attrs.jobs) ? attrs.jobs : [];
    const statuses = { queued: "In coda", running: "In corso", succeeded: "Completata", failed: "Fallita", interrupted: "Interrotta" };
    const kinds = { refresh_showreel: "Aggiornamento video", refresh_photos: "Aggiornamento foto",
      sync_content: "Sincronizzazione contenuti", open_slides: "Apertura Slides", import_pdf: "Importazione PDF" };
    root.querySelector(".job-summary").textContent = jobs.length ? jobs.slice(-3).map(job =>
      `${kinds[job.kind] || "Attività"}: ${statuses[job.status] || job.status}${Number.isFinite(job.progress) ? ` · ${job.progress}%` : ""}${job.error ? ` — ${job.error}` : ""}`
    ).join("\n") : "Nessuna attività recente.";
    root.querySelector(".device-errors").textContent = Object.entries(attrs.errors || {}).map(([key, value]) => `${key}: ${value}`).join("\n");
  }

  async _control(key) {
    if (this._request || !this._config.show_controls) return;
    const entity = this._hass?.states?.[this._config.entity];
    if (!entity || ["unknown", "unavailable"].includes(entity.state)) return;
    const entityId = entity.attributes?.control_entities?.[key];
    const state = this._hass.states[entityId];
    if (!state || state.state === "unavailable") return;
    const expectedDomain = key === "volume" ? "number" : key === "muted" ? "switch" : key === "meeting_title" ? "text" : "button";
    if (typeof entityId !== "string" || !entityId.startsWith(`${expectedDomain}.`)) return;
    if (key === "release_screen" && !window.confirm("Interrompere la condivisione e tornare alla modalità Riunione?")) return;
    let service = "press";
    const data = { entity_id: entityId };
    if (key === "volume") { service = "set_value"; data.value = Number(this.shadowRoot.querySelector("#volume").value); }
    if (key === "meeting_title") { service = "set_value"; data.value = this.shadowRoot.querySelector("#meeting-title").value; }
    if (key === "muted") service = state.state === "on" ? "turn_off" : "turn_on";
    await this._call(expectedDomain, service, data);
  }

  async _select(index) {
    if (!this._hass || this._buttons[index].disabled) return;
    const option = this._config.modes[index].option;
    if (this._hass.states[this._config.entity]?.state === option) return;
    await this._call("select", "select_option", { entity_id: this._config.entity, option });
  }

  async _call(domain, service, data) {
    if (this._request) return;
    const request = {};
    this._request = request;
    this._error = "";
    this._update();
    try {
      await this._hass.callService(domain, service, data);
    } catch (error) {
      if (this._request === request) this._error = `Comando non riuscito: ${error?.message || String(error)}`;
    } finally {
      if (this._request === request) { this._request = null; this._update(); }
    }
  }
}

if (!customElements.get("showreel-mode-card")) {
  customElements.define("showreel-mode-card", ShowreelModeCard);
}
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "showreel-mode-card")) {
  window.customCards.push({
    type: "showreel-mode-card",
    name: "Showreel Mode Card",
    description: "Modalità, riunioni, audio e presentazioni del media center.",
  });
}
