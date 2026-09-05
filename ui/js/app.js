/**
 * PharmaPolySCOPE Physicochemical Input Generator
 * Streamlined & Focused Scientific Workstation Engine
 */

let allStoredRecords = [];
let allDrugs = [];
let allPolymers = [];

// Safe formatting utility
function safeFormat(val, fallback = "-") {
  if (val === null || val === undefined) return fallback;
  if (typeof val === "number") {
    return isNaN(val) ? fallback : String(val);
  }
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed === "" || trimmed.toLowerCase() === "null" || trimmed.toLowerCase() === "undefined") {
      return fallback;
    }
    return trimmed;
  }
  if (typeof val === "object") {
    if (val.value !== undefined && val.value !== null) {
      return safeFormat(val.value, fallback);
    }
    if (val.primary !== undefined && val.primary !== null) {
      return safeFormat(val.primary, fallback);
    }
    if (val.tm_K !== undefined && val.tm_K !== null) {
      return safeFormat(val.tm_K, fallback);
    }
    if (val.tg_K !== undefined && val.tg_K !== null) {
      return safeFormat(val.tg_K, fallback);
    }
    if (val.density_g_cm3 !== undefined && val.density_g_cm3 !== null) {
      return safeFormat(val.density_g_cm3, fallback);
    }
    if (val.note) {
      return val.note;
    }
    return fallback;
  }
  return String(val);
}

// QC Status badge generator
function renderQcBadge(status) {
  const s = (status || "APPROVED").toUpperCase();
  if (s === "APPROVED") return `<span class="badge badge-success"><span class="badge-dot"></span>APPROVED</span>`;
  if (s.includes("FLAG") || s === "BORDERLINE") return `<span class="badge badge-warning"><span class="badge-dot"></span>APPROVED W/ FLAGS</span>`;
  if (s.includes("REJECT") || s.includes("INVALID")) return `<span class="badge badge-error"><span class="badge-dot"></span>REJECTED</span>`;
  return `<span class="badge badge-info"><span class="badge-dot"></span>${s}</span>`;
}

// View title map for breadcrumbs
const viewTitleMap = {
  "workspace": "Overview & Action Center",
  "workstation": "Input Workstation",
  "library": "Entity Libraries",
  "output": "Ready Sheet & Output",
  "methodology": "Scientific User Manual & SOP Protocol"
};

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  loadAllWorkbenchData();
});

// Primary Navigation Switcher
function switchNav(viewName, subTabId = null) {
  document.querySelectorAll(".workspace-view").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".sidebar .nav-item").forEach(el => el.classList.remove("active"));

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) targetView.classList.add("active");

  const clickedItem = Array.from(document.querySelectorAll(".sidebar .nav-item")).find(b => b.getAttribute("onclick")?.includes(`'${viewName}'`));
  if (clickedItem) clickedItem.classList.add("active");

  const breadcrumbEl = document.getElementById("breadcrumb-active-view");
  if (breadcrumbEl) breadcrumbEl.innerText = viewTitleMap[viewName] || "Workspace";

  if (subTabId) {
    const parentContainer = document.getElementById(subTabId)?.parentElement?.id;
    if (parentContainer) {
      switchSubTab(parentContainer, subTabId);
    }
  }

  if (viewName === "workspace") loadAllWorkbenchData();
  if (viewName === "library") { renderDrugRegistry(); renderPolymerRegistry(); }
  if (viewName === "output") { populateReadyEntityDropdown(); }
}

// Sub-Tab Switcher
function switchSubTab(containerId, tabId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const viewSection = container.closest(".workspace-view");
  if (viewSection) {
    viewSection.querySelectorAll(".sub-tabs .sub-tab-btn").forEach(btn => {
      if (btn.getAttribute("onclick")?.includes(tabId)) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  container.querySelectorAll(".sub-tab-content").forEach(el => el.classList.remove("active"));
  const targetTab = document.getElementById(tabId);
  if (targetTab) targetTab.classList.add("active");

  if (tabId === "sub-ready-sheet") populateReadyEntityDropdown();
}

// -------------------------------------------------------------
// DATA LOADING & RENDERING
// -------------------------------------------------------------

async function loadAllWorkbenchData() {
  try {
    const qcRes = await fetch("/api/qc/summary");
    const qcSummary = await qcRes.json();

    const drugsRes = await fetch("/api/drugs");
    const drugsData = await drugsRes.json();
    allDrugs = drugsData.drugs || [];

    const polyRes = await fetch("/api/polymers");
    const polyData = await polyRes.json();
    allPolymers = polyData.polymers || [];

    allStoredRecords = [...allDrugs, ...allPolymers];

    // Update Counts
    const totalCountEl = document.getElementById("count-total-records");
    if (totalCountEl) totalCountEl.innerText = allStoredRecords.length;
    const libTotalEl = document.getElementById("count-library-total");
    if (libTotalEl) libTotalEl.innerText = allStoredRecords.length;

    // Status Summary Cards
    const qApprovedEl = document.getElementById("q-approved");
    if (qApprovedEl) qApprovedEl.innerText = qcSummary.approved_records;
    const qFlagsEl = document.getElementById("q-flags");
    if (qFlagsEl) qFlagsEl.innerText = qcSummary.approved_with_flags;
    const qRejectedEl = document.getElementById("q-rejected");
    if (qRejectedEl) qRejectedEl.innerText = qcSummary.rejected_records;
    const qReadyEl = document.getElementById("q-ready");
    if (qReadyEl) qReadyEl.innerText = allStoredRecords.length;

    // Render Tables
    renderSummaryTable();
    renderDrugRegistry();
    renderPolymerRegistry();

  } catch (err) {
    console.error("Failed to load workbench data:", err);
  }
}

function renderSummaryTable() {
  const tbody = document.querySelector("#summary-records-table tbody");
  if (!tbody) return;

  tbody.innerHTML = allStoredRecords.map(r => {
    const isDrug = r.entity_type === "drug";
    const tm = isDrug ? safeFormat(r.tm_K, "-") : "-";
    const tg = safeFormat(r.tg_K, "-");
    
    let dens;
    if (isDrug) {
      dens = safeFormat(r.density_g_cm3, "-");
    } else {
      const densVal = (typeof r.density_g_cm3 === 'object' && r.density_g_cm3 !== null) ? r.density_g_cm3.value : r.density_g_cm3;
      dens = (densVal !== null && densVal !== undefined && densVal !== "") ? safeFormat(densVal) : "Datasheet spec";
    }

    const dD = safeFormat(r.hsp_mpa_half?.delta_D || r.delta_D, "-");
    const dP = safeFormat(r.hsp_mpa_half?.delta_P || r.delta_P, "-");
    const dH = safeFormat(r.hsp_mpa_half?.delta_H || r.delta_H, "-");
    const hsp = (dD !== "-" && dP !== "-" && dH !== "-") ? `${dD} / ${dP} / ${dH}` : "-";

    const smiles = isDrug ? safeFormat(r.canonical_smiles, "-") : safeFormat(r.repeat_unit_smiles, "-");

    return `
      <tr onclick="viewReadySheetById('${r.entity_id}')" style="cursor: pointer;" title="View Manual Entry Sheet">
        <td class="font-mono" style="font-weight: 700; color: var(--color-primary-action);">${r.entity_id}</td>
        <td><span class="badge ${isDrug ? 'badge-calculated' : 'badge-mfg'}">${r.entity_type}</span></td>
        <td><strong>${r.name}</strong> ${r.abbreviation ? `<span style="color: var(--color-secondary-text);">(${r.abbreviation})</span>` : ''}</td>
        <td class="font-mono" style="max-width: 220px; overflow: hidden; text-overflow: ellipsis;">${smiles}</td>
        <td class="num-col">${tm !== '-' ? tm + '<span class="unit-tag">K</span>' : '-'}</td>
        <td class="num-col">${tg !== '-' ? tg + '<span class="unit-tag">K</span>' : '-'}</td>
        <td class="num-col">${dens !== '-' && dens !== 'Datasheet spec' ? dens + '<span class="unit-tag">g/cm³</span>' : dens}</td>
        <td class="font-mono">${hsp}</td>
        <td>${renderQcBadge(r.qc?.status)}</td>
      </tr>
    `;
  }).join("");
}

// -------------------------------------------------------------
// DRUG REGISTRY & PIPELINE A
// -------------------------------------------------------------

function renderDrugRegistry() {
  const tbody = document.querySelector("#drug-registry-table tbody");
  if (!tbody) return;

  tbody.innerHTML = allDrugs.map(d => `
    <tr onclick="viewReadySheetById('${d.entity_id}')" style="cursor: pointer;" title="View Manual Entry Sheet">
      <td class="font-mono" style="font-weight: 700; color: var(--color-primary-action);">${d.entity_id}</td>
      <td><strong>${d.name}</strong></td>
      <td class="font-mono" style="max-width: 180px; overflow: hidden; text-overflow: ellipsis;">${safeFormat(d.canonical_smiles)}</td>
      <td class="num-col">${safeFormat(d.mw)}</td>
      <td class="num-col">${safeFormat(d.tm_K)}</td>
      <td class="num-col">${safeFormat(d.tg_K)}</td>
      <td class="num-col">${safeFormat(d.density_g_cm3)}</td>
      <td class="num-col">${safeFormat(d.hsp_mpa_half?.delta_D || d.delta_D)}</td>
      <td class="num-col">${safeFormat(d.hsp_mpa_half?.delta_P || d.delta_P)}</td>
      <td class="num-col">${safeFormat(d.hsp_mpa_half?.delta_H || d.delta_H)}</td>
      <td class="num-col" style="font-weight: 700;">${safeFormat(d.hsp_mpa_half?.primary_total)}</td>
      <td class="num-col">${safeFormat(d.logP)}</td>
      <td class="num-col">${safeFormat(d.TPSA)}</td>
      <td><span class="badge badge-info">${safeFormat(d.BCS_class, 'II')}</span></td>
      <td>${renderQcBadge(d.qc?.status)}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="viewReadySheetById('${d.entity_id}')"><i class="fa-solid fa-file-lines"></i> Sheet</button>
        <button class="btn btn-danger btn-sm" onclick="deleteEntity('${d.entity_id}', 'drug')"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join("");
}

let smilesDebounceTimer = null;
function onSmilesInputLive() {
  clearTimeout(smilesDebounceTimer);
  const smiles = document.getElementById("drug-smiles").value.trim();
  if (!smiles) {
    document.getElementById("drug-svg-container").innerHTML = `<span style="color: var(--color-muted-text); font-size: 11px;">2D structure renders upon SMILES entry</span>`;
    return;
  }

  smilesDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/drugs/render_svg?smiles=${encodeURIComponent(smiles)}`);
      const data = await res.json();
      if (data.valid && data.svg) {
        document.getElementById("drug-svg-container").innerHTML = data.svg;
      } else {
        document.getElementById("drug-svg-container").innerHTML = `<span style="color: var(--color-warning); font-size: 11px;">Invalid or incomplete SMILES syntax</span>`;
      }
    } catch (e) {
      console.error("SVG render error:", e);
    }
  }, 250);
}

