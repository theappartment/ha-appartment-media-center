// Showreel Mode Card 1.0.0 — standalone Lovelace module, no build required.
const DEFAULT_MODES = [
  { label: "Automatico", option: "Automatico", description: "Ultimo showreel scelto in attesa. AirPlay quando ti colleghi." },
  { label: "Showreel video", option: "Showreel video", description: "Video in loop. AirPlay sempre disponibile." },
  { label: "Showreel foto", option: "Showreel foto", description: "Gli shooting in loop. AirPlay sempre disponibile." },
  { label: "Schermo nero", option: "Schermo nero", description: "Standby silenzioso. AirPlay sempre disponibile." },
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
    if (!Array.isArray(modes) || modes.length !== 4) {
      throw new Error("modes deve contenere esattamente quattro modalità.");
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
      return { ...DEFAULT_MODES[index], ...mode, label: mode.label ?? DEFAULT_MODES[index].label };
    });
    if (new Set(normalized.map((mode) => mode.option)).size !== 4) {
      throw new Error("Ogni modalità deve avere un valore option diverso.");
    }
    this._config = { entity: config.entity, modes: normalized };
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
          .grid { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
          button { min-height: 280px; padding: 30px; }
        }
        @container (min-width: 1600px) {
          ha-card { padding: 28px; }
          button { min-height: 330px; padding: 36px; }
          .label { font-size: 32px; } .description { font-size: 22px; }
          .number { font-size: 21px; } .top { margin-bottom: 48px; }
        }
        @media (prefers-reduced-motion: reduce) { button { transition: none; } }
      </style>
      <ha-card>
        <div class="grid" role="group" aria-label="Modalità schermo"></div>
        <p class="status" role="status" aria-live="polite" aria-atomic="true"></p>
      </ha-card>`;
    const grid = this.shadowRoot.querySelector(".grid");
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
    this._status.textContent = this._error || (this._request ? "Invio comando…" : message);
  }

  async _select(index) {
    if (!this._hass || this._buttons[index].disabled) return;
    const option = this._config.modes[index].option;
    if (this._hass.states[this._config.entity]?.state === option) return;
    const request = {};
    this._request = request;
    this._error = "";
    this._update();
    try {
      await this._hass.callService("select", "select_option", {
        entity_id: this._config.entity,
        option,
      });
    } catch (error) {
      if (this._request === request) {
        this._error = `Impossibile cambiare modalità: ${error?.message || String(error)}`;
      }
    } finally {
      // A late response from a previous YAML configuration must not affect this one.
      if (this._request === request) {
        this._request = null;
        this._update();
      }
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
    description: "Quattro modalità schermo controllate da un'entità select (configurazione YAML).",
  });
}
