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

// QC Status badge generator (Interactive Inspector Button)
function renderQcBadge(status, entityId = null) {
  const s = (status || "APPROVED").toUpperCase();
  const clickAttr = entityId ? `onclick="event.stopPropagation(); openQcComplianceModal('${entityId}', event)" title="Click to inspect QC parameter compliance and rule diagnostics"` : '';
  const clickClass = entityId ? 'badge-clickable' : '';

  if (s === "APPROVED") {
    return `<span class="badge badge-success ${clickClass}" ${clickAttr}><span class="badge-dot"></span>APPROVED <i class="fa-solid fa-circle-info" style="font-size: 8.5px; margin-left: 3px; opacity: 0.8;"></i></span>`;
  }
  if (s.includes("FLAG") || s === "BORDERLINE") {
    return `<span class="badge badge-warning ${clickClass}" ${clickAttr}><span class="badge-dot"></span>APPROVED W/ FLAGS <i class="fa-solid fa-triangle-exclamation" style="font-size: 8.5px; margin-left: 3px;"></i></span>`;
  }
  if (s.includes("REJECT") || s.includes("INVALID")) {
    return `<span class="badge badge-error ${clickClass}" ${clickAttr}><span class="badge-dot"></span>REJECTED <i class="fa-solid fa-circle-xmark" style="font-size: 8.5px; margin-left: 3px;"></i></span>`;
  }
  return `<span class="badge badge-info ${clickClass}" ${clickAttr}><span class="badge-dot"></span>${s}</span>`;
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
    populateReadyEntityDropdown();

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
        <td>${renderQcBadge(r.qc?.status, r.entity_id)}</td>
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
      <td>${renderQcBadge(d.qc?.status, d.entity_id)}</td>
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

async function saveCurrentDrug(forceDistinct = false, silent = false) {
  if (!currentCalculatedDrug) {
    await calculateDrugLive();
  }
  if (!currentCalculatedDrug) return null;

  const r = currentCalculatedDrug;
  const payload = {
    name: r.name,
    canonical_smiles: r.canonical_smiles,
    tm_K: r.tm_K?.tm_K || r.tm_K?.value || r.tm_K,
    tm_form: r.tm_K?.form || "form I (stable at 25 C)",
    tg_K: r.tg_K?.tg_K || r.tg_K?.value || r.tg_K,
    density_g_cm3: r.density_g_cm3?.density_g_cm3 || r.density_g_cm3?.value || r.density_g_cm3,
    delta_D: r.hsp_mpa_half?.delta_D,
    delta_P: r.hsp_mpa_half?.delta_P,
    delta_H: r.hsp_mpa_half?.delta_H,
    logP: r.logP,
    TPSA: r.TPSA,
    HBD: r.HBD,
    HBA: r.HBA,
    BCS_class: r.BCS_class || "II",
    pubchem_cid: parseInt(document.getElementById("drug-cid")?.value) || null,
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
      if (silent) {
        if (currentCalculatedDrug) currentCalculatedDrug.entity_id = result.existing_record.entity_id;
        return { success: true, entity_id: result.existing_record.entity_id, is_duplicate: true };
      }
      const choice = prompt(
        `DUPLICATE RECORD DETECTED\n\nExisting record:\n${result.existing_record.entity_id} — ${result.existing_record.name}\n\nOptions:\n1: Open existing record in Ready Sheet\n2: Create intentionally distinct version\n3: Cancel`,
        "1"
      );
      if (choice === "1") {
        viewReadySheetById(result.existing_record.entity_id);
      } else if (choice === "2") {
        return await saveCurrentDrug(true, silent);
      }
      return { success: false, entity_id: result.existing_record.entity_id };
    }

    if (result.success) {
      if (currentCalculatedDrug) {
        currentCalculatedDrug.entity_id = result.entity_id;
      }
      await loadAllWorkbenchData();
      if (!silent) {
        alert(`Drug ${result.entity_id} saved successfully with status: ${result.qc.status}`);
        switchNav("library", "sub-drug-lib");
      }
      return { success: true, entity_id: result.entity_id };
    }
    return null;
  } catch (err) {
    console.error("Save error:", err);
    if (!silent) alert("Failed to save drug record. Check console for details.");
    return null;
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
        <td>${renderQcBadge(p.qc?.status, p.entity_id)}</td>
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

async function saveCurrentPolymer(forceDistinct = false, silent = false) {
  const name = document.getElementById("poly-name")?.value.trim() || "Custom Polymer";
  const smiles = document.getElementById("poly-repeat-smiles")?.value.trim() || "*CC(*)N1CCCC1=O";
  const tgK = parseFloat(document.getElementById("poly-tg-k")?.value) || null;
  const tgC = parseFloat(document.getElementById("poly-tg-c")?.value) || null;
  const density = parseFloat(document.getElementById("poly-density")?.value) || 0.40;

  const payload = {
    name: name,
    repeat_unit_smiles: smiles,
    tg_value_k: tgK,
    tg_value_c: tgC,
    custom_bulk_density: density,
    force_distinct: forceDistinct
  };

  try {
    const res = await fetch("/api/polymers/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.success) {
      if (currentCalculatedPolymer) {
        currentCalculatedPolymer.entity_id = result.entity_id;
      }
      await loadAllWorkbenchData();
      if (!silent) {
        alert(`Polymer ${result.entity_id} (${name}) saved successfully.`);
        switchNav("library", "sub-poly-lib");
      }
      return { success: true, entity_id: result.entity_id };
    }
    return null;
  } catch (err) {
    console.error("Polymer save error:", err);
    if (!silent) alert("Failed to save polymer record. Check console for details.");
    return null;
  }
}

// -------------------------------------------------------------
// PHARMAPOLYSCOPE READY MANUAL ENTRY SHEET
// -------------------------------------------------------------

function populateReadyEntityDropdown(selectedId = null) {
  const select = document.getElementById("ready-entity-select");
  if (!select) return;

  const prevValue = selectedId || select.value;

  select.innerHTML = allStoredRecords.map(r => `
    <option value="${r.entity_id}">${r.name} (${r.entity_id} — ${r.entity_type.toUpperCase()})</option>
  `).join("");

  if (allStoredRecords.length > 0) {
    if (prevValue && allStoredRecords.some(r => r.entity_id === prevValue)) {
      select.value = prevValue;
    } else {
      select.value = allStoredRecords[0].entity_id;
    }
    loadReadySheet(select.value);
  }
}

async function viewReadySheetById(entityId) {
  if (!allStoredRecords || allStoredRecords.length === 0) {
    await loadAllWorkbenchData();
  }

  // Switch navigation directly without clearing dropdown
  document.querySelectorAll(".workspace-view").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".sidebar .nav-item").forEach(el => el.classList.remove("active"));

  const targetView = document.getElementById("view-output");
  if (targetView) targetView.classList.add("active");

  const outputNav = Array.from(document.querySelectorAll(".sidebar .nav-item")).find(b => b.getAttribute("onclick")?.includes("'output'"));
  if (outputNav) outputNav.classList.add("active");

  const breadcrumbEl = document.getElementById("breadcrumb-active-view");
  if (breadcrumbEl) breadcrumbEl.innerText = viewTitleMap["output"] || "Ready Sheet & Output";

  populateReadyEntityDropdown(entityId);
  await loadReadySheet(entityId);
}

async function generateReportForCurrent(type) {
  try {
    if (type === "DRG") {
      if (!currentCalculatedDrug) {
        await calculateDrugLive();
      }
      if (!currentCalculatedDrug) {
        alert("Please enter drug parameters and verify calculation first.");
        return;
      }
      const res = await saveCurrentDrug(false, true); // save silently
      const entityId = res?.entity_id || currentCalculatedDrug?.entity_id || "DRG-0001";
      await viewReadySheetById(entityId);
    } else if (type === "POL") {
      if (!currentCalculatedPolymer) {
        await calculatePolymerLive();
      }
      if (!currentCalculatedPolymer) {
        alert("Please enter polymer parameters and verify calculation first.");
        return;
      }
      const res = await saveCurrentPolymer(false, true); // save silently
      const entityId = res?.entity_id || currentCalculatedPolymer?.entity_id || "POL-0001";
      await viewReadySheetById(entityId);
    }
  } catch (err) {
    console.error("Error generating report for current entity:", err);
  }
}

function viewReadySheetForCurrent(type) {
  generateReportForCurrent(type);
}

let currentLoadedReadySheet = null;

async function loadReadySheet(forcedEntityId = null) {
  const select = document.getElementById("ready-entity-select");
  const entityId = forcedEntityId || (select ? select.value : null);
  if (!entityId) return;

  if (select && select.value !== entityId) {
    select.value = entityId;
  }

  const container = document.getElementById("ready-sheet-render-container");
  if (!container) return;

  try {
    const res = await fetch(`/api/export/pharmapolyscope_ready/${entityId}`);
    if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
    const sheet = await res.json();
    currentLoadedReadySheet = sheet;

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
            <span class="ready-status-pill badge-clickable" onclick="openQcComplianceModal('${sheet.entity_id}', event)" style="cursor: pointer;" title="Click to inspect QC parameter compliance"><i class="fa-solid fa-shield-halved"></i> ${sheet.qc_status || "APPROVED"}</span>
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
    if (container) {
      container.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--color-error); background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 6px;">
          <i class="fa-solid fa-triangle-exclamation" style="font-size: 24px; margin-bottom: 8px;"></i>
          <div style="font-weight: 700; font-size: 14px;">Failed to load Manual Entry Sheet for ${entityId}</div>
          <p style="font-size: 12px; color: #7F1D1D; margin: 4px 0 12px 0;">${err.message}</p>
          <button class="btn btn-secondary btn-sm" onclick="loadReadySheet('${entityId}')"><i class="fa-solid fa-rotate-right"></i> Retry Loading</button>
        </div>
      `;
    }
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

async function printReadySheet() {
  const select = document.getElementById("ready-entity-select");
  const entityId = select?.value || (allStoredRecords[0] ? allStoredRecords[0].entity_id : null);
  if (!entityId) {
    alert("No records available to print. Please calculate or save a record first.");
    return;
  }

  // Ensure output view is active without resetting dropdown
  document.querySelectorAll(".workspace-view").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".sidebar .nav-item").forEach(el => el.classList.remove("active"));
  const targetView = document.getElementById("view-output");
  if (targetView) targetView.classList.add("active");
  const outputNav = Array.from(document.querySelectorAll(".sidebar .nav-item")).find(b => b.getAttribute("onclick")?.includes("'output'"));
  if (outputNav) outputNav.classList.add("active");

  // Ensure current sheet is fully loaded
  if (!currentLoadedReadySheet || currentLoadedReadySheet.entity_id !== entityId) {
    await loadReadySheet(entityId);
  }

  // Wait for browser paint cycle before triggering print dialog
  requestAnimationFrame(() => {
    setTimeout(() => {
      window.print();
    }, 150);
  });
}

function downloadReadySheetReport() {
  const select = document.getElementById("ready-entity-select");
  const entityId = select?.value || currentLoadedReadySheet?.entity_id;
  if (!entityId) {
    alert("Please select a record first.");
    return;
  }
  const downloadUrl = `/api/export/report_html/${entityId}?download=true`;
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = `PharmaPolySCOPE_Report_${entityId}.html`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
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
        <td>${renderQcBadge(r.qc?.status, r.entity_id)}</td>
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

// -------------------------------------------------------------
// QC ENGINE PARAMETER COMPLIANCE INSPECTOR MODAL
// -------------------------------------------------------------

function openQcComplianceModal(entityId, event) {
  if (event) {
    event.stopPropagation();
  }

  const r = allStoredRecords.find(x => x.entity_id === entityId) ||
            allDrugs.find(x => x.entity_id === entityId) ||
            allPolymers.find(x => x.entity_id === entityId);

  if (!r) {
    alert(`Record ${entityId} not found in active workbench.`);
    return;
  }

  const modal = document.getElementById("qc-compliance-modal");
  const titleEl = document.getElementById("qc-modal-title");
  const badgeEl = document.getElementById("qc-modal-status-badge");
  const bodyEl = document.getElementById("qc-modal-body");
  if (!modal || !titleEl || !bodyEl) return;

  const isDrug = r.entity_type === "drug";
  const qc = r.qc || {};
  const status = (qc.status || "APPROVED").toUpperCase();
  const diagnostics = qc.diagnostics || [];
  const warnings = qc.warnings || [];

  // Header Title & Badge
  titleEl.innerHTML = `<i class="fa-solid fa-shield-halved" style="color: var(--color-primary-action);"></i> QC Parameter Compliance: <span style="font-family: var(--font-mono); color: #0284C7; margin-left: 4px;">${r.entity_id}</span> — ${r.name}`;
  
  if (badgeEl) {
    if (status.includes("FLAG") || status === "BORDERLINE") {
      badgeEl.innerHTML = `<span class="qc-pill-flag"><i class="fa-solid fa-triangle-exclamation"></i> APPROVED W/ FLAGS</span>`;
    } else if (status.includes("REJECT")) {
      badgeEl.innerHTML = `<span class="qc-pill-error"><i class="fa-solid fa-circle-xmark"></i> REJECTED</span>`;
    } else {
      badgeEl.innerHTML = `<span class="qc-pill-pass"><i class="fa-solid fa-circle-check"></i> 100% COMPLIANT</span>`;
    }
  }

  // Extract core parameters
  const mw = typeof r.mw === "number" ? r.mw : parseFloat(r.mw) || 0;
  
  let tmVal = null;
  if (typeof r.tm_K === "object" && r.tm_K !== null) {
    tmVal = r.tm_K.value || r.tm_K.tm_K;
  } else if (typeof r.tm_K === "number") {
    tmVal = r.tm_K;
  }

  let tgVal = null;
  if (typeof r.tg_K === "object" && r.tg_K !== null) {
    tgVal = r.tg_K.value || r.tg_K.tg_K;
  } else if (typeof r.tg_K === "number") {
    tgVal = r.tg_K;
  }

  let densVal = null;
  if (typeof r.density_g_cm3 === "object" && r.density_g_cm3 !== null) {
    densVal = r.density_g_cm3.value || r.density_g_cm3.density_g_cm3;
  } else if (typeof r.density_g_cm3 === "number") {
    densVal = r.density_g_cm3;
  }

  const hsp = r.hsp_mpa_half || {};
  const dD = typeof hsp.delta_D === "number" ? hsp.delta_D : parseFloat(r.delta_D) || 0;
  const dP = typeof hsp.delta_P === "number" ? hsp.delta_P : parseFloat(r.delta_P) || 0;
  const dH = typeof hsp.delta_H === "number" ? hsp.delta_H : parseFloat(r.delta_H) || 0;
  const disp = hsp.displacement !== undefined ? hsp.displacement : (qc.hsp_primary_secondary_displacement !== undefined ? qc.hsp_primary_secondary_displacement : null);
  
  const tpsa = typeof r.TPSA === "number" ? r.TPSA : parseFloat(r.TPSA) || 0;
  const logP = typeof r.logP === "object" && r.logP !== null ? (r.logP.primary || 0) : (parseFloat(r.logP) || 0);
  const hbd = parseInt(r.HBD) || 0;
  const hba = parseInt(r.HBA) || 0;

  // Build Comprehensive 10-Point Parameter Rule Checklist
  const checks = [];

  if (isDrug) {
    // 1. Chemical Structure & Valence
    const hasSmilesSyntaxErr = diagnostics.some(d => d.code === "QC-ERR-SMILES-SYNTAX" || d.code === "QC-ERR-SMILES-MISSING");
    const hasInorganicErr = diagnostics.some(d => d.code === "QC-ERR-INORGANIC-SUBSTANCE");
    const hasSaltFlag = diagnostics.some(d => d.code === "QC-FLAG-ION-SALT");
    const structPass = !hasSmilesSyntaxErr && !hasInorganicErr && !hasSaltFlag;
    checks.push({
      param: "Chemical Structure & Neutral State",
      observed: r.canonical_smiles ? `<span class="font-mono" style="font-size: 10px; max-width: 170px; display: inline-block; overflow: hidden; text-overflow: ellipsis; vertical-align: middle;">${r.canonical_smiles}</span>` : "None",
      rule: "Organic API (≥1 Carbon, valid valence, neutral active moiety)",
      isPass: structPass,
      explanation: structPass ? "Valid neutral small-molecule API structure canonicalized by RDKit." : "Contains salt counter-ions or non-standard valence."
    });

    // 2. Melting Point Range & Units
    const tmInKelvin = tmVal && tmVal >= 100.0;
    const tmInRange = tmVal && tmVal >= 250.0 && tmVal <= 650.0;
    const tmPass = tmInKelvin && tmInRange;
    checks.push({
      param: "Melting Point (Tm) Range & Units",
      observed: tmVal ? `${tmVal.toFixed(2)} K` : "None",
      rule: "250.0 to 650.0 K (Absolute Thermodynamic Kelvin)",
      isPass: tmPass,
      explanation: tmPass ? "Melting temperature falls cleanly within the standard crystalline API thermal envelope." : (tmVal < 100.0 ? "Temperature appears in Celsius instead of Kelvin." : "Extreme lattice energy / melting point exceeding 650 K.")
    });

    // 3. Glass Transition Ratio (Beaman-Boyer Rule)
    const expectedTg = tmVal ? roundTo(0.70 * tmVal, 1) : null;
    const ratio = (tgVal && tmVal && tmVal > 0) ? (tgVal / tmVal) : null;
    const ratioPass = ratio !== null && ratio >= 0.60 && ratio <= 0.85;
    checks.push({
      param: "Glass Transition (Tg) & Fragility Index",
      observed: tgVal ? `${tgVal.toFixed(1)} K ${ratio ? `(Tg/Tm: ${ratio.toFixed(2)})` : ''}` : "None",
      rule: "Tg = 0.70 × Tm (±21 K 1σ); Fragility 0.60 ≤ Tg/Tm ≤ 0.85",
      isPass: ratioPass,
      explanation: ratioPass ? "Conforms to the 0.70×Tm Boyer–Kauzmann expectation ratio and typical pharmaceutical fragility." : "Atypical thermodynamic fragility; requires high-Tg polymers (e.g. PVP K90, HPMCAS) to prevent phase separation."
    });

    // 4. Solid-State Density
    const hasDensFlag = diagnostics.some(d => d.code === "QC-FLAG-DENS-RANGE");
    const hasHalogenInfo = diagnostics.some(d => d.code === "QC-FLAG-DENS-HALOGEN");
    const densPass = !hasDensFlag;
    checks.push({
      param: "Solid-State Density (ρ)",
      observed: densVal ? `${densVal.toFixed(3)} g/cm³` : "None",
      rule: "0.85 to 2.20 g/cm³ (Standard crystalline/amorphous envelope)",
      isPass: densPass,
      explanation: densPass ? (hasHalogenInfo ? "High density confirmed authentic due to heavy halogen (Br/I) atomic mass." : "Liquid-state Fedors surrogate volume and density within standard envelope.") : "Outside standard [0.85, 2.20] envelope. Often caused by substituted quaternary bridgeheads with negative volume increments in Fedors tables."
    });

    // 5. HSP Cross-Method Concordance Displacement
    const hasDispFatal = diagnostics.some(d => d.code === "QC-ERR-HSP-DISP-FATAL");
    const hasDispFlag = diagnostics.some(d => d.code === "QC-FLAG-HSP-DISP-01");
    const dispPass = disp !== null && disp <= 2.00 && !hasDispFatal && !hasDispFlag;
    checks.push({
      param: "HSP Method Concordance (Δdisp)",
      observed: disp !== null ? `${Number(disp).toFixed(2)} MPa½` : "Not evaluated",
      rule: "Δ = |δt,HVK - δt,Fedors| ≤ 2.00 MPa½ (High Agreement)",
      isPass: dispPass,
      explanation: dispPass ? "Excellent cross-method thermodynamic agreement between Hoftyzer–van Krevelen and Fedors group tables." : "Moderate displacement (2.0–5.0 MPa½) arising from ring closure or conjugated heteroatom energy offsets. Handled by 10k Monte Carlo UQ."
    });

    // 6. Lipinski Molecular Weight (Mw)
    const mwPass = mw > 0 && mw <= 500.0;
    checks.push({
      param: "Molecular Weight (Mw, Lipinski Rule-of-5)",
      observed: `${mw.toFixed(2)} g/mol`,
      rule: "Mw ≤ 500.00 g/mol (Classical Oral Rule-of-5 Boundary)",
      isPass: mwPass,
      explanation: mwPass ? "Falls inside the classical Lipinski small-molecule oral bioavailability space." : "Beyond-Rule-of-5 (bRo5) chemical space. High Mw lowers molecular mobility and diffusion; typically requires higher polymer ratios (1:3 or 1:4)."
    });

    // 7. Topological Polar Surface Area (TPSA, Veber Rule)
    const tpsaPass = tpsa <= 140.0;
    checks.push({
      param: "Polar Surface Area (TPSA, Veber Criterion)",
      observed: `${tpsa.toFixed(1)} Å²`,
      rule: "TPSA ≤ 140.00 Å² (Veber Oral Permeability Boundary)",
      isPass: tpsaPass,
      explanation: tpsaPass ? "Polar surface area is compatible with passive transcellular intestinal permeation." : "High TPSA indicates potential passive membrane permeation limitations; provides abundant polar interaction sites for polymer miscibility synthons."
    });

    // 8. Partition Coefficient (logP)
    const logPPass = logP >= -3.0 && logP <= 8.0;
    checks.push({
      param: "Lipophilicity (RDKit Crippen logP)",
      observed: `${Number(logP).toFixed(2)}`,
      rule: "-3.00 ≤ logP ≤ 8.00 (Pharmaceutical Formulation Envelope)",
      isPass: logPPass,
      explanation: logPPass ? "Lipophilicity falls within the standard pharmaceutical oral drug formulation range." : "Extreme lipophilicity outside formulation boundaries."
    });

    // 9. Hydrogen-Bonding Capacity (HBD & HBA)
    const hbdPass = hbd <= 12 && hba <= 20;
    checks.push({
      param: "Hydrogen-Bond Donors & Acceptors (HBD/HBA)",
      observed: `HBD: ${hbd} | HBA: ${hba}`,
      rule: "HBD ≤ 12, HBA ≤ 20 (Lipinski/Veber Extended Lattice)",
      isPass: hbdPass,
      explanation: hbdPass ? "Hydrogen-bonding capacity conforms to oral drug-likeness rules." : "Excessive hydrogen-bonding capacity exceeds oral drug guidelines."
    });

    // 10. Data Provenance & Monograph Standards
    const hasProvFlag = diagnostics.some(d => d.code === "QC-FLAG-PROV-EST-TM");
    const provPass = !hasProvFlag;
    checks.push({
      param: "Data Provenance & Source Traceability",
      observed: r.provenance?.tm_K || "LITERATURE",
      rule: "Verified Controlled Vocabulary (EXPERIMENTAL, LITERATURE, CALCULATED)",
      isPass: provPass,
      explanation: provPass ? "Full methodological provenance and literature citations recorded in compliance with ICH Q8/Q9." : "Melting point is currently an estimated surrogate (350 K default); experimental DSC value recommended."
    });
  } else {
    // Polymer Checks
    const hasUngraded = diagnostics.some(d => d.code === "QC-ERR-POLY-UNGRADED");
    checks.push({
      param: "Commercial Grade & Carrier Identity",
      observed: r.grade?.grade || r.abbreviation || "Grade spec",
      rule: "Specific commercial grade identification required (e.g. K30, E5)",
      isPass: !hasUngraded,
      explanation: !hasUngraded ? "Verified commercial grade registered." : "Ungraded generic polymer name is strictly invalid."
    });

    const hasPolyTgCalc = diagnostics.some(d => d.code === "QC-ERR-POLY-TG-CALCULATED");
    checks.push({
      param: "Polymer Glass Transition (Tg) Methodology",
      observed: tgVal ? `${tgVal.toFixed(1)} K` : "None",
      rule: "Acquired from Literature/Grade Datasheet (NEVER 0.70×Tm)",
      isPass: !hasPolyTgCalc,
      explanation: !hasPolyTgCalc ? "Polymer Tg correctly documented from dry-state grade DSC literature." : "Prohibited Beaman–Boyer calculation used for polymer Tg."
    });
  }

  const totalRules = checks.length;
  const compliantCount = checks.filter(c => c.isPass).length;
  const flaggedCount = checks.filter(c => !c.isPass).length;

  // Render Table Rows
  const tableRowsHtml = checks.map(c => `
    <tr class="${c.isPass ? 'qc-row-compliant' : 'qc-row-flagged'}">
      <td style="font-weight: 600; color: ${c.isPass ? 'var(--color-primary-text)' : '#92400E'};">
        ${c.param}
      </td>
      <td class="font-mono" style="font-weight: 700; color: ${c.isPass ? 'var(--color-primary-action)' : '#B45309'};">
        ${c.observed}
      </td>
      <td style="color: var(--color-secondary-text); font-size: 11px;">
        ${c.rule}
      </td>
      <td>
        ${c.isPass 
          ? `<span class="qc-pill-pass"><i class="fa-solid fa-circle-check"></i> PASSED</span>`
          : `<span class="qc-pill-flag"><i class="fa-solid fa-triangle-exclamation"></i> FLAGGED</span>`
        }
      </td>
      <td style="font-size: 11px; line-height: 1.4; color: ${c.isPass ? 'var(--color-secondary-text)' : '#92400E'};">
        ${c.explanation}
      </td>
    </tr>
  `).join("");

  // Render Root-Cause Diagnostics Cards
  let diagHtml = "";
  if (diagnostics.length > 0) {
    diagHtml = `
      <div class="qc-diagnostics-section">
        <div style="font-weight: 700; font-size: 12px; color: #92400E; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
          <i class="fa-solid fa-microscope"></i> Scientific Root-Cause Diagnostics (${diagnostics.length} item${diagnostics.length > 1 ? 's' : ''})
        </div>
        ${diagnostics.map(d => `
          <div class="qc-diag-card">
            <div class="qc-diag-card-title">
              <span><i class="fa-solid fa-circle-exclamation"></i> ${d.title}</span>
              <span class="font-mono" style="font-size: 9.5px; background: #FEF3C7; padding: 2px 6px; border-radius: 4px; border: 1px solid #FCD34D;">${d.code}</span>
            </div>
            <div class="qc-diag-rationale">
              <strong>Root Cause:</strong> ${d.scientific_rationale}
            </div>
            <div class="qc-diag-rationale">
              <strong>Screening Impact:</strong> ${d.screening_impact}
            </div>
            <div class="qc-diag-remediation">
              <strong>Formulation Recommendation:</strong> ${d.remediation_guidance}
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  bodyEl.innerHTML = `
    <div class="qc-modal-summary-grid">
      <div class="qc-summary-stat-box">
        <div class="qc-summary-stat-val" style="color: var(--color-primary-action);">${totalRules}</div>
        <div class="qc-summary-stat-label">Total QC Rules</div>
      </div>
      <div class="qc-summary-stat-box" style="border-color: #A7F3D0; background: #F0FDF4;">
        <div class="qc-summary-stat-val" style="color: #059669;">${compliantCount}</div>
        <div class="qc-summary-stat-label" style="color: #065F46;">Compliant (Passed)</div>
      </div>
      <div class="qc-summary-stat-box" style="border-color: ${flaggedCount > 0 ? '#FCD34D' : 'var(--color-border)'}; background: ${flaggedCount > 0 ? '#FFFBEB' : 'var(--color-surface-subtle)'};">
        <div class="qc-summary-stat-val" style="color: ${flaggedCount > 0 ? '#D97706' : 'var(--color-muted-text)'};">${flaggedCount}</div>
        <div class="qc-summary-stat-label" style="color: ${flaggedCount > 0 ? '#92400E' : 'var(--color-muted-text)'};">Flagged / Atypical</div>
      </div>
      <div class="qc-summary-stat-box">
        <div class="qc-summary-stat-val" style="color: ${flaggedCount > 0 ? '#B45309' : '#059669'}; font-size: 13px;">${status}</div>
        <div class="qc-summary-stat-label">Overall QC Verdict</div>
      </div>
    </div>

    <div style="font-size: 11.5px; color: var(--color-secondary-text); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
      <span><strong>Deterministic Parameter Compliance Checklist:</strong> Compares candidate properties against Table 17-1 standard rules.</span>
      <span style="font-size: 10px; color: var(--color-muted-text);"><i class="fa-solid fa-circle-info"></i> Rows highlighted in amber denote boundary deviations</span>
    </div>

    <div style="max-height: 48vh; overflow-y: auto; border: 1px solid var(--color-border); border-radius: var(--radius-md);">
      <table class="qc-compliance-table" style="margin-bottom: 0;">
        <thead>
          <tr>
            <th style="width: 24%;">QC Parameter & Rule</th>
            <th style="width: 17%;">Observed Value</th>
            <th style="width: 23%;">Expected Rule Threshold</th>
            <th style="width: 13%;">Compliance</th>
            <th style="width: 23%;">Scientific Impact</th>
          </tr>
        </thead>
        <tbody>
          ${tableRowsHtml}
        </tbody>
      </table>
    </div>

    ${diagHtml}
  `;

  modal.style.display = "flex";
}

function closeQcComplianceModal(event) {
  const modal = document.getElementById("qc-compliance-modal");
  if (modal) modal.style.display = "none";
}

function roundTo(val, dec) {
  if (val === null || val === undefined || isNaN(val)) return 0;
  const factor = Math.pow(10, dec);
  return Math.round(val * factor) / factor;
}