function quickSearch(term) {
  const input = document.getElementById("drug-search-input");
  if (input) {
    input.value = term;
    searchPubchemDrug();
  }
}

let lastFetchedPubchemData = null;

async function searchPubchemDrug() {
  const query = document.getElementById("drug-search-input").value.trim();
  if (!query) return;

  const statusEl = document.getElementById("drug-search-status");
  const previewBox = document.getElementById("pubchem-preview-box");
  const previewContent = document.getElementById("pubchem-preview-content");
  const previewTitle = document.getElementById("pubchem-preview-title");

  if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-primary-action);"><i class="fa-solid fa-spinner fa-spin"></i> Searching PubChem for "${query}"...</span>`;
  if (previewBox) previewBox.style.display = "none";

  const btn = document.querySelector("button[onclick='searchPubchemDrug()']");
  const origText = btn ? btn.innerHTML : "Search";
  if (btn) btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

  try {
    const res = await fetch(`/api/drugs/search_pubchem?query=${encodeURIComponent(query)}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = errData.detail || `Server error (${res.status})`;
      if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-error);"><i class="fa-solid fa-triangle-exclamation"></i> ${msg}</span>`;
      return;
    }

    const data = await res.json();
    if (data.found && data.data) {
      lastFetchedPubchemData = data.data;
      const p = data.data;
      if (statusEl) {
        statusEl.innerHTML = `<span style="color: var(--color-success); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Found in PubChem (CID: ${p.cid || 'N/A'})</span>`;
      }
      if (previewBox && previewContent) {
        let tmText = "Not reported in PubChem";
        if (p.experimental_tm_sources && p.experimental_tm_sources.length > 0) {
          tmText = p.experimental_tm_sources[0];
        }
        if (previewTitle) previewTitle.innerText = `${p.name || query} (CID: ${p.cid || 'N/A'})`;
        previewContent.innerHTML = `
          <strong>SMILES:</strong> <span class="font-mono" style="word-break: break-all;">${p.canonical_smiles || 'N/A'}</span><br>
          <strong>Literature Tm:</strong> ${tmText}<br>
          <strong>BCS Class:</strong> ${p.bcs_class || 'Class II (Default)'}
        `;
        previewBox.style.display = "block";
      }
    } else {
      const msg = data.message || `No matching records found in PubChem for "${query}"`;
      if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-warning);"><i class="fa-solid fa-triangle-exclamation"></i> ${msg}</span>`;
    }
  } catch (err) {
    console.error("Search error:", err);
    if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-error);"><i class="fa-solid fa-triangle-exclamation"></i> Search network error</span>`;
  } finally {
    if (btn) btn.innerHTML = origText;
  }
}

function transferPubchemDataToInputs() {
  if (!lastFetchedPubchemData) return;
  const p = lastFetchedPubchemData;
  document.getElementById("drug-name").value = p.name || "";
  document.getElementById("drug-smiles").value = p.canonical_smiles || "";
  document.getElementById("drug-cid").value = p.cid || "";
  if (p.bcs_class) {
    document.getElementById("drug-bcs").value = p.bcs_class;
  }
  if (p.experimental_tm_sources && p.experimental_tm_sources.length > 0) {
    document.getElementById("drug-tm-form").value = `PubChem experimental: ${p.experimental_tm_sources[0]}`;
    const match = p.experimental_tm_sources[0].match(/(\d+\.?\d*)/);
    if (match) {
      document.getElementById("drug-tm-c").value = match[1];
      updateTmFromC();
    }
  } else {
    document.getElementById("drug-tm-form").value = "";
    document.getElementById("drug-tm-c").value = "";
    document.getElementById("drug-tm-k").value = "";
  }

  const previewBox = document.getElementById("pubchem-preview-box");
  if (previewBox) previewBox.style.display = "none";

  calculateDrugLive();
}

function updateTmFromC() {
  const cVal = parseFloat(document.getElementById("drug-tm-c").value);
  if (!isNaN(cVal)) {
    document.getElementById("drug-tm-k").value = (cVal + 273.15).toFixed(2);
  }
}

function updateTmFromK() {
  const kVal = parseFloat(document.getElementById("drug-tm-k").value);
  if (!isNaN(kVal)) {
    document.getElementById("drug-tm-c").value = (kVal - 273.15).toFixed(2);
  }
}

