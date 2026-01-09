const state = {
  records: [],
  filtered: [],
  searchTerm: "",
  sortKey: "",
  sortDir: "asc",
  currentPage: 1,
  pageSize: 10,
  currentSorted: [],
  outputsDir: null,
  benchmarks: [],
  currentBenchmark: null,
  guardrailFiles: new Map(),
};

const LANGUAGE_STORAGE_KEY = "srl4children_language";
const THEME_STORAGE_KEY = "srl4children_theme";
const DEFAULT_LANGUAGE = "en";
const DEFAULT_THEME = "light";

function safeGetLocalStorage(key) {
  try {
    return window.localStorage?.getItem(key) ?? null;
  } catch (error) {
    return null;
  }
}

function safeSetLocalStorage(key, value) {
  try {
    window.localStorage?.setItem(key, value);
  } catch (error) {
    // ignore storage errors (private mode, etc.)
  }
}

state.language = safeGetLocalStorage(LANGUAGE_STORAGE_KEY) || DEFAULT_LANGUAGE;
state.theme = safeGetLocalStorage(THEME_STORAGE_KEY) || DEFAULT_THEME;

const TRANSLATIONS = {
  en: {
    "SRL4Children | Design Principles and Tools – POC": "SRL4Children | Design Principles and Tools – POC",
    "Bienvenue sur SRL4Children : sélectionnez un dossier de benchmark (JSON) pour explorer les prompts et résultats.": "Welcome to SRL4Children – choose a benchmark folder (JSON) to explore prompts and results.",
    "Choisir le dossier <code>outputs</code>": "Select the <code>outputs</code> folder",
    "Ou charger via sélection de dossier": "Or load via directory picker",
    "Benchmarks disponibles :": "Available benchmarks:",
    "— Aucun dossier sélectionné —": "— No folder selected —",
    "Rechercher un mot-clé dans les prompts": "Search for a keyword in prompts",
    "Recherche sur les prompts": "Prompts search",
    "Exporter le tableau en CSV": "Export table to CSV",
    "Modèle :": "Model:",
    "Score global moyen": "Average global score",
    "Chargement du graphique…": "Loading chart…",
    "Modèle": "Model",
    "Prompts": "Prompts",
    "Preset critères": "Criteria preset",
    "Catégorie": "Category",
    "Date - Heure": "Date - Time",
    "Tranche Âge": "Age band",
    "Preset": "Preset",
    "DP Check": "DP Check",
    "Scores": "Scores",
    "Actions": "Actions",
    "Aucun fichier chargé.": "No files loaded.",
    "Fermer": "Close",
    "Détails": "Details",
    "Résumé": "Overview",
    "Critères": "Criteria",
    "Guardrails": "Guardrails",
    "Principes de conception": "Design Principles",
    "Avant / Après Guardrails": "Before / After Guardrails",
    "Prompt avec Guardrails": "Prompt with guardrails",
    "Télécharger le rapport": "Download report",
    "Synthèse globale": "Global summary",
    "Sections du record": "Record sections",
    "Score global": "Overall score",
    "Métadonnées": "Metadata",
    "Aucun score du juge v1.1 disponible pour ce record.": "No judge v1.1 score available for this record.",
    "Aucun contenu disponible.": "No content available.",
    "Aucun critère évalué pour ce record.": "No criteria were evaluated for this record.",
    "Aucune donnée détaillée disponible.": "No detailed data available.",
    "Aucun détail pour cette catégorie.": "No detail for this category.",
    "Aucun critère listé.": "No criteria listed.",
    "Aucun guardrail disponible.": "No guardrails available.",
    "Aucun fichier de guardrails détecté.": "No guardrail file detected.",
    "Copier la commande": "Copy command",
    "Commande copiée": "Command copied",
    "Copiez la commande suivante :": "Copy the following command:",
    "Rafraîchir": "Refresh",
    "Chargement...": "Loading...",
    "Chargement des guardrails…": "Loading guardrails…",
    "Impossible de charger les guardrails.": "Unable to load guardrails.",
    "Erreur lors du rafraîchissement des guardrails": "Error while refreshing guardrails",
    "Aucun guardrail généré pour ce record.": "No guardrails generated for this record.",
    "Guardrail generation metadata": "Guardrail generation metadata",
    "Prompt": "Prompt",
    "Réponse": "Response",
    "Aucun guardrail généré. Veuillez créer des guardrails pour activer cette section.": "No guardrails generated. Please create guardrails to enable this section.",
    "Avant SRL4Children": "Before SRL4Children",
    "Après SRL4Children (DP => Auto-Guardrails)": "After SRL4Children (DP => Auto-Guardrails)",
    "Générer automatiquement": "Generate automatically",
    "Exécution de la commande…": "Running command…",
    "Commande exécutée. Actualisation en cours…": "Command executed. Refreshing…",
    "Guardrails générés avec succès.": "Guardrails generated successfully.",
    "Impossible d'exécuter automatiquement la commande. Veuillez l'exécuter manuellement.": "Unable to execute the command automatically. Please run it manually.",
    "Impossible de recharger automatiquement les guardrails. Veuillez re-sélectionner le dossier ou recharger la page.": "Unable to refresh guardrails automatically. Please re-select the folder or reload the page.",
    "criterion_id": "Criterion ID",
    "Pass {index}": "Pass {index}",
    "Aucun score du juge v1.1 disponible pour ce record.": "No judge v1.1 score available for this record.",
    "Chargement du benchmark…": "Loading benchmark…",
    "Benchmark chargé.": "Benchmark loaded.",
    "Aucun fichier sélectionné.": "No file selected.",
    "Chargement de {count} fichiers…": "Loading {count} files…",
    "{count} fichiers chargés.": "{count} files loaded.",
    "Aucun guardrail généré": "No guardrails generated",
    "Aucun juge n'a évalué ce critère.": "No judge evaluated this criterion.",
    "Consensus faible": "Low consensus",
    "Données partielles · Les résultats peuvent être erronés.": "Partial data · Results may be inaccurate.",
    "Données complètes": "Complete data",
    "Prompt complet": "Full prompt",
    "Réponse du modèle": "Model response",
    "Scores par sous-catégorie": "Scores by subcategory",
    "Scores par catégorie": "Scores by category",
    "Sous-catégorie": "Subcategory",
    "Maturité": "Maturity",
    "Mode": "Mode",
    "Date de mise à jour": "Last updated",
    "Aucun critère noté pour cette catégorie.": "No scored criteria for this category.",
    "Extraits": "Extracts",
    "Aucune donnée pour ce juge.": "No data for this judge.",
    "Scores individuels": "Individual scores",
    "Détails des passes": "Pass details",
    "Extraits principaux": "Key extracts",
    "Réponses brutes": "Raw responses",
    "Aucun guardrail détecté. Générer via python tools/generate_guardrails.py --record \"{path}\".": "No guardrails detected. Generate via python tools/generate_guardrails.py --record \"{path}\".",
    "Prompt complet (avec guardrails)": "Full prompt (with guardrails)",
    "Passer en mode sombre": "Switch to dark mode",
    "Passer en mode clair": "Switch to light mode",
    "Mode clair/sombre": "Dark/Light Mode",
    "Langue": "Language",
    "Guardrails couvrent {covered}/{total} des principes de Conception évalués.": "Guardrails cover {covered}/{total} Design Principles.",
    "Guardrails générés": "Guardrails generated",
    "Guardrails manquants": "Guardrails missing",
    "Aucun critère noté pour cette catégorie.": "No scored criteria for this category.",
    "Aucun fichier JSON trouvé dans ce dossier.": "No JSON file found in this folder.",
    "{loaded} fichiers chargés avec {errors} erreurs. Consultez la console.": "{loaded} files loaded with {errors} errors. Check the console.",
    "{loaded} fichiers chargés avec succès.": "{loaded} files loaded successfully.",
    "showDirectoryPicker n'est pas supporté dans ce navigateur. Utilisez la sélection de dossier classique.": "showDirectoryPicker is not supported in this browser. Use the standard folder picker instead.",
    "Dossier outputs sélectionné. Choisissez un benchmark dans la liste.": "Outputs folder selected. Choose a benchmark from the list.",
    "Impossible d'accéder au dossier: {message}": "Unable to access folder: {message}",
    "Aucun sous-dossier trouvé dans outputs.": "No subfolders found in outputs.",
    "Benchmark non trouvé.": "Benchmark not found.",
    "Aucun fichier JSON dans {name}.": "No JSON file in {name}.",
    "{loaded} fichiers chargés pour {name}.": "{loaded} files loaded for {name}.",
    "Aucune donnée à exporter.": "No data to export.",
    "Export CSV généré ({rows} lignes).": "CSV export generated ({rows} rows).",
    "Aucun résultat.": "No results.",
    "(non défini)": "(not set)",
    "— Sélectionnez un benchmark —": "— Select a benchmark —",
    "Variance globale: {value}": "Global variance: {value}",
    "Accord moyen: {value}": "Average agreement: {value}",
    "Principes de conception": "Design Principles",
    "Sélectionnez un Design Principle dans la liste pour afficher et modifier son prompt.": "Select a Design Principle from the list to view and edit its prompt.",
    "Enregistrer": "Save",
    "Des modifications non enregistrées seront perdues. Continuer ?": "Unsaved changes will be lost. Continue?",
    "Veuillez sélectionner le dossier assets/criteria.": "Please select the assets/criteria folder.",
    "Design Principle sauvegardé.": "Design Principle saved.",
    "Chargement des Design Principles…": "Loading Design Principles…",
    "Aucun Design Principle détecté.": "No Design Principles found.",
    "Impossible de charger ce Design Principle.": "Unable to load this Design Principle.",
    "Impossible d'enregistrer ce Design Principle.": "Unable to save this Design Principle.",
    "Autorisation refusée pour accéder aux Design Principles.": "Permission denied to access Design Principles.",
    "Impossible de charger les Design Principles.": "Unable to load Design Principles.",
  },
};

function formatTemplate(template, params = {}) {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    return params[key] !== undefined ? params[key] : match;
  });
}

function translate(text, params = {}) {
  if (!text) return "";
  if (state.language === "fr") {
    return formatTemplate(text, params);
  }
  const dictionary = TRANSLATIONS[state.language] || {};
  const template = dictionary[text] || text;
  return formatTemplate(template, params);
}

const guardrailRegistry = new Map();

fetch("guardrail_registry_lookup.json")
  .then((response) => (response.ok ? response.json() : null))
  .then((data) => {
    if (!data) return;
    Object.entries(data).forEach(([id, meta]) => {
      const normalized = normalizeCriterionId(id);
      registerGuardrailMeta(normalized, meta);
      if (meta?.category) {
        registerGuardrailMeta(normalizeCriterionId(meta.category), {
          category: meta.category,
          label: humanizeIdentifier(meta.category),
        });
      }
      if (meta?.category && meta?.subcategory) {
        registerGuardrailMeta(normalizeCriterionId(`${meta.category}.${meta.subcategory}`), {
          category: meta.category,
          subcategory: meta.subcategory,
        });
      }
    });
    if (currentRecordDetail?.guardrailData) {
      renderGuardrailsPanel(currentRecordDetail);
    }
  })
  .catch((error) => {
    console.warn("Impossible de charger guardrail_registry_lookup.json", error);
  });

const tableBody = document.getElementById("tableBody");
const statusEl = document.getElementById("status");
const statsEl = document.getElementById("stats");
const paginationEl = document.getElementById("pagination");
const searchInput = document.getElementById("searchInput");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const detailsOverlay = document.getElementById("detailsOverlay");
const tabList = document.querySelector(".details-tabs");
const tabButtons = Array.from(document.querySelectorAll(".tab-btn"));
const overviewPanel = document.getElementById("tab-overview");
const criteriaPanel = document.getElementById("tab-criteria");
const guardrailsPanel = document.getElementById("tab-guardrails");
const promptOptimizationPanel = document.getElementById("tab-prompt_optimization");
const detailsTitleEl = document.getElementById("detailsTitle");
const languageSelect = document.getElementById("languageSelect");
const themeToggle = document.getElementById("themeToggle");
const appTitleEl = document.getElementById("appTitle");
const instructionsEl = document.getElementById("instructions");
const filePickerLabelEl = document.getElementById("filePickerLabel");
const benchmarkSelectLabel = document.getElementById("benchmarkSelectLabel");
const benchmarkSelectEl = document.getElementById("benchmarkSelect");
const tableEmptyEl = document.getElementById("tableEmpty");
const pickOutputsBtn = document.getElementById("pickOutputsBtn");
const gsModelLabelEl = document.getElementById("gsModelLabel");
const gsAvgScoreLabelEl = document.getElementById("gsAvgScoreLabel");
const thModel = document.getElementById("thModel");
const thPrompt = document.getElementById("thPrompt");
const thCategory = document.getElementById("thCategory");
const thDate = document.getElementById("thDate");
const thMaturity = document.getElementById("thMaturity");
const thDpCheck = document.getElementById("thDpCheck");
const thScore = document.getElementById("thScore");
const thActions = document.getElementById("thActions");
// Global summary (homepage)
const gsSection = document.getElementById("globalSummarySection");
const gsModelEl = document.getElementById("gsModel");
const gsAvgScoreEl = document.getElementById("gsAvgScore");
const gsRadarCanvas = document.getElementById("gsRadar");
const gsRadarFallback = document.getElementById("gsRadarFallback");
const gsSubcategoryList = document.getElementById("gsSubcategoryList");
const tabPanels = {
  overview: overviewPanel,
  criteria: criteriaPanel,
  guardrails: guardrailsPanel,
  prompt_optimization: promptOptimizationPanel,
};
const downloadReportBtn = document.getElementById("downloadReport");
const closeOverlayBtn = document.getElementById("closeOverlay");
const benchmarkSelect = document.getElementById("benchmarkSelect");
const benchmarkInput = document.getElementById("benchmarkInput");
const designPrinciplesBtn = document.getElementById("designPrinciplesBtn");
const designPrinciplesOverlay = document.getElementById("designPrinciplesOverlay");
const closeDesignPrinciplesBtn = document.getElementById("closeDesignPrinciples");
const designPrinciplesTree = document.getElementById("designPrinciplesTree");
const designPrinciplesEditor = document.getElementById("designPrinciplesEditor");
const designPrinciplesSaveBtn = document.getElementById("designPrinciplesSaveBtn");
const designPrinciplesEmpty = document.getElementById("designPrinciplesEmpty");
const designPrinciplesPathEl = document.getElementById("designPrinciplesPath");
const designPrinciplesTitleEl = document.getElementById("designPrinciplesTitle");

const MATURITY_OPTIONS = ["Child", "Teen", "YoungAdult", "Emerging"];
const MAX_RADAR_SCORE = 5;
const CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js";

let activeTab = "overview";
let overviewRadarChart = null;
let criteriaRadarChart = null;
let lastFocusedTrigger = null;
let activeCriteriaCategory = null;
let chartJsPromise = null;
let currentRecordDetail = null;
let globalSummaryRadarChart = null;
const designPrinciplesState = {
  rootHandle: null,
  tree: [],
  nodeMap: new Map(),
  fileHandles: new Map(),
  cache: new Map(),
  expanded: new Set(),
  selectedPath: null,
  originalContent: "",
  dirty: false,
  lastFocusedTrigger: null,
  loading: false,
};

function applyTheme() {
  const isDark = state.theme === "dark";
  document.body.classList.toggle("theme-dark", isDark);
  if (themeToggle) {
    const label = isDark ? "Passer en mode clair" : "Passer en mode sombre";
    const translated = translate(label);
    themeToggle.textContent = translated;
    themeToggle.setAttribute("aria-label", translated);
    themeToggle.setAttribute("title", translated);
  }
}

