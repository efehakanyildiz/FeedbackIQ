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
    tierTitle = "Aşama 1: Onaylandı / Yeterli Veri";
    if (result.requires_ai_call || (result.missing_fields && result.missing_fields.length > 0)) {
      tierActionHtml = `
        <div style="margin-top:10px; display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
          <span style="font-weight:700; color:#065f46;">
            Vaka onay eşiğini (90+) karşıladı ve onaylandı.
          </span>
          <button class="btn btn-primary" onclick="openAiCallFromAnalysis('${case_id}')">
            Yapay Zeka Sesli Aramasını Başlat
          </button>
        </div>
      `;
    } else {
      tierActionHtml = `
        <div style="margin-top:10px; font-weight:700; color:#065f46;">
          Tüm operasyonel gereksinimler eksiksiz tespit edildi. Vaka doğrudan ilgili poliklinik yöneticisine aktarılmıştır.
        </div>
      `;
    }
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
          <div style="display:flex; align-items:center; gap:6px;">
            <strong style="color:#334155;">${m.display_name}</strong>
            <span class="field-status-tag ${m.is_critical ? 'critical' : 'missing'}">
              ${m.is_critical ? 'Büyük Eksik' : 'Eksik'}
            </span>
          </div>
          <div style="color:var(--primary); font-size:0.8rem; margin-top:3px; font-weight:500;">Önerilen Soru: "${m.suggested_question}"</div>
        </div>
      `).join("")
    : `<div style="color:#059669; font-weight:600; font-size:0.85rem; padding:8px 0;">Eksik operasyonel parametre bulunmuyor.</div>`;

  container.innerHTML = `
    <div class="notice-box ${tierClass}">
      <div style="font-weight:800; font-size:1rem; margin-bottom:4px; font-family:var(--font-heading);">${tierTitle} &bull; <span style="font-family:var(--font-mono); font-size:0.95rem;">${case_id}</span></div>
      <div style="font-size:0.88rem; line-height:1.5;">${result.triage_reason}</div>
      ${tierActionHtml}
    </div>

    <div class="glass-card">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:1rem;">
        <div>
          <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#64748b; letter-spacing:0.05em;">Operasyonel Kalite Skoru</div>
          <div style="display:flex; align-items:baseline; gap:10px; margin-top:4px;">
            <span style="font-size:2.4rem; font-weight:800; color:var(--text-main); font-family:var(--font-heading); font-variant-numeric:tabular-nums;">${score}</span>
            <span style="color:#94a3b8; font-size:1rem; font-weight:700;">/ 100</span>
            <span class="badge-pill ${getTierBadgeClass(tier)}">${getTierBadgeLabel(tier)}</span>
          </div>
        </div>
        <div style="min-width:220px; flex:1; max-width:320px;">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; margin-bottom:6px; font-weight:600;">
            <span>Tamamlanma Oranı</span>
            <span style="font-family:var(--font-mono); font-weight:700;">${score}%</span>
          </div>
          <div style="background:#f1f5f9; border-radius:9999px; height:8px; overflow:hidden; border:1px solid #e2e8f0;">
            <div style="background:var(--primary-gradient); width:${score}%; height:100%; border-radius:9999px; transition:width 0.4s ease;"></div>
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
      <td><span style="font-family:var(--font-mono); font-weight:700; color:#0f172a; font-size:0.86rem;">${c.case_id}</span></td>
      <td><span style="font-family:var(--font-mono); font-size:0.8rem; color:#64748b;">${c.created_at}</span></td>
      <td><span style="font-size:0.78rem; font-weight:600; color:#475569; background:#f8fafc; border:1px solid #e2e8f0; padding:2px 7px; border-radius:4px;">${c.source_channel}</span></td>
      <td style="font-weight:600; color:#1e293b;">${c.issue_type}</td>
      <td><span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span></td>
      <td><span class="badge-pill ${getTierBadgeClass(c.triage_tier)}">${getTierBadgeLabel(c.triage_tier)}</span></td>
      <td style="color:#64748b; font-size:0.82rem; font-weight:500;">${c.status}</td>
      <td>
        <button class="btn btn-secondary" style="padding:4px 10px; font-size:0.75rem; border-radius:6px; font-weight:600;" onclick="inspectCase('${c.case_id}')">İncele</button>
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
        <div style="margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:700; margin-bottom:5px;">
            <span>${getTierBadgeLabel(row.triage_tier)}</span>
            <span style="color:#64748b; font-family:var(--font-mono); font-size:0.78rem;">${row.count} vaka (${pct}%)</span>
          </div>
          <div style="background:#f1f5f9; border-radius:9999px; height:8px; overflow:hidden; border:1px solid #e2e8f0;">
            <div style="background:${barColor}; width:${pct}%; height:100%; border-radius:9999px; transition:width 0.4s ease;"></div>
          </div>
        </div>
      `;
    });

    // Top Missing Fields List
    const missingContainer = document.getElementById("topMissingContainer");
    missingContainer.innerHTML = "";
    data.top_missing.slice(0, 5).forEach(m => {
      missingContainer.innerHTML += `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:9px 0; border-bottom:1px solid #f8fafc; font-size:0.85rem;">
          <span style="font-weight:600; color:#334155;">${formatFieldName(m.field_name)}</span>
          <span class="kpi-foot-pill" style="font-weight:700; font-size:0.74rem;">
            ${m.count} vakada eksik
          </span>
        </div>
      `;
    });
  } catch (err) {
    console.error("Dashboard analitik verisi yüklenemedi:", err);
  }
}

// AI Voice Queue Loader
function loadAiQueue() {
  const container = document.getElementById("aiQueueCardsContainer");
  container.innerHTML = "";

  const aiCases = appState.cases.filter(c => 
    c.triage_tier === "AI Call Scheduled" || 
    c.status === "AI Call Scheduled" ||
    (c.completeness_score >= 90 && c.completeness_score < 100 && c.contact_status !== "Completed" && c.contact_status !== "AI Call Completed") ||
    (c.triage_tier === "Approved" && c.missing_fields_count > 0 && c.contact_status !== "Completed" && c.contact_status !== "AI Call Completed")
  );

  if (aiCases.length === 0) {
    container.innerHTML = `
      <div class="notice-box notice-box-success">
        Yapay Zeka Sesli Arama Kuyruğunda bekleyen vaka bulunmuyor. Tüm veri eksiklikleri tamamlandı ve onaylandı.
      </div>
    `;
    return;
  }

  aiCases.forEach(c => {
    const isApprovedTier = c.completeness_score >= 90 || c.triage_tier === "Approved";
    const tierBadgeHtml = isApprovedTier
      ? `<span class="badge-pill tier-pill-1">Aşama 1: Onaylandı</span>`
      : `<span class="badge-pill tier-pill-ai">Kademe 2: AI Sesli Arama</span>`;

    const card = document.createElement("div");
    card.className = "glass-card";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
        <div>
          <span style="font-family:var(--font-mono); font-size:1.15rem; font-weight:800; color:var(--text-main); margin-right:8px;">${c.case_id}</span>
          <span style="font-family:var(--font-mono); font-size:0.8rem; color:#64748b; margin-right:8px;">${c.created_at}</span>
          <span style="background:#f8fafc; color:#475569; border:1px solid #e2e8f0; padding:2px 7px; border-radius:4px; font-size:0.72rem; font-weight:600;">
            Kanal: ${c.source_channel}
          </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span>
          ${tierBadgeHtml}
        </div>
      </div>
      <div style="font-size:0.88rem; color:#334155; margin-bottom:12px; font-style:normal; background:#f8fafc; padding:12px 16px; border-radius:6px; border:1px solid #e2e8f0; border-left:3px solid var(--primary); line-height:1.6;">
        "${c.original_feedback}"
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:#64748b; flex-wrap:wrap; gap:8px;">
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
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
        <div>
          <span style="font-family:var(--font-mono); font-size:1.15rem; font-weight:800; color:var(--text-main); margin-right:8px;">${c.case_id}</span>
          <span style="font-family:var(--font-mono); font-size:0.8rem; color:#64748b; margin-right:8px;">${c.created_at}</span>
          <span style="background:#f8fafc; color:#475569; border:1px solid #e2e8f0; padding:2px 7px; border-radius:4px; font-size:0.72rem; font-weight:600;">
            Kanal: ${c.source_channel}
          </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="score-badge-element ${getScoreBadgeClass(c.completeness_score)}">${c.completeness_score}/100</span>
          <span class="badge-pill tier-pill-csr">Kademe 3: Temsilci İncelemesi</span>
        </div>
      </div>
      <div style="font-size:0.88rem; color:#334155; margin-bottom:12px; font-style:normal; background:#f8fafc; padding:12px 16px; border-radius:6px; border:1px solid #e2e8f0; border-left:3px solid var(--tier3-rose); line-height:1.6;">
        "${c.original_feedback}"
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:#64748b; flex-wrap:wrap; gap:8px;">
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

const CLINICAL_DEPARTMENTS = [
  "Ortopedi",
  "Kardiyoloji",
  "Göz",
  "Dahiliye",
  "Çocuk Sağlığı ve Hastalıkları",
  "Radyoloji",
  "Biyokimya Laboratuvarı",
  "Acil Servis",
  "Vezne ve Muhasebe",
  "Hasta Kabul ve Kayıt",
  "Nöroloji",
  "Genel Cerrahi",
  "Kulak Burun Boğaz (KBB)",
  "Fizik Tedavi ve Rehabilitasyon",
  "Üroloji",
  "Cildiye (Dermatoloji)",
  "Göğüs Hastalıkları",
  "Kadın Hastalıkları ve Doğum",
  "Ağız ve Diş Sağlığı",
  "Beslenme ve Diyet"
];

const HOSPITAL_OPTIONS = [
  "Merkez Şehir Hastanesi",
  "Anadolu Şehir Hastanesi",
  "Kadıköy Tıp Merkezi",
  "Şişli Sağlık Merkezi",
  "Çamlıca Tıp Merkezi",
  "Bakırköy Polikliniği",
  "Kartal Tıp Merkezi",
  "Levent Sağlık Kompleksi"
];

const SERVICE_TYPE_OPTIONS = [
  "Poliklinik Muayenesi",
  "Kan Tahlili / Laboratuvar",
  "Radyoloji / Görüntüleme (MR, Tomografi, Eko)",
  "Ameliyat / Cerrahi Müdahale",
  "Hasta Kayıt / Giriş İşlemi",
  "Vezne / Fatura Tahsilatı",
  "Klinik Servis / Yatan Hasta",
  "Reçete / Rapor Onayı",
  "Acil Müdahale"
];

const STAFF_ROLE_OPTIONS = [
  "Doktor",
  "Hemşire",
  "Tıbbi Sekreter",
  "Hasta Kayıt Görevlisi",
  "Vezne Görevlisi",
  "Laborant / Teknisyen",
  "Güvenlik Görevlisi",
  "Temizlik / Kat Görevlisi",
  "Hasta Hakları Temsilcisi"
];

function extractTimeForInput(timeStr) {
  if (!timeStr) return "";
  const match = timeStr.match(/\b([01]?\d|2[0-3]):([0-5]\d)\b/);
  if (match) {
    let h = match[1];
    if (h.length === 1) h = "0" + h;
    return `${h}:${match[2]}`;
  }
  return "";
}

function extractDateForInput(dateStr) {
  if (!dateStr) return "";
  const match = dateStr.match(/\b\d{4}-\d{2}-\d{2}\b/);
  if (match) return match[0];
  const lower = dateStr.toLowerCase();
  const today = new Date();
  if (lower.includes("bugün") || lower.includes("today")) {
    return today.toISOString().split("T")[0];
  }
  if (lower.includes("dün") || lower.includes("yesterday")) {
    const yest = new Date(today);
    yest.setDate(yest.getDate() - 1);
    return yest.toISOString().split("T")[0];
  }
  return "";
}

function buildSelectOptions(optionsList, selectedVal, placeholder, allowCustom = true) {
  let html = `<option value="">${placeholder}</option>`;
  let matched = false;
  const sLower = (selectedVal || "").toLowerCase().trim();

  optionsList.forEach(opt => {
    const isSel = sLower && (sLower === opt.toLowerCase() || sLower.includes(opt.toLowerCase()) || opt.toLowerCase().includes(sLower));
    if (isSel && !matched) {
      html += `<option value="${opt}" selected>${opt}</option>`;
      matched = true;
    } else {
      html += `<option value="${opt}">${opt}</option>`;
    }
  });

  if (selectedVal && !matched && selectedVal.trim()) {
    html += `<option value="${selectedVal}" selected>${selectedVal}</option>`;
  }

  if (allowCustom) {
    html += `<option value="__custom__">Farklı / Özel Değer Girin...</option>`;
  }
  return html;
}

window.setCsrTime = function (t) {
  const el = document.getElementById("csrTime");
  if (el) el.value = t;
};

window.setCsrDate = function (type) {
  const el = document.getElementById("csrDate");
  if (!el) return;
  const today = new Date();
  if (type === "today") {
    el.value = today.toISOString().split("T")[0];
  } else if (type === "yesterday") {
    const yest = new Date(today);
    yest.setDate(yest.getDate() - 1);
    el.value = yest.toISOString().split("T")[0];
  }
};

window.handleSelectCustomToggle = function (selectEl, customInputId) {
  const customEl = document.getElementById(customInputId);
  if (!customEl) return;
  if (selectEl.value === "__custom__") {
    customEl.style.display = "block";
    customEl.focus();
  } else {
    customEl.style.display = "none";
  }
};

function renderCaseDetailWorkspace(detail) {
  const container = document.getElementById("caseDetailContent");
  const c = detail.case;
  const missing = detail.missing_fields || [];
  const history = detail.history || [];

  const missingSet = new Set(missing.map(m => m.field_name));
  const criticalSet = new Set(missing.filter(m => m.is_critical).map(m => m.field_name));

  const detectedItems = [
    { key: "hospital", label: "Hastane / Şube", val: c.hospital },
    { key: "department", label: "Poliklinik / Birim", val: c.department },
    { key: "incident_date", label: "Olay Tarihi", val: c.incident_date },
    { key: "approximate_time", label: "Randevu / Olay Saati", val: c.approximate_time },
    { key: "service_type", label: "Hizmet / Tetkik", val: c.service_type },
    { key: "staff_role", label: "Personel Unvanı", val: c.staff_role },
    { key: "staff_name", label: "Personel Adı", val: c.staff_name },
    { key: "billing_context", label: "Fatura / Ödeme Detayı", val: c.billing_context }
  ];

  const detectedRowsHtml = detectedItems.map(f => {
    const isMissing = missingSet.has(f.key) || !f.val;
    const isCrit = criticalSet.has(f.key);
    const statusTag = isMissing
      ? `<span class="field-status-tag ${isCrit ? 'critical' : 'missing'}">${isCrit ? 'Büyük Eksik' : 'Eksik'}</span>`
      : `<span class="field-status-tag detected">Teyitli</span>`;

    return `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #f1f5f9; font-size:0.84rem;">
        <span style="color:#64748b; display:flex; align-items:center; gap:6px;">
          ${f.label}
          ${statusTag}
        </span>
        <span style="font-weight:700; color:#0f172a; text-align:right; max-width:60%;">
          ${f.val || '<span style="color:#94a3b8; font-weight:normal; font-style:italic;">Belirtilmemiş</span>'}
        </span>
      </div>
    `;
  }).join("");

  const missingHtml = missing.length > 0
    ? missing.map(m => `
        <div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #f8fafc; font-size:0.83rem;">
          <div>
            <strong style="color:#334155;">${formatFieldName(m.field_name)}</strong>
            <span class="field-status-tag ${m.is_critical ? 'critical' : 'missing'}" style="margin-left:4px;">
              ${m.is_critical ? 'Büyük Eksik' : 'Eksik'}
            </span>
          </div>
          <div style="color:var(--primary); font-size:0.8rem; margin-top:2px;">Önerilen İletişim Sorusu: "${getQuestionText(m.field_name)}"</div>
        </div>
      `).join("")
    : `<div style="color:#059669; font-weight:700; font-size:0.86rem; padding:10px 0;">Tüm operasyonel gereksinimler eksiksiz teyit edildi.</div>`;

  const timeVal = extractTimeForInput(c.approximate_time);
  const dateVal = extractDateForInput(c.incident_date);

  container.innerHTML = `
    <div class="glass-card" style="margin-bottom:1.2rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <span style="font-size:1.35rem; font-weight:800; color:#0f172a; margin-right:12px;">Vaka Kaydı: <span style="font-family:var(--font-mono); font-size:1.25rem;">${c.case_id}</span></span>
          <span style="font-size:0.84rem; color:#64748b;">Tarih: <span style="font-family:var(--font-mono);">${c.created_at}</span> &bull; Kanal: <span style="background:#f8fafc; border:1px solid #e2e8f0; padding:1px 6px; border-radius:4px; font-weight:600; color:#475569;">${c.source_channel}</span></span>
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
      <div style="background:#f8fafc; border:1px solid #e2e8f0; border-left:3px solid var(--primary); padding:1rem 1.2rem; border-radius:6px; font-size:0.92rem; color:#1e293b; line-height:1.6;">
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
        <div class="card-title">Mevcut Operasyonel Durum</div>
        ${detectedRowsHtml}
      </div>

      <div class="glass-card">
        <div class="card-title">Eksik Kalan Bilgiler & İletişim İpuçları</div>
        ${missingHtml}
      </div>
    </div>

    <!-- CSR Investigation & Re-evaluation Form -->
    <div class="glass-card" style="border: 1px solid #cbd5e1; background:#ffffff; box-shadow:var(--shadow-sm);">
      <div class="card-title" style="color:var(--primary-dark); font-size:1.05rem;">
        Müşteri Hizmetleri Masası: Operasyonel Bilgileri Tamamlama ve Teyit Formu
      </div>
      <p style="font-size:0.84rem; color:#475569; margin-bottom:14px; line-height:1.5;">
        Hasta ile yapılan telefon görüşmesinde teyit edilen bilgileri aşağıdan seçip tamamlayınız. Temsilcinin girdiği teyitli bilgiler yapay zekanın ilk tespitlerinin üzerine yazılarak vakayı anında yeniden puanlar ve onaylar.
      </p>

      <div class="grid-3col form-row">
        <!-- Hastane / Şube -->
        <div class="form-group">
          <label class="form-label">Teyit Edilen Hastane / Şube</label>
          <select class="form-select form-select-sm" id="csrHospital" onchange="handleSelectCustomToggle(this, 'csrHospitalCustom')">
            ${buildSelectOptions(HOSPITAL_OPTIONS, c.hospital, "Hastane / Şube Seçiniz...")}
          </select>
          <input type="text" class="form-input form-input-sm" id="csrHospitalCustom" placeholder="Farklı hastane/şube adı yazınız..." style="display:none; margin-top:6px;" />
        </div>

        <!-- Poliklinik / Birim -->
        <div class="form-group">
          <label class="form-label">Teyit Edilen Poliklinik / Birim</label>
          <select class="form-select form-select-sm" id="csrDept" onchange="handleSelectCustomToggle(this, 'csrDeptCustom')">
            ${buildSelectOptions(CLINICAL_DEPARTMENTS, c.department, "Poliklinik / Birim Seçiniz...")}
          </select>
          <input type="text" class="form-input form-input-sm" id="csrDeptCustom" placeholder="Farklı birim adı yazınız..." style="display:none; margin-top:6px;" />
        </div>

        <!-- Randevu / Olay Saati -->
        <div class="form-group">
          <label class="form-label">Teyit Edilen Saat (HH:MM)</label>
          <input type="time" class="form-input form-input-sm" id="csrTime" value="${timeVal}" />
          <div class="shortcuts-bar">
            <span style="font-size:0.72rem; color:#64748b; line-height:1.8;">Hızlı:</span>
            <button type="button" class="shortcut-btn" onclick="setCsrTime('09:00')">09:00</button>
            <button type="button" class="shortcut-btn" onclick="setCsrTime('10:30')">10:30</button>
            <button type="button" class="shortcut-btn" onclick="setCsrTime('14:00')">14:00</button>
            <button type="button" class="shortcut-btn" onclick="setCsrTime('15:30')">15:30</button>
          </div>
        </div>
      </div>

      <div class="grid-3col form-row">
        <!-- Olay / Randevu Tarihi -->
        <div class="form-group">
          <label class="form-label">Teyit Edilen Tarih</label>
          <input type="date" class="form-input form-input-sm" id="csrDate" value="${dateVal}" />
          <div class="shortcuts-bar">
            <span style="font-size:0.72rem; color:#64748b; line-height:1.8;">Hızlı:</span>
            <button type="button" class="shortcut-btn" onclick="setCsrDate('today')">Bugün</button>
            <button type="button" class="shortcut-btn" onclick="setCsrDate('yesterday')">Dün</button>
          </div>
        </div>

        <!-- Hizmet / Tetkik Türü -->
        <div class="form-group">
          <label class="form-label">Hizmet / Tetkik Türü</label>
          <select class="form-select form-select-sm" id="csrServiceType">
            ${buildSelectOptions(SERVICE_TYPE_OPTIONS, c.service_type, "Hizmet Türü Seçiniz...", false)}
          </select>
        </div>

        <!-- Personel Unvanı -->
        <div class="form-group">
          <label class="form-label">İlgili Personel Unvanı</label>
          <select class="form-select form-select-sm" id="csrStaffRole">
            ${buildSelectOptions(STAFF_ROLE_OPTIONS, c.staff_role, "Personel Unvanı Seçiniz...", false)}
          </select>
        </div>
      </div>

      <div class="grid-2col form-row">
        <!-- Personel Adı -->
        <div class="form-group">
          <label class="form-label">Personel Adı (Varsa)</label>
          <input type="text" class="form-input form-input-sm" id="csrStaffName" value="${c.staff_name || ''}" placeholder="Örn: Dr. Ahmet Yılmaz veya Hemşire Fatma" />
        </div>

        <!-- Fatura / Ödeme Detayı -->
        <div class="form-group">
          <label class="form-label">Fatura / Ödeme / Tutar Detayı (Varsa)</label>
          <input type="text" class="form-input form-input-sm" id="csrBilling" value="${c.billing_context || ''}" placeholder="Örn: Mükerrer kart çekimi, POS slip no, 350 TL" />
        </div>
      </div>

      <div class="grid-2col form-row">
        <!-- Görüşme Sonucu -->
        <div class="form-group">
          <label class="form-label">Görüşme İletişim Sonucu</label>
          <select class="form-select form-select-sm" id="csrContactStatus">
            <option value="Information Collected" selected>Görüşme Yapıldı — Eksik Bilgiler Teyit Edildi</option>
            <option value="In Progress">İnceleme Devam Ediyor</option>
            <option value="Patient Reached - Partially Resolved">Hastaya Ulaşıldı — Kısmi Bilgi Alındı</option>
            <option value="No Answer / Busy">Cevap Vermedi / Ulaşılamadı</option>
          </select>
        </div>

        <!-- Temsilci Görüşme Notu -->
        <div class="form-group">
          <label class="form-label">Temsilci İnceleme ve Çözüm Notu</label>
          <input type="text" class="form-input form-input-sm" id="csrNotes" placeholder="Örn: Hasta telefonla arandı, randevu saati ve poliklinik teyit edildi." />
        </div>
      </div>

      <div class="form-actions" style="margin-top:1.2rem;">
        <button class="btn btn-primary btn-large" style="width:100%; justify-content:center; font-weight:700; font-size:0.95rem; padding:0.75rem 1.5rem;" onclick="submitCsrReevaluation('${c.case_id}')">
          Teyitli Operasyonel Bilgileri Kaydet, Vakayı Yeniden Değerlendir ve Onayla
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

  // Hospital
  const hospEl = document.getElementById("csrHospital");
  const hospCustomEl = document.getElementById("csrHospitalCustom");
  let hosp = hospEl ? hospEl.value.trim() : "";
  if (hosp === "__custom__" && hospCustomEl) {
    hosp = hospCustomEl.value.trim();
  }
  if (hosp) confirmed.hospital = hosp;

  // Department
  const deptEl = document.getElementById("csrDept");
  const deptCustomEl = document.getElementById("csrDeptCustom");
  let dept = deptEl ? deptEl.value.trim() : "";
  if (dept === "__custom__" && deptCustomEl) {
    dept = deptCustomEl.value.trim();
  }
  if (dept) confirmed.department = dept;

  // Time
  const timeEl = document.getElementById("csrTime");
  if (timeEl && timeEl.value.trim()) {
    confirmed.approximate_time = timeEl.value.trim();
  }

  // Date
  const dateEl = document.getElementById("csrDate");
  if (dateEl && dateEl.value.trim()) {
    confirmed.incident_date = dateEl.value.trim();
  }

  // Service Type
  const srvEl = document.getElementById("csrServiceType");
  if (srvEl && srvEl.value.trim()) {
    confirmed.service_type = srvEl.value.trim();
  }

  // Staff Role
  const roleEl = document.getElementById("csrStaffRole");
  if (roleEl && roleEl.value.trim()) {
    confirmed.staff_role = roleEl.value.trim();
  }

  // Staff Name
  const nameEl = document.getElementById("csrStaffName");
  if (nameEl && nameEl.value.trim()) {
    confirmed.staff_name = nameEl.value.trim();
  }

  // Billing Context
  const billEl = document.getElementById("csrBilling");
  if (billEl && billEl.value.trim()) {
    confirmed.billing_context = billEl.value.trim();
  }

  // Notes
  const notesEl = document.getElementById("csrNotes");
  const notes = notesEl && notesEl.value.trim() ? notesEl.value.trim() : "Müşteri Hizmetleri Masası üzerinden teyit edildi.";

  // Contact Status
  const statusEl = document.getElementById("csrContactStatus");
  const contactStatus = statusEl && statusEl.value ? statusEl.value : "Information Collected";

  try {
    const res = await fetch(`${API_BASE}/api/cases/${caseId}/reevaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        confirmed_fields: confirmed,
        notes: notes,
        contact_status: contactStatus
      })
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const resultData = await res.json();
    alert(`Vaka başarıyla yeniden değerlendirildi!\nYeni Skor: ${resultData.result.completeness_score}/100\nDurum: ${resultData.case.status}`);
    refreshAllData();
  } catch (err) {
    console.error(err);
    alert("Yeniden değerlendirme sırasında bir hata oluştu.");
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
        <div style="margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:700; margin-bottom:5px;">
            <span>${ch.source_channel}</span>
            <span style="color:#64748b; font-family:var(--font-mono); font-size:0.78rem;">${ch.avg_score}/100 Puan (${ch.total_cases} vaka)</span>
          </div>
          <div style="background:#f1f5f9; border-radius:9999px; height:8px; overflow:hidden; border:1px solid #e2e8f0;">
            <div style="background:var(--primary-gradient); width:${ch.avg_score}%; height:100%; border-radius:9999px; transition:width 0.4s ease;"></div>
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
        <div style="margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:700; margin-bottom:5px;">
            <span>${getTierBadgeLabel(t.triage_tier)}</span>
            <span style="color:#64748b; font-family:var(--font-mono); font-size:0.78rem;">${t.count} kayıt (${pct}%)</span>
          </div>
          <div style="background:#f1f5f9; border-radius:9999px; height:8px; overflow:hidden; border:1px solid #e2e8f0;">
            <div style="background:${color}; width:${pct}%; height:100%; border-radius:9999px; transition:width 0.4s ease;"></div>
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
  if (tier === "Approved") return "Aşama 1: Onaylandı";
  if (tier === "AI Call Scheduled") return "Kademe 2: AI Sesli Arama";
  return "Kademe 3: Müşteri Hizmetleri";
}

function getScoreBadgeClass(score) {
  if (score >= 90) return "tier-pill-1";
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
