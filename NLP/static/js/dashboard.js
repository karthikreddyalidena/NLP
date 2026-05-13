/**
 * CrisisAI Sentinel — Main Dashboard JavaScript
 * Real-time Socket.IO updates, Chart.js visualizations, Leaflet maps
 */

// ── Socket Connection ────────────────────────────────────────────
const socket = io();
let tweetCount = 0;
let anomalyCount = 0;
let alertCounts = { CRITICAL: 0, HIGH: 0, MODERATE: 0, LOW: 0 };
let currentPlatformFilter = 'all';

// ── Chart Instances ──────────────────────────────────────────────
let crisisTimelineChart = null;
let sentimentDonutChart = null;
let topicBarChart       = null;
let radarChart          = null;
let distHistogram       = null;
let anomalyHistogram    = null;
let clusterProfileChart = null;
let sentimentTrendChart = null;
let alertTimelineChart  = null;
let sourceBreakdownChart = null;

// ── Data Buffers ─────────────────────────────────────────────────
const crisisHistory       = [];
const sentimentHistory    = { negative: 0, neutral: 0, positive: 0 };
const topicCounts         = {};
const distressBuffer      = [];
const anomalyBuffer       = [];
const alertTimeline       = { labels: [], counts: [] };
const sourceCounts        = { reddit: 0, usgs: 0, gdelt: 0, news: 0 };

// ── Map Instance ─────────────────────────────────────────────────
let crisisMap = null;
let mapMarkers = [];

// ── Chart.js Global Defaults ─────────────────────────────────────
Chart.defaults.color = '#8899bb';
Chart.defaults.borderColor = '#1e2d45';
Chart.defaults.font.family = "'Inter', sans-serif";

// ════════════════════════════════════════════════════════════════
//  DASHBOARD INIT
// ════════════════════════════════════════════════════════════════
function initDashboard() {
  startClock();
  initCrisisTimeline();
  initSentimentDonut();
  initTopicBar();
  initRadarChart();
  initMap();
}

// ── Clock ────────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('clockDisplay');
  if (!el) return;
  setInterval(() => {
    el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
  }, 1000);
}

// ── Socket Events ────────────────────────────────────────────────
socket.on('connect', () => {
  console.log('[WS] Connected to CrisisAI stream');
  document.getElementById('liveIndicator') && document.getElementById('liveIndicator').classList.add('connected');
});

socket.on('init_data', (data) => {
  console.log('[INIT]', data);
  if (data.alerts?.length) {
    data.alerts.forEach(a => updateAlertBadge(a));
  }
});

socket.on('stream_update', (data) => {
  // 1. Update KPIs
  updateKPIs(data);

  // 2. Update charts
  updateCrisisTimeline(data.crisis_trend);
  updateSentimentDonut(data.tweets);
  updateTopicBar(data.topic_distribution);
  updateRadar(data.components);

  // 3. Update map
  updateMap(data.geo_points);

  // 4. Update tweet feed
  if (data.tweets?.length) renderTweets(data.tweets);

  // 5. Handle alert
  if (data.alert) {
    showAlertToast(data.alert);
    updateAlertBadge(data.alert);
  }

  // 6. Update sidebar
  updateSidebar(data.crisis_score);

  // 7. Analytics page updates
  updateAnalytics(data);
});

socket.on('crisis_simulated', (data) => {
  console.log('[CRISIS SIM] score:', data.score);
});

