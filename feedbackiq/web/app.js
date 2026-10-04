/**
 * FeedbackIQ Modern Web Frontend Application
 * Fully in Turkish, zero emojis, modern B2B SaaS workflow.
 */

const API_BASE = "";

// State
let appState = {
  activeTab: "dashboard",
  kpis: {},
  cases: [],
  selectedCaseId: null,
  activeAiCallCaseId: null
};

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initScenarios();
  initFormActions();
  initModalActions();
  refreshAllData();
});

// Navigation Handling
function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      switchTab(target);
    });
  });

  document.getElementById("btnRefreshData").addEventListener("click", () => {
    refreshAllData();
  });
}

function switchTab(tabName) {
  appState.activeTab = tabName;

  // Update nav buttons
  document.querySelectorAll(".nav-tab").forEach(t => {
    if (t.getAttribute("data-tab") === tabName) {
      t.classList.add("active");
    } else {
      t.classList.remove("active");
    }
  });

  // Update view panels
  document.querySelectorAll(".tab-view").forEach(v => {
    v.classList.remove("active");
  });
  const activeView = document.getElementById(`view-${tabName}`);
  if (activeView) {
    activeView.classList.add("active");
  }

  // Tab specific actions
  if (tabName === "dashboard") {
    loadDashboard();
  } else if (tabName === "ai-queue") {
    loadAiQueue();
  } else if (tabName === "csr-queue") {
    loadCsrQueue();
  } else if (tabName === "case-detail") {
    loadCaseDetail(appState.selectedCaseId);
  } else if (tabName === "analytics") {
    loadAnalytics();
  }
}

// Scenarios Setup
function initScenarios() {
  const scenarios = {
    btnScen1: {
      text: "Dün saat 14:00'te Merkez Şehir Hastanesi Kardiyoloji polikliniğindeki randevuma gittim. Randevum olmasına rağmen banko kaydı 45 dakika sürdü ve muayeneye gecikmeli alındım.",
      channel: "Web Sitesi",
      hospital: "Merkez Şehir Hastanesi",
      date: "Dün"
    },
    btnScen2: {
      text: "Dün Example Hospital yerleşkesine gittim ve bekleme odasında kimse açıklama yapmadan neredeyse bir saat bekletildim.",
      channel: "QR Kod",
      hospital: "Example Hospital",
      date: "Dün"
    },
    btnScen3: {
      text: "Dün aldığım hizmet için kartımdan iki defa çekim yapılmış. Muhasebeye yazdım kimse cevap vermedi, acil dönüş bekliyorum.",
      channel: "E-posta",
      hospital: "",
      date: "Dün"
    }
  };

  Object.keys(scenarios).forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener("click", () => {
        const sc = scenarios[btnId];
        document.getElementById("inputFeedbackText").value = sc.text;
        document.getElementById("selectChannel").value = sc.channel;
        document.getElementById("inputHospitalHint").value = sc.hospital;
        document.getElementById("inputDateHint").value = sc.date;
      });
    }
  });
}

// Form Actions
function initFormActions() {
  const btnAnalyze = document.getElementById("btnRunAnalysis");
  btnAnalyze.addEventListener("click", async () => {
    const feedbackText = document.getElementById("inputFeedbackText").value.trim();
    if (!feedbackText) {
      alert("Lütfen analiz edilecek bir geri bildirim metni giriniz.");
      return;
    }

    const payload = {
      feedback_text: feedbackText,
      source_channel: document.getElementById("selectChannel").value,
      known_hospital: document.getElementById("inputHospitalHint").value.trim() || null,
      known_date: document.getElementById("inputDateHint").value.trim() || null
    };

    btnAnalyze.disabled = true;
    btnAnalyze.textContent = "Analiz Ediliyor...";

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      renderAnalysisResult(data);
      refreshAllData();
    } catch (err) {
      console.error(err);
      alert("Analiz sırasında bir bağlantı hatası oluştu.");
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = `
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        Operasyonel Analizi Çalıştır
      `;
    }
  });
}