function rerenderDetails() {
  if (!currentRecordDetail) return;
  renderOverview(currentRecordDetail);
  renderCriteriaPanel(currentRecordDetail);
  renderGuardrailsPanel(currentRecordDetail);
  renderPromptOptimizationPanel(currentRecordDetail);
  updateTabLabels(currentRecordDetail);
  setActiveTab(activeTab, { focusPanel: false });
}

function applyLanguage() {
  document.documentElement.lang = state.language;
  if (languageSelect) {
    languageSelect.value = state.language;
    languageSelect.setAttribute("aria-label", translate("Langue"));
  }
  if (appTitleEl) {
    const title = translate("SRL4Children | Design Principles and Tools – POC");
    appTitleEl.textContent = title;
    document.title = title;
  }
  if (instructionsEl) {
    instructionsEl.textContent = translate("Bienvenue sur SRL4Children : sélectionnez un dossier de benchmark (JSON) pour explorer les prompts et résultats.");
  }
  if (pickOutputsBtn) {
    pickOutputsBtn.innerHTML = translate("Choisir le dossier <code>outputs</code>");
  }
  if (filePickerLabelEl) {
    filePickerLabelEl.textContent = translate("Ou charger via sélection de dossier");
  }
  if (designPrinciplesBtn) {
    designPrinciplesBtn.textContent = translate("Principes de conception");
  }
  if (benchmarkSelectLabel) {
    benchmarkSelectLabel.textContent = translate("Benchmarks disponibles :");
  }
  if (benchmarkSelectEl && benchmarkSelectEl.options && benchmarkSelectEl.options.length) {
    benchmarkSelectEl.options[0].textContent = translate("— Aucun dossier sélectionné —");
  }
  if (searchInput) {
    searchInput.placeholder = translate("Rechercher un mot-clé dans les prompts");
    searchInput.setAttribute("aria-label", translate("Recherche sur les prompts"));
  }
  if (exportCsvBtn) {
    exportCsvBtn.textContent = translate("Exporter le tableau en CSV");
  }
  if (tableEmptyEl) {
    tableEmptyEl.textContent = translate("Aucun fichier chargé.");
  }
  if (gsModelLabelEl) {
    gsModelLabelEl.textContent = translate("Modèle :");
  }
  if (gsAvgScoreLabelEl) {
    gsAvgScoreLabelEl.textContent = translate("Score global moyen");
  }
  if (thModel) thModel.textContent = translate("Modèle");
  if (thPrompt) thPrompt.textContent = translate("Prompts");
  if (thCategory) thCategory.textContent = translate("Catégorie");
  if (thDate) thDate.textContent = translate("Date - Heure");
  if (thMaturity) thMaturity.textContent = translate("Tranche Âge");
  if (thDpCheck) thDpCheck.textContent = translate("DP Check");
  if (thScore) thScore.textContent = translate("Scores");
  if (thActions) thActions.textContent = translate("Actions");
  const tabLabelKeys = [
    "Résumé",
    "Principes de conception",
    "Guardrails",
    "Avant / Après Guardrails",
  ];
  tabButtons.forEach((btn, index) => {
    const key = tabLabelKeys[index] || btn.textContent;
    btn.dataset.defaultLabelKey = key;
    const translated = translate(index === 0 ? "Résumé" : key);
    btn.textContent = translated;
  });
  updateTabLabels(currentRecordDetail);
  if (downloadReportBtn) {
    const label = translate("Télécharger le rapport");
    downloadReportBtn.textContent = label;
    downloadReportBtn.setAttribute("aria-label", label);
  }
  if (designPrinciplesSaveBtn) {
    const saveLabel = translate("Enregistrer");
    designPrinciplesSaveBtn.textContent = saveLabel;
    designPrinciplesSaveBtn.setAttribute("aria-label", saveLabel);
  }
  if (closeOverlayBtn) {
    closeOverlayBtn.setAttribute("aria-label", translate("Fermer"));
  }
  if (closeDesignPrinciplesBtn) {
    closeDesignPrinciplesBtn.setAttribute("aria-label", translate("Fermer"));
  }
  if (detailsTitleEl) {
    detailsTitleEl.textContent = translate("Détails");
  }
  if (designPrinciplesTitleEl) {
    designPrinciplesTitleEl.textContent = translate("Principes de conception");
  }
  if (designPrinciplesTree) {
    designPrinciplesTree.setAttribute("aria-label", translate("Principes de conception"));
  }
  if (designPrinciplesEmpty) {
    designPrinciplesEmpty.textContent = translate("Sélectionnez un Design Principle dans la liste pour afficher et modifier son prompt.");
  }
  if (tabList) {
    tabList.setAttribute("aria-label", translate("Sections du record"));
  }
  if (gsSection) {
    gsSection.setAttribute("aria-label", translate("Synthèse globale"));
  }
  applyTheme();
  rerenderDetails();
  updateDesignPrinciplesPath(designPrinciplesState.selectedPath ? designPrinciplesState.nodeMap.get(designPrinciplesState.selectedPath) : null);
  renderDesignPrinciplesTree();
}

applyLanguage();
resetDesignPrinciplesEditor();

function updateTabLabels(record = currentRecordDetail) {
  const fallback = translate(tabButtons[0]?.dataset.defaultLabelKey || "Résumé");
  const labels = [
    record?.model ? record.model : fallback,
    translate("Principes de conception"),
    translate("Guardrails"),
    translate("Avant / Après Guardrails"),
  ];
  tabButtons.forEach((btn, index) => {
    if (!btn) return;
    const label = labels[index];
    if (label) {
      btn.textContent = label;
    }
  });
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    state.theme = state.theme === "dark" ? "light" : "dark";
    safeSetLocalStorage(THEME_STORAGE_KEY, state.theme);
    applyTheme();
  });
}

if (languageSelect) {
  languageSelect.addEventListener("change", (event) => {
    const nextLanguage = event.target.value === "en" ? "en" : "fr";
    if (state.language === nextLanguage) return;
    state.language = nextLanguage;
    safeSetLocalStorage(LANGUAGE_STORAGE_KEY, state.language);
    applyLanguage();
  });
}

function setStatus(message, type = "info", params = {}) {
  statusEl.textContent = translate(message, params);
  statusEl.dataset.type = type;
}

function readJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const text = reader.result;
        const parsed = JSON.parse(text);
        resolve(parsed);
      } catch (error) {
        reject(new Error(`Impossible de parser ${file.name}: ${error.message}`));
      }
    };
    reader.onerror = () => reject(new Error(`Erreur lecture ${file.name}`));
    reader.readAsText(file);
  });
}

function normaliseValue(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  if (typeof value === "string") return value.trim();
  return String(value);
}

function formatDate(timestamp) {
  if (!timestamp) return "";
  try {
    return new Date(timestamp).toLocaleString();
  } catch (err) {
    return "";
  }
}

function formatScore(score, fallback = "—") {
  if (typeof score === "number" && Number.isFinite(score)) {
    return score.toFixed(2);
  }
  return fallback;
}

async function ensureFsPermission(handle, mode = "read") {
  if (!handle) return false;
  if (typeof handle.queryPermission !== "function" || typeof handle.requestPermission !== "function") {
    return true;
  }
  try {
    const options = { mode };
    const current = await handle.queryPermission(options);
    if (current === "granted") return true;
    if (current === "denied") return false;
    const requested = await handle.requestPermission(options);
    return requested === "granted";
  } catch (error) {
    console.warn("Permission request failed", error);
    return false;
  }
}

async function locateCriteriaDirectory(handle) {
  if (!handle || handle.kind !== "directory") return null;
  if (handle.name === "criteria") return handle;

  const tryGet = async (dir, name) => {
    try {
      return await dir.getDirectoryHandle(name);
    } catch (error) {
      return null;
    }
  };

  const direct = await tryGet(handle, "criteria");
  if (direct) return direct;
  const assets = await tryGet(handle, "assets");
  if (assets) {
    const criteria = await tryGet(assets, "criteria");
    if (criteria) return criteria;
  }
  return null;
}

async function ensureDesignPrinciplesRoot() {
  if (designPrinciplesState.rootHandle) {
    const ok = await ensureFsPermission(designPrinciplesState.rootHandle, "read");
    if (!ok) {
      const retry = await ensureFsPermission(designPrinciplesState.rootHandle, "readwrite");
      if (!retry) {
        setStatus("Autorisation refusée pour accéder aux Design Principles.", "warning");
        return null;
      }
    }
    return designPrinciplesState.rootHandle;
  }

  if (!window.showDirectoryPicker) {
    setStatus("showDirectoryPicker n'est pas supporté dans ce navigateur. Utilisez la sélection de dossier classique.", "warning");
    return null;
  }

  try {
    const picked = await window.showDirectoryPicker({ mode: "readwrite" });
    const criteria = await locateCriteriaDirectory(picked);
    if (!criteria) {
      setStatus("Veuillez sélectionner le dossier assets/criteria.", "warning");
      return null;
    }
    const allowed = await ensureFsPermission(criteria, "readwrite");
    if (!allowed) {
      setStatus("Autorisation refusée pour accéder aux Design Principles.", "warning");
      return null;
    }
    designPrinciplesState.rootHandle = criteria;
    designPrinciplesState.rootLabel = criteria.name || "criteria";
    if (!designPrinciplesState.expanded.size) {
      designPrinciplesState.expanded.add("");
    }
    return criteria;
  } catch (error) {
    if (error.name !== "AbortError") {
      setStatus("Impossible d'accéder au dossier: {message}", "warning", { message: error.message });
    }
    return null;
  }
}

async function buildDesignPrinciplesTree(handle, pathParts = []) {
  const nodes = [];
  for await (const entry of handle.values()) {
    if (entry.name?.startsWith(".")) continue;
    if (entry.kind === "directory") {
      const childParts = [...pathParts, entry.name];
      const pathKey = childParts.join("/");
      const node = {
        type: "directory",
        name: entry.name,
        displayName: humanizeIdentifier(entry.name),
        handle: entry,
        pathParts: childParts,
        pathKey,
      };
      node.children = await buildDesignPrinciplesTree(entry, childParts);
      designPrinciplesState.nodeMap.set(pathKey, node);
      nodes.push(node);
    } else if (entry.kind === "file" && entry.name.endsWith(".prompt")) {
      const childParts = [...pathParts, entry.name];
      const pathKey = childParts.join("/");
      const node = {
        type: "file",
        name: entry.name,
        displayName: humanizeIdentifier(entry.name.replace(/\.prompt$/i, "")),
        handle: entry,
        pathParts: childParts,
        pathKey,
      };
      designPrinciplesState.nodeMap.set(pathKey, node);
      designPrinciplesState.fileHandles.set(pathKey, entry);
      nodes.push(node);
    }
  }
  nodes.sort((a, b) => {
    if (a.type === b.type) {
      return a.displayName.localeCompare(b.displayName);
    }
    return a.type === "directory" ? -1 : 1;
  });
  return nodes;
}

async function loadDesignPrinciplesTree({ force = false } = {}) {
  const rootHandle = await ensureDesignPrinciplesRoot();
  if (!rootHandle) return false;

  if (!force && !designPrinciplesState.loading && designPrinciplesState.tree.length) {
    renderDesignPrinciplesTree();
    return true;
  }

  designPrinciplesState.loading = true;
  renderDesignPrinciplesTree();
  designPrinciplesState.nodeMap = new Map();
  designPrinciplesState.fileHandles = new Map();

  try {
    const tree = await buildDesignPrinciplesTree(rootHandle, []);
    designPrinciplesState.tree = tree;
    if (designPrinciplesState.expanded.size <= 1) {
      tree.forEach((node) => {
        if (node.type === "directory") {
          designPrinciplesState.expanded.add(node.pathKey);
        }
      });
    }
    if (designPrinciplesState.selectedPath && !designPrinciplesState.nodeMap.has(designPrinciplesState.selectedPath)) {
      resetDesignPrinciplesEditor();
    }
  } catch (error) {
    console.error("Unable to build Design Principles tree", error);
    setStatus("Impossible de charger les Design Principles.", "warning");
  } finally {
    designPrinciplesState.loading = false;
    renderDesignPrinciplesTree();
  }

  return true;
}

function renderDesignPrinciplesTree() {
  if (!designPrinciplesTree) return;
  designPrinciplesTree.innerHTML = "";

  if (designPrinciplesState.loading) {
    const loading = document.createElement("div");
    loading.className = "design-principles-message";
    loading.textContent = translate("Chargement des Design Principles…");
    designPrinciplesTree.appendChild(loading);
    return;
  }

  if (!designPrinciplesState.tree.length) {
    const empty = document.createElement("div");
    empty.className = "design-principles-message";
    empty.textContent = translate("Aucun Design Principle détecté.");
    designPrinciplesTree.appendChild(empty);
    return;
  }

  const list = createDesignPrinciplesList(designPrinciplesState.tree);
  designPrinciplesTree.appendChild(list);
}

function createDesignPrinciplesList(nodes) {
  const list = document.createElement("ul");
  list.className = "design-principles-tree-list";

  nodes.forEach((node) => {
    const item = document.createElement("li");
    if (node.type === "directory") {
      const details = document.createElement("details");
      details.className = "design-principles-dir";
      details.dataset.path = node.pathKey;
      if (!node.pathKey || designPrinciplesState.expanded.has(node.pathKey)) {
        details.open = true;
      }
      details.addEventListener("toggle", handleDesignPrinciplesToggle);

      const summary = document.createElement("summary");
      summary.className = "design-principles-summary";
      summary.dataset.path = node.pathKey;
      summary.textContent = node.displayName;
      details.appendChild(summary);

      const children = node.children?.length ? createDesignPrinciplesList(node.children) : document.createElement("ul");
      if (!node.children?.length) {
        children.className = "design-principles-tree-list";
      }
      details.appendChild(children);
      item.appendChild(details);
    } else {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "design-principles-file-btn";
      if (designPrinciplesState.selectedPath === node.pathKey) {
        button.classList.add("active");
      }
      button.dataset.path = node.pathKey;
      button.textContent = node.displayName;
      item.appendChild(button);
    }
    list.appendChild(item);
  });

  return list;
}

function handleDesignPrinciplesToggle(event) {
  const details = event.target;
  if (!(details instanceof HTMLDetailsElement)) return;
  const path = details.dataset.path;
  if (!path) return;
  if (details.open) {
    designPrinciplesState.expanded.add(path);
  } else {
    designPrinciplesState.expanded.delete(path);
  }
}

function updateDesignPrinciplesPath(node) {
  if (!designPrinciplesPathEl) return;
  if (!node) {
    designPrinciplesPathEl.textContent = "—";
    designPrinciplesPathEl.removeAttribute("title");
    return;
  }
  const formatted = formatDesignPrinciplePath(node.pathParts);
  designPrinciplesPathEl.textContent = formatted;
  designPrinciplesPathEl.title = node.pathParts.join("/");
}

function formatDesignPrinciplePath(parts = []) {
  if (!parts.length) return "—";
  return parts
    .map((part, index) => formatDesignPrincipleLabel(part, index === parts.length - 1))
    .join(" › ");
}

function formatDesignPrincipleLabel(part, isFile) {
  if (isFile) {
    return humanizeIdentifier(part.replace(/\.prompt$/i, ""));
  }
  return humanizeIdentifier(part);
}

function resetDesignPrinciplesEditor() {
  designPrinciplesState.selectedPath = null;
  designPrinciplesState.originalContent = "";
  designPrinciplesState.dirty = false;
  if (designPrinciplesEditor) {
    designPrinciplesEditor.value = "";
    designPrinciplesEditor.classList.add("is-hidden");
    designPrinciplesEditor.disabled = true;
  }
  if (designPrinciplesEmpty) {
    designPrinciplesEmpty.classList.remove("is-hidden");
    designPrinciplesEmpty.textContent = translate("Sélectionnez un Design Principle dans la liste pour afficher et modifier son prompt.");
  }
  updateDesignPrinciplesPath(null);
  updateDesignPrinciplesSaveState();
}