async function calculateDrugLive() {
  const name = document.getElementById("drug-name").value.trim() || "Candidate Drug";
  const smiles = document.getElementById("drug-smiles").value.trim();
  const tmK = parseFloat(document.getElementById("drug-tm-k").value);
  const tmC = parseFloat(document.getElementById("drug-tm-c").value);
  const bcs = document.getElementById("drug-bcs").value;
  const cid = parseInt(document.getElementById("drug-cid").value) || null;
  const litDens = parseFloat(document.getElementById("drug-lit-density").value) || null;
  const seed = 42;

  if (!smiles) {
    alert("Please enter a canonical SMILES string.");
    return;
  }

  const payload = {
    name: name,
    smiles: smiles,
    tm_value_k: !isNaN(tmK) ? tmK : null,
    tm_value_c: !isNaN(tmC) ? tmC : null,
    bcs_class: bcs,
    pubchem_cid: cid,
    lit_pycnometric_density: litDens,
    seed: seed
  };

  try {
    const res = await fetch("/api/drugs/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      alert("Calculation error: " + (err.detail || "Invalid input"));
      return;
    }

    const data = await res.json();
    currentCalculatedDrug = data.calculated_record;

    const r = data.calculated_record;
    const hsp = r.hsp_mpa_half;
    const dual = data.dual_representation || {};

    const tgBase = dual.tg_K?.base_scalar ? safeFormat(dual.tg_K.base_scalar) : safeFormat(r.tg_K?.tg_K || r.tg_K);
    const tgUq = dual.tg_K?.uncertainty_str || "±21.0 K";
    const densBase = dual.density_g_cm3?.base_scalar ? safeFormat(dual.density_g_cm3.base_scalar) : safeFormat(r.density_g_cm3?.density_g_cm3 || r.density_g_cm3);
    const densUq = dual.density_g_cm3?.uncertainty_str || "±5.0%";
    const dDBase = dual.delta_D?.base_scalar ? safeFormat(dual.delta_D.base_scalar) : safeFormat(hsp.delta_D);
    const dDUq = dual.delta_D?.uncertainty_str || "±1.50 MPa½";
    const dPBase = dual.delta_P?.base_scalar ? safeFormat(dual.delta_P.base_scalar) : safeFormat(hsp.delta_P);
    const dPUq = dual.delta_P?.uncertainty_str || "±1.50 MPa½";
    const dHBase = dual.delta_H?.base_scalar ? safeFormat(dual.delta_H.base_scalar) : safeFormat(hsp.delta_H);
    const dHUq = dual.delta_H?.uncertainty_str || "±1.50 MPa½";
    const dtBase = dual.delta_t?.base_scalar ? safeFormat(dual.delta_t.base_scalar) : safeFormat(hsp.primary_total);
    const dtUq = dual.delta_t?.uncertainty_str || "±1.62 MPa½";

    const rBody = document.querySelector("#drug-calc-results-table tbody");
    rBody.innerHTML = `
      <tr class="clickable-param-row" onclick="inspectParameterDetails('mw')">
        <td><strong>Molecular Weight (MW)</strong></td>
        <td>
          <span class="val-cell-base">${safeFormat(r.mw)}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${safeFormat(r.mw)}', 'MW', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td><span class="val-cell-uq">Exact</span></td>
        <td>g/mol</td>
        <td class="font-mono">DESC-RDKIT-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('tm_K')">
        <td><strong>Melting Temp (Tm)</strong></td>
        <td>
          <span class="val-cell-base">${safeFormat(r.tm_K?.tm_K || r.tm_K)}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${safeFormat(r.tm_K?.tm_K || r.tm_K)}', 'Tm', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td><span class="val-cell-uq">Literature Spec</span></td>
        <td>K</td>
        <td class="font-mono">LIT-ACQ-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('tg_K')">
        <td><strong>Glass Transition (Tg)</strong></td>
        <td>
          <span class="val-cell-base">${tgBase}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${tgBase}', 'Tg', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>
          <span class="val-cell-uq">${tgUq}</span>
          <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${tgBase} ${tgUq}', 'Tg with UQ', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>K</td>
        <td class="font-mono">TG-RATIO-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('density_g_cm3')">
        <td><strong>Fedors Density (ρ)</strong></td>
        <td>
          <span class="val-cell-base">${densBase}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${densBase}', 'Density', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>
          <span class="val-cell-uq">${densUq}</span>
          <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${densBase} ${densUq}', 'Density with UQ', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>g/cm³</td>
        <td class="font-mono">DENS-FEDORS-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_D')">
        <td><strong>HSP Dispersion (δD)</strong></td>
        <td>
          <span class="val-cell-base">${dDBase}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dDBase}', 'delta_D', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>
          <span class="val-cell-uq">${dDUq}</span>
          <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dDBase} ${dDUq}', 'delta_D with UQ', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>MPa½</td>
        <td class="font-mono">HSP-HVK-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_P')">
        <td><strong>HSP Polar (δP)</strong></td>
        <td>
          <span class="val-cell-base">${dPBase}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dPBase}', 'delta_P', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>
          <span class="val-cell-uq">${dPUq}</span>
          <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dPBase} ${dPUq}', 'delta_P with UQ', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>MPa½</td>
        <td class="font-mono">HSP-HVK-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_H')">
        <td><strong>HSP Hydrogen-Bond (δH)</strong></td>
        <td>
          <span class="val-cell-base">${dHBase}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dHBase}', 'delta_H', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>
          <span class="val-cell-uq">${dHUq}</span>
          <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dHBase} ${dHUq}', 'delta_H with UQ', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>MPa½</td>
        <td class="font-mono">HSP-HVK-01</td>
      </tr>
      <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_t')">
        <td><strong>Total Solubility (δt)</strong></td>
        <td>
          <span class="val-cell-base" style="color: var(--color-primary-action);">${dtBase}</span>
          <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dtBase}', 'delta_t', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>
          <span class="val-cell-uq">${dtUq}</span>
          <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dtBase} ${dtUq}', 'delta_t with UQ', this)"><i class="fa-regular fa-copy"></i></button>
        </td>
        <td>MPa½</td>
        <td class="font-mono">HSP-HVK-01</td>
      </tr>
    `;

    const qcBadge = document.getElementById("drug-qc-badge");
    if (qcBadge && data.qc?.status) {
      qcBadge.innerText = data.qc.status;
      qcBadge.className = `badge ${data.qc.status === 'APPROVED' ? 'badge-success' : (data.qc.status.includes('flags') ? 'badge-warning' : 'badge-error')}`;
      qcBadge.style.display = 'inline-block';
    }

    // Render Table 2: 10,000-Run Monte Carlo Uncertainty Quantification & Final Single Values
    const uqBody = document.querySelector("#drug-uq-calc-table tbody");
    if (uqBody && data.uncertainty_table) {
      uqBody.innerHTML = data.uncertainty_table.map(row => `
        <tr class="clickable-param-row" onclick="inspectParameterDetails('${row.param_key}')">
          <td><strong>${row.name}</strong></td>
          <td class="font-mono">${row.nominal_base}</td>
          <td style="font-size: 11px; color: var(--color-secondary-text);">${row.distribution_type}</td>
          <td class="font-mono" style="color: #B45309;">${row.uncertainty_1sigma}</td>
          <td class="font-mono" style="font-size: 11px;">${row.ci_95_str}</td>
          <td>
            <span class="val-cell-base" style="color: var(--color-primary-action);">${row.final_value}</span>
            <button class="copy-mini-btn" title="Copy Final Single Value for PharmaPolySCOPE" onclick="event.stopPropagation(); copyScalarValue('${row.final_value}', '${row.name}', this)"><i class="fa-solid fa-copy"></i></button>
          </td>
          <td>${row.unit}</td>
        </tr>
      `).join("");
    }

    renderQCDiagnosticCards(data.qc?.diagnostics, "drug-qc-diagnostics-container");

    if (data.svg) {
      document.getElementById("drug-svg-container").innerHTML = data.svg;
    }

    const gBody = document.querySelector("#drug-groups-table tbody");
    if (gBody) {
      gBody.innerHTML = (data.hvk_breakdown || []).map(g => `
        <tr>
          <td><strong>${g.group}</strong></td>
          <td class="num-col">${g.count}</td>
          <td class="num-col">${g.delta_u_each !== undefined && g.delta_u_each !== null ? g.delta_u_each : '-'}</td>
          <td class="num-col">${g.delta_v_each || g.V || '-'}</td>
          <td class="num-col">${g.Fd ? g.Fd : '-'}</td>
          <td class="num-col">${g.Fp ? g.Fp : '-'}</td>
          <td class="num-col">${g.Eh ? g.Eh : '-'}</td>
        </tr>
      `).join("");
    }

  } catch (err) {
    console.error("Live calculation failed:", err);
  }
}