// Render Analysis Output
function renderAnalysisResult(data) {
  const container = document.getElementById("analysisResultContainer");
  container.style.display = "block";

  const { case_id, extracted, result } = data;
  const score = result.completeness_score;
  const tier = result.triage_tier;

  let tierClass = "notice-box-info";
  let tierTitle = "Kademe 2: Yapay Zeka Sesli Arama Planlandı";
  let tierActionHtml = "";

  if (tier === "Approved") {
    tierClass = "notice-box-success";
    tierTitle = "Kademe 1: Onaylandı / Doğrudan İş Akışına Sevk";
    tierActionHtml = `
      <div style="margin-top:10px; font-weight:700; color:#065f46;">
        Tüm operasyonel gereksinimler eksiksiz tespit edildi. Vaka doğrudan ilgili poliklinik yöneticisine aktarılmıştır.
      </div>
    `;
  } else if (tier === "AI Call Scheduled") {
    tierClass = "notice-box-info";
    tierTitle = "Kademe 2: Yapay Zeka Sesli Arama Planlandı";
    tierActionHtml = `
      <div style="margin-top:10px;">
        <button class="btn btn-primary" onclick="openAiCallFromAnalysis('${case_id}')">
          Hemen AI Sesli Arama Simülasyonunu Başlat
        </button>
      </div>
    `;
  } else {
    tierClass = "notice-box-danger";
    tierTitle = "Kademe 3: Müşteri Hizmetleri Temsilci İncelemesi";
    tierActionHtml = `
      <div style="margin-top:10px;">
        <button class="btn btn-secondary" onclick="openCsrFromAnalysis('${case_id}')">
          Vakayı Müşteri Hizmetleri Masasında Aç
        </button>
      </div>
    `;
  }

  // Detected parameters rows
  const detectedFields = [
    { label: "Hastane / Şube", val: extracted.hospital },
    { label: "Poliklinik / Birim", val: extracted.department },
    { label: "Olay Tarihi", val: extracted.incident_date },
    { label: "Yaklaşık Saat", val: extracted.approximate_time },
    { label: "Hizmet Türü", val: extracted.service_type },
    { label: "Personel Unvanı / Adı", val: [extracted.staff_role, extracted.staff_name].filter(Boolean).join(" ") || null },
    { label: "Fatura Detayı", val: extracted.billing_context },
    { label: "Olay Açıklaması", val: extracted.description_of_event }
  ];

  const detectedRowsHtml = detectedFields.map(f => `
    <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f1f5f9; font-size:0.84rem;">
      <span style="color:#64748b;">${f.label}</span>
      <span style="font-weight:700; color:#0f172a; text-align:right; max-width:60%;">${f.val || '<span style="color:#94a3b8; font-weight:normal; font-style:italic;">Belirtilmemiş</span>'}</span>
    </div>
  `).join("");

  // Missing fields list
  const missingRowsHtml = (result.missing_field_items && result.missing_field_items.length > 0)
    ? result.missing_field_items.map(m => `
        <div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #f8fafc; font-size:0.83rem;">
          <div>
            <strong style="color:#334155;">${m.display_name}</strong>
            <span style="background:${m.is_critical ? '#fee2e2' : '#f1f5f9'}; color:${m.is_critical ? '#991b1b' : '#475569'}; font-size:0.68rem; font-weight:700; padding:1px 5px; border-radius:3px; margin-left:4px;">
              ${m.is_critical ? 'KRİTİK EKSİK' : 'KÜÇÜK DETAY'}
            </span>
          </div>
          <div style="color:var(--primary); font-size:0.8rem; margin-top:2px;">Önerilen Soru: "${m.suggested_question}"</div>
        </div>
      `).join("")
    : `<div style="color:#059669; font-weight:600; font-size:0.85rem; padding:8px 0;">Eksik operasyonel parametre bulunmuyor.</div>`;

  container.innerHTML = `
    <div class="notice-box ${tierClass}">
      <div style="font-weight:800; font-size:1rem; margin-bottom:4px;">${tierTitle} &bull; Vaka: ${case_id}</div>
      <div style="font-size:0.88rem;">${result.triage_reason}</div>
      ${tierActionHtml}
    </div>

    <div class="glass-card">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:1rem;">
        <div>
          <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#64748b; letter-spacing:0.05em;">Operasyonel Kalite Skoru</div>
          <div style="display:flex; align-items:baseline; gap:10px; margin-top:4px;">
            <span style="font-size:2.2rem; font-weight:800; color:var(--text-main);">${score}</span>
            <span style="color:#94a3b8; font-size:1rem; font-weight:700;">/ 100</span>
            <span class="badge-pill ${getTierBadgeClass(tier)}">${getTierBadgeLabel(tier)}</span>
          </div>
        </div>
        <div style="min-width:220px; flex:1; max-width:320px;">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; margin-bottom:4px;">
            <span>Tamamlanma Oranı</span>
            <span>${score}%</span>
          </div>
          <div style="background:#e2e8f0; border-radius:3px; height:8px; overflow:hidden;">
            <div style="background:var(--primary-gradient); width:${score}%; height:100%;"></div>
          </div>
        </div>
      </div>

      <div class="grid-2col">
        <div>
          <div class="card-title">Tespit Edilen Değişkenler</div>
          ${detectedRowsHtml}
        </div>
        <div>
          <div class="card-title">Eksik Bilgiler & Takip Soruları</div>
          ${missingRowsHtml}
        </div>
      </div>
    </div>
  `;

  container.scrollIntoView({ behavior: "smooth" });
}