function updateDesignPrinciplesSaveState() {
  if (!designPrinciplesSaveBtn) return;
  const disabled = !designPrinciplesState.selectedPath || !designPrinciplesState.dirty;
  designPrinciplesSaveBtn.disabled = disabled;
}

function setDesignPrinciplesDirty(isDirty) {
  designPrinciplesState.dirty = Boolean(isDirty);
  updateDesignPrinciplesSaveState();
}

function confirmDesignPrinciplesDiscard() {
  if (!designPrinciplesState.dirty) return true;
  return window.confirm(translate("Des modifications non enregistrées seront perdues. Continuer ?"));
}

async function selectDesignPrinciple(pathKey) {
  if (!pathKey || designPrinciplesState.selectedPath === pathKey) return;
  if (!confirmDesignPrinciplesDiscard()) return;

  const node = designPrinciplesState.nodeMap.get(pathKey);
  if (!node || node.type !== "file") return;

  try {
    let content = designPrinciplesState.cache.get(pathKey);
    if (content === undefined) {
      content = await readDesignPrincipleContent(node);
      designPrinciplesState.cache.set(pathKey, content);
    }

    designPrinciplesState.selectedPath = pathKey;
    designPrinciplesState.originalContent = content;
    setDesignPrinciplesDirty(false);

    if (designPrinciplesEditor) {
      designPrinciplesEditor.disabled = false;
      designPrinciplesEditor.classList.remove("is-hidden");
      designPrinciplesEditor.value = content;
      designPrinciplesEditor.focus();
    }
    if (designPrinciplesEmpty) {
      designPrinciplesEmpty.classList.add("is-hidden");
    }
    updateDesignPrinciplesPath(node);
    renderDesignPrinciplesTree();
  } catch (error) {
    console.error("Unable to load design principle", error);
    setStatus("Impossible de charger ce Design Principle.", "warning");
  }
}

async function readDesignPrincipleContent(node) {
  try {
    const handle = designPrinciplesState.fileHandles.get(node.pathKey) || node.handle;
    if (!handle) throw new Error("Missing file handle");
    const hasPermission = await ensureFsPermission(handle, "read");
    if (!hasPermission) {
      const retry = await ensureFsPermission(handle, "readwrite");
      if (!retry) {
        throw new Error("Permission denied");
      }
    }
    const file = await handle.getFile();
    return await file.text();
  } catch (error) {
    throw error;
  }
}

async function saveDesignPrinciple() {
  if (!designPrinciplesState.selectedPath) return;
  const handle = designPrinciplesState.fileHandles.get(designPrinciplesState.selectedPath);
  if (!handle || !designPrinciplesEditor) return;

  try {
    const allowed = await ensureFsPermission(handle, "readwrite");
    if (!allowed) {
      setStatus("Autorisation refusée pour accéder aux Design Principles.", "warning");
      return;
    }
    const writable = await handle.createWritable();
    await writable.write(designPrinciplesEditor.value);
    await writable.close();

    designPrinciplesState.originalContent = designPrinciplesEditor.value;
    designPrinciplesState.cache.set(designPrinciplesState.selectedPath, designPrinciplesEditor.value);
    setDesignPrinciplesDirty(false);
    setStatus("Design Principle sauvegardé.", "info");
  } catch (error) {
    console.error("Unable to save design principle", error);
    setStatus("Impossible d'enregistrer ce Design Principle.", "warning");
  }
}

async function openDesignPrinciplesModal() {
  designPrinciplesState.lastFocusedTrigger = document.activeElement;
  const loaded = await loadDesignPrinciplesTree({ force: false });
  if (!loaded) return;
  if (designPrinciplesOverlay) {
    designPrinciplesOverlay.classList.remove("hidden");
    designPrinciplesOverlay.focus();
  }
  renderDesignPrinciplesTree();
  const focusTarget =
    (designPrinciplesTree && designPrinciplesTree.querySelector(".design-principles-file-btn.active")) ||
    (designPrinciplesTree && designPrinciplesTree.querySelector(".design-principles-file-btn"));
  if (focusTarget && typeof focusTarget.focus === "function") {
    focusTarget.focus();
  }
}

function closeDesignPrinciplesModal({ force = false } = {}) {
  if (!designPrinciplesOverlay || designPrinciplesOverlay.classList.contains("hidden")) return;
  if (!force && !confirmDesignPrinciplesDiscard()) return;
  designPrinciplesOverlay.classList.add("hidden");
  if (designPrinciplesState.lastFocusedTrigger && typeof designPrinciplesState.lastFocusedTrigger.focus === "function") {
    designPrinciplesState.lastFocusedTrigger.focus();
  }
  designPrinciplesState.lastFocusedTrigger = null;
  renderDesignPrinciplesTree();
}

function handleDesignPrinciplesTreeClick(event) {
  const button = event.target.closest(".design-principles-file-btn");
  if (!button) return;
  const path = button.dataset.path;
  if (path) {
    selectDesignPrinciple(path);
  }
}

function getScoreZone(score) {
  if (typeof score !== "number" || !Number.isFinite(score)) return "";
  if (score <= 1) return "low";
  if (score <= 3) return "mid";
  return "high";
}

function applyScoreZone(element, score) {
  if (!element) return;
  const zone = getScoreZone(score);
  if (zone) {
    element.setAttribute("data-zone", zone);
  } else {
    element.removeAttribute("data-zone");
  }
}

function buildRecord(file, json, options = {}) {
  const { sourcePath = null } = options;
  const recordData = json.record_data || {};
  const fileTimestamp = file && file.lastModified ? file.lastModified : undefined;
  const fallbackTimestamp = (() => {
    const ts = recordData.timestamp || json.timestamp;
    if (!ts) return undefined;
    const numeric = Date.parse(ts);
    return Number.isNaN(numeric) ? undefined : numeric;
  })();
  const lastModified = fileTimestamp ?? fallbackTimestamp;
  const judgeResult = recordData.judge_v1_1_result || json.judge_v1_1_result || null;
  const fallbackScore = recordData.judge_final_score || json.judge_final_score;
  const finalScore = (() => {
    const value = judgeResult?.final_aggregate_score ?? fallbackScore;
    return typeof value === "number" && Number.isFinite(value) ? value : null;
  })();
  const fullPrompt = typeof recordData.full_prompt === "string"
    ? recordData.full_prompt
    : typeof json.full_prompt === "string"
      ? json.full_prompt
      : recordData.prompt || "";
  const reply = typeof recordData.reply === "string"
    ? recordData.reply
    : typeof json.reply === "string"
      ? json.reply
      : "";
  const filePath = (() => {
    if (typeof sourcePath === "string" && sourcePath.trim()) return sourcePath.trim();
    if (file && typeof file.webkitRelativePath === "string" && file.webkitRelativePath.trim()) {
      return file.webkitRelativePath.trim();
    }
    if (file && typeof file.name === "string" && file.name.trim()) {
      return file.name.trim();
    }
    if (typeof json?.record_path === "string" && json.record_path.trim()) {
      return json.record_path.trim();
    }
    return "";
  })();
  const recordFileName = file ? file.name : (sourcePath ? sourcePath.split("/").pop() : "");
  return {
    fileName: recordFileName || "",
    filePath,
    id: normaliseValue(recordData.id || recordData.guid || ""),
    model: normaliseValue(recordData.model || json.model, "inconnu"),
    prompt: normaliseValue(recordData.prompt || recordData.full_prompt || ""),
    category: normaliseValue(recordData.category || ""),
    maturity: normaliseValue(recordData.maturity || ""),
    criteria_selection: normaliseValue(recordData.criteria_selection || json.criteria_selection || ""),
    date: formatDate(lastModified || recordData.timestamp || json.timestamp),
    lastModified,
    selected: true,
    guardrail_status: "0",
    hasGuardrails: false,
    finalScore,
    judgeResult,
    fullPrompt,
    reply,
    phaseResults: json.phase_results || {},
    raw: json,
  };
}

function applySearch(records, term) {
  if (!term) return [...records];
  const lower = term.toLowerCase();
  return records.filter((record) => record.prompt.toLowerCase().includes(lower));
}

function applySort(records, key, dir) {
  if (!key) return [...records];
  const multiplier = dir === "desc" ? -1 : 1;
  return [...records].sort((a, b) => {
    if (key === "date") {
      const aTime = a.lastModified || 0;
      const bTime = b.lastModified || 0;
      if (aTime < bTime) return -1 * multiplier;
      if (aTime > bTime) return 1 * multiplier;
      return 0;
    }
    if (key === "finalScore") {
      const defaultVal = dir === "asc" ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
      const aScore = typeof a.finalScore === "number" ? a.finalScore : defaultVal;
      const bScore = typeof b.finalScore === "number" ? b.finalScore : defaultVal;
      if (aScore < bScore) return -1 * multiplier;
      if (aScore > bScore) return 1 * multiplier;
      return 0;
    }
    const valA = (a[key] || "").toLowerCase();
    const valB = (b[key] || "").toLowerCase();
    if (valA < valB) return -1 * multiplier;
    if (valA > valB) return 1 * multiplier;
    return 0;
  });
}

function paginate(records, pageSize, page) {
  const totalPages = Math.max(1, Math.ceil(records.length / pageSize));
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const start = (safePage - 1) * pageSize;
  const slice = records.slice(start, start + pageSize);
  return { slice, totalPages, page: safePage };
}

function renderTable() {
  const { sortKey, sortDir, pageSize, currentPage, filtered } = state;
  const sorted = applySort(filtered, sortKey, sortDir);
  state.currentSorted = sorted;
  const { slice, totalPages, page } = paginate(sorted, pageSize, currentPage);
  state.currentPage = page;

  if (!slice.length) {
    tableBody.innerHTML = `<tr><td colspan="9" class="empty">${translate("Aucun résultat.")}</td></tr>`;
  } else {
    tableBody.innerHTML = slice
      .map((record, index) => {
        const globalIndex = (page - 1) * pageSize + index;
        const categoryValue = escapeAttr(record.category);
        const maturitySelect = renderMaturitySelect(record, globalIndex);
        const formattedScore = formatScore(record.finalScore, "—");
        const scoreZone = getScoreZone(record.finalScore);
        const scoreAttr = scoreZone ? ` data-zone="${scoreZone}"` : "";
        const scoreHtml = formattedScore !== "—"
          ? `<span class="score-badge score-badge-table"${scoreAttr}>${escapeHtml(formattedScore)}</span>`
          : escapeHtml(formattedScore);
        const hasGuardrails = record.guardrail_status === "1";
        const dpLabel = translate(hasGuardrails ? "Guardrails générés" : "Guardrails manquants");
        const dpClass = hasGuardrails ? "dp-check dp-check--ok" : "dp-check dp-check--missing";
        const dpIcon = hasGuardrails ? "✅" : "❌";
        const dpCheckHtml = `<span class="${dpClass}" role="img" aria-label="${escapeAttr(dpLabel)}" title="${escapeAttr(dpLabel)}">${dpIcon}</span>`;
        return `
          <tr>
            <td class="select-col"><input type="checkbox" class="row-select" data-index="${globalIndex}" ${record.selected ? "checked" : ""}></td>
            <td>${escapeHtml(record.model)}</td>
            <td class="prompt">${escapeHtml(record.prompt)}</td>
            <td class="editable"><input type="text" class="category-input" data-index="${globalIndex}" value="${categoryValue}" placeholder="Catégorie"></td>
            <td class="date">${escapeHtml(record.date)}</td>
            <td class="editable">${maturitySelect}</td>
            <td class="dp-check-cell">${dpCheckHtml}</td>
            <td class="score">${scoreHtml}</td>
            <td><button class="details-btn" data-index="${globalIndex}">Détails</button></td>
          </tr>
        `;
      })
      .join("");
  }

  renderPagination(totalPages);
  updateHeaderIndicators();
  updateStats();
  renderGlobalSummary();
}

function renderPagination(totalPages) {
  if (totalPages <= 1) {
    paginationEl.innerHTML = "";
    return;
  }
  const { currentPage } = state;
  const buttons = [];

  const addButton = (label, page, disabled = false, active = false) => {
    buttons.push(`<button ${disabled ? "disabled" : ""} data-page="${page}" class="${active ? "active" : ""}">${label}</button>`);
  };

  addButton("◀", Math.max(1, currentPage - 1), currentPage === 1);
  for (let p = 1; p <= totalPages; p++) {
    addButton(p, p, false, p === currentPage);
  }
  addButton("▶", Math.min(totalPages, currentPage + 1), currentPage === totalPages);

  paginationEl.innerHTML = buttons.join("");
}

function updateHeaderIndicators() {
  const headers = document.querySelectorAll("thead th[data-key]");
  headers.forEach((th) => {
    th.classList.remove("sort-asc", "sort-desc");
    const key = th.dataset.key;
    if (key === state.sortKey) {
      th.classList.add(state.sortDir === "asc" ? "sort-asc" : "sort-desc");
    }
  });
}

function updateStats() {
  const totalRecords = state.records.length;
  const shown = state.filtered.length;
  const included = state.records.reduce((sum, record) => sum + (record.selected ? 1 : 0), 0);
  statsEl.textContent = totalRecords
    ? `${shown} résultats (sur ${totalRecords} fichiers chargés) · ${included} inclus`
    : "";
}

function escapeHtml(value) {
  const str = value === undefined || value === null ? "" : String(value);
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

function escapeHtmlSimple(value) {
  const str = value === undefined || value === null ? "" : String(value);
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function basicMarkdownToHtml(text) {
  const lines = text.split(/\r?\n/);
  const html = [];
  let inList = false;

  const flushList = () => {
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trimEnd();
    if (!line.trim()) {
      flushList();
      html.push("");
      return;
    }

    const listMatch = line.match(/^[-*+]\s+(.*)$/);
    if (listMatch) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      const content = basicInlineFormatting(listMatch[1]);
      html.push(`<li>${content}</li>`);
      return;
    }

    flushList();
    html.push(`<p>${basicInlineFormatting(line)}</p>`);
  });

  flushList();
  return html.join("\n").replace(/(?:\n){3,}/g, "\n\n");
}

