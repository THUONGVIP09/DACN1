/* ─────────────────────────────────────────────────────
   TrafficAI — Frontend Application Logic
   Mobile-First with Camera & GPS
───────────────────────────────────────────────────── */

const API = 'http://localhost:8000';
let allReports = [];

// Global state cho camera và location
let capturedImage = null;
let currentGPS = { lat: null, lng: null };
let isGPSAcquired = false;

const EXAMPLES = [
  'Nước ngập đến bánh xe ở đường Nguyễn Hữu Cảnh từ sáng sớm, triều cường dâng cao đột ngột, nhiều xe chết máy.',
  'Kẹt xe cứng ngắc từ vòng xoay Hàng Xanh kéo dài đến ngã tư Điện Biên Phủ, kẹt từ 7h sáng đến giờ chưa thông.',
  'Tai nạn nghiêm trọng ở ngã tư Phú Nhuận, xe tải tông xe máy, 1 người bị thương đang nằm giữa đường rất nguy hiểm.',
  'Cây to đổ ngang đường Nguyễn Trãi sau cơn mưa lớn, chắn hết lòng đường, xe cộ không qua lại được.',
  'Lô cốt thi công đường Lê Lợi rào chắn chiếm hết 2/3 lòng đường mà không có đèn cảnh báo ban đêm, nguy hiểm quá.',
];

// ── Tab switching ────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(`tab-${tab}`).classList.add('active');
  document.getElementById(`nav-${tab}`).classList.add('active');

  if (tab === 'dashboard') loadDashboard();
}

// ── Fill example text ────────────────────────────────
function fillExample(idx) {
  const ta = document.getElementById('report-text');
  ta.value = EXAMPLES[idx];
  updateCharCount();
  ta.focus();
}

// ── Character count ──────────────────────────────────
function updateCharCount() {
  const val = document.getElementById('report-text').value;
  document.getElementById('char-count').textContent = val.length;
}
document.getElementById('report-text').addEventListener('input', updateCharCount);

// ── Camera Handling ─────────────────────────────────
function handleImageCapture(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    showToast('Vui lòng chọn file ảnh hợp lệ.', 'error');
    return;
  }
  
  // Validate file size (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    showToast('Ảnh quá lớn. Vui lòng chọn ảnh dưới 10MB.', 'error');
    return;
  }
  
  capturedImage = file;
  
  // Show preview
  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = document.getElementById('camera-preview');
    preview.innerHTML = `<img src="${e.target.result}" class="preview-image" alt="Preview" />`;
    document.getElementById('camera-actions').style.display = 'flex';
    showToast('Đã chụp ảnh. AI sẽ phân tích khi gửi.', 'success');
  };
  reader.readAsDataURL(file);
}

function retakePhoto() {
  capturedImage = null;
  const preview = document.getElementById('camera-preview');
  preview.innerHTML = `
    <div class="camera-placeholder" onclick="document.getElementById('camera-input').click()">
      <div class="camera-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
      </div>
      <p>Chạm để chụp ảnh</p>
      <span class="camera-hint">Hoặc chọn từ thư viện</span>
    </div>
  `;
  document.getElementById('camera-actions').style.display = 'none';
  document.getElementById('camera-input').value = '';
}

// ── GPS Location Handling ───────────────────────────
function getCurrentLocation() {
  const btn = document.getElementById('btn-gps');
  const text = document.getElementById('gps-text');
  const status = document.getElementById('location-status');
  
  if (!navigator.geolocation) {
    showToast('Trình duyệt không hỗ trợ GPS. Vui lòng nhập thủ công.', 'error');
    showManualLocation();
    return;
  }
  
  btn.disabled = true;
  text.textContent = 'Đang lấy vị trí...';
  status.innerHTML = '<span class="loading-dots">Đang định vị</span>';
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      currentGPS.lat = position.coords.latitude;
      currentGPS.lng = position.coords.longitude;
      isGPSAcquired = true;
      
      btn.disabled = false;
      text.textContent = '📍 Đã lấy vị trí';
      btn.classList.add('gps-active');
      status.innerHTML = `<span class="gps-success">✓ ${currentGPS.lat.toFixed(4)}, ${currentGPS.lng.toFixed(4)}</span>`;
      
      showToast('Đã lấy vị trí GPS thành công!', 'success');
    },
    (error) => {
      btn.disabled = false;
      text.textContent = 'Lấy vị trí thất bại';
      status.innerHTML = '<span class="gps-error">✗ ' + getGPSErrorMessage(error) + '</span>';
      
      showToast('Không thể lấy GPS. Vui lòng nhập thủ công.', 'error');
      showManualLocation();
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000
    }
  );
}