// ════════════════════════════════════════════════════════════════
//  KPI UPDATES
// ════════════════════════════════════════════════════════════════
function updateKPIs(data) {
  const score = data.crisis_score || 0;
  const severity = data.severity || {};
  const stats = data.stats || {};

  // Crisis Score
  setVal('kpiCrisisScore', score.toFixed(3));
  const badge = document.getElementById('kpiSeverityBadge');
  if (badge) {
    badge.textContent = severity.level || 'MONITORING';
    badge.style.background = (severity.color || '#10b981') + '22';
    badge.style.color = severity.color || '#10b981';
  }

  // Tweet count
  tweetCount += (data.tweets?.length || 0);
  setVal('kpiTweets', formatNum(tweetCount));

  // Alerts
  const totalAlerts = stats.total_alerts || 0;
  setVal('kpiAlerts', totalAlerts);
  if (data.alert_counts) {
    alertCounts = {...alertCounts, ...data.alert_counts};
    const el = document.getElementById('kpiAlertBreak');
    if (el) el.textContent = `🔴${alertCounts.CRITICAL} 🟠${alertCounts.HIGH} 🟡${alertCounts.MODERATE}`;
  }

  // Distress
  const distress = data.components?.sentiment || 0;
  setVal('kpiDistress', distress.toFixed(3));
  const dBar = document.getElementById('kpiDistressBar');
  if (dBar) dBar.style.width = (distress * 100).toFixed(1) + '%';

  // Anomalies
  const topA = data.top_anomalies || [];
  if (topA.length) anomalyCount++;
  setVal('kpiAnomalies', anomalyCount);

  // Volume spike
  const volEl = document.getElementById('kpiVolSpike');
  if (volEl && data.vol_anomaly) {
    const va = data.vol_anomaly;
    volEl.textContent = va.is_anomaly ? `⚡ Volume Spike z=${va.z_score}` : 'Normal volume';
    volEl.style.color = va.is_anomaly ? '#f97316' : '#10b981';
  }

  // Source counting
  (data.tweets || []).forEach(t => {
    distressBuffer.push(t.sentiment?.distress_score || 0);
    anomalyBuffer.push(t.anomaly_score || 0);
    const p = (t.platform || 'reddit').toLowerCase();
    if (sourceCounts.hasOwnProperty(p)) sourceCounts[p]++;
  });
  if (distressBuffer.length > 500) distressBuffer.splice(0, distressBuffer.length - 500);
  if (anomalyBuffer.length > 500) anomalyBuffer.splice(0, anomalyBuffer.length - 500);
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = val;
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 500);
  }
}

function formatNum(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return n;
}

// ════════════════════════════════════════════════════════════════
//  CHARTS
// ════════════════════════════════════════════════════════════════
function initCrisisTimeline() {
  const ctx = document.getElementById('crisisTimelineChart');
  if (!ctx) return;
  crisisTimelineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Crisis Score',
        data: [],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239,68,68,0.08)',
        borderWidth: 2.5,
        pointRadius: 0,
        fill: true,
        tension: 0.4
      }, {
        label: 'Distress',
        data: [],
        borderColor: '#f97316',
        backgroundColor: 'rgba(249,115,22,0.06)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 400 },
      scales: {
        x: { grid: { color: '#1e2d45' }, ticks: { maxTicksLimit: 8, font: { size: 10 } } },
        y: { min: 0, max: 1, grid: { color: '#1e2d45' }, ticks: { stepSize: 0.25, font: { size: 10 } } }
      },
      plugins: { legend: { position: 'top', labels: { font: { size: 11 }, boxWidth: 12 } } }
    }
  });
}

function updateCrisisTimeline(crisisTrend) {
  if (!crisisTimelineChart || !crisisTrend?.length) return;
  const labels = crisisTrend.map(d => d.time);
  const scores = crisisTrend.map(d => d.score);
  crisisTimelineChart.data.labels = labels;
  crisisTimelineChart.data.datasets[0].data = scores;
  crisisTimelineChart.update('none');
}

function initSentimentDonut() {
  const ctx = document.getElementById('sentimentDonutChart');
  if (!ctx) return;
  sentimentDonutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Negative', 'Neutral', 'Positive'],
      datasets: [{
        data: [33, 34, 33],
        backgroundColor: ['rgba(239,68,68,0.8)', 'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)'],
        borderColor: ['#ef4444', '#3b82f6', '#10b981'],
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '70%',
      plugins: { legend: { display: false } }
    }
  });
}

function updateSentimentDonut(tweets) {
  if (!sentimentDonutChart || !tweets?.length) return;
  let neg = 0, neu = 0, pos = 0;
  tweets.forEach(t => {
    const lbl = t.sentiment?.sentiment_label || 'neutral';
    if (lbl === 'negative') neg++;
    else if (lbl === 'positive') pos++;
    else neu++;
  });
  sentimentDonutChart.data.datasets[0].data = [neg, neu, pos];
  sentimentDonutChart.update('none');
}

function initTopicBar() {
  const ctx = document.getElementById('topicBarChart');
  if (!ctx) return;
  topicBarChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: 'Topic Share',
        data: [],
        backgroundColor: ['#FF6B35','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD'],
        borderWidth: 0,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 600 },
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#1e2d45' }, max: 0.5, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } }
      }
    }
  });
}