function basicInlineFormatting(text) {
  const escaped = escapeHtmlSimple(text);
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMaturitySelect(record, index) {
  const current = record.maturity || "";
  const options = new Set(MATURITY_OPTIONS.concat(current ? [current] : []));
  const htmlOptions = Array.from(options)
    .map((opt) => {
      const selected = opt === current ? "selected" : "";
      return `<option value="${escapeAttr(opt)}" ${selected}>${escapeHtml(opt)}</option>`;
    })
    .join("");
  const emptySelected = current ? "" : "selected";
  const undefinedLabel = escapeHtml(translate("(non défini)"));
  return `<select class=\"maturity-select\" data-index=\"${index}\">
    <option value=\"\" ${emptySelected}>${undefinedLabel}</option>
    ${htmlOptions}
  </select>`;
}

function clearElement(el) {
  while (el.firstChild) {
    el.removeChild(el.firstChild);
  }
}

function syncGuardrailStatus(record) {
  if (!record) return;
  const hasGuardrails = Boolean(record.guardrailData || record.guardrailSource);
  record.hasGuardrails = hasGuardrails;
  record.guardrail_status = hasGuardrails ? "1" : "0";
}

function getGuardrailCommandContext() {
  const explicit = window.guardrailCommandCwd || document.body?.dataset?.guardrailCwd;
  if (typeof explicit === "string" && explicit.trim()) {
    return explicit.trim();
  }
  return null;
}

async function executeGuardrailCommand(command, options = {}) {
  if (!command || typeof command !== "string") {
    throw new Error("Command must be a non-empty string.");
  }
  const context = options.cwd ?? getGuardrailCommandContext();
  if (window.guardrailExecutor?.runCommand) {
    return window.guardrailExecutor.runCommand({ command, cwd: context, recordPath: options.recordPath || null });
  }
  if (window.guardrailExecutor?.run) {
    return window.guardrailExecutor.run(command, context, options.recordPath || null);
  }
  if (window.api?.runGuardrailCommand) {
    return window.api.runGuardrailCommand({ command, cwd: context, recordPath: options.recordPath || null });
  }
  if (window.electronAPI?.runGuardrailCommand) {
    return window.electronAPI.runGuardrailCommand(command, context);
  }
  if (window.electronAPI?.invoke) {
    return window.electronAPI.invoke("run-guardrail-command", { command, cwd: context, recordPath: options.recordPath || null });
  }
  if (window.__TAURI__?.invoke) {
    return window.__TAURI__.invoke("run_guardrail_command", { command, cwd: context, recordPath: options.recordPath || null });
  }

  const endpoint = options.endpoint
    || window.guardrailCommandEndpoint
    || document.body?.dataset?.guardrailEndpoint
    || null;

  if (endpoint && typeof fetch === "function") {
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command,
          cwd: context,
          recordPath: options.recordPath || null,
        }),
      });
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.code = "RUNNER_HTTP_ERROR";
        throw error;
      }
      const data = await response.json().catch(() => null);
      return data;
    } catch (error) {
      if (!error.code) {
        error.code = "RUNNER_REQUEST_FAILED";
      }
      throw error;
    }
  }

  const unavailable = new Error("Guardrail command execution is not configured.");
  unavailable.code = "RUNNER_UNAVAILABLE";
  throw unavailable;
}

function collectGuardrailFilesFromUpload(files) {
  const map = new Map();
  files.forEach((file) => {
    const relativePath = typeof file.webkitRelativePath === "string" && file.webkitRelativePath
      ? file.webkitRelativePath
      : file.name;
    if (!relativePath.toLowerCase().includes("/guardrails/")) return;
    const segments = relativePath.split("/");
    const fileName = segments.pop();
    if (!fileName.toLowerCase().endsWith(".json")) return;
    if (!fileName.startsWith("guardrails_")) return;
    if (!segments.length) return;
    const parentSegments = [...segments];
    const lastSegment = parentSegments[parentSegments.length - 1];
    if (lastSegment === "guardrails") {
      parentSegments.pop();
    }
    const recordFileName = fileName.replace(/^guardrails_/, "record_");
    const recordPath = parentSegments.length
      ? `${parentSegments.join("/")}/${recordFileName}`
      : recordFileName;
    map.set(recordPath, { type: "file", file, path: relativePath });
  });
  return map;
}

async function collectGuardrailHandlesFromDirectory(dirHandle) {
  const map = new Map();
  try {
    const guardrailsDir = await dirHandle.getDirectoryHandle("guardrails");
    for await (const entry of guardrailsDir.values()) {
      if (entry.kind !== "file") continue;
      if (!entry.name.toLowerCase().endsWith(".json")) continue;
      if (!entry.name.startsWith("guardrails_")) continue;
      const recordFileName = entry.name.replace(/^guardrails_/, "record_");
      const recordPath = `${dirHandle.name}/${recordFileName}`;
      const fullPath = `${dirHandle.name}/guardrails/${entry.name}`;
      map.set(recordPath, { type: "handle", handle: entry, path: fullPath });
    }
  } catch (err) {
    // guardrails directory may not exist; ignore
  }
  return map;
}

async function loadGuardrailContent(source) {
  if (!source) return null;
  try {
    if (source.type === "file" && source.file) {
      const text = await source.file.text();
      return JSON.parse(text);
    }
    if (source.type === "handle" && source.handle?.getFile) {
      const file = await source.handle.getFile();
      const text = await file.text();
      return JSON.parse(text);
    }
  } catch (error) {
    console.error("Failed to load guardrails:", error);
  }
  return null;
}

function setActiveTab(tabName, options = {}) {
  const { focusPanel = true } = options;
  if (!tabPanels[tabName]) return;
  activeTab = tabName;
  tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === tabName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.tabIndex = isActive ? 0 : -1;
  });
  Object.entries(tabPanels).forEach(([name, panel]) => {
    if (!panel) return;
    const isActive = name === tabName;
    panel.classList.toggle("hidden", !isActive);
    panel.setAttribute("aria-hidden", isActive ? "false" : "true");
    if (isActive && focusPanel) {
      panel.focus();
    }
  });
}

function renderOverview(record) {
  if (!overviewPanel) return;
  clearElement(overviewPanel);

  const judge = record.judgeResult;

  const layout = document.createElement("div");
  layout.className = "overview-combined";

  const leftColumn = document.createElement("div");
  leftColumn.className = "overview-left";

  const promptContent = record.fullPrompt || record.prompt || record.raw?.record_data?.full_prompt || record.raw?.record_data?.prompt || "";
  const responseContent = record.reply || record.raw?.record_data?.reply || "";

  leftColumn.appendChild(createTextPanel(translate("Prompt complet"), promptContent, { variant: "prompt" }));
  leftColumn.appendChild(createTextPanel(translate("Réponse du modèle"), responseContent, { variant: "prompt" }));

  const rightColumn = document.createElement("aside");
  rightColumn.className = "overview-right";

  const scoreSummary = document.createElement("section");
  scoreSummary.className = "score-summary-card";
  const scoreTitle = document.createElement("p");
  scoreTitle.className = "score-summary-label";
  scoreTitle.textContent = translate("Score global");
  const scoreBadge = document.createElement("span");
  scoreBadge.className = "score-badge score-badge-large";
  scoreBadge.textContent = formatScore(record.finalScore);
  applyScoreZone(scoreBadge, record.finalScore);
  scoreSummary.append(scoreTitle, scoreBadge);
  rightColumn.appendChild(scoreSummary);

  if (judge) {
    const subcategoryEntries = Object.entries(judge.subcategory_scores || {})
      .filter(([, value]) => typeof value === "number")
      .sort(([a], [b]) => a.localeCompare(b));

    if (subcategoryEntries.length) {
      const subSection = document.createElement("section");
      subSection.className = "score-section score-section-sidebar";
      renderOverviewRadarChart(subSection, judge, {
        customEntries: subcategoryEntries,
        title: translate("Scores par sous-catégorie"),
      });
      const subList = document.createElement("ul");
      subList.className = "score-list";
      subcategoryEntries.forEach(([path, value]) => {
        const item = document.createElement("li");
        const label = document.createElement("span");
        label.textContent = humanizePath(path);
        const scoreEl = document.createElement("span");
        scoreEl.className = "score-badge score-badge-inline";
        scoreEl.textContent = formatScore(value);
        applyScoreZone(scoreEl, value);
        item.append(label, scoreEl);
        subList.appendChild(item);
      });
      subSection.appendChild(subList);
      rightColumn.appendChild(subSection);
    }
  }

  const metadataCard = document.createElement("section");
  metadataCard.className = "metadata-card";
  const metadataTitle = document.createElement("h3");
  metadataTitle.textContent = translate("Métadonnées");
  const metaList = document.createElement("dl");
  metaList.className = "meta-grid";
  appendMeta(metaList, translate("ID record"), record.id || record.fileName || "—");
  appendMeta(metaList, translate("Fichier source"), record.filePath || "—");
  appendMeta(metaList, translate("Modèle"), record.model || "—");
  appendMeta(metaList, translate("Preset critères"), record.criteria_selection || "—");
  // Extract main category (first part) and subcategories
  const fullCategory = record.category || "";
  const categoryParts = fullCategory.split(".");
  const mainCategory = categoryParts[0] || "—";
  const subCategories = categoryParts.length > 1 ? categoryParts.slice(1).join(" → ") : "—";

  appendMeta(metaList, translate("Catégorie"), mainCategory);
  appendMeta(metaList, translate("Sous-catégorie"), subCategories);
  appendMeta(metaList, translate("Maturité"), record.maturity || "—");
  appendMeta(metaList, translate("Mode"), normaliseValue(record.raw?.record_data?.mode || "") || "—");
  appendMeta(metaList, translate("Date de mise à jour"), record.date || "—");
  metadataCard.append(metadataTitle, metaList);
  metadataCard.classList.add("metadata-wide");

  layout.append(leftColumn, rightColumn);

  overviewPanel.append(layout, metadataCard);

  if (!judge) {
    const note = document.createElement("p");
    note.className = "empty";
    note.textContent = translate("Aucun score du juge v1.1 disponible pour ce record.");
    overviewPanel.appendChild(note);
  }
}
function appendMeta(list, label, value) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  dd.textContent = value || "—";
  list.append(dt, dd);
}

function renderOverviewRadarChart(container, judge, options = {}) {
  const { customEntries = null, title: titleOverride } = options;
  const chartData = customEntries
    ? { source: "custom", entries: customEntries }
    : pickRadarData(judge);
  if (!chartData || !chartData.entries || !chartData.entries.length) return;

  const chartSection = document.createElement("section");
  chartSection.className = "radar-section";
  const title = document.createElement("h3");
  title.textContent = titleOverride
    ? titleOverride
    : chartData.source === "subcategory"
      ? translate("Scores par sous-catégorie")
      : translate("Scores par catégorie");
  chartSection.appendChild(title);

  const canvas = document.createElement("canvas");
  const fallback = document.createElement("div");
  fallback.className = "radar-fallback hidden";
  fallback.textContent = translate("Chargement du graphique…");
  chartSection.append(canvas, fallback);
  container.appendChild(chartSection);

  const labels = chartData.entries.map(([key]) => humanizePath(key));
  const values = chartData.entries.map(([, value]) => (typeof value === "number" ? value : 0));

  renderRadarWithFallback({
    labels,
    values,
    canvas,
    fallback,
    setChartInstance(chart) {
      if (overviewRadarChart) {
        overviewRadarChart.destroy();
      }
      overviewRadarChart = chart;
    },
  });
}
function pickRadarData(judge) {
  if (!judge) return [];
  const subEntries = Object.entries(judge.subcategory_scores || {})
    .filter(([, value]) => typeof value === "number")
    .sort(([a], [b]) => a.localeCompare(b));
  if (subEntries.length >= 3) {
    return { source: "subcategory", entries: subEntries };
  }
  const catEntries = Object.entries(judge.category_scores || {})
    .filter(([, value]) => typeof value === "number")
    .sort(([a], [b]) => a.localeCompare(b));
  if (catEntries.length) {
    return { source: "category", entries: catEntries };
  }
  return [];
}

function createTextPanel(title, content, options = {}) {
  const { variant = "default" } = options;
  const article = document.createElement("article");
  article.className = "text-card";
  if (variant === "prompt") {
    article.classList.add("text-card--prompt");
  }
  const heading = document.createElement("h3");
  heading.textContent = title;
  const body = document.createElement("div");
  body.className = "text-card-body";

  if (variant === "prompt") {
    body.classList.add("text-card-body--prompt");
    const pre = document.createElement("pre");
    pre.className = "prompt-text";
    pre.classList.add("prompt-text--in-card");
    pre.textContent = content && content.trim() ? content : translate("Aucun contenu disponible.");
    body.appendChild(pre);
  } else if (content && content.trim()) {
    renderMarkdownToElement(body, content);
  } else {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = translate("Aucun contenu disponible.");
    body.appendChild(empty);
  }

  article.appendChild(heading);
  article.appendChild(body);
  return article;
}

function renderMarkdownToElement(container, text) {
  clearElement(container);
  container.classList.add("markdown-content");
  if (!text) {
    container.textContent = "";
    return;
  }
  const trimmed = text.trim();
  if (!trimmed) {
    container.textContent = "";
    return;
  }

  if (window.marked && window.DOMPurify) {
    const html = DOMPurify.sanitize(marked.parse(trimmed));
    container.innerHTML = html;
  } else if (window.marked) {
    container.innerHTML = marked.parse(trimmed);
  } else {
    container.innerHTML = basicMarkdownToHtml(trimmed);
  }
}

function renderCriteriaPanel(record) {
  if (!criteriaPanel) return;
  clearElement(criteriaPanel);
  const judge = record.judgeResult;

  if (!judge) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = translate("Aucun critère évalué pour ce record.");
    criteriaPanel.appendChild(empty);
  return;
}

  const tree = buildCriteriaTree(judge, record.phaseResults || {});
  const categories = Object.values(tree);
  if (!categories.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = translate("Aucune donnée détaillée disponible.");
    criteriaPanel.appendChild(empty);
    return;
  }

  const sortedCategories = categories.sort((a, b) => a.name.localeCompare(b.name));

  const expectedJudgeCount = Object.keys(record.phaseResults || {}).length;
  const hasPartialData = hasPartialJudgeData(sortedCategories, expectedJudgeCount);
  renderCriteriaSummarySection(criteriaPanel, sortedCategories, record.judgeResult?.consistency_metrics, { hasPartialData });

  sortedCategories.forEach((category) => {
      const catDetails = document.createElement("details");
      catDetails.className = "criteria-level category";
      catDetails.open = true;

      const summary = document.createElement("summary");
      summary.appendChild(createLabelWithScore(humanizeIdentifier(category.name), category.score));
      catDetails.appendChild(summary);

      const subcategories = Object.values(category.subcategories).sort((a, b) => a.name.localeCompare(b.name));
      if (!subcategories.length) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = translate("Aucun détail pour cette catégorie.");
        catDetails.appendChild(empty);
      } else {
        subcategories.forEach((sub) => {
            const subDetails = document.createElement("details");
            subDetails.className = "criteria-level subcategory";
            subDetails.open = true;
            const subSummary = document.createElement("summary");
            subSummary.appendChild(createLabelWithScore(humanizeIdentifier(sub.name), sub.score));
            subDetails.appendChild(subSummary);

            if (!sub.criteria.length) {
              const emptyCriterion = document.createElement("p");
              emptyCriterion.className = "empty";
              emptyCriterion.textContent = translate("Aucun critère listé.");
              subDetails.appendChild(emptyCriterion);
            } else {
              const cardsWrapper = document.createElement("div");
              cardsWrapper.className = "criteria-cards";
              sub.criteria
                .sort((a, b) => a.label.localeCompare(b.label))
                .forEach((criterion) => {
                  cardsWrapper.appendChild(createCriterionCard(criterion));
                });
              subDetails.appendChild(cardsWrapper);
            }

            catDetails.appendChild(subDetails);
          });
      }

      criteriaPanel.appendChild(catDetails);
    });
}

async function loadGuardrails() {
  if (state.currentBenchmark?.handle) {
    const guardrailMap = await collectGuardrailHandlesFromDirectory(state.currentBenchmark.handle);
    state.guardrailFiles = guardrailMap;
    state.records.forEach((item) => {
      const source = guardrailMap.get(item.filePath);
      if (source) {
        item.guardrailSource = source;
        item.guardrailPath = source.path || "";
      } else {
        item.guardrailSource = null;
        item.guardrailPath = "";
      }
      item.guardrailData = null;
      syncGuardrailStatus(item);
    });
    return true;
  }
  const error = new Error("Guardrail refresh unavailable.");
  error.code = "REFRESH_UNAVAILABLE";
  throw error;
}

function displayGuardrails() {
  if (!currentRecordDetail) return;
  renderGuardrailsPanel(currentRecordDetail);
}