function getGPSErrorMessage(error) {
  switch(error.code) {
    case error.PERMISSION_DENIED:
      return 'Người dùng từ chối cấp quyền';
    case error.POSITION_UNAVAILABLE:
      return 'Không thể xác định vị trí';
    case error.TIMEOUT:
      return 'Hết thời gian chờ';
    default:
      return 'Lỗi không xác định';
  }
}

function showManualLocation() {
  document.getElementById('location-manual').style.display = 'block';
}

function getLocationForSubmit() {
  // Ưu tiên GPS, fallback sang text input
  if (isGPSAcquired && currentGPS.lat && currentGPS.lng) {
    return { lat: currentGPS.lat, lng: currentGPS.lng };
  }
  
  const manualLoc = document.getElementById('location-text')?.value;
  // Nếu có manual location text, sẽ được xử lý ở backend (NER extraction)
  return { lat: null, lng: null };
}

// ── Submit Report with Image (Mobile Optimized) ─────
async function submitReportWithImage() {
  const text = document.getElementById('report-text').value.trim();
  
  // Validation
  if (!text) { 
    showToast('Vui lòng nhập nội dung phản ánh.', 'error'); 
    return; 
  }
  
  if (!capturedImage) {
    showToast('Vui lòng chụp ảnh sự cố.', 'error');
    return;
  }

  const btn = document.getElementById('submit-btn');
  const label = document.getElementById('btn-label');
  btn.disabled = true;
  label.textContent = 'Đang phân tích AI...';

  try {
    // Build FormData cho multipart upload
    const formData = new FormData();
    formData.append('text', text);
    formData.append('image', capturedImage);
    
    const loc = getLocationForSubmit();
    if (loc.lat !== null) {
      formData.append('latitude', loc.lat);
      formData.append('longitude', loc.lng);
    }

    const res = await fetch(`${API}/reports/with-image`, {
      method: 'POST',
      body: formData
      // Không cần Content-Type header, browser sẽ tự đặt với boundary
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    
    const data = await res.json();
    renderResultWithImage(data);
    showToast('Phản ánh đã được gửi và phân tích thành công!', 'success');
    
    // Reset form
    resetForm();
    loadStats();
    
  } catch (err) {
    showToast(`Lỗi: ${err.message}`, 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    label.textContent = 'Gửi phản ánh & Phân tích AI';
  }
}

function resetForm() {
  document.getElementById('report-text').value = '';
  updateCharCount();
  retakePhoto();
  
  // Reset GPS
  currentGPS = { lat: null, lng: null };
  isGPSAcquired = false;
  const btn = document.getElementById('btn-gps');
  const text = document.getElementById('gps-text');
  btn.classList.remove('gps-active');
  text.textContent = 'Lấy vị trí tự động';
  document.getElementById('location-status').innerHTML = '';
  document.getElementById('location-manual').style.display = 'none';
  document.getElementById('location-text').value = '';
}

// ── Legacy Submit (Text-only fallback) ────────────────
async function submitReport() {
  const text = document.getElementById('report-text').value.trim();
  if (!text) { showToast('Vui lòng nhập nội dung phản ánh.', 'error'); return; }

  const btn = document.getElementById('submit-btn');
  const label = document.getElementById('btn-label');
  btn.disabled = true;
  label.textContent = 'Đang phân tích...';

  try {
    const res = await fetch(`${API}/reports/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderResult(data);
    showToast('Phản ánh đã được gửi thành công!', 'success');
    loadStats();
  } catch (err) {
    showToast(`Lỗi kết nối API: ${err.message}`, 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    label.textContent = 'Gửi phản ánh & Phân tích AI';
  }
}

// ── Render Result (Legacy - text only) ───────────────
function renderResult(data) {
  const card = document.getElementById('result-card');
  card.style.display = 'flex';
  card.style.animation = 'none';
  void card.offsetWidth; // reflow
  card.style.animation = 'fadeIn 0.4s ease';

  // Status badge
  const badge = document.getElementById('result-badge');
  const statusText = document.getElementById('result-status-text');
  const isApproved = data.status === 'Auto-Approved';
  badge.className = `result-status-badge ${isApproved ? '' : 'pending'}`;
  statusText.textContent = isApproved ? '✓ Auto-Approved' : '⏳ Chờ duyệt thủ công';

  document.getElementById('result-rawtext').textContent = data.raw_text;
  document.getElementById('result-id').textContent = `#RPT-${String(data.id).padStart(5, '0')}`;
  
  // Hide image section for text-only
  document.getElementById('result-image-section').style.display = 'none';
  document.getElementById('vision-section').style.display = 'none';

  // Categories
  const catEl = document.getElementById('result-categories');
  catEl.innerHTML = '';
  if (data.predicted_categories) {
    data.predicted_categories.split(',').forEach((c, i) => {
      const tag = document.createElement('span');
      tag.className = 'tag tag-category';
      tag.style.animationDelay = `${i * 0.05}s`;
      tag.textContent = c.trim();
      catEl.appendChild(tag);
    });
  } else {
    catEl.innerHTML = '<span class="tag tag-empty">Không xác định</span>';
  }

  // Locations
  const locEl = document.getElementById('result-locations');
  locEl.innerHTML = '';
  if (data.extracted_locations) {
    data.extracted_locations.split('|').forEach((l, i) => {
      const tag = document.createElement('span');
      tag.className = 'tag tag-location';
      tag.style.animationDelay = `${i * 0.05}s`;
      tag.textContent = l.trim();
      locEl.appendChild(tag);
    });
  } else {
    locEl.innerHTML = '<span class="tag tag-empty">Chưa trích xuất được</span>';
  }

  // Times
  const timeEl = document.getElementById('result-times');
  timeEl.innerHTML = '';
  if (data.extracted_times) {
    data.extracted_times.split('|').forEach((t, i) => {
      const tag = document.createElement('span');
      tag.className = 'tag tag-time';
      tag.style.animationDelay = `${i * 0.05}s`;
      tag.textContent = t.trim();
      timeEl.appendChild(tag);
    });
  } else {
    timeEl.innerHTML = '<span class="tag tag-empty">Không tìm thấy</span>';
  }
  
  // Confidence (if available)
  const confEl = document.getElementById('result-confidence');
  if (data.final_confidence !== null && data.final_confidence !== undefined) {
    confEl.textContent = `${(data.final_confidence * 100).toFixed(1)}%`;
  } else {
    confEl.textContent = 'N/A';
  }
}

// ── Render Result with Image (Full Analysis) ─────────
function renderResultWithImage(data) {
  // First call base render
  renderResult(data);
  
  // Then add image and vision details
  const card = document.getElementById('result-card');
  
  // Show image
  if (data.image_path) {
    const imgSection = document.getElementById('result-image-section');
    const img = document.getElementById('result-image');
    img.src = `${API}/uploads/${data.image_path.split(/[\/\\]/).pop()}`;
    imgSection.style.display = 'block';
  }
  
  // Show vision labels
  if (data.vision_labels) {
    try {
      const labels = JSON.parse(data.vision_labels);
      const visionSection = document.getElementById('vision-section');
      const labelsContainer = document.getElementById('vision-labels');
      
      labelsContainer.innerHTML = labels.slice(0, 10).map(label => 
        `<span class="vision-tag">${label}</span>`
      ).join('');
      
      visionSection.style.display = 'block';
    } catch (e) {
      console.error('Error parsing vision labels:', e);
    }
  }
  
  // Show confidence with color coding
  const confDisplay = document.getElementById('confidence-display');
  if (data.final_confidence !== null && data.final_confidence !== undefined) {
    const score = data.final_confidence;
    let colorClass = 'low';
    if (score >= 0.85) colorClass = 'high';
    else if (score >= 0.6) colorClass = 'medium';
    
    confDisplay.innerHTML = `
      <div class="confidence-badge ${colorClass}">
        <span class="conf-value">${(score * 100).toFixed(0)}%</span>
        <span class="conf-label">Confidence</span>
      </div>
    `;
  }
}

// ── Load Stats ───────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch(`${API}/reports/?limit=1000`);
    const data = await res.json();
    const total = data.length;
    const approved = data.filter(r => r.status === 'Auto-Approved').length;
    const pending = total - approved;
    const rate = total > 0 ? Math.round((approved / total) * 100) : 0;

    animateNumber('stat-total', total);
    animateNumber('stat-approved', approved);
    animateNumber('stat-pending', pending);
    document.getElementById('stat-rate').textContent = `${rate}%`;
  } catch (e) { /* silence */ }
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  const start = parseInt(el.textContent) || 0;
  const duration = 600;
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / duration, 1);
    el.textContent = Math.round(start + (target - start) * easeOut(t));
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

// ── Load Dashboard ───────────────────────────────────
async function loadDashboard() {
  const list = document.getElementById('reports-list');
  list.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Đang tải dữ liệu...</p></div>';

  try {
    const res = await fetch(`${API}/reports/?limit=200`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allReports = await res.json();
    renderReports(allReports);
  } catch (err) {
    list.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <p>Không thể kết nối API. Kiểm tra server đang chạy tại <strong>localhost:8000</strong></p>
      </div>`;
  }
}

function renderReports(reports) {
  const list = document.getElementById('reports-list');
  if (!reports.length) {
    list.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <p>Chưa có phản ánh nào. Hãy gửi phản ánh đầu tiên!</p>
      </div>`;
    return;
  }

  list.innerHTML = reports.map((r, i) => {
    const isApproved = r.status === 'Auto-Approved';
    const cats = r.predicted_categories
      ? r.predicted_categories.split(',').map(c => `<span class="tag tag-category">${c.trim()}</span>`).join('')
      : '<span class="tag tag-empty">Chưa phân loại</span>';
    const locs = r.extracted_locations
      ? r.extracted_locations.split('|').map(l => `<span class="tag tag-location">📍 ${l.trim()}</span>`).join('')
      : '';
    const times = r.extracted_times
      ? r.extracted_times.split('|').map(t => `<span class="tag tag-time">⏰ ${t.trim()}</span>`).join('')
      : '';

    const dateStr = new Date(r.created_at + 'Z').toLocaleString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });

    return `
    <div class="report-item" style="animation-delay:${i * 0.04}s">
      <div class="report-id">#${String(r.id).padStart(3, '0')}</div>
      <div class="report-body">
        <p class="report-text">${escapeHtml(r.raw_text)}</p>
        <div class="report-meta">
          ${cats}${locs}${times}
        </div>
      </div>
      <div class="report-right">
        <span class="status-badge ${isApproved ? 'badge-approved' : 'badge-pending'}">
          <span class="badge-dot"></span>
          ${isApproved ? 'Auto-Approved' : 'Chờ duyệt'}
        </span>
        <span class="report-time">${dateStr}</span>
      </div>
    </div>`;
  }).join('');
}

// ── Filter Reports ───────────────────────────────────
function filterReports() {
  const query = document.getElementById('search-input').value.toLowerCase();
  const status = document.getElementById('filter-status').value;
  const category = document.getElementById('filter-category').value;

  const filtered = allReports.filter(r => {
    const matchText = !query || r.raw_text.toLowerCase().includes(query);
    const matchStatus = !status || r.status === status;
    const matchCat = !category || (r.predicted_categories && r.predicted_categories.includes(category));
    return matchText && matchStatus && matchCat;
  });
  renderReports(filtered);
}

// ── Toast ────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => { toast.className = 'toast'; }, 3500);
}

// ── Utilities ────────────────────────────────────────
function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ─────────────────────────────────────────────
loadStats();