function updateTopicBar(topicDist) {
  if (!topicBarChart || !topicDist?.length) return;
  topicBarChart.data.labels = topicDist.map(t => t.label?.slice(0, 20) || `T${t.topic_id}`);
  topicBarChart.data.datasets[0].data = topicDist.map(t => t.proportion);
  topicBarChart.data.datasets[0].backgroundColor = topicDist.map(t => t.color || '#888');
  topicBarChart.update('none');
}

function initRadarChart() {
  const ctx = document.getElementById('radarChart');
  if (!ctx) return;
  radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Sentiment', 'Anomaly', 'Cluster', 'Keyword', 'Volume', 'Engagement'],
      datasets: [{
        label: 'Crisis Signal',
        data: [0, 0, 0, 0, 0, 0],
        backgroundColor: 'rgba(239,68,68,0.15)',
        borderColor: '#ef4444',
        borderWidth: 2,
        pointBackgroundColor: '#ef4444',
        pointRadius: 3
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 400 },
      scales: {
        r: {
          min: 0, max: 1,
          grid: { color: '#1e2d45' },
          ticks: { stepSize: 0.25, color: '#4a5a78', font: { size: 9 }, backdropColor: 'transparent' },
          pointLabels: { font: { size: 9 }, color: '#8899bb' }
        }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function updateRadar(components) {
  if (!radarChart || !components) return;
  radarChart.data.datasets[0].data = [
    components.sentiment || 0,
    components.anomaly || 0,
    components.cluster || 0,
    components.keyword || 0,
    components.volume || 0,
    components.engagement || 0
  ];
  radarChart.update('none');
}

// ════════════════════════════════════════════════════════════════
//  MAP
// ════════════════════════════════════════════════════════════════
function initMap() {
  const mapEl = document.getElementById('crisisMap');
  if (!mapEl) return;

  crisisMap = L.map('crisisMap', {
    center: [37.5, -95],
    zoom: 4,
    zoomControl: true,
    attributionControl: false
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(crisisMap);
}

function updateMap(geoPoints) {
  if (!crisisMap || !geoPoints?.length) return;

  // Remove old markers (keep last 50)
  if (mapMarkers.length > 80) {
    const toRemove = mapMarkers.splice(0, mapMarkers.length - 80);
    toRemove.forEach(m => crisisMap.removeLayer(m));
  }

  const recent = geoPoints.slice(-15);
  recent.forEach(pt => {
    const d = pt.distress || 0;
    let color = '#2979ff';
    if (d > 0.85) color = '#ff1744';
    else if (d > 0.65) color = '#ff6d00';
    else if (d > 0.45) color = '#ffd600';

    const radius = 4 + d * 12;
    const m = L.circleMarker([pt.lat, pt.lon], {
      radius: radius,
      fillColor: color,
      color: 'rgba(255,255,255,0.2)',
      weight: 1,
      opacity: 0.9,
      fillOpacity: 0.75
    }).addTo(crisisMap);

    m.bindPopup(`
      <div style="font-family:Inter;font-size:12px;min-width:160px">
        <b>📍 ${pt.location}</b><br/>
        Type: <b>${(pt.type || 'normal').toUpperCase()}</b><br/>
        Distress: <b style="color:${color}">${(d * 100).toFixed(0)}%</b>
      </div>
    `);

    mapMarkers.push(m);
  });
}

// ════════════════════════════════════════════════════════════════
//  TWEET FEED
// ════════════════════════════════════════════════════════════════
function renderTweets(tweets) {
  const feed = document.getElementById('tweetFeed');
  if (!feed) return;

  tweets.slice(0, 5).forEach(t => {
    const d = t.sentiment?.distress_score || 0;
    let pillClass = 'low', pillText = 'Low';
    if (d > 0.80) { pillClass = 'critical'; pillText = 'Critical'; }
    else if (d > 0.60) { pillClass = 'high'; pillText = 'High'; }
    else if (d > 0.40) { pillClass = 'med'; pillText = 'Medium'; }

    const urgentBadge = t.sentiment?.is_urgent
      ? `<span class="urgent-badge">URGENT</span>` : '';

    const cardClass = d > 0.80 ? 'crisis' : (d > 0.60 ? 'high' : '');

    const div = document.createElement('div');
    div.className = `tweet-card ${cardClass}`;
    div.dataset.platform = (t.platform || 'reddit').toLowerCase();
    
    // Hide initially if filter active
    if (currentPlatformFilter !== 'all' && div.dataset.platform !== currentPlatformFilter) {
      div.style.display = 'none';
    }
    
    // Platform icon logic
    let platformIcon = '🌐';
    if (t.platform === 'reddit') platformIcon = '👾';
    else if (t.platform === 'usgs') platformIcon = '🌋';
    else if (t.platform === 'gdelt') platformIcon = '🌍';
    else if (t.platform === 'news') platformIcon = '📰';
    else if (t.platform === 'gdacs') platformIcon = '🚨';
    else if (t.platform === 'reliefweb') platformIcon = '🏥';
    else if (t.platform === 'synthetic') platformIcon = '🤖';
    else if (t.platform === 'twitter') platformIcon = '🐦';
    else if (t.platform === 'facebook') platformIcon = '📘';
    else if (t.platform === 'instagram') platformIcon = '📸';

    div.innerHTML = `
      <div class="tweet-header">
        <span class="tweet-platform ${t.platform}">${platformIcon} ${(t.platform||'twitter').toUpperCase()}</span>
        <span class="tweet-location">📍 ${t.location}</span>
        <span class="tweet-type ${t.disaster_type || 'normal'}">${(t.disaster_type||'normal').toUpperCase()}</span>
        ${urgentBadge}
      </div>
      <div class="tweet-text">${escapeHtml(t.text)}</div>
      <div class="tweet-meta">
        <span class="distress-pill ${pillClass}">⚡ ${pillText} (${d.toFixed(2)})</span>
        <span class="tweet-anomaly">Anomaly: ${(t.anomaly_score||0).toFixed(2)}</span>
        <span class="tweet-stats">🔁${t.retweets} ❤${t.likes}</span>
      </div>`;

    feed.insertBefore(div, feed.firstChild);

    // Remove old cards
    while (feed.children.length > 12) {
      feed.removeChild(feed.lastChild);
    }
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ════════════════════════════════════════════════════════════════
//  ALERT TOASTS
// ════════════════════════════════════════════════════════════════
function showAlertToast(alert) {
  if (!alert) return;
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const level = (alert.severity_level || 'LOW').toLowerCase();
  const toast = document.createElement('div');
  toast.className = `toast ${level}`;
  toast.innerHTML = `
    <div class="toast-icon">${alert.severity_icon || '⚠️'}</div>
    <div class="toast-body">
      <div class="toast-title">${alert.severity_level} — ${alert.disaster_type?.toUpperCase()}</div>
      <div class="toast-msg">📍 ${alert.location} · ID: #${alert.alert_id}</div>
      <div class="toast-score ${level}">Crisis Score: ${(alert.crisis_score||0).toFixed(3)}</div>
    </div>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

function updateAlertBadge(alert) {
  const badge = document.getElementById('alertBadge');
  if (!badge) return;
  const current = parseInt(badge.textContent) || 0;
  badge.textContent = current + 1;
}

// ════════════════════════════════════════════════════════════════
//  SIDEBAR
// ════════════════════════════════════════════════════════════════
function updateSidebar(score) {
  const bar = document.getElementById('sidebarCrisisBar');
  const val = document.getElementById('sidebarCrisisVal');
  if (bar) bar.style.width = ((score || 0) * 100).toFixed(1) + '%';
  if (val) val.textContent = (score || 0).toFixed(3);
}

// ════════════════════════════════════════════════════════════════
//  SIMULATE CRISIS
// ════════════════════════════════════════════════════════════════
async function simulateCrisis() {
  const btn = document.getElementById('btnSimulate');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Simulating…'; }
  try {
    const res = await fetch('/api/simulate_crisis', { method: 'POST' });
    const data = await res.json();
    console.log('[SIM]', data);
    if (btn) {
      btn.textContent = `✅ Score: ${(data.score||0).toFixed(2)}`;
      setTimeout(() => { btn.disabled = false; btn.textContent = '⚡ Simulate Crisis'; }, 3000);
    }
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = '⚡ Simulate Crisis'; }
  }
}

// ════════════════════════════════════════════════════════════════
//  ANALYTICS PAGE
// ════════════════════════════════════════════════════════════════
function initAnalytics() {
  initDistHistogram();
  initAnomalyHistogram();
  initClusterProfileChart();
  initSentimentTrendChart();
  initSourceBreakdownChart();
  loadModelStats();
  loadTopicsGrid();
}

async function loadModelStats() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const clust = data.models?.clustering || {};
    const sil = document.getElementById('silhouetteScore');
    const db = document.getElementById('dbScore');
    if (sil) sil.textContent = clust.silhouette_score !== undefined ? clust.silhouette_score.toFixed(3) : '—';
    if (db) db.textContent = clust.davies_bouldin_score !== undefined ? clust.davies_bouldin_score.toFixed(3) : '—';
  } catch {}
}

async function loadTopicsGrid() {
  try {
    const res = await fetch('/api/topics');
    const topics = await res.json();
    const grid = document.getElementById('topicsGrid');
    if (!grid || !topics.length) return;
    grid.innerHTML = topics.map(t => `
      <div class="topic-card" style="border-left-color:${t.color}">
        <div class="topic-label" style="color:${t.color}">${t.label}</div>
        <div class="topic-words">${t.word_string || (t.words||[]).map(w=>w[0]).join(', ')}</div>
      </div>`).join('');
  } catch {}
}

function initDistHistogram() {
  const ctx = document.getElementById('distHistogram');
  if (!ctx) return;
  distHistogram = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['0-.1','0.1-.2','0.2-.3','0.3-.4','0.4-.5','0.5-.6','0.6-.7','0.7-.8','0.8-.9','0.9-1'],
      datasets: [{
        label: 'Frequency',
        data: new Array(10).fill(0),
        backgroundColor: 'rgba(139,92,246,0.6)',
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: '#1e2d45' }, ticks: { font: { size: 9 } } }, y: { grid: { color: '#1e2d45' } } }
    }
  });
}

function initAnomalyHistogram() {
  const ctx = document.getElementById('anomalyHistogram');
  if (!ctx) return;
  anomalyHistogram = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['0-.1','0.1-.2','0.2-.3','0.3-.4','0.4-.5','0.5-.6','0.6-.7','0.7-.8','0.8-.9','0.9-1'],
      datasets: [{
        label: 'Frequency',
        data: new Array(10).fill(0),
        backgroundColor: 'rgba(249,115,22,0.6)',
        borderColor: '#f97316',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: '#1e2d45' }, ticks: { font: { size: 9 } } }, y: { grid: { color: '#1e2d45' } } }
    }
  });
}

function initClusterProfileChart() {
  const ctx = document.getElementById('clusterProfileChart');
  if (!ctx) return;
  clusterProfileChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        { label: 'Mean Distress', data: [], backgroundColor: 'rgba(239,68,68,0.7)', borderRadius: 4 },
        { label: 'Max Distress', data: [], backgroundColor: 'rgba(249,115,22,0.5)', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { size: 11 } } } },
      scales: {
        x: { grid: { color: '#1e2d45' } },
        y: { min: 0, max: 1, grid: { color: '#1e2d45' } }
      }
    }
  });
  // Load cluster profiles
  setTimeout(loadClusterProfiles, 3000);
}

async function loadClusterProfiles() {
  try {
    const res = await fetch('/api/cluster_profiles');
    const profiles = await res.json();
    if (!clusterProfileChart || !profiles || profiles.error) return;
    const labels = Object.keys(profiles).map(k => `Cluster ${k}`);
    const means = Object.values(profiles).map(p => p.mean_distress);
    const maxes = Object.values(profiles).map(p => p.max_distress);
    clusterProfileChart.data.labels = labels;
    clusterProfileChart.data.datasets[0].data = means;
    clusterProfileChart.data.datasets[1].data = maxes;
    clusterProfileChart.update();
  } catch {}
}

function initSentimentTrendChart() {
  const ctx = document.getElementById('sentimentTrendChart');
  if (!ctx) return;
  sentimentTrendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Distress',
        data: [],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239,68,68,0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#1e2d45' }, ticks: { maxTicksLimit: 6, font: { size: 9 } } },
        y: { min: 0, max: 1, grid: { color: '#1e2d45' } }
      }
    }
  });
}

function updateAnalytics(data) {
  // Update histograms
  if (distHistogram && distressBuffer.length > 5) {
    const hist = new Array(10).fill(0);
    distressBuffer.forEach(v => {
      const bin = Math.min(9, Math.floor(v * 10));
      hist[bin]++;
    });
    distHistogram.data.datasets[0].data = hist;
    distHistogram.update('none');
  }
  if (anomalyHistogram && anomalyBuffer.length > 5) {
    const hist = new Array(10).fill(0);
    anomalyBuffer.forEach(v => {
      const bin = Math.min(9, Math.floor(v * 10));
      hist[bin]++;
    });
    anomalyHistogram.data.datasets[0].data = hist;
    anomalyHistogram.update('none');
  }

  // Sentiment trend
  if (sentimentTrendChart && data.sentiment_trend?.length) {
    sentimentTrendChart.data.labels = data.sentiment_trend.map(s => s.time);
    sentimentTrendChart.data.datasets[0].data = data.sentiment_trend.map(s => s.distress);
    sentimentTrendChart.update('none');
  }

  // Source breakdown
  if (sourceBreakdownChart) {
    sourceBreakdownChart.data.datasets[0].data = Object.values(sourceCounts);
    sourceBreakdownChart.update('none');
  }
}

function initSourceBreakdownChart() {
  const ctx = document.getElementById('sourceBreakdownChart');
  if (!ctx) return;
  sourceBreakdownChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Reddit', 'USGS', 'GDELT', 'Global News', 'Twitter', 'Facebook', 'Instagram'],
      datasets: [{
        label: 'Post Count',
        data: [0, 0, 0, 0, 0, 0, 0],
        backgroundColor: ['#ff4500', '#22c55e', '#3b82f6', '#f59e0b', '#1DA1F2', '#1877F2', '#E1306C'],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: '#1e2d45' } }
      }
    }
  });
}

// ════════════════════════════════════════════════════════════════
//  ALERTS PAGE
// ════════════════════════════════════════════════════════════════
function initAlertsPage() {
  initAlertTimeline();
}

function initAlertTimeline() {
  const ctx = document.getElementById('alertTimelineChart');
  if (!ctx) return;
  alertTimelineChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        { label: 'Critical', data: [], backgroundColor: 'rgba(239,68,68,0.8)', borderRadius: 4 },
        { label: 'High', data: [], backgroundColor: 'rgba(249,115,22,0.7)', borderRadius: 4 },
        { label: 'Moderate', data: [], backgroundColor: 'rgba(234,179,8,0.7)', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { size: 11 } } } },
      scales: {
        x: { stacked: true, grid: { color: '#1e2d45' } },
        y: { stacked: true, grid: { color: '#1e2d45' }, ticks: { stepSize: 1 } }
      }
    }
  });
}

// Update alert counts from socket
socket.on('stream_update', (data) => {
  if (data.alert_counts) {
    const c = data.alert_counts;
    setVal('cntCritical', c.CRITICAL || 0);
    setVal('cntHigh', c.HIGH || 0);
    setVal('cntModerate', c.MODERATE || 0);
    setVal('cntLow', c.LOW || 0);

    // Update badge
    const badge = document.getElementById('alertBadge');
    if (badge) badge.textContent = (c.CRITICAL||0) + (c.HIGH||0) + (c.MODERATE||0) + (c.LOW||0);
  }
  if (data.alert) {
    // Append to alert log if on alerts page
    if (typeof allAlerts !== 'undefined') {
      allAlerts.unshift(data.alert);
      if (typeof renderAlerts === 'function') renderAlerts();
    }
  }
});

/**
 * Filter the live feed based on the selected platform.
 * @param {string} platform - The platform to show ('all', 'reddit', 'usgs', 'gdelt', 'news')
 */
function filterFeed(platform) {
  currentPlatformFilter = platform;
  
  // Update UI buttons
  const btns = document.querySelectorAll('.filter-btn');
  btns.forEach(b => {
    const btnText = b.textContent.toLowerCase();
    // Check for platform match or 'all'
    if (btnText.includes(platform.toLowerCase()) || (platform === 'all' && btnText === 'all')) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  // Filter existing cards in the DOM
  const cards = document.querySelectorAll('.tweet-card');
  cards.forEach(c => {
    if (platform === 'all' || c.dataset.platform === platform) {
      c.style.display = 'block';
    } else {
      c.style.display = 'none';
    }
  });
}