function openAiCallFromAnalysis(caseId) {
  appState.selectedCaseId = caseId;
  switchTab("ai-queue");
  triggerAiCallSimulation(caseId);
}

function openCsrFromAnalysis(caseId) {
  appState.selectedCaseId = caseId;
  switchTab("case-detail");
}

// Data Refresh
async function refreshAllData() {
  try {
    const [kpiRes, casesRes] = await Promise.all([
      fetch(`${API_BASE}/api/kpis`),
      fetch(`${API_BASE}/api/cases?sort_by=score_asc`)
    ]);
    appState.kpis = await kpiRes.json();
    appState.cases = await casesRes.json();

    updateKpiCards();
    updateQueueCounts();

    if (appState.activeTab === "dashboard") {
      loadDashboard();
    } else if (appState.activeTab === "ai-queue") {
      loadAiQueue();
    } else if (appState.activeTab === "csr-queue") {
      loadCsrQueue();
    } else if (appState.activeTab === "case-detail") {
      loadCaseDetail(appState.selectedCaseId);
    } else if (appState.activeTab === "analytics") {
      loadAnalytics();
    }
  } catch (err) {
    console.error("Veri yenileme hatası:", err);
  }
}

function updateKpiCards() {
  const k = appState.kpis;
  document.getElementById("kpiTotal").textContent = k.total_cases ?? 0;
  document.getElementById("kpiApproved").textContent = k.tier_1_approved ?? 0;
  document.getElementById("kpiAiCall").textContent = k.tier_2_ai_call ?? 0;
  document.getElementById("kpiCsr").textContent = k.tier_3_csr ?? 0;
  document.getElementById("kpiAvgScore").textContent = (k.avg_score ?? 0) + "/100";
}

function updateQueueCounts() {
  const k = appState.kpis;
  document.getElementById("aiQueueCount").textContent = k.tier_2_ai_call ?? 0;
  document.getElementById("csrQueueCount").textContent = k.tier_3_csr ?? 0;
}