function renderGuardrailsPanel(record) {
  if (!guardrailsPanel) return;
  clearElement(guardrailsPanel);

  if (!record) {
    const empty = document.createElement("p");
    empty.className = "empty guardrails-empty";
    empty.textContent = translate("Aucun guardrail disponible.");
    guardrailsPanel.appendChild(empty);
    return;
  }

  const container = document.createElement("div");
  container.className = "guardrails-container";
  guardrailsPanel.appendChild(container);

  const header = document.createElement("div");
  header.className = "guardrails-header";
  const title = document.createElement("h3");
  title.textContent = translate("Guardrails");
  header.appendChild(title);
  const path = record.guardrailPath || record.guardrailSource?.path || "";
  if (path) {
    const pathEl = document.createElement("code");
    pathEl.className = "guardrails-path";
    pathEl.textContent = path;
    header.appendChild(pathEl);
  }
  container.appendChild(header);

  const content = document.createElement("div");
  content.className = "guardrails-content";
  container.appendChild(content);

  if (record.guardrailData) {
    renderGuardrailsContent(content, record.guardrailData.guardrails || [], record);
    renderPromptOptimizationPanel(record);
    return;
  }

  const source = record.guardrailSource;
  if (!source) {
    const message = document.createElement("p");
    message.className = "guardrails-empty";
    let commandPath = record.filePath || record.fileName || "record.json";
    // Ensure path starts with ./outputs/ if it doesn't already
    if (!commandPath.startsWith("./outputs/") && !commandPath.startsWith("outputs/")) {
      commandPath = `./outputs/${commandPath}`;
    }
    const command = `python tools/generate_guardrails.py --record "${commandPath}"`;
    message.textContent = translate("Aucun fichier de guardrails détecté.");
    const actions = document.createElement("div");
    actions.className = "guardrails-actions";
    const commandBlock = document.createElement("pre");
    commandBlock.className = "guardrails-command";
    commandBlock.textContent = command;
    const feedback = document.createElement("p");
    feedback.className = "guardrails-feedback";
    feedback.hidden = true;
    const runBtn = document.createElement("button");
    runBtn.type = "button";
    runBtn.className = "guardrails-run-btn";
    runBtn.textContent = translate("Générer automatiquement");
    let running = false;
    runBtn.addEventListener("click", async () => {
      if (running) return;
      running = true;
      runBtn.disabled = true;
      generateBtn.disabled = true;
      refreshBtn.disabled = true;
      feedback.hidden = false;
      feedback.classList.remove("error");
      feedback.textContent = translate("Exécution de la commande…");
      try {
        const cwd = getGuardrailCommandContext();
        await executeGuardrailCommand(command, { cwd, recordPath: commandPath });
        feedback.textContent = translate("Commande exécutée. Actualisation en cours…");
        try {
          await loadGuardrails();
        } catch (refreshError) {
          console.error("Guardrail refresh failed:", refreshError);
          feedback.textContent = translate("Impossible de recharger automatiquement les guardrails. Veuillez re-sélectionner le dossier ou recharger la page.");
          feedback.classList.add("error");
          runBtn.disabled = false;
          generateBtn.disabled = false;
          refreshBtn.disabled = false;
          running = false;
          return;
        }
        renderTable();
        displayGuardrails();
        setStatus("Guardrails générés avec succès.", "info");
      } catch (error) {
        console.error("Guardrail command execution failed:", error);
        feedback.textContent = translate("Impossible d'exécuter automatiquement la commande. Veuillez l'exécuter manuellement.");
        feedback.classList.add("error");
        runBtn.disabled = false;
        generateBtn.disabled = false;
        refreshBtn.disabled = false;
      } finally {
        running = false;
      }
    });

    const generateBtn = document.createElement("button");
    generateBtn.type = "button";
    generateBtn.className = "guardrails-generate-btn";
    generateBtn.textContent = translate("Copier la commande");
    generateBtn.addEventListener("click", () => {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(command).then(() => {
          generateBtn.textContent = translate("Commande copiée");
          setTimeout(() => {
            generateBtn.textContent = translate("Copier la commande");
          }, 2000);
        }).catch(() => {
          window.prompt(translate("Copiez la commande suivante :"), command);
        });
      } else {
        window.prompt(translate("Copiez la commande suivante :"), command);
      }
    });

    const refreshBtn = document.createElement("button");
    refreshBtn.type = "button";
    refreshBtn.className = "guardrails-refresh-btn";
    refreshBtn.textContent = translate("Rafraîchir");
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = translate("Chargement...");
      try {
        // Reload the current record's guardrails
        await loadGuardrails();
        // Re-render the guardrails tab
        renderTable();
        displayGuardrails();
      } catch (error) {
        console.error("Failed to refresh guardrails:", error);
        if (error?.code === "REFRESH_UNAVAILABLE") {
          alert(translate("Impossible de recharger automatiquement les guardrails. Veuillez re-sélectionner le dossier ou recharger la page."));
        } else {
          alert(translate("Erreur lors du rafraîchissement des guardrails"));
        }
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = translate("Rafraîchir");
      }
    });

    actions.append(runBtn, generateBtn, refreshBtn);
    content.append(message, actions, feedback, commandBlock);
    return;
  }

  const loading = document.createElement("p");
  loading.className = "guardrails-loading";
  loading.textContent = translate("Chargement des guardrails…");
  content.appendChild(loading);

  const token = Symbol("guardrailLoad");
  record.guardrailRenderToken = token;

  loadGuardrailContent(source)
    .then((data) => {
      if (!data || typeof data !== "object") {
        throw new Error("Guardrails data vide");
      }
      record.guardrailData = data;
      syncGuardrailStatus(record);
      if (record.guardrailRenderToken !== token || currentRecordDetail !== record) return;
      renderGuardrailsContent(content, data.guardrails || [], record);
      renderPromptOptimizationPanel(record);
    })
    .catch((error) => {
      console.error(error);
      if (record.guardrailRenderToken !== token || currentRecordDetail !== record) return;
      clearElement(content);
      const err = document.createElement("p");
      err.className = "guardrails-empty";
      err.textContent = translate("Impossible de charger les guardrails.");
      content.appendChild(err);
      renderPromptOptimizationPanel(record);
      syncGuardrailStatus(record);
    });
}

function createPromptBlock(title, promptText, responseText) {
  const section = document.createElement("section");
  section.className = "prompt-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  section.appendChild(heading);

  const content = document.createElement("div");
  content.className = "prompt-block-content";
  section.appendChild(content);

  const promptLabel = document.createElement("p");
  promptLabel.className = "prompt-subtitle";
  promptLabel.textContent = translate("Prompt");
  content.appendChild(promptLabel);

  const promptPre = document.createElement("pre");
  promptPre.className = "prompt-text";
  promptPre.textContent = promptText || "—";
  content.appendChild(promptPre);

  const responseLabel = document.createElement("p");
  responseLabel.className = "prompt-subtitle";
  responseLabel.textContent = translate("Réponse");
  content.appendChild(responseLabel);

  const responsePre = document.createElement("pre");
  responsePre.className = "prompt-text";
  responsePre.textContent = responseText || "—";
  content.appendChild(responsePre);

  return section;
}

function renderPromptOptimizationPanel(record) {
  if (!promptOptimizationPanel) return;
  clearElement(promptOptimizationPanel);

  if (!record || !record.guardrailData) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = translate("Aucun guardrail généré. Veuillez créer des guardrails pour activer cette section.");
    promptOptimizationPanel.appendChild(empty);
    return;
  }

  const data = record.guardrailData;
  const originalPrompt = data.full_prompt || record.fullPrompt || record.prompt || data.prompt || "";
  const originalResponse = data.response || record.reply || "";
  const optimizedPrompt = data.full_prompt_guardrails || originalPrompt;
  const optimizedResponse = data.response_optimized_guardrails || "—";

  const grid = document.createElement("div");
  grid.className = "prompt-optimization-grid";
  grid.appendChild(createPromptBlock(translate("Avant SRL4Children"), originalPrompt, originalResponse));
  grid.appendChild(createPromptBlock(translate("Après SRL4Children (DP => Auto-Guardrails)"), optimizedPrompt, optimizedResponse));

  promptOptimizationPanel.appendChild(grid);
}

function registerGuardrailMeta(key, meta = {}) {
  if (!key) return;
  const labelParts = [];
  if (meta.category) labelParts.push(humanizeIdentifier(meta.category));
  if (meta.subcategory) labelParts.push(humanizeIdentifier(meta.subcategory));
  if (meta.name) labelParts.push(humanizeIdentifier(meta.name));
  const label = meta.label || labelParts.join(" / ") || humanizePath(key);
  guardrailRegistry.set(key, {
    category: meta.category || "",
    subcategory: meta.subcategory || "",
    name: meta.name || "",
    label,
  });
}

function normalizeCriterionId(value) {
  if (!value) return "";
  return value
    .toLowerCase()
    .replace(/__v[\d_]+$/, "")
    .replace(/[^a-z0-9]+/g, ".")
    .replace(/\.+/g, ".")
    .replace(/^\.|\.$/g, "");
}

function resolveCriterionLabel(normalized, fallbackId = "") {
  let current = normalized;
  while (current) {
    const meta = guardrailRegistry.get(current);
    if (meta && meta.label) return meta.label;
    const idx = current.lastIndexOf('.');
    if (idx === -1) break;
    current = current.slice(0, idx);
  }
  if (fallbackId) {
    const cleaned = fallbackId
      .replace(/__v[\d_]+$/, "")
      .replace(/_/g, ".");
    return humanizePath(cleaned);
  }
  return humanizePath(normalized);
}

function formatGenerationValue(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value, null, 2);
  } catch (err) {
    return String(value);
  }
}

function renderGuardrailsContent(container, guardrails, record) {
  clearElement(container);
  if (!Array.isArray(guardrails) || !guardrails.length) {
    const empty = document.createElement("p");
    empty.className = "guardrails-empty";
    empty.textContent = translate("Aucun guardrail généré pour ce record.");
    container.appendChild(empty);
    return;
  }

  const criteria = Array.isArray(record?.judgeResult?.detailed_criteria)
    ? record.judgeResult.detailed_criteria
    : [];
  const criteriaCoverage = new Map();
  const criteriaMeta = criteria.map((entry) => {
    const id = entry?.criterion || "";
    const normalized = normalizeCriterionId(id);
    criteriaCoverage.set(normalized, false);
    return {
      id,
      normalized,
      label: resolveCriterionLabel(normalized, id),
    };
  });

  const guardrailMeta = guardrails.map((item) => {
    const criterionId = item?.criterion_id || item?.category || "";
    const normalized = normalizeCriterionId(criterionId);
    return {
      item,
      criterionId,
      normalized,
    };
  });

  guardrailMeta.forEach(({ normalized }) => {
    if (!normalized) return;
    criteriaMeta.forEach((criterion) => {
      if (!criterion.normalized) return;
      const full = criterion.normalized;
      if (
        normalized === full
        || full.startsWith(`${normalized}.`)
        || normalized.startsWith(`${full}.`)
        || normalized === full.split(".")[0]
      ) {
        criteriaCoverage.set(full, true);
      }
    });
  });

  const covered = Array.from(criteriaCoverage.values()).filter(Boolean).length;
  const missing = criteriaMeta.filter((criterion) => !criteriaCoverage.get(criterion.normalized));

  if (criteriaMeta.length) {
    const summary = document.createElement("div");
    summary.className = "guardrails-coverage";
    const status = document.createElement("p");
    status.className = "guardrails-coverage-status";
    status.textContent = translate(
      "Guardrails couvrent {covered}/{total} des principes de Conception évalués.",
      { covered, total: criteriaMeta.length },
    );
    summary.appendChild(status);
    if (missing.length) {
      const list = document.createElement("ul");
      list.className = "guardrails-coverage-missing";
      missing.forEach((criterion) => {
        const li = document.createElement("li");
        li.textContent = resolveCriterionLabel(criterion.normalized, criterion.id);
        list.appendChild(li);
      });
      summary.appendChild(list);
    }
    container.appendChild(summary);
  }

  const list = document.createElement("div");
  list.className = "guardrail-list";
  guardrailMeta.forEach(({ item, criterionId }, index) => {
    const card = document.createElement("article");
    card.className = "guardrail-item";

    const ruleLine = document.createElement("p");
    ruleLine.className = "guardrail-rule";
    const number = document.createElement("span");
    number.className = "guardrail-index";
    number.textContent = `#${index + 1}`;
    const separator = document.createTextNode(" — ");
    const strong = document.createElement("strong");
    strong.textContent = item?.rule || "—";
    ruleLine.append(number, separator, strong);
    card.appendChild(ruleLine);

    if (item?.rationale) {
      const rationale = document.createElement("p");
      rationale.className = "guardrail-rationale";
      rationale.textContent = item.rationale;
      card.appendChild(rationale);
    }

    const criterionLine = document.createElement("p");
    criterionLine.className = "guardrail-criterion";
    const label = item?.criterion_id || criterionId || "—";
    criterionLine.textContent = `${translate("criterion_id")}: ${label}`;
    card.appendChild(criterionLine);

    list.appendChild(card);
  });

  container.appendChild(list);

  const generationMeta = record?.guardrailData?.generation;
  if (generationMeta && typeof generationMeta === "object") {
    const metaSection = document.createElement("section");
    metaSection.className = "guardrail-generation";
    const metaTitle = document.createElement("h4");
    metaTitle.textContent = translate("Guardrail generation metadata");
    metaSection.appendChild(metaTitle);

    const metaList = document.createElement("dl");
    metaList.className = "guardrail-generation-list";
    Object.entries(generationMeta).forEach(([key, value]) => {
      const dt = document.createElement("dt");
      dt.textContent = key;
      const dd = document.createElement("dd");
      dd.textContent = formatGenerationValue(value);
      metaList.append(dt, dd);
    });
    metaSection.appendChild(metaList);
    container.appendChild(metaSection);
  }
}

function renderCriteriaSummarySection(container, categories, metrics, options = {}) {
  const { hasPartialData = false } = options;
  if (!categories.length) return;

  const summarySection = document.createElement("section");
  summarySection.className = "criteria-summary";

  if (metrics) {
    const { overall_variance: variance, judge_agreement_avg: agreement } = metrics;
    const hasLowConsensus = (typeof variance === "number" && variance > 0.5)
      || (typeof agreement === "number" && agreement < 0.9);
    if (hasLowConsensus) {
      const consensusBadge = document.createElement("div");
      consensusBadge.className = "consensus-badge";
      const parts = [];
      if (typeof variance === "number") {
        parts.push(translate("Variance globale: {value}", { value: formatScore(variance) }));
      }
      if (typeof agreement === "number") {
        parts.push(translate("Accord moyen: {value}", { value: formatScore(agreement) }));
      }
      const consensusLabel = translate("Consensus faible");
      consensusBadge.innerHTML = `<strong>${consensusLabel}</strong> · ${parts.join(" · ")}`;
      summarySection.appendChild(consensusBadge);
    }
  }

  const dataBadge = document.createElement("div");
  dataBadge.className = hasPartialData ? "data-badge partial" : "data-badge complete";
  dataBadge.textContent = hasPartialData
    ? translate("Données partielles · Les résultats peuvent être erronés.")
    : translate("Données complètes");
  summarySection.appendChild(dataBadge);

  const tabs = document.createElement("div");
  tabs.className = "criteria-summary-tabs";

  const chartWrapper = document.createElement("div");
  chartWrapper.className = "criteria-summary-chart";
  const chartCanvas = document.createElement("canvas");
  const fallback = document.createElement("div");
  fallback.className = "radar-fallback hidden";
  fallback.textContent = translate("Chargement du graphique…");
  chartWrapper.append(chartCanvas, fallback);

  summarySection.append(tabs, chartWrapper);

  container.appendChild(summarySection);

  const categoryMap = new Map();
  categories.forEach((category) => {
    categoryMap.set(category.name, category);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "criteria-tab";
    button.dataset.category = category.name;
    const label = document.createElement("span");
    label.textContent = humanizeIdentifier(category.name);
    const badge = document.createElement("span");
    badge.className = "score-badge score-badge-inline";
    badge.textContent = formatScore(category.score);
    applyScoreZone(badge, category.score);
    button.append(label, badge);
    button.addEventListener("click", () => {
      if (activeCriteriaCategory === category.name) return;
      setActiveCategory(category.name);
    });
    tabs.appendChild(button);
  });

  if (!activeCriteriaCategory || !categoryMap.has(activeCriteriaCategory)) {
    activeCriteriaCategory = categories[0].name;
  }

  function setActiveCategory(name) {
    if (!categoryMap.has(name)) return;
    activeCriteriaCategory = name;
    tabs.querySelectorAll(".criteria-tab").forEach((button) => {
      const isActive = button.dataset.category === name;
      button.classList.toggle("active", isActive);
    });
    renderCriteriaRadarChart(chartCanvas, fallback, categoryMap.get(name));
  }

  setActiveCategory(activeCriteriaCategory);
}