function copyScalarValue(val, label, btnElement) {
  if (!val || val === "-") return;
  navigator.clipboard.writeText(val).then(() => {
    const origHtml = btnElement.innerHTML;
    btnElement.innerHTML = `<i class="fa-solid fa-check" style="color: var(--color-success);"></i>`;
    btnElement.style.borderColor = "var(--color-success)";
    setTimeout(() => {
      btnElement.innerHTML = origHtml;
      btnElement.style.borderColor = "";
    }, 1200);
  }).catch(err => {
    console.error("Clipboard copy failed:", err);
  });
}

function renderQCDiagnosticCards(diagnostics, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!diagnostics || diagnostics.length === 0) {
    container.innerHTML = `
      <div class="qc-diagnostic-card info" style="background: #F0FDF4; border-left: 4px solid var(--color-success);">
        <div class="qc-diag-header">
          <div class="qc-diag-title" style="color: var(--color-success); font-weight: 700;">
            <i class="fa-solid fa-circle-check"></i> Quality Control Clean Pass
          </div>
          <span class="qc-diag-code">QC-PASS-100</span>
        </div>
        <div class="qc-rationale-text" style="color: #15803D; font-size: 11px;">
          All physical parameters, group contributions, and thermodynamic ratios comply strictly with standard pharmaceutical distributions and the 13-step SOP battery.
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = diagnostics.map(d => {
    const sevClass = d.severity === 'ERROR' ? 'error' : (d.severity === 'WARNING' ? 'warning' : 'info');
    const sevIcon = d.severity === 'ERROR' ? 'fa-shield-halved' : (d.severity === 'WARNING' ? 'fa-triangle-exclamation' : 'fa-circle-info');
    const motifHtml = d.molecular_motif ? `<div class="qc-motif-tag"><i class="fa-solid fa-atom"></i> ${d.molecular_motif}</div>` : '';
    
    let actionBtnHtml = '';
    if (d.action_type === 'RUN_MC') {
      actionBtnHtml = `<button class="qc-action-btn" onclick="switchTab('screen-tab'); triggerAutoSensitivity();"><i class="fa-solid fa-chart-line"></i> ${d.action_label || 'Launch Monte Carlo UQ'}</button>`;
    } else if (d.action_type === 'STRIP_SALT') {
      actionBtnHtml = `<button class="qc-action-btn" onclick="autoStripSalt()"><i class="fa-solid fa-wand-magic-sparkles"></i> Strip Salt</button>`;
    } else if (d.action_type === 'CONVERT_KELVIN') {
      actionBtnHtml = `<button class="qc-action-btn" onclick="updateTmFromC(); calculateDrugLive();"><i class="fa-solid fa-temperature-arrow-up"></i> ${d.action_label || 'Convert to Kelvin'}</button>`;
    } else if (d.action_type === 'INSPECT_GROUPS') {
      actionBtnHtml = `<button class="qc-action-btn" onclick="document.querySelector('#drug-view details').open = true;"><i class="fa-solid fa-layer-group"></i> Inspect Groups</button>`;
    } else if (d.action_type === 'SWITCH_TO_POLYMER_TAB') {
      actionBtnHtml = `<button class="qc-action-btn" onclick="switchTab('poly-tab')"><i class="fa-solid fa-shapes"></i> Switch to Pipeline B</button>`;
    } else if (d.action_type === 'FOCUS_INPUT') {
      actionBtnHtml = `<button class="qc-action-btn" onclick="document.getElementById('drug-tm-c').focus();"><i class="fa-solid fa-pen-to-square"></i> Enter Value</button>`;
    }

    return `
      <div class="qc-diagnostic-card ${sevClass}">
        <div class="qc-diag-header">
          <div class="qc-diag-title">
            <i class="fa-solid ${sevIcon}"></i> ${d.title}
          </div>
          <span class="qc-diag-code">${d.code}</span>
        </div>

        <div class="qc-metric-strip">
          <div class="qc-metric-chip">
            <span class="qc-metric-label">Observed:</span>
            <span class="qc-metric-val">${d.observed_value}</span>
          </div>
          <span style="color: var(--color-border-subtle);">|</span>
          <div class="qc-metric-chip">
            <span class="qc-metric-label">Standard Range:</span>
            <span class="qc-metric-val">${d.expected_threshold}</span>
          </div>
          <span style="color: var(--color-border-subtle);">|</span>
          <div class="qc-metric-chip" style="color: ${d.severity === 'ERROR' ? 'var(--color-error)' : 'var(--color-warning)'};">
            <span class="qc-metric-label">Delta:</span>
            <span>${d.delta_description}</span>
          </div>
        </div>

        ${motifHtml}

        <div class="qc-rationale-text">
          <strong>Scientific Rationale:</strong> ${d.scientific_rationale}
        </div>

        <div class="qc-impact-box">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <span><strong>Screening Impact:</strong> ${d.screening_impact}</span>
        </div>

        <div class="qc-remediation-box">
          <div class="qc-remediation-text">
            <strong>Remediation:</strong> ${d.remediation_guidance}
          </div>
          ${actionBtnHtml}
        </div>
      </div>
    `;
  }).join("");
}

async function saveCurrentDrug(forceDistinct = false) {
  if (!currentCalculatedDrug) {
    await calculateDrugLive();
  }
  if (!currentCalculatedDrug) return;

  const r = currentCalculatedDrug;
  const payload = {
    name: r.name,
    canonical_smiles: r.canonical_smiles,
    tm_K: r.tm_K.tm_K || r.tm_K.value || r.tm_K,
    tm_form: r.tm_K.form || "form I (stable at 25 C)",
    tg_K: r.tg_K.tg_K || r.tg_K.value || r.tg_K,
    density_g_cm3: r.density_g_cm3.density_g_cm3 || r.density_g_cm3.value || r.density_g_cm3,
    delta_D: r.hsp_mpa_half.delta_D,
    delta_P: r.hsp_mpa_half.delta_P,
    delta_H: r.hsp_mpa_half.delta_H,
    logP: r.logP,
    TPSA: r.TPSA,
    HBD: r.HBD,
    HBA: r.HBA,
    BCS_class: r.BCS_class || "II",
    pubchem_cid: parseInt(document.getElementById("drug-cid").value) || null,
    force_distinct: forceDistinct
  };

  try {
    const res = await fetch("/api/drugs/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.duplicate_detected) {
      const choice = prompt(
        `DUPLICATE RECORD DETECTED\n\nExisting record:\n${result.existing_record.entity_id} — ${result.existing_record.name}\n\nOptions:\n1: Open existing record\n2: Create intentionally distinct version\n3: Cancel`,
        "1"
      );
      if (choice === "1") {
        viewReadySheetById(result.existing_record.entity_id);
      } else if (choice === "2") {
        saveCurrentDrug(true);
      }
      return;
    }

    if (result.success) {
      alert(`Drug ${result.entity_id} saved successfully with status: ${result.qc.status}`);
      loadAllWorkbenchData();
      switchNav("library", "sub-drug-lib");
    }
  } catch (err) {
    console.error("Save error:", err);
  }
}

// -------------------------------------------------------------
// POLYMER REGISTRY & PIPELINE B
// -------------------------------------------------------------

function renderPolymerRegistry() {
  const tbody = document.querySelector("#polymer-registry-table tbody");
  if (!tbody) return;

  tbody.innerHTML = allPolymers.map(p => {
    const densVal = (typeof p.density_g_cm3 === 'object' && p.density_g_cm3 !== null) ? p.density_g_cm3.value : p.density_g_cm3;
    const dens = (densVal !== null && densVal !== undefined && densVal !== "") ? safeFormat(densVal) : "Datasheet spec";
    const hsp = p.hsp_mpa_half || {};

    return `
      <tr onclick="viewReadySheetById('${p.entity_id}')" style="cursor: pointer;" title="View Manual Entry Sheet">
        <td class="font-mono" style="font-weight: 700; color: var(--color-tag-mfg);">${p.entity_id}</td>
        <td><strong>${p.name}</strong></td>
        <td><span class="badge badge-mfg">${p.abbreviation || p.grade?.grade || 'Grade Spec'}</span></td>
        <td class="font-mono" style="max-width: 180px; overflow: hidden; text-overflow: ellipsis;">${safeFormat(p.repeat_unit_smiles)}</td>
        <td class="num-col">${safeFormat(p.mn, 'Grade spec')}</td>
        <td class="num-col">${safeFormat(p.tg_K)}</td>
        <td class="num-col">${dens}</td>
        <td class="num-col">${safeFormat(hsp.delta_D || p.delta_D)}</td>
        <td class="num-col">${safeFormat(hsp.delta_P || p.delta_P)}</td>
        <td class="num-col">${safeFormat(hsp.delta_H || p.delta_H)}</td>
        <td class="num-col" style="font-weight: 700;">${safeFormat(hsp.tabulated_total || hsp.recomputed_total)}</td>
        <td>${renderQcBadge(p.qc?.status)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewReadySheetById('${p.entity_id}')"><i class="fa-solid fa-file-lines"></i> Sheet</button>
          <button class="btn btn-danger btn-sm" onclick="deleteEntity('${p.entity_id}', 'polymer')"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>
    `;
  }).join("");
}

let lastFetchedPolymerPubchemData = null;

async function searchPubchemPolymer() {
  const query = document.getElementById("poly-pubchem-query")?.value.trim();
  const statusEl = document.getElementById("poly-search-status");
  const previewBox = document.getElementById("poly-pubchem-preview-box");
  const previewTitle = document.getElementById("poly-pubchem-preview-title");
  const previewContent = document.getElementById("poly-pubchem-preview-content");

  if (!query) {
    if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-error);"><i class="fa-solid fa-triangle-exclamation"></i> Please enter a polymer name or PubChem CID</span>`;
    return;
  }

  if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-primary-action);"><i class="fa-solid fa-spinner fa-spin"></i> Searching PubChem database...</span>`;
  if (previewBox) previewBox.style.display = "none";

  try {
    const res = await fetch(`/api/polymers/search_pubchem?query=${encodeURIComponent(query)}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || "PubChem query failed.";
      if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-error);"><i class="fa-solid fa-triangle-exclamation"></i> ${msg}</span>`;
      return;
    }

    const data = await res.json();
    if (data.found && data.data) {
      lastFetchedPolymerPubchemData = data.data;
      const p = data.data;
      if (statusEl) {
        statusEl.innerHTML = `<span style="color: var(--color-success); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Found in PubChem (CID: ${p.cid || 'N/A'})</span>`;
      }
      if (previewBox && previewContent) {
        if (previewTitle) previewTitle.innerText = `${p.name || query} (CID: ${p.cid || 'N/A'})`;
        previewContent.innerHTML = `
          <strong>SMILES / Repeat:</strong> <span class="font-mono" style="word-break: break-all;">${p.canonical_smiles || 'N/A'}</span><br>
          <strong>Formula / IUPAC:</strong> ${p.iupac_name || p.formula || 'N/A'}
        `;
        previewBox.style.display = "block";
      }
    } else {
      const msg = data.message || `No matching records found in PubChem for "${query}"`;
      if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-warning);"><i class="fa-solid fa-triangle-exclamation"></i> ${msg}</span>`;
    }
  } catch (err) {
    console.error("Polymer search error:", err);
    if (statusEl) statusEl.innerHTML = `<span style="color: var(--color-error);"><i class="fa-solid fa-triangle-exclamation"></i> Search network error</span>`;
  }
}