// Dashboard View Loader
async function loadDashboard() {
  // Recent cases table
  const tbody = document.getElementById("recentCasesTableBody");
  tbody.innerHTML = "";

  const recent = appState.cases.slice(0, 8);
  recent.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${c.case_id}</strong></td>
      <td>${c.created_at}</td>
      <td>${c.source_channel}</td>
      <td>${c.issue_type}</td>
      <td><span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span></td>
      <td><span class="badge-pill ${getTierBadgeClass(c.triage_tier)}">${getTierBadgeLabel(c.triage_tier)}</span></td>
      <td>${c.status}</td>
      <td>
        <button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="inspectCase('${c.case_id}')">İncele</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Triage Distribution Bars
  try {
    const res = await fetch(`${API_BASE}/api/analytics`);
    const data = await res.json();

    const distContainer = document.getElementById("triageDistContainer");
    distContainer.innerHTML = "";
    const total = appState.kpis.total_cases || 1;

    data.tier_dist.forEach(row => {
      const pct = Math.round((row.count / total) * 100);
      const barColor = row.triage_tier === "Approved" ? "var(--tier1-green)" : row.triage_tier === "AI Call Scheduled" ? "var(--primary)" : "var(--tier3-rose)";
      distContainer.innerHTML += `
        <div style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:700; margin-bottom:4px;">
            <span>${getTierBadgeLabel(row.triage_tier)}</span>
            <span style="color:#64748b;">${row.count} vaka (${pct}%)</span>
          </div>
          <div style="background:#e2e8f0; border-radius:3px; height:8px; overflow:hidden;">
            <div style="background:${barColor}; width:${pct}%; height:100%;"></div>
          </div>
        </div>
      `;
    });

    // Top Missing Fields List
    const missingContainer = document.getElementById("topMissingContainer");
    missingContainer.innerHTML = "";
    data.top_missing.slice(0, 5).forEach(m => {
      missingContainer.innerHTML += `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #f8fafc; font-size:0.85rem;">
          <span style="font-weight:600; color:#334155;">${formatFieldName(m.field_name)}</span>
          <span style="background:#f1f5f9; color:#475569; font-weight:700; padding:2px 8px; border-radius:4px; font-size:0.75rem;">
            ${m.count} vakada eksik
          </span>
        </div>
      `;
    });
  } catch (err) {
    console.error("Dashboard analitik verisi yüklenemedi:", err);
  }
}