function renderCriteriaRadarChart(canvas, fallback, category) {
  if (!canvas) return;
  const dataset = buildCriteriaRadarDataset(category);

  renderRadarWithFallback({
    labels: dataset.labels,
    values: dataset.values,
    canvas,
    fallback,
    datasetLabel: "Score critère",
    setChartInstance(chart) {
      if (criteriaRadarChart) {
        criteriaRadarChart.destroy();
      }
      criteriaRadarChart = chart;
    },
  });
}

function buildCriteriaRadarDataset(category) {
  if (!category) return { labels: [], values: [] };

  const entries = [];
  const subcategories = Object.values(category.subcategories || {});
  subcategories.forEach((sub) => {
    const baseScore = typeof sub.score === "number" ? sub.score : calculateAverageScore(sub.criteria);
    if (Number.isFinite(baseScore)) {
      entries.push({ label: humanizeIdentifier(sub.name), value: baseScore });
    }
  });

  if (!entries.length) {
    subcategories.forEach((sub) => {
      (sub.criteria || []).forEach((criterion) => {
        const value = criterion?.scores?.final_score;
        if (Number.isFinite(value)) {
          entries.push({ label: humanizeIdentifier(criterion.label), value });
        }
      });
    });
  }

  if (!entries.length) {
    return { labels: [], values: [] };
  }

  const sorted = entries.sort((a, b) => a.label.localeCompare(b.label));

  return {
    labels: sorted.map((entry) => entry.label),
    values: sorted.map((entry) => entry.value),
  };
}

function calculateAverageScore(criteria = []) {
  const values = (criteria || [])
    .map((criterion) => criterion?.scores?.final_score)
    .filter((value) => Number.isFinite(value));
  if (!values.length) return null;
  const total = values.reduce((sum, value) => sum + value, 0);
  return total / values.length;
}

function generateRecordMarkdown(record) {
  const lines = [];
  const recordData = record.raw?.record_data || {};
  lines.push(`# Détails du record`);
  lines.push("");

  lines.push("## Métadonnées");
  lines.push("| Clé | Valeur |");
  lines.push("| --- | --- |");
  const metaEntries = [
    ["ID record", record.id || recordData.id || record.fileName || "—"],
    ["Modèle", record.model || recordData.model || "—"],
    ["Preset critères", record.criteria_selection || recordData.criteria_selection || "—"],
    ["Catégorie", record.category || recordData.category || "—"],
    ["Sous-catégorie", normaliseValue(recordData.subcategory || "") || "—"],
    ["Maturité", record.maturity || recordData.maturity || "—"],
    ["Mode", normaliseValue(recordData.mode || "") || "—"],
    ["Date de mise à jour", record.date || recordData.timestamp || record.raw?.timestamp || "—"],
  ];
  metaEntries.forEach(([label, value]) => {
    lines.push(`| ${label} | ${value || "—"} |`);
  });
  lines.push("");

  if (record.raw?.metadata) {
    const tech = record.raw.metadata;
    lines.push("### Informations techniques");
    Object.entries(tech).forEach(([key, value]) => {
      if (value && typeof value === "object") {
        lines.push(`- **${humanizeIdentifier(key)}**`);
        Object.entries(value).forEach(([subKey, subValue]) => {
          lines.push(`  - ${humanizeIdentifier(subKey)} : ${typeof subValue === "object" ? JSON.stringify(subValue, null, 2) : subValue}`);
        });
      } else {
        lines.push(`- ${humanizeIdentifier(key)} : ${value}`);
      }
    });
    lines.push("");
  }

  lines.push("## Scores");
  lines.push(`- Score global : **${formatScore(record.finalScore)}**`);

  const categoryScores = Object.entries(record.judgeResult?.category_scores || {});
  if (categoryScores.length) {
    lines.push("");
    lines.push("### Scores par catégorie");
    lines.push("| Catégorie | Score |");
    lines.push("| --- | --- |");
    categoryScores.sort(([a], [b]) => a.localeCompare(b)).forEach(([key, value]) => {
      lines.push(`| ${humanizeIdentifier(key)} | ${formatScore(value)} |`);
    });
  }

  const subcategoryScores = Object.entries(record.judgeResult?.subcategory_scores || {});
  if (subcategoryScores.length) {
    lines.push("");
    lines.push("### Scores par sous-catégorie");
    lines.push("| Sous-catégorie | Score |");
    lines.push("| --- | --- |");
    subcategoryScores.sort(([a], [b]) => a.localeCompare(b)).forEach(([path, value]) => {
      lines.push(`| ${humanizePath(path)} | ${formatScore(value)} |`);
    });
  }

  lines.push("");
  lines.push("## Prompt & Réponse");
  const prompt = record.fullPrompt || record.prompt || recordData.full_prompt || recordData.prompt || "";
  const reply = record.reply || recordData.reply || "";
  lines.push("### Prompt complet");
  lines.push("```");
  lines.push(prompt);
  lines.push("```");
  lines.push("");
  lines.push("### Réponse du modèle");
  lines.push("```");
  lines.push(reply);
  lines.push("```");
  lines.push("");

  const tree = buildCriteriaTree(record.judgeResult, record.phaseResults || {});
  const categories = Object.values(tree).sort((a, b) => a.name.localeCompare(b.name));
  const expectedJudgeCount = Object.keys(record.phaseResults || {}).length;
  const hasPartialData = hasPartialJudgeData(categories, expectedJudgeCount);
  lines.push(hasPartialData
    ? "> **Données partielles** · Les résultats peuvent être erronés."
    : "> **Données complètes**.");
  lines.push("");

  lines.push("## Détails des critères");

  categories.forEach((category) => {
    lines.push("");
    lines.push(`### Catégorie : ${humanizeIdentifier(category.name)} (${formatScore(category.score)})`);
    const subcategories = Object.values(category.subcategories || {}).sort((a, b) => a.name.localeCompare(b.name));
    subcategories.forEach((sub) => {
      lines.push("");
      lines.push(`#### Sous-catégorie : ${humanizeIdentifier(sub.name)} (${formatScore(sub.score)})`);
      const criteria = (sub.criteria || []).sort((a, b) => a.label.localeCompare(b.label));
      criteria.forEach((criterion) => {
        lines.push("");
        lines.push(`- **${humanizeIdentifier(criterion.label)}** (score ${formatScore(criterion.scores?.final_score)})`);
        if (typeof criterion.scores?.consistency_variance === "number" || typeof criterion.scores?.judge_agreement?.agreement_score === "number") {
          lines.push(`  - Variance : ${formatScore(criterion.scores?.consistency_variance)}`);
          lines.push(`  - Accord : ${formatScore(criterion.scores?.judge_agreement?.agreement_score)}`);
        }
        const judges = Array.isArray(criterion.judges) ? criterion.judges : [];
        judges.forEach((judge) => {
          lines.push(`  - Juge ${judge.judgeLabel || judge.judgeId} (score ${formatScore(judge.finalScore)})`);
          if (typeof judge.consistencyVariance === "number") {
            lines.push(`    - Variance : ${formatScore(judge.consistencyVariance)}`);
          }
          if (typeof judge.agreementScore === "number") {
            lines.push(`    - Accord : ${formatScore(judge.agreementScore)}`);
          }
          if (judge.model && (judge.model.model || judge.model.name)) {
            lines.push(`    - Modèle : ${judge.model.model || judge.model.name}`);
          }
          if (judge.individualPasses && judge.individualPasses.length) {
            lines.push("    - Scores individuels :");
            judge.individualPasses.forEach((group, gIndex) => {
              const label = judge.individualPasses.length > 1
                ? translate("Pass {index}", { index: gIndex + 1 })
                : translate("Scores");
              lines.push(`      - ${label} : ${group.map((value) => formatScore(value)).join(", ")}`);
            });
          }
          if (judge.passes && judge.passes.length) {
            lines.push("    - Détails des passes :");
            judge.passes.forEach((pass, pIndex) => {
              const passLabel = pass.pass_number
                ? translate("Pass {index}", { index: pass.pass_number })
                : translate("Pass {index}", { index: pIndex + 1 });
              lines.push(`      - ${passLabel} (score ${formatScore(pass.score)})`);
              if (pass.explanation && pass.explanation.trim()) {
                lines.push("        > " + pass.explanation.trim().replace(/\n/g, "\n        > "));
              }
              if (Array.isArray(pass.evidence_extracts) && pass.evidence_extracts.length) {
                lines.push("        - Extraits :");
                pass.evidence_extracts.forEach((extract) => {
                  lines.push(`          - ${extract}`);
                });
              }
            });
          }
          if (Array.isArray(judge.evidenceExtracts) && judge.evidenceExtracts.length) {
            lines.push("    - Extraits principaux :");
            judge.evidenceExtracts.forEach((extract) => {
              lines.push(`      - ${extract}`);
            });
          }
          if (Array.isArray(judge.rawResponses) && judge.rawResponses.length) {
            lines.push("    - Réponses brutes :");
            judge.rawResponses.forEach((response, index) => {
              lines.push("      ````");
              lines.push(typeof response === "string" ? response : JSON.stringify(response, null, 2));
              lines.push("      ````");
            });
          }
        });
      });
    });
  });

  return lines.join("\n");
}

function downloadCurrentRecordReport() {
  if (!currentRecordDetail) return;
  const markdown = generateRecordMarkdown(currentRecordDetail);
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8;" });
  const fileName = `record_${(currentRecordDetail.id || currentRecordDetail.fileName || "report")}.md`;
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = fileName.replace(/\s+/g, "_");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

function ensureChartJs() {
  if (typeof Chart !== "undefined") return Promise.resolve(true);
  if (chartJsPromise) return chartJsPromise;

  chartJsPromise = new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = CHART_JS_CDN;
    script.async = true;
    script.dataset.loader = "chartjs";
    script.onload = () => {
      chartJsPromise = null;
      resolve(true);
    };
    script.onerror = () => {
      chartJsPromise = null;
      resolve(false);
    };
    document.head.appendChild(script);
  });

  return chartJsPromise;
}