function transferPubchemDataToPolymerInputs() {
  if (!lastFetchedPolymerPubchemData) return;
  const p = lastFetchedPolymerPubchemData;
  if (document.getElementById("poly-name")) document.getElementById("poly-name").value = p.name || "";
  if (document.getElementById("poly-repeat-smiles")) document.getElementById("poly-repeat-smiles").value = p.canonical_smiles || "";

  const previewBox = document.getElementById("poly-pubchem-preview-box");
  if (previewBox) previewBox.style.display = "none";

  calculatePolymerLive();
}

function syncPolymerTg(source) {
  const cEl = document.getElementById("poly-tg-c");
  const kEl = document.getElementById("poly-tg-k");
  if (!cEl || !kEl) return;
  if (source === "C") {
    const cVal = parseFloat(cEl.value);
    if (!isNaN(cVal)) {
      kEl.value = (cVal + 273.15).toFixed(1);
    }
  } else {
    const kVal = parseFloat(kEl.value);
    if (!isNaN(kVal)) {
      cEl.value = (kVal - 273.15).toFixed(1);
    }
  }
}

async function calculatePolymerLive() {
  const name = document.getElementById("poly-name")?.value.trim() || "Custom Polymer";
  const smiles = document.getElementById("poly-repeat-smiles")?.value.trim();
  const tgK = parseFloat(document.getElementById("poly-tg-k")?.value) || null;
  const tgC = parseFloat(document.getElementById("poly-tg-c")?.value) || null;
  const density = parseFloat(document.getElementById("poly-density")?.value) || 0.40;
  const seed = 42;

  if (!smiles) {
    alert("Please enter the Polymer Repeat-Unit SMILES (e.g. *CC(*)N1CCCC1=O) to calculate properties.");
    return;
  }

  const payload = {
    name: name,
    repeat_unit_smiles: smiles,
    tg_value_k: tgK,
    tg_value_c: tgC,
    density_g_cm3: density,
    seed: seed
  };

  try {
    const res = await fetch("/api/polymers/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;

    const data = await res.json();
    const dual = data.dual_representation || {};

    const tgBase = dual.tg_K?.base_scalar !== null && dual.tg_K?.base_scalar !== undefined ? dual.tg_K.base_scalar : '-';
    const tgUq = dual.tg_K?.uncertainty_str || '-';
    const densBase = dual.density_g_cm3?.base_scalar !== null && dual.density_g_cm3?.base_scalar !== undefined ? dual.density_g_cm3.base_scalar : '-';
    const densUq = dual.density_g_cm3?.uncertainty_str || '-';
    const dDBase = dual.delta_D?.base_scalar !== null && dual.delta_D?.base_scalar !== undefined ? dual.delta_D.base_scalar : '-';
    const dDUq = dual.delta_D?.uncertainty_str || '-';
    const dPBase = dual.delta_P?.base_scalar !== null && dual.delta_P?.base_scalar !== undefined ? dual.delta_P.base_scalar : '-';
    const dPUq = dual.delta_P?.uncertainty_str || '-';
    const dHBase = dual.delta_H?.base_scalar !== null && dual.delta_H?.base_scalar !== undefined ? dual.delta_H.base_scalar : '-';
    const dHUq = dual.delta_H?.uncertainty_str || '-';
    const dtBase = dual.delta_t?.base_scalar !== null && dual.delta_t?.base_scalar !== undefined ? dual.delta_t.base_scalar : '-';
    const dtUq = dual.delta_t?.uncertainty_str || '-';

    const pBody = document.querySelector("#poly-calc-results-table tbody");
    if (pBody) {
      pBody.innerHTML = `
        <tr class="clickable-param-row" onclick="inspectParameterDetails('poly_tg')">
          <td><strong>Glass Transition (Tg)</strong></td>
          <td>
            <span class="val-cell-base">${tgBase}</span>
            <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${tgBase}', 'Polymer Tg', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>
            <span class="val-cell-uq">${tgUq}</span>
            <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${tgBase} ${tgUq}', 'Polymer Tg with UQ', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>K</td>
          <td>DSC / User Input</td>
        </tr>
        <tr class="clickable-param-row" onclick="inspectParameterDetails('density_g_cm3')">
          <td><strong>Polymer Density (ρ)</strong></td>
          <td>
            <span class="val-cell-base">${densBase}</span>
            <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${densBase}', 'Density', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>
            <span class="val-cell-uq">${densUq}</span>
            <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${densBase} ${densUq}', 'Density with UQ', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>g/cm³</td>
          <td>Manufacturer / User Spec</td>
        </tr>
        <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_D')">
          <td><strong>HSP Dispersion (δD)</strong></td>
          <td>
            <span class="val-cell-base">${dDBase}</span>
            <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dDBase}', 'δD', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>
            <span class="val-cell-uq">${dDUq}</span>
            <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dDBase} ${dDUq}', 'δD with UQ', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>MPa½</td>
          <td>Hoftyzer–van Krevelen (1990)</td>
        </tr>
        <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_P')">
          <td><strong>HSP Polar (δP)</strong></td>
          <td>
            <span class="val-cell-base">${dPBase}</span>
            <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dPBase}', 'δP', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>
            <span class="val-cell-uq">${dPUq}</span>
            <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dPBase} ${dPUq}', 'δP with UQ', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>MPa½</td>
          <td>Hoftyzer–van Krevelen (1990)</td>
        </tr>
        <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_H')">
          <td><strong>HSP Hydrogen-Bond (δH)</strong></td>
          <td>
            <span class="val-cell-base">${dHBase}</span>
            <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dHBase}', 'δH', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>
            <span class="val-cell-uq">${dHUq}</span>
            <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dHBase} ${dHUq}', 'δH with UQ', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>MPa½</td>
          <td>Hoftyzer–van Krevelen (1990)</td>
        </tr>
        <tr class="clickable-param-row" onclick="inspectParameterDetails('delta_t')">
          <td><strong>Total Solubility (δt)</strong></td>
          <td>
            <span class="val-cell-base" style="color: var(--color-primary-action);">${dtBase}</span>
            <button class="copy-mini-btn" title="Copy base value" onclick="event.stopPropagation(); copyScalarValue('${dtBase}', 'δt', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>
            <span class="val-cell-uq">${dtUq}</span>
            <button class="copy-mini-btn" title="Copy with uncertainty" onclick="event.stopPropagation(); copyScalarValue('${dtBase} ${dtUq}', 'δt with UQ', this)"><i class="fa-regular fa-copy"></i></button>
          </td>
          <td>MPa½</td>
          <td>Vector Norm √(δD² + δP² + δH²)</td>
        </tr>
      `;
    }

    // Render Polymer Table 2: 10k Monte Carlo UQ Table
    const pUqBody = document.querySelector("#poly-uq-calc-table tbody");
    if (pUqBody && data.uncertainty_table) {
      pUqBody.innerHTML = data.uncertainty_table.map(row => `
        <tr class="clickable-param-row" onclick="inspectParameterDetails('${row.param_key}')">
          <td><strong>${row.name}</strong></td>
          <td class="font-mono">${row.nominal_base}</td>
          <td style="font-size: 11px; color: var(--color-secondary-text);">${row.distribution_type}</td>
          <td class="font-mono" style="color: #B45309;">${row.uncertainty_1sigma}</td>
          <td class="font-mono" style="font-size: 11px;">${row.ci_95_str}</td>
          <td>
            <span class="val-cell-base" style="color: var(--color-primary-action);">${row.final_value}</span>
            <button class="copy-mini-btn" title="Copy Final Single Value for PharmaPolySCOPE" onclick="event.stopPropagation(); copyScalarValue('${row.final_value}', '${row.name}', this)"><i class="fa-solid fa-copy"></i></button>
          </td>
          <td>${row.unit}</td>
        </tr>
      `).join("");
    }

  } catch (err) {
    console.error("Polymer calculation error:", err);
  }
}

async function saveCurrentPolymer(forceDistinct = false) {
  const name = document.getElementById("poly-name")?.value.trim() || "Custom Polymer";
  const smiles = document.getElementById("poly-repeat-smiles")?.value.trim() || "*CC(*)N1CCCC1=O";
  const tgK = parseFloat(document.getElementById("poly-tg-k")?.value) || null;
  const tgC = parseFloat(document.getElementById("poly-tg-c")?.value) || null;
  const density = parseFloat(document.getElementById("poly-density")?.value) || 0.40;
  const seed = 42;

  const payload = {
    name: name,
    repeat_unit_smiles: smiles,
    tg_value_k: tgK,
    tg_value_c: tgC,
    custom_bulk_density: density,
    force_distinct: forceDistinct,
    seed: seed
  };

  try {
    const res = await fetch("/api/polymers/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.success) {
      alert(`Polymer ${result.entity_id} (${name}) saved successfully.`);
      loadAllWorkbenchData();
      switchNav("library", "sub-poly-lib");
    }
  } catch (err) {
    console.error("Polymer save error:", err);
  }
}

// -------------------------------------------------------------
// PHARMAPOLYSCOPE READY MANUAL ENTRY SHEET
// -------------------------------------------------------------

function populateReadyEntityDropdown() {
  const select = document.getElementById("ready-entity-select");
  if (!select) return;

  select.innerHTML = allStoredRecords.map(r => `
    <option value="${r.entity_id}">${r.name} (${r.entity_id} — ${r.entity_type.toUpperCase()})</option>
  `).join("");

  if (allStoredRecords.length > 0) {
    loadReadySheet();
  }
}

function viewReadySheetById(entityId) {
  switchNav("output", "sub-ready-sheet");
  setTimeout(() => {
    const sel = document.getElementById("ready-entity-select");
    if (sel) {
      sel.value = entityId;
      loadReadySheet();
    }
  }, 100);
}

function viewReadySheetForCurrent(type) {
  if (type === "DRG" && currentCalculatedDrug) {
    saveCurrentDrug().then(() => {
      viewReadySheetById(currentCalculatedDrug.entity_id || "DRG-0001");
    });
  } else if (type === "POL" && currentCalculatedPolymer) {
    saveCurrentPolymer().then(() => {
      viewReadySheetById(currentCalculatedPolymer.entity_id || "POL-0001");
    });
  }
}

let currentLoadedReadySheet = null;

async function loadReadySheet() {
  const select = document.getElementById("ready-entity-select");
  if (!select) return;
  const entityId = select.value;
  if (!entityId) return;

  try {
    const res = await fetch(`/api/export/pharmapolyscope_ready/${entityId}`);
    const sheet = await res.json();
    currentLoadedReadySheet = sheet;

    const container = document.getElementById("ready-sheet-render-container");
    
    // Group fields by category
    const categoryOrder = [
      "Chemical Identity & Descriptors",
      "Polymer Identity & Specification",
      "Thermal & Physical Properties",
      "Hansen Solubility Parameters (HSP)"
    ];
    
    const groups = {};
    sheet.fields.forEach(f => {
      const cat = f.category || "General Properties";
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(f);
    });

    const sortedCategories = Object.keys(groups).sort((a, b) => {
      let idxA = categoryOrder.indexOf(a);
      let idxB = categoryOrder.indexOf(b);
      if (idxA === -1) idxA = 99;
      if (idxB === -1) idxB = 99;
      return idxA - idxB;
    });

    let tableRowsHtml = "";
    sortedCategories.forEach(catName => {
      tableRowsHtml += `
        <tr>
          <td colspan="6" class="ready-category-header">
            <i class="fa-solid fa-layer-group"></i> ${catName}
          </td>
        </tr>
      `;

      groups[catName].forEach(f => {
        const baseVal = safeFormat(f.base_value !== undefined ? f.base_value : f.value, "-");
        const finalVal = safeFormat(f.final_value !== undefined ? f.final_value : f.value, "-");
        const paramKey = f.key || "";
        const isSmiles = paramKey.includes("smiles");
        const isNumeric = !isSmiles && (typeof f.value === 'number' || typeof f.base_value === 'number' || (!isNaN(parseFloat(baseVal)) && !String(baseVal).includes('-') && !String(baseVal).includes(' ')));

        let ciDisplay = f.uncertainty_str || "-";
        if (f.ci_95 && Array.isArray(f.ci_95)) {
          ciDisplay = `<span>${f.uncertainty_str || ''}</span> <span class="ci-bracket" style="font-size: 9px; color: #64748B; font-weight: 500; white-space: nowrap;">[${f.ci_95[0]}–${f.ci_95[1]}]</span>`;
        }

        tableRowsHtml += `
          <tr>
            <td style="cursor: pointer;" onclick="inspectParameterDetails('${paramKey}')" title="Click to view governing scientific formula">
              <strong style="color: var(--color-primary-action); font-size: 11px;">${f.label}</strong>
            </td>
            <td class="val-cell ${isNumeric ? 'val-numeric' : ''}">
              <div class="ready-cell-wrap ${isNumeric ? 'wrap-numeric' : ''}">
                ${isSmiles ? `<span class="ready-code-box">${baseVal}</span>` : `<span style="font-weight: 600;">${baseVal}</span>`}
                ${baseVal !== '-' ? `<button class="ready-cell-copy" onclick="copyReadyParamValue('${baseVal}', '${f.label} (Base)')" title="Copy Base Nominal Value"><i class="fa-regular fa-copy"></i></button>` : ''}
              </div>
            </td>
            <td class="val-cell val-cell-final ${isNumeric ? 'val-numeric' : ''}">
              <div class="ready-cell-wrap ${isNumeric ? 'wrap-numeric' : ''}">
                ${isSmiles ? `<span class="ready-code-box" style="color: #1D4ED8;">${finalVal}</span>` : `<span style="font-weight: 700; color: #1D4ED8;">${finalVal}</span>`}
                ${finalVal !== '-' ? `<button class="ready-cell-copy" style="background: var(--color-primary-action); color: #FFF; border-color: var(--color-primary-action);" onclick="copyReadyParamValue('${finalVal}', '${f.label} (Final)')" title="Copy 10k MC Final Converged Value"><i class="fa-solid fa-copy"></i></button>` : ''}
              </div>
            </td>
            <td style="font-size: 10.5px; overflow-wrap: anywhere;">${ciDisplay}</td>
            <td><strong>${f.unit || '-'}</strong></td>
            <td style="text-align: center;"><span class="badge badge-calculated" style="font-size: 8.5px; padding: 1.5px 5px; display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: middle;" title="${f.provenance || ''}">${f.method_id || 'COMPUTED'}</span></td>
          </tr>
        `;
      });
    });

    container.innerHTML = `
      <div class="ready-sheet-container">
        <div class="ready-sheet-header-box">
          <div class="ready-sheet-header-left">
            <div class="ready-sheet-super-title">${sheet.title || "PHARMAPOLYSCOPE: MANUAL ENTRY SHEET"}</div>
            <div class="ready-sheet-sub-title">${sheet.subtitle || sheet.name}</div>
            <div class="ready-sheet-meta-row">
              <span><strong>Identifier:</strong> <span style="font-family: var(--font-mono); font-weight: 700; color: #0284C7;">${sheet.entity_id}</span></span>
              <span style="color: #CBD5E1;">|</span>
              <span><strong>Class:</strong> <span class="badge ${sheet.entity_type === 'drug' ? 'badge-calculated' : 'badge-mfg'}" style="font-size: 9.5px; padding: 2px 7px;">${sheet.entity_type.toUpperCase()}</span></span>
            </div>
          </div>
          <div class="ready-sheet-header-right">
            <span class="ready-status-pill"><i class="fa-solid fa-circle-check"></i> ${sheet.qc_status || "READY FOR ENTRY"}</span>
          </div>
        </div>

        <div class="ready-instructions-bar">
          <div>
            <i class="fa-solid fa-circle-info"></i>
            <strong>PharmaPolySCOPE Manual Entry Guide:</strong>
            Grouped authoritative parameters with dual representations. Use cell copy buttons or top toolbar exports to transcribe directly.
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="ready-cell-copy" onclick="copyReadyAllNominal()"><i class="fa-solid fa-copy"></i> Copy Nominal Base</button>
            <button class="ready-cell-copy" style="background: var(--color-primary-action); color: #FFF; border-color: var(--color-primary-action);" onclick="copyReadyAllFinal()"><i class="fa-solid fa-check"></i> Copy Converged Final</button>
          </div>
        </div>

        <table class="ready-sheet-table">
          <colgroup>
            <col style="width: 23%;">
            <col style="width: 17%;">
            <col style="width: 18%;">
            <col style="width: 19%;">
            <col style="width: 8%;">
            <col style="width: 15%;">
          </colgroup>
          <thead>
            <tr>
              <th>Parameter</th>
              <th class="th-numeric">Nominal Base (Before UQ)</th>
              <th class="th-numeric">10k MC Final (After UQ)</th>
              <th>Uncertainty (95% CI)</th>
              <th>Unit</th>
              <th style="text-align: center;">Method</th>
            </tr>
          </thead>
          <tbody>
            ${tableRowsHtml}
          </tbody>
        </table>

        <div class="ready-sheet-footer" style="display: flex; justify-content: space-between; font-size: 10px; color: var(--color-muted-text); border-top: 1px solid var(--color-border); padding-top: 8px; margin-top: 4px;">
          <span><i class="fa-solid fa-microscope" style="color: #0284C7;"></i> PharmaPolySCOPE Upstream Physicochemical Generator</span>
          <span>Quality-Assured Physicochemical Dataset</span>
        </div>
      </div>
    `;
  } catch (err) {
    console.error("Error loading ready sheet:", err);
  }
}

function copyReadyParamValue(val, label) {
  if (val === undefined || val === null || val === "-") return;
  navigator.clipboard.writeText(String(val)).then(() => {
    alert(`Copied ${label}: ${val}`);
  });
}

function copyReadyAllFinal() {
  if (!currentLoadedReadySheet) {
    alert("Please select a record first.");
    return;
  }
  const sheet = currentLoadedReadySheet;
  let text = `=== PHARMAPOLYSCOPE MANUAL ENTRY: ${sheet.name.toUpperCase()} (${sheet.entity_id}) ===\n`;
  text += `Entity Type: ${sheet.entity_type.toUpperCase()}\n`;
  text += `--------------------------------------------------\n`;
  sheet.fields.forEach(f => {
    const val = f.final_value !== undefined ? f.final_value : f.value;
    text += `${f.label}: ${val} ${f.unit !== '-' ? f.unit : ''}\n`;
  });

  navigator.clipboard.writeText(text).then(() => {
    alert(`All final converged values for ${sheet.name} copied to clipboard!`);
  });
}

function copyReadyAllNominal() {
  if (!currentLoadedReadySheet) {
    alert("Please select a record first.");
    return;
  }
  const sheet = currentLoadedReadySheet;
  let text = `=== PHARMAPOLYSCOPE NOMINAL BASE: ${sheet.name.toUpperCase()} (${sheet.entity_id}) ===\n`;
  text += `Entity Type: ${sheet.entity_type.toUpperCase()}\n`;
  text += `--------------------------------------------------\n`;
  sheet.fields.forEach(f => {
    const val = f.base_value !== undefined ? f.base_value : f.value;
    text += `${f.label}: ${val} ${f.unit !== '-' ? f.unit : ''}\n`;
  });

  navigator.clipboard.writeText(text).then(() => {
    alert(`All nominal base values for ${sheet.name} copied to clipboard!`);
  });
}

function copyReadyCsvRow() {
  if (!currentLoadedReadySheet) {
    alert("Please select a record first.");
    return;
  }
  const sheet = currentLoadedReadySheet;
  const header = sheet.fields.map(f => f.key || f.label).join("\t");
  const row = sheet.fields.map(f => f.final_value !== undefined ? f.final_value : f.value).join("\t");
  const fullText = `Entity_ID\tName\tType\t${header}\n${sheet.entity_id}\t${sheet.name}\t${sheet.entity_type}\t${row}`;

  navigator.clipboard.writeText(fullText).then(() => {
    alert(`Tab-delimited row for ${sheet.name} copied! Ready to paste directly into Excel or software table.`);
  });
}

function copyReadyJson() {
  if (!currentLoadedReadySheet) {
    alert("Please select a record first.");
    return;
  }
  const jsonStr = JSON.stringify(currentLoadedReadySheet.json_export || currentLoadedReadySheet, null, 2);
  navigator.clipboard.writeText(jsonStr).then(() => {
    alert(`JSON payload for ${currentLoadedReadySheet.name} copied to clipboard!`);
  });
}

function printReadySheet() {
  switchNav("output", "sub-ready-sheet");
  setTimeout(() => {
    window.print();
  }, 100);
}

// -------------------------------------------------------------
// GLOBAL SEARCH & ACTIONS
// -------------------------------------------------------------

function handleGlobalSearch() {
  const q = document.getElementById("global-search").value.trim().toLowerCase();
  if (!q) {
    renderSummaryTable();
    renderDrugRegistry();
    renderPolymerRegistry();
    return;
  }

  const filtered = allStoredRecords.filter(r => 
    r.entity_id.toLowerCase().includes(q) ||
    r.name.toLowerCase().includes(q) ||
    (r.abbreviation && r.abbreviation.toLowerCase().includes(q)) ||
    (r.canonical_smiles && r.canonical_smiles.toLowerCase().includes(q))
  );

  const tbody = document.querySelector("#summary-records-table tbody");
  if (tbody) {
    tbody.innerHTML = filtered.map(r => `
      <tr onclick="viewReadySheetById('${r.entity_id}')" style="cursor: pointer;" title="View Manual Entry Sheet">
        <td class="font-mono" style="font-weight: 700; color: var(--color-primary-action);">${r.entity_id}</td>
        <td><span class="badge badge-calculated">${r.entity_type}</span></td>
        <td><strong>${r.name}</strong> ${r.abbreviation ? `(${r.abbreviation})` : ''}</td>
        <td class="font-mono">${safeFormat(r.canonical_smiles || r.repeat_unit_smiles)}</td>
        <td class="num-col">${safeFormat(r.tm_K)}</td>
        <td class="num-col">${safeFormat(r.tg_K)}</td>
        <td class="num-col">${safeFormat(r.density_g_cm3)}</td>
        <td class="font-mono">${safeFormat(r.hsp_mpa_half?.delta_D)} / ${safeFormat(r.hsp_mpa_half?.delta_P)} / ${safeFormat(r.hsp_mpa_half?.delta_H)}</td>
        <td>${renderQcBadge(r.qc?.status)}</td>
      </tr>
    `).join("");
  }
}

async function syncDataset() {
  await fetch("/api/qc/run_all", { method: "POST" });
  await loadAllWorkbenchData();
  alert("Data store synchronized with input_dataset.json and input_dataset.csv!");
}

async function deleteEntity(entityId, entityType) {
  if (!confirm(`Are you sure you want to delete ${entityId}?`)) return;
  const endpoint = entityType === "drug" ? `/api/drugs/${entityId}` : `/api/polymers/${entityId}`;
  await fetch(endpoint, { method: "DELETE" });
  loadAllWorkbenchData();
}

// -------------------------------------------------------------
// DYNAMIC ON-DEMAND PARAMETER CALCULATION INSPECTOR
// -------------------------------------------------------------

function inspectParameterDetails(paramKey) {
  const modal = document.getElementById("calc-inspector-modal");
  const title = document.getElementById("modal-param-title");
  const body = document.getElementById("modal-param-body");
  if (!modal || !title || !body) return;

  const infoMap = {
    "mw": {
      title: "Molecular Weight (MW)",
      equation: "MW = Σ (Atomic Weights from Neutral Canonical SMILES)",
      uncertainty: "Exact (Chemical Formula / Monoisotopic or Average MW)",
      method: "DESC-RDKIT-01",
      notes: "Calculated from canonical neutral active moiety representation in RDKit."
    },
    "tm_K": {
      title: "Melting Point (Tm)",
      equation: "Tm (K) = Tm (°C) + 273.15",
      uncertainty: "Literature Spec / Experimental DSC Onset",
      method: "LIT-ACQ-01",
      notes: "Acquired from curated literature or experimental differential scanning calorimetry (DSC) for the thermodynamically stable crystalline polymorph."
    },
    "tg_K": {
      title: "Glass Transition Temperature (Tg)",
      equation: "Tg = 0.70 × Tm  [Boyer–Kauzmann 0.70 Expectation Ratio]",
      uncertainty: "± 21.0 K (1σ standard error, Koop et al. 2011 survey of 142 APIs)",
      method: "TG-RATIO-01",
      notes: "For amorphous solid dispersion (ASD) screening, Tg establishes the baseline for the Gordon–Taylor mixture curve and anti-plasticization evaluation."
    },
    "poly_tg": {
      title: "Polymer Dry-State Glass Transition (Tg)",
      equation: "Tg = Literature / Pharmacopoeial Dry-State DSC Midpoint",
      uncertainty: "± 2.0 to 5.0 K (Grade-Specific Manufacturer Certificate)",
      method: "LIT-POLY-01",
      notes: "Polymer Tg is NEVER calculated via 0.70×Tm. It is strictly acquired as a verified dry-state property for the specific commercial grade."
    },
    "density_g_cm3": {
      title: "Solid-State Density (ρ)",
      equation: "ρ = MW / Vm  where Vm = Σ Δvi (Fedors 1974 group volume sum)",
      uncertainty: "± 5.0% (dispersion relative to helium pycnometry)",
      method: "DENS-FEDORS-01",
      notes: "Calculated from atomic and structural group volumes at 25 °C without requiring crystalline unit-cell packing data."
    },
    "delta_D": {
      title: "HSP Dispersion Partial Parameter (δD)",
      equation: "δD = (Σ Fdi) / Vm  [Hoftyzer–van Krevelen group contribution]",
      uncertainty: "± 1.50 MPa½ (1σ standard uncertainty band)",
      method: "HSP-HVK-01",
      notes: "Quantifies London dispersion interactions derived from atomic polarizabilities."
    },
    "delta_P": {
      title: "HSP Polar Partial Parameter (δP)",
      equation: "δP = √(Σ Fpi²) / Vm  [Hoftyzer–van Krevelen group contribution]",
      uncertainty: "± 1.50 MPa½ (1σ standard uncertainty band)",
      method: "HSP-HVK-01",
      notes: "Quantifies permanent dipole-dipole electrostatic interactions."
    },
    "delta_H": {
      title: "HSP Hydrogen-Bonding Partial Parameter (δH)",
      equation: "δH = √(Σ Ehi / Vm)  [Hoftyzer–van Krevelen group contribution]",
      uncertainty: "± 1.50 MPa½ (1σ standard uncertainty band)",
      method: "HSP-HVK-01",
      notes: "Quantifies donor-acceptor hydrogen bonding and acid-base associations."
    },
    "delta_t": {
      title: "Total Solubility Parameter (δt)",
      equation: "δt = √(δD² + δP² + δH²)  [Hansen 3D Euclidean vector magnitude]",
      uncertainty: "± 1.62 MPa½ (combined quadrature uncertainty)",
      method: "HSP-HVK-01",
      notes: "Cross-checked against secondary Fedors total solubility parameter."
    }
  };

  const item = infoMap[paramKey] || {
    title: paramKey,
    equation: "Standard physical chemistry evaluation",
    uncertainty: "N/A",
    method: "DETERMINISTIC",
    notes: "Detailed parameter provenance."
  };

  title.innerHTML = `<i class="fa-solid fa-calculator"></i> ${item.title}`;
  body.innerHTML = `
    <div style="margin-bottom: 12px;">
      <strong>Governing Scientific Equation:</strong>
      <div class="math-equation-box">${item.equation}</div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
      <div style="background: #F8FAFC; padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border);">
        <span style="font-size: 10.5px; color: var(--color-muted-text); text-transform: uppercase;">Method ID</span><br>
        <strong style="font-family: var(--font-mono); color: var(--color-primary-text);">${item.method}</strong>
      </div>
      <div style="background: #F8FAFC; padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border);">
        <span style="font-size: 10.5px; color: var(--color-muted-text); text-transform: uppercase;">Uncertainty Margin</span><br>
        <strong style="font-family: var(--font-mono); color: #B45309;">${item.uncertainty}</strong>
      </div>
    </div>
    <div style="font-size: 11.5px; line-height: 1.5; color: var(--color-secondary-text);">
      <strong>Scientific Context:</strong><br>
      ${item.notes}
    </div>
  `;

  modal.style.display = "flex";
}

function closeInspectorModal(event) {
  const modal = document.getElementById("calc-inspector-modal");
  if (modal) modal.style.display = "none";
}