// AI Voice Queue (Tier 2) Loader
function loadAiQueue() {
  const container = document.getElementById("aiQueueCardsContainer");
  container.innerHTML = "";

  const aiCases = appState.cases.filter(c => c.triage_tier === "AI Call Scheduled" || c.status === "AI Call Scheduled");

  if (aiCases.length === 0) {
    container.innerHTML = `
      <div class="notice-box notice-box-success">
        Yapay Zeka Sesli Arama Kuyruğunda bekleyen vaka bulunmuyor. Tüm küçük veri eksiklikleri arandı ve onaylandı.
      </div>
    `;
    return;
  }

  aiCases.forEach(c => {
    const card = document.createElement("div");
    card.className = "glass-card";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
        <div>
          <span style="font-size:1.1rem; font-weight:800; color:var(--text-main); margin-right:8px;">${c.case_id}</span>
          <span style="font-size:0.8rem; color:#64748b; margin-right:8px;">${c.created_at}</span>
          <span style="background:#f1f5f9; color:#475569; padding:2px 7px; border-radius:3px; font-size:0.72rem; font-weight:700;">
            Kanal: ${c.source_channel}
          </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span>
          <span class="badge-pill tier-pill-ai">Kademe 2: AI Sesli Arama</span>
        </div>
      </div>
      <div style="font-size:0.9rem; color:#334155; margin-bottom:10px; font-style:italic; background:#f8fafc; padding:10px 14px; border-radius:4px; border-left:3px solid var(--primary);">
        "${c.original_feedback}"
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:#64748b;">
        <div>
          <strong>Kategori:</strong> ${c.issue_type} &bull;
          <strong>Arama Durumu:</strong> <span style="color:var(--primary); font-weight:700;">${c.contact_status}</span>
        </div>
        <button class="btn btn-primary" onclick="triggerAiCallSimulation('${c.case_id}')">
          Yapay Zeka Sesli Aramasını Başlat
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

// CSR Queue (Tier 3) Loader
function loadCsrQueue() {
  const container = document.getElementById("csrQueueCardsContainer");
  container.innerHTML = "";

  const csrCases = appState.cases.filter(c => c.triage_tier === "Customer Service Review" && c.status !== "Approved" && c.status !== "Resolved / Ready for Workflow");

  if (csrCases.length === 0) {
    container.innerHTML = `
      <div class="notice-box notice-box-success">
        Müşteri Hizmetleri İnceleme Masasında bekleyen kritik vaka bulunmuyor.
      </div>
    `;
    return;
  }

  csrCases.forEach(c => {
    const card = document.createElement("div");
    card.className = "glass-card";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
        <div>
          <span style="font-size:1.1rem; font-weight:800; color:var(--text-main); margin-right:8px;">${c.case_id}</span>
          <span style="font-size:0.8rem; color:#64748b; margin-right:8px;">${c.created_at}</span>
          <span style="background:#f1f5f9; color:#475569; padding:2px 7px; border-radius:3px; font-size:0.72rem; font-weight:700;">
            Kanal: ${c.source_channel}
          </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span>
          <span class="badge-pill tier-pill-csr">Kademe 3: Temsilci İncelemesi</span>
        </div>
      </div>
      <div style="font-size:0.9rem; color:#334155; margin-bottom:10px; font-style:italic; background:#f8fafc; padding:10px 14px; border-radius:4px; border-left:3px solid var(--tier3-rose);">
        "${c.original_feedback}"
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:#64748b;">
        <div>
          <strong>Kategori:</strong> ${c.issue_type} &bull;
          <strong>Eksik Alan Sayısı:</strong> <span style="color:#b91c1c; font-weight:700;">${c.missing_fields_count}</span> &bull;
          <strong>Temas Durumu:</strong> ${c.contact_status}
        </div>
        <button class="btn btn-secondary" onclick="inspectCase('${c.case_id}')">
          Vakayı Çözümleme Masasında Aç
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

// Case Detail Loader
async function loadCaseDetail(caseId) {
  const dropdown = document.getElementById("selectCaseDropdown");
  dropdown.innerHTML = "";

  if (appState.cases.length === 0) return;
  if (!caseId) {
    caseId = appState.cases[0].case_id;
  }
  appState.selectedCaseId = caseId;

  appState.cases.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.case_id;
    opt.textContent = `${c.case_id} — ${c.issue_type} (${c.completeness_score}/100, ${getTierBadgeLabel(c.triage_tier)})`;
    if (c.case_id === caseId) opt.selected = true;
    dropdown.appendChild(opt);
  });

  dropdown.onchange = (e) => {
    loadCaseDetail(e.target.value);
  };

  try {
    const res = await fetch(`${API_BASE}/api/cases/${caseId}`);
    const detail = await res.json();
    renderCaseDetailWorkspace(detail);
  } catch (err) {
    console.error(err);
  }
}

function renderCaseDetailWorkspace(detail) {
  const container = document.getElementById("caseDetailContent");
  const c = detail.case;
  const missing = detail.missing_fields || [];
  const history = detail.history || [];

  const detectedItems = [
    { label: "Hastane / Şube", val: c.hospital },
    { label: "Poliklinik / Birim", val: c.department },
    { label: "Olay Tarihi", val: c.incident_date },
    { label: "Yaklaşık Saat", val: c.approximate_time },
    { label: "Hizmet / Tetkik", val: c.service_type },
    { label: "Personel Unvanı", val: c.staff_role },
    { label: "Personel Adı", val: c.staff_name },
    { label: "Fatura Detayı", val: c.billing_context }
  ];

  const detectedRowsHtml = detectedItems.map(f => `
    <div style="display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #f1f5f9; font-size:0.83rem;">
      <span style="color:#64748b;">${f.label}</span>
      <span style="font-weight:700; color:#0f172a; text-align:right; max-width:65%;">${f.val || '<span style="color:#94a3b8; font-weight:normal; font-style:italic;">Belirtilmemiş</span>'}</span>
    </div>
  `).join("");

  const missingHtml = missing.length > 0
    ? missing.map(m => `
        <div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #f8fafc; font-size:0.83rem;">
          <div>
            <strong style="color:#334155;">${formatFieldName(m.field_name)}</strong>
            <span style="background:${m.is_critical ? '#fee2e2' : '#f1f5f9'}; color:${m.is_critical ? '#991b1b' : '#475569'}; font-size:0.68rem; font-weight:700; padding:1px 5px; border-radius:3px; margin-left:4px;">
              ${m.is_critical ? 'KRİTİK EKSİK' : 'KÜÇÜK DETAY'}
            </span>
          </div>
          <div style="color:var(--primary); font-size:0.8rem; margin-top:2px;">Önerilen İletişim Sorusu: "${getQuestionText(m.field_name)}"</div>
        </div>
      `).join("")
    : `<div style="color:#059669; font-weight:700; font-size:0.86rem; padding:10px 0;">Tüm operasyonel gereksinimler eksiksiz teyit edildi.</div>`;

  container.innerHTML = `
    <div class="glass-card" style="margin-bottom:1.2rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <span style="font-size:1.35rem; font-weight:800; color:#0f172a; margin-right:12px;">Vaka Kaydı: ${c.case_id}</span>
          <span style="font-size:0.84rem; color:#64748b;">Tarih: ${c.created_at} &bull; Kanal: ${c.source_channel}</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span>
          <span class="badge-pill ${getTierBadgeClass(c.triage_tier)}">${getTierBadgeLabel(c.triage_tier)}</span>
          <span class="badge-pill tier-pill-1">${c.status}</span>
        </div>
      </div>
    </div>

    <div class="glass-card">
      <div class="card-title">Orijinal Hasta Mesajı</div>
      <div style="background:#f8fafc; border-left:3px solid var(--primary); padding:1rem 1.2rem; border-radius:4px; font-size:0.92rem; color:#1e293b; line-height:1.5;">
        "${c.original_feedback}"
      </div>
      <div style="margin-top:8px; font-size:0.8rem; color:#64748b;">
        <strong>Özet:</strong> ${c.extracted_summary || 'N/A'} &bull; 
        <strong>Duygu:</strong> ${c.sentiment} &bull; 
        <strong>Kategori:</strong> ${c.issue_type}
      </div>
    </div>

    <div class="grid-2col">
      <div class="glass-card">
        <div class="card-title">Tespit Edilen Operasyonel Bilgiler</div>
        ${detectedRowsHtml}
      </div>

      <div class="glass-card">
        <div class="card-title">Eksik Kalan Bilgiler & İletişim İpuçları</div>
        ${missingHtml}
      </div>
    </div>

    <!-- CSR Investigation & Re-evaluation Form -->
    <div class="glass-card" style="border: 2px solid #ddd6fe;">
      <div class="card-title" style="color:var(--primary-dark);">Müşteri Hizmetleri İncelemesi & Yeniden Değerlendirme</div>
      <p style="font-size:0.84rem; color:#475569; margin-bottom:12px;">
        Hasta ile yapılan görüşmede teyit edilen bilgileri aşağıya girin. Girilen teyitli bilgiler yapay zekanın ilk tahminlerini kesin olarak ezer.
      </p>

      <div class="grid-3col form-row">
        <div class="form-group">
          <label class="form-label">Teyit Edilen Hastane</label>
          <input type="text" class="form-input" id="csrHospital" value="${c.hospital || ''}" placeholder="Örn: Merkez Şehir Hastanesi" />
        </div>
        <div class="form-group">
          <label class="form-label">Teyit Edilen Poliklinik</label>
          <input type="text" class="form-input" id="csrDept" value="${c.department || ''}" placeholder="Örn: Kardiyoloji" />
        </div>
        <div class="form-group">
          <label class="form-label">Teyit Edilen Saat</label>
          <input type="text" class="form-input" id="csrTime" value="${c.approximate_time || ''}" placeholder="Örn: 14:15" />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Temsilci Görüşme Notu</label>
        <input type="text" class="form-input" id="csrNotes" placeholder="Örn: Hasta telefonla arandı, randevu saati ve poliklinik teyit edildi." />
      </div>

      <div class="form-actions">
        <button class="btn btn-primary btn-large" onclick="submitCsrReevaluation('${c.case_id}')">
          Vakayı Yeniden Değerlendir ve Onayla
        </button>
      </div>
    </div>

    ${c.ai_call_transcript ? `
      <div class="glass-card">
        <div class="card-title">AI Sesli Arama Telefon Görüşme Dökümü</div>
        <pre style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:12px; font-size:0.82rem; color:var(--primary-dark); white-space:pre-wrap; font-family:monospace; line-height:1.5;">${c.ai_call_transcript}</pre>
      </div>
    ` : ''}
  `;
}

// CSR Re-evaluation Action
async function submitCsrReevaluation(caseId) {
  const confirmed = {};
  const hosp = document.getElementById("csrHospital").value.trim();
  const dept = document.getElementById("csrDept").value.trim();
  const time = document.getElementById("csrTime").value.trim();
  const notes = document.getElementById("csrNotes").value.trim();

  if (hosp) confirmed.hospital = hosp;
  if (dept) confirmed.department = dept;
  if (time) confirmed.approximate_time = time;

  try {
    const res = await fetch(`${API_BASE}/api/cases/${caseId}/reevaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        confirmed_fields: confirmed,
        notes: notes || "Temsilci inceleme masası üzerinden teyit edildi.",
        contact_status: "Information Collected"
      })
    });
    const resultData = await res.json();
    alert(`Vaka başarıyla yeniden değerlendirildi!\nSkor: ${resultData.result.completeness_score}/100\nDurum: Onaylandı / İş Akışına Sevk`);
    refreshAllData();
  } catch (err) {
    console.error(err);
    alert("Yeniden değerlendirme sırasında hata oluştu.");
  }
}

// Interactive AI Voice Call Simulator
function triggerAiCallSimulation(caseId) {
  appState.activeAiCallCaseId = caseId;
  const modal = document.getElementById("aiCallModal");
  modal.classList.add("active");

  const title = document.getElementById("callPatientTitle");
  const transcriptBox = document.getElementById("callTranscriptBox");
  const finishBtn = document.getElementById("btnFinishCall");

  title.textContent = `Hasta Telefon Hattı Aranıyor (Vaka: ${caseId})...`;
  transcriptBox.innerHTML = `<div class="transcript-placeholder">Telefon çalıyor... Hat bağlandı. Görüşme başlatılıyor.</div>`;
  finishBtn.style.display = "none";

  // Simulate call steps after brief realistic delay
  setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/cases/${caseId}/simulate-ai-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();

      title.textContent = "Görüşme Tamamlandı — Veriler Teyit Edildi";
      const lines = data.transcript.split("\n");
      transcriptBox.innerHTML = "";

      lines.forEach((line, idx) => {
        setTimeout(() => {
          const div = document.createElement("div");
          div.className = "transcript-line";
          if (line.startsWith("AI AGENT:")) {
            div.innerHTML = `<span class="transcript-agent">AI ASİSTAN:</span> ${line.replace("AI AGENT:", "")}`;
          } else {
            div.innerHTML = `<span class="transcript-patient">HASTA:</span> ${line.replace("PATIENT:", "")}`;
          }
          transcriptBox.appendChild(div);
          transcriptBox.scrollTop = transcriptBox.scrollHeight;
        }, idx * 400);
      });

      setTimeout(() => {
        finishBtn.style.display = "block";
        refreshAllData();
      }, lines.length * 400 + 200);

    } catch (err) {
      console.error(err);
      transcriptBox.innerHTML = `<div style="color:red;">Arama simülasyonunda hata oluştu.</div>`;
    }
  }, 1000);
}

function initModalActions() {
  document.getElementById("btnCloseCallModal").addEventListener("click", () => {
    document.getElementById("aiCallModal").classList.remove("active");
  });

  document.getElementById("btnFinishCall").addEventListener("click", () => {
    document.getElementById("aiCallModal").classList.remove("active");
    refreshAllData();
    switchTab("ai-queue");
  });
}

function inspectCase(caseId) {
  appState.selectedCaseId = caseId;
  switchTab("case-detail");
}

// Analytics View Loader
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/api/analytics`);
    const data = await res.json();

    // Channel chart
    const channelContainer = document.getElementById("analyticsChannelChart");
    channelContainer.innerHTML = "";
    data.channel_quality.forEach(ch => {
      channelContainer.innerHTML += `
        <div style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:700; margin-bottom:4px;">
            <span>${ch.source_channel}</span>
            <span style="color:#64748b;">${ch.avg_score}/100 Puan (${ch.total_cases} vaka)</span>
          </div>
          <div style="background:#e2e8f0; border-radius:3px; height:8px; overflow:hidden;">
            <div style="background:var(--primary-gradient); width:${ch.avg_score}%; height:100%;"></div>
          </div>
        </div>
      `;
    });

    // Tier distribution chart
    const tierContainer = document.getElementById("analyticsTierChart");
    tierContainer.innerHTML = "";
    const total = appState.kpis.total_cases || 1;
    data.tier_dist.forEach(t => {
      const pct = Math.round((t.count / total) * 100);
      const color = t.triage_tier === "Approved" ? "var(--tier1-green)" : t.triage_tier === "AI Call Scheduled" ? "var(--primary)" : "var(--tier3-rose)";
      tierContainer.innerHTML += `
        <div style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:700; margin-bottom:4px;">
            <span>${getTierBadgeLabel(t.triage_tier)}</span>
            <span style="color:#64748b;">${t.count} kayıt (${pct}%)</span>
          </div>
          <div style="background:#e2e8f0; border-radius:3px; height:8px; overflow:hidden;">
            <div style="background:${color}; width:${pct}%; height:100%;"></div>
          </div>
        </div>
      `;
    });

  } catch (err) {
    console.error(err);
  }
}

// Helpers
function getTierBadgeClass(tier) {
  if (tier === "Approved") return "tier-pill-1";
  if (tier === "AI Call Scheduled") return "tier-pill-ai";
  return "tier-pill-csr";
}

function getTierBadgeLabel(tier) {
  if (tier === "Approved") return "Kademe 1: Onaylandı";
  if (tier === "AI Call Scheduled") return "Kademe 2: AI Sesli Arama";
  return "Kademe 3: Müşteri Hizmetleri";
}

function getScoreBadgeClass(score) {
  if (score >= 80) return "tier-pill-1";
  if (score >= 50) return "tier-pill-ai";
  return "tier-pill-csr";
}

function formatFieldName(fieldName) {
  const map = {
    hospital: "Hastane / Şube",
    department: "Poliklinik / Birim",
    incident_date: "Olay Tarihi",
    approximate_time: "Yaklaşık Saat",
    service_type: "Hizmet / Tetkik Türü",
    staff_role: "Personel Unvanı",
    staff_name: "Personel Adı",
    billing_context: "Fatura / Ödeme Detayı",
    description_of_event: "Olay Açıklaması",
    impact: "Mağduriyet / Etki"
  };
  return map[fieldName] || fieldName;
}

function getQuestionText(fieldName) {
  const qMap = {
    hospital: "Ziyaret ettiğiniz hastane şubesini öğrenebilir miyiz?",
    department: "Hangi poliklinikten hizmet aldınız?",
    incident_date: "Olay hangi tarihte gerçekleşti?",
    approximate_time: "Durum yaklaşık saat kaçta meydana geldi?",
    service_type: "Hangi işlem sırasında bu aksaklık yaşandı?",
    staff_role: "İlgili personelin görevini hatırlıyor musunuz?",
    staff_name: "Görüştüğünüz personelin adını hatırlıyor musunuz?",
    billing_context: "Ödeme tutarsızlığı hakkında detay verebilir misiniz?",
    description_of_event: "Yaşanan durumu kısaca biraz daha detaylandırabilir misiniz?"
  };
  return qMap[fieldName] || "Bu detay hakkında bilgi verebilir misiniz?";
}