function renderRadarWithFallback({ labels, values, canvas, fallback, setChartInstance = () => {}, datasetLabel = "Score" }) {
  const token = String(Date.now()) + Math.random();
  canvas.dataset.renderToken = token;
  if (fallback) fallback.dataset.renderToken = token;

  const hasData = Array.isArray(labels) && labels.length && Array.isArray(values) && values.length;

  if (!hasData) {
    canvas.classList.add("hidden");
    if (fallback) {
      fallback.classList.remove("hidden");
      fallback.textContent = translate("Aucun critère noté pour cette catégorie.");
    }
    setChartInstance(null);
    return;
  }

  if (fallback) {
    fallback.classList.remove("hidden");
    fallback.textContent = translate("Chargement du graphique…");
  }
  canvas.classList.add("hidden");
  setChartInstance(null);

  ensureChartJs().then((available) => {
    if (canvas.dataset.renderToken !== token) return;

    if (!available || typeof Chart === "undefined") {
      canvas.classList.add("hidden");
    if (fallback) {
      fallback.classList.remove("hidden");
      renderSvgRadar(fallback, labels, values);
    }
      setChartInstance(null);
      return;
    }

    if (fallback) {
      fallback.classList.add("hidden");
      fallback.innerHTML = "";
    }
    canvas.classList.remove("hidden");

    const dataset = {
      labels,
      datasets: [
        {
          label: datasetLabel,
          data: values,
          borderColor: "#4b6cff",
          backgroundColor: "rgba(75, 108, 255, 0.2)",
          pointBackgroundColor: "#4b6cff",
          pointBorderColor: "#fff",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "#4b6cff",
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          suggestedMin: 0,
          suggestedMax: MAX_RADAR_SCORE,
          ticks: {
            stepSize: 1,
          },
          angleLines: {
            color: "rgba(75, 108, 255, 0.2)",
          },
          grid: {
            color: "rgba(75, 108, 255, 0.2)",
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    };

    const chart = new Chart(canvas, {
      type: "radar",
      data: dataset,
      options,
    });

    setChartInstance(chart);
  });
}

function renderSvgRadar(container, labels, values) {
  if (!container) return;
  container.innerHTML = "";
  container.classList.remove("hidden");

  if (!labels.length) {
    container.textContent = translate("Aucun critère noté pour cette catégorie.");
    return;
  }

  const size = 260;
  const center = size / 2;
  const radius = center - 32;
  const levels = MAX_RADAR_SCORE;
  const svgNS = "http://www.w3.org/2000/svg";

  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
  svg.setAttribute("class", "radar-svg");

  const angles = labels.map((_, index) => ((Math.PI * 2) * index) / labels.length - Math.PI / 2);

  // Grid levels
  for (let level = 1; level <= levels; level += 1) {
    const ratio = level / levels;
    const points = angles.map((angle) => {
      const r = radius * ratio;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    const polygon = document.createElementNS(svgNS, "polygon");
    polygon.setAttribute("points", points.join(" "));
    polygon.setAttribute("fill", level === levels ? "rgba(75, 108, 255, 0.05)" : "none");
    polygon.setAttribute("stroke", "rgba(75, 108, 255, 0.15)");
    polygon.setAttribute("stroke-width", level === levels ? "1.2" : "0.8");
    svg.appendChild(polygon);
  }

  // Axes lines and labels
  angles.forEach((angle, index) => {
    const axis = document.createElementNS(svgNS, "line");
    axis.setAttribute("x1", center);
    axis.setAttribute("y1", center);
    axis.setAttribute("x2", (center + radius * Math.cos(angle)).toFixed(2));
    axis.setAttribute("y2", (center + radius * Math.sin(angle)).toFixed(2));
    axis.setAttribute("stroke", "rgba(75, 108, 255, 0.25)");
    axis.setAttribute("stroke-width", "1");
    svg.appendChild(axis);

    const labelRadius = radius + 16;
    const labelX = center + labelRadius * Math.cos(angle);
    const labelY = center + labelRadius * Math.sin(angle);

    const text = document.createElementNS(svgNS, "text");
    text.textContent = labels[index];
    text.setAttribute("x", labelX.toFixed(2));
    text.setAttribute("y", labelY.toFixed(2));
    const cos = Math.cos(angle);
    if (Math.abs(cos) < 0.1) {
      text.setAttribute("text-anchor", "middle");
    } else {
      text.setAttribute("text-anchor", cos > 0 ? "start" : "end");
    }
    const sin = Math.sin(angle);
    if (sin > 0.3) {
      text.setAttribute("dominant-baseline", "hanging");
    } else if (sin < -0.3) {
      text.setAttribute("dominant-baseline", "alphabetic");
    } else {
      text.setAttribute("dominant-baseline", "middle");
    }
    text.setAttribute("class", "radar-label");
    svg.appendChild(text);
  });

  // Data polygon
  const dataPoints = angles.map((angle, index) => {
    const value = Math.max(0, Math.min(values[index], MAX_RADAR_SCORE));
    const r = radius * (value / MAX_RADAR_SCORE);
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  });

  const polygon = document.createElementNS(svgNS, "polygon");
  polygon.setAttribute("points", dataPoints.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" "));
  polygon.setAttribute("fill", "rgba(75, 108, 255, 0.35)");
  polygon.setAttribute("stroke", "#4b6cff");
  polygon.setAttribute("stroke-width", "1.5");
  svg.appendChild(polygon);

  dataPoints.forEach((point) => {
    const circle = document.createElementNS(svgNS, "circle");
    circle.setAttribute("cx", point.x.toFixed(2));
    circle.setAttribute("cy", point.y.toFixed(2));
    circle.setAttribute("r", "3.5");
    circle.setAttribute("fill", "#fff");
    circle.setAttribute("stroke", "#4b6cff");
    circle.setAttribute("stroke-width", "1.2");
    svg.appendChild(circle);
  });

  container.appendChild(svg);
}


function hasPartialJudgeData(categories, expectedJudgeCount) {
  return categories.some((category) =>
    Object.values(category.subcategories || {}).some((sub) =>
      (sub.criteria || []).some((criterion) => {
        const judges = Array.isArray(criterion.judges) ? criterion.judges : [];
        if (!judges.length) return true;
        if (expectedJudgeCount && judges.length < expectedJudgeCount) return true;
        return judges.some((judge) => judge.isPartial);
      })
    )
  );
}

function createLabelWithScore(label, score) {
  const wrapper = document.createElement("span");
  wrapper.className = "label-score";
  const text = document.createElement("span");
  text.className = "label";
  text.textContent = label;
  const badge = document.createElement("span");
  badge.className = "score-badge score-badge-inline";
  badge.textContent = formatScore(score);
  applyScoreZone(badge, typeof score === "number" ? score : null);
  wrapper.append(text, badge);
  return wrapper;
}

function createCriterionCard(entry) {
  const card = document.createElement("article");
  card.className = "criterion-card";
  applyScoreZone(card, entry.scores?.final_score);

  const header = document.createElement("header");
  header.className = "criterion-card-header";
  const title = document.createElement("h4");
  title.textContent = humanizeIdentifier(entry.label);
  const score = document.createElement("span");
  score.className = "score-badge";
  score.textContent = formatScore(entry.scores?.final_score);
  applyScoreZone(score, entry.scores?.final_score);
  header.append(title, score);
  card.appendChild(header);

  const metrics = document.createElement("dl");
  metrics.className = "criterion-metrics";
  const hasConsistency = typeof entry.scores?.consistency_variance === "number";
  const agreementScore = typeof entry.scores?.judge_agreement?.agreement_score === "number"
    ? entry.scores.judge_agreement.agreement_score
    : entry.scores?.agreement_score;
  const hasAgreement = typeof agreementScore === "number";
  const hasOtherScores = Array.isArray(entry.scores?.individual_passes);
  if (hasConsistency) {
    appendMetric(metrics, "Variance", formatScore(entry.scores.consistency_variance));
  }
  if (hasAgreement) {
    appendMetric(metrics, "Accord", formatScore(agreementScore));
  }
  if (hasOtherScores) {
    appendMetric(metrics, "Passes", String(entry.scores.individual_passes.length));
  }
  if (metrics.childElementCount) {
    card.appendChild(metrics);
  }

  if (entry.explanation && entry.explanation.trim()) {
    const explanation = document.createElement("div");
    explanation.className = "criterion-explanation";
    renderMarkdownToElement(explanation, entry.explanation);
    card.appendChild(explanation);
  }

  if (entry.evidence && entry.evidence.length) {
    const evidenceBlock = document.createElement("div");
    evidenceBlock.className = "criterion-evidence";
    const title = document.createElement("h5");
    title.textContent = translate("Extraits");
    const list = document.createElement("ul");
    entry.evidence.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    evidenceBlock.append(title, list);
    card.appendChild(evidenceBlock);
  }

  if (entry.judges && entry.judges.length) {
    card.appendChild(createJudgeSection(entry));
  }

  return card;
}

function createJudgeSection(entry) {
  const section = document.createElement("section");
  section.className = "judge-section";

  const tabs = document.createElement("div");
  tabs.className = "judge-tabs";
  const detail = document.createElement("div");
  detail.className = "judge-detail";

  entry.judges.forEach((judge, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "judge-tab";
    button.dataset.index = String(index);
    button.textContent = judge.judgeLabel || `Juge ${index + 1}`;
    if (index === 0) {
      button.classList.add("active");
    }
    button.addEventListener("click", () => {
      tabs.querySelectorAll(".judge-tab").forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");
      renderJudgeDetail(detail, judge);
    });
    tabs.appendChild(button);
  });

  section.append(tabs, detail);
  if (entry.judges.length) {
    renderJudgeDetail(detail, entry.judges[0]);
  }

  return section;
}

function renderJudgeDetail(container, judge) {
  clearElement(container);
  if (!judge) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = translate("Aucune donnée pour ce juge.");
    container.appendChild(empty);
    return;
  }

  const header = document.createElement("div");
  header.className = "judge-header";
  const title = document.createElement("h5");
  title.textContent = judge.judgeLabel || "Juge";
  header.appendChild(title);

  if (judge.model && (judge.model.model || judge.model.name)) {
    const modelInfo = document.createElement("span");
    modelInfo.className = "judge-model";
    const modelName = judge.model.model || judge.model.name || "";
    modelInfo.textContent = modelName;
    header.appendChild(modelInfo);
  }
  container.appendChild(header);

  const metrics = document.createElement("div");
  metrics.className = "judge-metrics";
  metrics.appendChild(createJudgeMetric("Score", judge.finalScore, true));
  if (typeof judge.consistencyVariance === "number") {
    metrics.appendChild(createJudgeMetric("Variance", judge.consistencyVariance));
  }
  if (typeof judge.agreementScore === "number") {
    metrics.appendChild(createJudgeMetric("Accord", judge.agreementScore));
  }
  container.appendChild(metrics);

  if (judge.individualPasses && judge.individualPasses.length) {
    const passesBlock = document.createElement("div");
    passesBlock.className = "judge-individual-passes";
    const heading = document.createElement("h6");
    heading.textContent = translate("Scores individuels");
    passesBlock.appendChild(heading);
    judge.individualPasses.forEach((passScores, groupIndex) => {
      const list = document.createElement("ol");
      list.className = "judge-pass-values";
      passScores.forEach((value, valueIndex) => {
        const item = document.createElement("li");
        item.innerHTML = `<span>${escapeHtml(translate("Pass {index}", { index: `${groupIndex + 1}.${valueIndex + 1}` }))}</span><span>${escapeHtml(formatScore(value))}</span>`;
        list.appendChild(item);
      });
      passesBlock.appendChild(list);
    });
    container.appendChild(passesBlock);
  }

  if (judge.passes && judge.passes.length) {
    const detailedPasses = document.createElement("div");
    detailedPasses.className = "judge-detailed-passes";
    const heading = document.createElement("h6");
    heading.textContent = translate("Détails des passes");
    detailedPasses.appendChild(heading);

    judge.passes.forEach((pass, index) => {
      const passCard = document.createElement("article");
      passCard.className = "judge-pass";
      const passHeader = document.createElement("div");
      passHeader.className = "judge-pass-header";
      const passTitle = document.createElement("h6");
      passTitle.textContent = translate("Pass {index}", { index: pass.pass_number || index + 1 });
      passHeader.appendChild(passTitle);
      if (typeof pass.score === "number") {
        const passScore = document.createElement("span");
        passScore.className = "score-badge";
        passScore.textContent = formatScore(pass.score);
        applyScoreZone(passScore, pass.score);
        passHeader.appendChild(passScore);
      }
      passCard.appendChild(passHeader);

      if (pass.explanation && pass.explanation.trim()) {
        const passExplanation = document.createElement("div");
        passExplanation.className = "judge-pass-explanation";
        renderMarkdownToElement(passExplanation, pass.explanation);
        passCard.appendChild(passExplanation);
      }

      if (Array.isArray(pass.evidence_extracts) && pass.evidence_extracts.length) {
        const passEvidence = document.createElement("ul");
        passEvidence.className = "judge-pass-evidence";
        pass.evidence_extracts.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          passEvidence.appendChild(li);
        });
        passCard.appendChild(passEvidence);
      }

      detailedPasses.appendChild(passCard);
    });
    container.appendChild(detailedPasses);
  }

  if (Array.isArray(judge.evidenceExtracts) && judge.evidenceExtracts.length) {
    const evidenceBlock = document.createElement("div");
    evidenceBlock.className = "judge-evidence";
    const heading = document.createElement("h6");
    heading.textContent = translate("Extraits principaux");
    const list = document.createElement("ul");
    judge.evidenceExtracts.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    evidenceBlock.append(heading, list);
    container.appendChild(evidenceBlock);
  }

  if (Array.isArray(judge.rawResponses) && judge.rawResponses.length) {
    const responses = document.createElement("details");
    responses.className = "judge-responses";
    const summary = document.createElement("summary");
    summary.textContent = translate("Réponses brutes");
    responses.appendChild(summary);
    judge.rawResponses.forEach((response, index) => {
      const pre = document.createElement("pre");
      pre.textContent = typeof response === "string" ? response : JSON.stringify(response, null, 2);
      pre.dataset.index = String(index);
      responses.appendChild(pre);
    });
    container.appendChild(responses);
  }
}

function createJudgeMetric(label, value, isScore = false) {
  const item = document.createElement("div");
  item.className = "judge-metric";
  const title = document.createElement("span");
  title.className = "judge-metric-label";
  title.textContent = label;
  const metricValue = document.createElement("span");
  metricValue.className = "judge-metric-value";
  metricValue.textContent = formatScore(value);
  if (isScore) {
    metricValue.classList.add("score-badge");
    applyScoreZone(metricValue, value);
  }
  item.append(title, metricValue);
  return item;
}

function appendMetric(list, label, value) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  dd.textContent = value;
  list.append(dt, dd);
}

function buildCriteriaTree(judge, phaseResults = {}) {
  const tree = {};
  if (!judge) return tree;
  const judgeDetailsMap = collectCriterionJudgeDetails(phaseResults);

  const ensureCategory = (name) => {
    if (!tree[name]) {
      tree[name] = {
        name,
        score: null,
        subcategories: {},
      };
    }
    return tree[name];
  };

  const ensureSubcategory = (categoryName, subName) => {
    const category = ensureCategory(categoryName);
    if (!category.subcategories[subName]) {
      category.subcategories[subName] = {
        name: subName,
        score: null,
        criteria: [],
      };
    }
    return category.subcategories[subName];
  };

  Object.entries(judge.category_scores || {}).forEach(([name, score]) => {
    const category = ensureCategory(name);
    category.score = typeof score === "number" ? score : category.score;
  });

  Object.entries(judge.subcategory_scores || {}).forEach(([path, score]) => {
    const [categoryName, subName = "Autre"] = path.split(".");
    const subcategory = ensureSubcategory(categoryName || "Autre", subName || "Autre");
    subcategory.score = typeof score === "number" ? score : subcategory.score;
  });

  const details = Array.isArray(judge.detailed_criteria) ? judge.detailed_criteria : [];
  details.forEach((entry) => {
    const raw = entry.criterion || "";
    const [path] = raw.split("__");
    const segments = path ? path.split(".") : [];
    const categoryName = segments.shift() || "Autre";
    const subName = segments.length > 1 ? segments.shift() : segments.shift() || "Autre";
    const criterionLabel = segments.length ? segments.join(".") : subName || raw || "Critère";
    const subcategory = ensureSubcategory(categoryName, subName || "Autre");
    subcategory.criteria.push({
      key: raw,
      label: criterionLabel,
      scores: entry.scores || {},
      explanation: entry.explanation || "",
      evidence: Array.isArray(entry.evidence_extracts) ? entry.evidence_extracts : [],
      metadata: entry.metadata || {},
      judges: judgeDetailsMap.get(raw) || [],
    });
  });

  return tree;
}

function collectCriterionJudgeDetails(phaseResults = {}) {
  const map = new Map();
  Object.entries(phaseResults || {}).forEach(([phaseName, phaseData]) => {
    const criteria = Array.isArray(phaseData?.detailed_criteria) ? phaseData.detailed_criteria : [];
    criteria.forEach((criterion) => {
      const key = criterion.criterion;
      if (!key) return;
      if (!map.has(key)) {
        map.set(key, []);
      }
      const container = map.get(key);
      const detailEntries = Array.isArray(criterion.detailed_judge_results) && criterion.detailed_judge_results.length
        ? criterion.detailed_judge_results
        : [null];
      detailEntries.forEach((detail, index) => {
        const judgeId = detail?.judge_id || `${phaseName}${detailEntries.length > 1 ? `_alt${index + 1}` : ""}`;
        const passes = Array.isArray(detail?.passes) ? detail.passes : [];
        container.push({
          judgeId,
          judgeLabel: humanizeJudgeId(judgeId),
          model: detail?.judge_model || phaseData?.metadata?.judge_model || null,
          finalScore: detail?.final_score ?? criterion.scores?.final_score ?? null,
          consistencyVariance: detail?.consistency_variance ?? criterion.scores?.consistency_variance ?? null,
          agreementScore: criterion.scores?.judge_agreement?.agreement_score ?? null,
          individualPasses: Array.isArray(criterion.scores?.individual_passes)
            ? criterion.scores.individual_passes
            : [],
          passes,
          rawResponses: Array.isArray(detail?.raw_responses) ? detail.raw_responses : [],
          explanation: criterion.explanation || "",
          evidenceExtracts: Array.isArray(criterion.evidence_extracts) ? criterion.evidence_extracts : [],
          metadata: detail?.metadata || criterion.metadata || {},
          phaseName,
          isPartial: !detail || !passes.length,
        });
      });
    });
  });
  return map;
}

function humanizeIdentifier(value) {
  if (!value) return "—";
  return value
    .replace(/__/g, " ")
    .replace(/_/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function humanizePath(value) {
  if (!value) return "—";
  return value
    .split(".")
    .map((segment) => humanizeIdentifier(segment))
    .join(" › ");
}

function humanizeJudgeId(value) {
  if (!value) return "Juge";
  const cleaned = value.replace(/^judge[_-]?/i, "");
  return humanizeIdentifier(cleaned || value);
}
function openDetails(record) {
  currentRecordDetail = record;
  if (downloadReportBtn) {
    downloadReportBtn.disabled = false;
  }
  lastFocusedTrigger = document.activeElement;
  activeTab = "overview";
  activeCriteriaCategory = null;
  renderOverview(record);
  renderCriteriaPanel(record);
  renderGuardrailsPanel(record);
  renderPromptOptimizationPanel(record);
  updateTabLabels(record);
  setActiveTab("overview", { focusPanel: false });
  detailsOverlay.classList.remove("hidden");
  if (tabButtons[0]) {
    tabButtons[0].focus();
  } else {
    detailsOverlay.focus();
  }
}

function closeDetails() {
  detailsOverlay.classList.add("hidden");
  Object.values(tabPanels).forEach(clearElement);
  if (overviewRadarChart) {
    overviewRadarChart.destroy();
    overviewRadarChart = null;
  }
  if (criteriaRadarChart) {
    criteriaRadarChart.destroy();
    criteriaRadarChart = null;
  }
  if (downloadReportBtn) {
    downloadReportBtn.disabled = true;
  }
  currentRecordDetail = null;
  updateTabLabels(null);
  if (lastFocusedTrigger && typeof lastFocusedTrigger.focus === "function") {
    lastFocusedTrigger.focus();
  }
}

async function handleBenchmarkSelection(event) {
  const files = Array.from(event.target.files || []);
  if (!files.length) {
    setStatus("Aucun fichier sélectionné.");
    return;
  }
  const guardrailMap = collectGuardrailFilesFromUpload(files);
  state.guardrailFiles = guardrailMap;
  const jsonFiles = files.filter((file) => {
    if (!file.name.toLowerCase().endsWith(".json")) return false;
    const relativePath = typeof file.webkitRelativePath === "string" ? file.webkitRelativePath : "";
    return !relativePath.toLowerCase().includes("/guardrails/");
  });
  if (!jsonFiles.length) {
    setStatus("Aucun fichier JSON trouvé dans ce dossier.", "warning");
    return;
  }

  setStatus("Chargement de {count} fichiers…", "info", { count: jsonFiles.length });
  state.records = [];
  state.filtered = [];
  state.currentPage = 1;

  const errors = [];

  for (const file of jsonFiles) {
    try {
      const parsed = await readJsonFile(file);
      const sourcePath = file.webkitRelativePath || file.name;
      const record = buildRecord(file, parsed, { sourcePath });
      const guardrailSource = state.guardrailFiles.get(record.filePath);
      if (guardrailSource) {
        record.guardrailSource = guardrailSource;
        record.guardrailPath = guardrailSource.path || "";
      } else {
        record.guardrailSource = null;
        record.guardrailPath = "";
      }
      record.guardrailData = null;
      syncGuardrailStatus(record);
      state.records.push(record);
    } catch (err) {
      errors.push(err.message);
    }
  }

  if (errors.length) {
    console.warn("Erreurs de lecture", errors);
    setStatus("{loaded} fichiers chargés avec {errors} erreurs. Consultez la console.", "warning", {
      loaded: state.records.length,
      errors: errors.length,
    });
  } else {
    setStatus("{loaded} fichiers chargés avec succès.", "info", { loaded: state.records.length });
  }

  state.filtered = applySearch(state.records, state.searchTerm);
  renderTable();
  renderGlobalSummary();
}

function handleSearch(event) {
  const term = event.target.value;
  state.searchTerm = term;
  state.currentPage = 1;
  state.filtered = applySearch(state.records, term);
  renderTable();
  renderGlobalSummary();
}

function handleTableClick(event) {
  const button = event.target.closest("button.details-btn");
  if (!button) return;
  const index = Number(button.dataset.index);
  const record = (state.currentSorted || [])[index];
  if (record) {
    openDetails(record);
  }
}

function handleTableChange(event) {
  const target = event.target;
  const index = Number(target.dataset.index);
  if (Number.isNaN(index)) return;
  const record = (state.currentSorted || [])[index];
  if (!record) return;

  let requiresRender = false;
  if (target.classList.contains("row-select")) {
    record.selected = target.checked;
    requiresRender = false;
  } else if (target.classList.contains("category-input")) {
    record.category = target.value;
    if (state.sortKey === "category") {
      requiresRender = true;
    }
  } else if (target.classList.contains("maturity-select")) {
    record.maturity = target.value;
    if (state.sortKey === "maturity") {
      requiresRender = true;
    }
  }

  if (state.sortKey === "date") {
    requiresRender = true;
  }

  if (requiresRender) {
    renderTable();
  } else {
    updateStats();
  }
  renderGlobalSummary();
}

function handlePaginationClick(event) {
  const button = event.target.closest("button[data-page]");
  if (!button || button.disabled) return;
  const targetPage = Number(button.dataset.page);
  if (!Number.isNaN(targetPage)) {
    state.currentPage = targetPage;
    renderTable();
  }
}

function handleSort(event) {
  const header = event.target.closest("th[data-key]");
  if (!header) return;
  const key = header.dataset.key;
  if (state.sortKey === key) {
    state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
  } else {
    state.sortKey = key;
    state.sortDir = "asc";
  }
  renderTable();
}

function handleTabKeyDown(event) {
  if (!tabButtons.length) return;
  const { key } = event;
  const currentIndex = tabButtons.findIndex((btn) => btn.dataset.tab === activeTab);
  if (key === "ArrowRight" || key === "ArrowLeft") {
    event.preventDefault();
    const direction = key === "ArrowRight" ? 1 : -1;
    const nextIndex = (currentIndex + direction + tabButtons.length) % tabButtons.length;
    const nextTab = tabButtons[nextIndex];
    setActiveTab(nextTab.dataset.tab, { focusPanel: false });
    nextTab.focus();
  } else if (key === "Home") {
    event.preventDefault();
    const first = tabButtons[0];
    setActiveTab(first.dataset.tab, { focusPanel: false });
    first.focus();
  } else if (key === "End") {
    event.preventDefault();
    const last = tabButtons[tabButtons.length - 1];
    setActiveTab(last.dataset.tab, { focusPanel: false });
    last.focus();
  }
}

// Event bindings
benchmarkInput.addEventListener("change", handleBenchmarkSelection);
searchInput.addEventListener("input", handleSearch);
tableBody.addEventListener("click", handleTableClick);
tableBody.addEventListener("change", handleTableChange);
paginationEl.addEventListener("click", handlePaginationClick);
document.querySelector("thead").addEventListener("click", handleSort);
closeOverlayBtn.addEventListener("click", closeDetails);
detailsOverlay.addEventListener("click", (event) => {
  if (event.target === detailsOverlay) {
    closeDetails();
  }
});

if (designPrinciplesBtn) {
  designPrinciplesBtn.addEventListener("click", openDesignPrinciplesModal);
}
if (closeDesignPrinciplesBtn) {
  closeDesignPrinciplesBtn.addEventListener("click", () => closeDesignPrinciplesModal());
}
if (designPrinciplesOverlay) {
  designPrinciplesOverlay.addEventListener("click", (event) => {
    if (event.target === designPrinciplesOverlay) {
      closeDesignPrinciplesModal();
    }
  });
}
if (designPrinciplesTree) {
  designPrinciplesTree.addEventListener("click", handleDesignPrinciplesTreeClick);
}
if (designPrinciplesEditor) {
  designPrinciplesEditor.addEventListener("input", () => {
    if (!designPrinciplesState.selectedPath) return;
    const isDirty = designPrinciplesEditor.value !== designPrinciplesState.originalContent;
    setDesignPrinciplesDirty(isDirty);
  });
}
if (designPrinciplesSaveBtn) {
  designPrinciplesSaveBtn.addEventListener("click", saveDesignPrinciple);
}

if (tabList) {
  tabList.addEventListener("click", (event) => {
    const button = event.target.closest(".tab-btn");
    if (!button) return;
    setActiveTab(button.dataset.tab, { focusPanel: false });
    button.focus();
  });
  tabList.addEventListener("keydown", handleTabKeyDown);
}

window.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (designPrinciplesOverlay && !designPrinciplesOverlay.classList.contains("hidden")) {
    event.preventDefault();
    closeDesignPrinciplesModal();
    return;
  }
  if (!detailsOverlay.classList.contains("hidden")) {
    event.preventDefault();
    closeDetails();
  }
});

async function pickOutputsDirectory() {
  if (!window.showDirectoryPicker) {
    setStatus("showDirectoryPicker n'est pas supporté dans ce navigateur. Utilisez la sélection de dossier classique.", "warning");
    return;
  }
  try {
    const dirHandle = await window.showDirectoryPicker();
    state.outputsDir = dirHandle;
    await refreshBenchmarkList();
    setStatus("Dossier outputs sélectionné. Choisissez un benchmark dans la liste.");
  } catch (err) {
    if (err.name !== "AbortError") {
      setStatus("Impossible d'accéder au dossier: {message}", "warning", { message: err.message });
    }
  }
}

async function refreshBenchmarkList() {
  const select = benchmarkSelect;
  const defaultOptionLabel = translate("— Sélectionnez un benchmark —");
  select.innerHTML = `<option value="">${defaultOptionLabel}</option>`;
  state.benchmarks = [];
  state.currentBenchmark = null;

  if (!state.outputsDir) return;

  const benchmarks = [];
  for await (const entry of state.outputsDir.values()) {
    if (entry.kind === "directory") {
      benchmarks.push({ name: entry.name, handle: entry });
    }
  }
  benchmarks.sort((a, b) => b.name.localeCompare(a.name));
  state.benchmarks = benchmarks;

  for (const bench of benchmarks) {
    const option = document.createElement("option");
    option.value = bench.name;
    option.textContent = bench.name;
    select.appendChild(option);
  }
  if (!benchmarks.length) {
    setStatus("Aucun sous-dossier trouvé dans outputs.", "warning");
  }
}

async function loadBenchmarkByName(name) {
  const bench = state.benchmarks.find((b) => b.name === name);
  if (!bench) {
    state.currentBenchmark = null;
    setStatus("Benchmark non trouvé.", "warning");
    return;
  }
  state.currentBenchmark = bench;
  await loadBenchmarkFromDirectory(bench.handle);
}

async function loadBenchmarkFromDirectory(dirHandle) {
  const guardrailMap = await collectGuardrailHandlesFromDirectory(dirHandle);
  state.guardrailFiles = guardrailMap;
  const jsonFiles = [];
  for await (const entry of dirHandle.values()) {
    if (entry.kind === "file" && entry.name.toLowerCase().endsWith(".json")) {
      if (entry.name.startsWith("guardrails_")) continue;
      jsonFiles.push(entry);
    }
  }

  if (!jsonFiles.length) {
    setStatus("Aucun fichier JSON dans {name}.", "warning", { name: dirHandle.name });
    state.records = [];
    state.filtered = [];
    renderTable();
    return;
  }

  setStatus("Chargement de {count} fichiers…", "info", { count: jsonFiles.length });
  state.records = [];
  state.filtered = [];
  state.currentPage = 1;
  const errors = [];

  for (const fileHandle of jsonFiles) {
    try {
      const file = await fileHandle.getFile();
      const parsed = await readJsonFile(file);
      const sourcePath = `${dirHandle.name}/${fileHandle.name}`;
      const record = buildRecord(file, parsed, { sourcePath });
      const guardrailSource = state.guardrailFiles.get(record.filePath);
      if (guardrailSource) {
        record.guardrailSource = guardrailSource;
        record.guardrailPath = guardrailSource.path || "";
      } else {
        record.guardrailSource = null;
        record.guardrailPath = "";
      }
      record.guardrailData = null;
      syncGuardrailStatus(record);
      state.records.push(record);
    } catch (err) {
      errors.push(err.message);
    }
  }

  if (errors.length) {
    console.warn("Erreurs de lecture", errors);
    setStatus("{loaded} fichiers chargés avec {errors} erreurs. Consultez la console.", "warning", {
      loaded: state.records.length,
      errors: errors.length,
    });
  } else {
    setStatus("{loaded} fichiers chargés pour {name}.", "info", {
      loaded: state.records.length,
      name: dirHandle.name,
    });
  }

  state.filtered = applySearch(state.records, state.searchTerm);
  renderTable();
  renderGlobalSummary();
}

pickOutputsBtn.addEventListener("click", pickOutputsDirectory);
benchmarkSelect.addEventListener("change", (event) => {
  const value = event.target.value;
  if (!value) {
    state.records = [];
    state.filtered = [];
    state.guardrailFiles = new Map();
    renderTable();
    renderGuardrailsPanel(null);
    return;
  }
  loadBenchmarkByName(value);
});
exportCsvBtn.addEventListener("click", exportTableToCsv);
if (downloadReportBtn) {
  downloadReportBtn.addEventListener("click", downloadCurrentRecordReport);
  downloadReportBtn.disabled = true;
}

setActiveTab(activeTab, { focusPanel: false });

// ---- Global summary (homepage) ----
function computeGlobalSummary(records) {
  const included = (records || []).filter((r) => r.selected);
  if (!included.length) return null;

  // Model (most frequent)
  const modelCount = new Map();
  included.forEach((r) => {
    const m = r.model || "";
    modelCount.set(m, (modelCount.get(m) || 0) + 1);
  });
  let topModel = "—";
  let best = 0;
  modelCount.forEach((count, model) => {
    if (count > best) { best = count; topModel = model; }
  });

  // Average of final scores
  const scoreValues = included
    .map((r) => (typeof r.finalScore === "number" && Number.isFinite(r.finalScore) ? r.finalScore : null))
    .filter((v) => v !== null);
  const avgScore = scoreValues.length
    ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length
    : null;

  // Subcategory averages
  const subMap = new Map();
  included.forEach((r) => {
    const sub = r.judgeResult?.subcategory_scores || {};
    Object.entries(sub).forEach(([path, value]) => {
      if (typeof value !== "number" || !Number.isFinite(value)) return;
      const cur = subMap.get(path) || { sum: 0, count: 0 };
      cur.sum += value;
      cur.count += 1;
      subMap.set(path, cur);
    });
  });
  const subcategoryEntries = Array.from(subMap.entries())
    .map(([path, { sum, count }]) => [path, sum / count])
    .sort(([a], [b]) => a.localeCompare(b));

  return { model: topModel, avgScore, subcategoryEntries };
}

function renderGlobalSummary() {
  if (!gsSection) return;
  if (!state.records.length) {
    gsSection.style.display = "none";
    return;
  }

  const summary = computeGlobalSummary(state.records);
  if (!summary) {
    gsSection.style.display = "none";
    return;
  }

  gsSection.style.display = "flex";
  if (gsModelEl) gsModelEl.textContent = summary.model || "—";
  if (gsAvgScoreEl) {
    gsAvgScoreEl.textContent = formatScore(summary.avgScore);
    applyScoreZone(gsAvgScoreEl, summary.avgScore);
  }

  if (gsSubcategoryList) {
    gsSubcategoryList.innerHTML = "";
    summary.subcategoryEntries.forEach(([path, value]) => {
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = humanizePath(path);
      const score = document.createElement("span");
      score.className = "score-badge score-badge-inline";
      score.textContent = formatScore(value);
      applyScoreZone(score, value);
      li.append(label, score);
      gsSubcategoryList.appendChild(li);
    });
  }

  const labels = summary.subcategoryEntries.map(([path]) => humanizePath(path));
  const values = summary.subcategoryEntries.map(([, v]) => (typeof v === "number" ? v : 0));
  renderRadarWithFallback({
    labels,
    values,
    canvas: gsRadarCanvas,
    fallback: gsRadarFallback,
    setChartInstance(chart) {
      if (globalSummaryRadarChart) globalSummaryRadarChart.destroy();
      globalSummaryRadarChart = chart;
    },
    datasetLabel: "Moyenne sous-catégories",
  });
}



function exportTableToCsv() {
  if (!state.records.length) {
    setStatus("Aucune donnée à exporter.", "warning");
    return;
  }

  const headers = [
    "selected",
    "id",
    "model",
    "prompt",
    "category",
    "maturity",
    "criteria_selection",
    "finalScore",
    "date"
  ];

  const rows = state.records.map((record) => headers.map((key) => {
    if (key === "selected") return record.selected ? "1" : "0";
    if (key === "finalScore") return formatScore(record.finalScore, "");
    return record[key] !== undefined ? record[key] : "";
  }));

  const csvLines = [headers.join(",")].concat(
    rows.map((row) => row.map(toCsvValue).join(","))
  );

  const blob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const fileName = `review_export_${timestamp}.csv`;
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
  setStatus("Export CSV généré ({rows} lignes).", "info", { rows: rows.length });
}

function toCsvValue(value) {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (str.includes('"') || str.includes(",") || str.includes("\n")) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}
