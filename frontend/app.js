/* ─────────────────────────────────────────────────────
   TrafficAI — Frontend Application Logic (Unified)
   Supports 3 Roles: Reporter, Moderator, Resolver/Admin
   ───────────────────────────────────────────────────── */

const API = window.location.origin;

// Global State
let capturedImage = null;
let currentGPS = { lat: null, lng: null };
let isGPSAcquired = false;

let currentUser = null; // { user_id, username, role, full_name, department, token }
let reporterInfo = { name: '', phone: '' };
let currentLoginRoleTarget = ''; // 'moderator' hoặc 'admin'

const EXAMPLES = [
  'Nước ngập đến bánh xe ở đường Nguyễn Hữu Cảnh từ sáng sớm, triều cường dâng cao đột ngột, nhiều xe chết máy.',
  'Kẹt xe cứng ngắc từ vòng xoay Hàng Xanh kéo dài đến ngã tư Điện Biên Phủ, kẹt từ 7h sáng đến giờ chưa thông.',
  'Tai nạn nghiêm trọng ở ngã tư Phú Nhuận, xe tải tông xe máy, 1 người bị thương đang nằm giữa đường rất nguy hiểm.',
  'Cây to đổ ngang đường Nguyễn Trãi sau cơn mưa lớn, chắn hết lòng đường, xe cộ không qua lại được.',
  'Lô cốt thi công đường Lê Lợi rào chắn chiếm hết 2/3 lòng đường mà không có đèn cảnh báo ban đêm, nguy hiểm quá.',
];

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  // Check login state in local storage
  const savedUser = localStorage.getItem('trafficai_user');
  const savedReporter = localStorage.getItem('trafficai_reporter');
  
  if (savedUser) {
    currentUser = JSON.parse(savedUser);
    enterCandoPortal(currentUser);
  } else if (savedReporter) {
    reporterInfo = JSON.parse(savedReporter);
    enterReporterPortal();
  } else {
    // Show Portal Selection gateway by default
    showGateway();
  }
});

// ── Gateway/Portal Selection Navigation ────────────────
function showGateway() {
  document.getElementById('portal-gateway').style.display = 'block';
  document.getElementById('main-header').style.display = 'none';
  document.getElementById('main-content').style.display = 'none';
  
  // Hide all view sections
  document.getElementById('portal-reporter-view').style.display = 'none';
  document.getElementById('portal-moderator-view').style.display = 'none';
  document.getElementById('portal-resolver-view').style.display = 'none';
}

function chooseRole(role) {
  if (role === 'reporter') {
    const savedReporter = localStorage.getItem('trafficai_reporter');
    if (savedReporter) {
      reporterInfo = JSON.parse(savedReporter);
      enterReporterPortal();
    } else {
      // Show identity register modal
      document.getElementById('reporter-modal').style.display = 'grid';
    }
  }
}

function enterReporterPortal() {
  document.getElementById('portal-gateway').style.display = 'none';
  document.getElementById('main-header').style.display = 'block';
  document.getElementById('main-content').style.display = 'block';
  
  // Update header labels
  document.getElementById('header-portal-title').textContent = 'TrafficAI – Người dân';
  document.getElementById('header-user-info').textContent = `Chào mừng công dân: ${reporterInfo.name} (${reporterInfo.phone})`;
  document.getElementById('reporter-display-name').textContent = `Người gửi: ${reporterInfo.name}`;

  // Show reporter view, hide others
  document.getElementById('portal-reporter-view').style.display = 'block';
  document.getElementById('portal-moderator-view').style.display = 'none';
  document.getElementById('portal-resolver-view').style.display = 'none';
}

function closeReporterModal() {
  document.getElementById('reporter-modal').style.display = 'none';
}

function submitReporterIdentity() {
  const name = document.getElementById('reporter-name').value.trim();
  const phone = document.getElementById('reporter-phone').value.trim();
  
  if (!name || !phone) {
    showToast('Vui lòng điền đầy đủ Họ tên và SĐT.', 'error');
    return;
  }
  
  reporterInfo = { name, phone };
  localStorage.setItem('trafficai_reporter', JSON.stringify(reporterInfo));
  closeReporterModal();
  enterReporterPortal();
  showToast('Đăng ký thông tin liên hệ thành công!', 'success');
}

// ── Officer Authentication (Login) ─────────────────────
function openLogin(role) {
  currentLoginRoleTarget = role;
  const title = role === 'moderator' ? 'Đăng nhập Cán bộ Kiểm duyệt' : 'Đăng nhập Đơn vị Xử lý';
  document.getElementById('login-title').textContent = title;
  document.getElementById('login-modal').style.display = 'grid';
}

function closeLogin() {
  document.getElementById('login-modal').style.display = 'none';
  document.getElementById('login-username').value = '';
  document.getElementById('login-password').value = '';
}

async function submitLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  
  if (!username || !password) {
    showToast('Vui lòng nhập tên đăng nhập và mật khẩu.', 'error');
    return;
  }
  
  try {
    const res = await fetch(`${API}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Đăng nhập không thành công');
    }
    
    const user = await res.json();
    
    // Check if matched the role selected
    if (user.role !== currentLoginRoleTarget) {
      throw new Error(`Tài khoản này thuộc vai trò ${user.role}, không thể dùng cho cổng này.`);
    }
    
    currentUser = user;
    localStorage.setItem('trafficai_user', JSON.stringify(currentUser));
    closeLogin();
    enterCandoPortal(currentUser);
    showToast(`Chào mừng ${user.full_name} đăng nhập thành công!`, 'success');
    
  } catch (err) {
    showToast(err.message, 'error');
    console.error(err);
  }
}

function enterCandoPortal(user) {
  document.getElementById('portal-gateway').style.display = 'none';
  document.getElementById('main-header').style.display = 'block';
  document.getElementById('main-content').style.display = 'block';
  
  document.getElementById('header-portal-title').textContent = user.role === 'moderator' ? 'TrafficAI – Cổng Kiểm Duyệt' : 'TrafficAI – Cổng Xử Lý';
  document.getElementById('header-user-info').textContent = `${user.full_name} (${user.department})`;

  if (user.role === 'moderator') {
    document.getElementById('portal-reporter-view').style.display = 'none';
    document.getElementById('portal-moderator-view').style.display = 'block';
    document.getElementById('portal-resolver-view').style.display = 'none';
    loadModeratorDashboard();
  } else {
    document.getElementById('portal-reporter-view').style.display = 'none';
    document.getElementById('portal-moderator-view').style.display = 'none';
    document.getElementById('portal-resolver-view').style.display = 'block';
    loadResolverDashboard();
  }
}

function logout() {
  localStorage.removeItem('trafficai_user');
  localStorage.removeItem('trafficai_reporter');
  currentUser = null;
  reporterInfo = { name: '', phone: '' };
  
  // Reset form inputs
  resetForm();
  
  showGateway();
  showToast('Đã đăng xuất tài khoản.', 'success');
}

// ── Fill Example Text ────────────────────────────────
function fillExample(idx) {
  const ta = document.getElementById('report-text');
  ta.value = EXAMPLES[idx];
  updateCharCount();
  ta.focus();
}

function updateCharCount() {
  const val = document.getElementById('report-text').value;
  document.getElementById('char-count').textContent = val.length;
}
document.getElementById('report-text').addEventListener('input', updateCharCount);

// ── Camera & Image handling ─────────────────────────
function handleImageCapture(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  if (!file.type.startsWith('image/')) {
    showToast('Vui lòng chọn tệp ảnh hợp lệ.', 'error');
    return;
  }
  
  capturedImage = file;
  
  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = document.getElementById('camera-preview');
    preview.innerHTML = `<img src="${e.target.result}" class="preview-image" alt="Preview" />`;
    document.getElementById('camera-actions').style.display = 'flex';
    showToast('Đã chụp và nạp ảnh sự cố.', 'success');
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

// ── Client-side Image Compression (HTML5 Canvas) ───
function compressImage(file, maxWidth = 1000, maxQuality = 0.8) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        if (width > maxWidth) {
          height = Math.round((height * maxWidth) / width);
          width = maxWidth;
        }

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob((blob) => {
          const compressedFile = new File([blob], file.name.replace(/\.[^/.]+$/, "") + ".jpg", {
            type: 'image/jpeg',
            lastModified: Date.now()
          });
          resolve(compressedFile);
        }, 'image/jpeg', maxQuality);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ── GPS Geolocation ─────────────────────────────────
function getCurrentLocation() {
  const btn = document.getElementById('btn-gps');
  const text = document.getElementById('gps-text');
  const status = document.getElementById('location-status');
  
  if (!navigator.geolocation) {
    showToast('Trình duyệt không hỗ trợ GPS.', 'error');
    return;
  }
  
  btn.disabled = true;
  text.textContent = 'Đang lấy tọa độ vệ tinh...';
  status.innerHTML = '<span class="loading-dots gps-success">Đang dò tìm tọa độ GPS</span>';
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      currentGPS = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      isGPSAcquired = true;
      btn.classList.add('gps-active');
      text.textContent = 'Đã định vị thành công ✔';
      status.innerHTML = `<span class="gps-success">Tọa độ: ${currentGPS.lat.toFixed(5)}, ${currentGPS.lng.toFixed(5)}</span>`;
      showToast('Đã ghi nhận tọa độ GPS thực địa.', 'success');
    },
    (err) => {
      console.error(err);
      btn.disabled = false;
      text.textContent = 'Lấy vị trí tự động';
      status.innerHTML = '<span class="gps-error">Lỗi GPS. Đã mở ô nhập địa chỉ thủ công.</span>';
      document.getElementById('location-manual').style.display = 'block';
      showToast('Định vị GPS thất bại. Vui lòng nhập địa chỉ bên dưới.', 'error');
    },
    { enableHighAccuracy: true, timeout: 8000 }
  );
}

// ── Reporter Submit Report with Image ───────────────
async function submitReportWithImage() {
  const text = document.getElementById('report-text').value.trim();
  
  if (!text) {
    showToast('Vui lòng nhập mô tả sự cố.', 'error');
    return;
  }
  
  if (!capturedImage) {
    showToast('Vui lòng chụp ảnh sự cố hiện trường.', 'error');
    return;
  }
  
  const btn = document.getElementById('submit-btn');
  const label = document.getElementById('btn-label');
  btn.disabled = true;
  
  try {
    label.textContent = 'Đang tối ưu dung lượng ảnh (4G)...';
    const compressedImage = await compressImage(capturedImage);
    
    label.textContent = 'Đang gửi & Chờ AI phân tích...';
    
    const formData = new FormData();
    formData.append('text', text);
    formData.append('image', compressedImage);
    formData.append('reporter_name', reporterInfo.name);
    formData.append('reporter_phone', reporterInfo.phone);
    
    if (isGPSAcquired && currentGPS.lat !== null) {
      formData.append('latitude', currentGPS.lat);
      formData.append('longitude', currentGPS.lng);
    } else {
      const manualLoc = document.getElementById('location-text')?.value.trim();
      if (manualLoc) {
        formData.append('text', `${text} tại ${manualLoc}`); // Gộp địa chỉ vào text để NER xử lý
      }
    }
    
    const res = await fetch(`${API}/reports/with-image`, {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi gửi phản ánh');
    }
    
    const data = await res.json();
    renderResultWithImage(data);
    showToast('Gửi phản ánh thành công! Đã tự động phân tích AI.', 'success');
    
    // Reset Form
    resetForm();
    
  } catch (err) {
    showToast(err.message, 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    label.textContent = 'Gửi phản ánh & Phân tích AI';
  }
}

function renderResultWithImage(report) {
  // Ẩn form gửi phản ánh ban đầu
  document.getElementById('submit-card').style.display = 'none';
  
  // Hiển thị thẻ thông báo thành công tinh tế
  const card = document.getElementById('result-card');
  card.style.display = 'flex';
  
  // Hiển thị Mã phản ánh số định dạng đẹp
  document.getElementById('result-id').textContent = `#RPT-${report.id.toString().padStart(5, '0')}`;
  
  // Cuộn mượt mà đến thẻ kết quả thành công
  card.scrollIntoView({ behavior: 'smooth' });
}

function resetReporterForm() {
  // Ẩn thẻ thông báo thành công
  document.getElementById('result-card').style.display = 'none';
  
  // Hiển thị lại form nhập phản ánh ban đầu
  document.getElementById('submit-card').style.display = 'block';
  
  // Reset toàn bộ dữ liệu form đầu vào
  resetForm();
  
  // Cuộn mượt mà về đầu form phản ánh
  document.getElementById('submit-card').scrollIntoView({ behavior: 'smooth' });
}

function resetForm() {
  document.getElementById('report-text').value = '';
  updateCharCount();
  retakePhoto();
  
  // Reset GPS
  currentGPS = { lat: null, lng: null };
  isGPSAcquired = false;
  const btn = document.getElementById('btn-gps');
  btn.disabled = false;
  btn.classList.remove('gps-active');
  document.getElementById('gps-text').textContent = 'Lấy vị trí tự động bằng GPS';
  document.getElementById('location-status').innerHTML = '';
  document.getElementById('location-text').value = '';
  document.getElementById('location-manual').style.display = 'none';
}

// ── Moderator Dashboard Logic ───────────────────────
async function loadModeratorDashboard() {
  const container = document.getElementById('mod-reports-list');
  container.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Đang đồng bộ dữ liệu...</p></div>';
  
  const statusFilter = document.getElementById('mod-filter-status').value;
  const searchVal = document.getElementById('mod-search-input').value.trim().toLowerCase();
  
  try {
    let url = `${API}/reports/?limit=50`;
    if (statusFilter) url += `&status=${statusFilter}`;
    
    const res = await fetch(url);
    if (!res.ok) throw new Error('Lỗi đồng bộ danh sách duyệt');
    
    let reports = await res.json();
    
    // Filter search locally
    if (searchVal) {
      reports = reports.filter(r => 
        r.raw_text.toLowerCase().includes(searchVal) || 
        (r.reporter_name && r.reporter_name.toLowerCase().includes(searchVal)) ||
        (r.extracted_locations && r.extracted_locations.toLowerCase().includes(searchVal))
      );
    }
    
    // Update stats
    updateModStats(reports, statusFilter);
    
    if (reports.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <p>Không có phản ánh nào khớp với bộ lọc kiểm duyệt.</p>
        </div>
      `;
      return;
    }
    
    container.innerHTML = '';
    reports.forEach(r => {
      const filename = r.image_path ? r.image_path.split('/').pop() : null;
      const imageUrl = filename ? `${API}/uploads/${filename}` : '';
      const reporterLabel = (r.reporter_name && r.reporter_phone) ? `<b>Người gửi:</b> ${r.reporter_name} (${r.reporter_phone})` : '<b>Người gửi:</b> <i>Ẩn danh (Vô danh)</i>';
      
      let badgeClass = 'badge-pending';
      let statusWord = 'Đang Chờ Duyệt';
      if (r.status === 'Auto-Approved') { badgeClass = 'badge-approved'; statusWord = 'Tự Động Duyệt'; }
      else if (r.status === 'Approved_By_Mod') { badgeClass = 'badge-approved'; statusWord = 'Cán bộ đã duyệt'; }
      else if (r.status === 'Rejected_By_Mod') { badgeClass = 'badge-pending'; statusWord = 'Cán bộ từ chối'; }
      else if (r.status === 'Auto-Dispatched') { badgeClass = 'badge-approved'; statusWord = 'Tự động Điều phối (AI)'; }
      else if (r.status === 'Assigned_Manually') { badgeClass = 'badge-approved'; statusWord = 'Cán bộ điều phối tay'; }
      else if (r.status === 'In_Progress') { badgeClass = 'badge-approved'; statusWord = 'Đang sửa chữa'; }
      else if (r.status === 'Resolved') { badgeClass = 'badge-approved'; statusWord = 'Sửa chữa thành công'; }
      
      const parsedLabels = r.vision_labels ? JSON.parse(r.vision_labels) : [];
      const visionLabelsHTML = parsedLabels.map(l => `<span class="vision-tag">${l}</span>`).join('');
      
      let actionButtons = '';
      const primaryCat = r.predicted_categories ? r.predicted_categories.split(', ')[0] : 'Sự cố hạ tầng & Đèn tín hiệu';
      
      if (r.status === 'Pending_Manual_Review' || r.status === 'Pending_Quick_Review') {
        actionButtons = `
          <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:12px;">
            <button class="btn-primary" onclick="moderatorDecision(${r.id}, 'approve')" style="padding:8px 12px; font-size:11px; min-height:32px; background:linear-gradient(135deg, #059669, #047857); box-shadow:none;">✓ Duyệt lưu trữ</button>
            <button class="btn-primary" onclick="openDispatchModal(${r.id}, '${primaryCat}', ${r.latitude || 'null'}, ${r.longitude || 'null'})" style="padding:8px 12px; font-size:11px; min-height:32px; background:linear-gradient(135deg, var(--accent), #1d4ed8); box-shadow:none;">⚙ Bàn giao việc</button>
            <button class="btn-primary" onclick="moderatorDecision(${r.id}, 'reject')" style="padding:8px 12px; font-size:11px; min-height:32px; background:linear-gradient(135deg, #dc2626, #b91c1c); box-shadow:none;">&times; Từ chối</button>
          </div>
        `;
      } else if (r.status === 'Auto-Approved' || r.status === 'Approved_By_Mod') {
        actionButtons = `
          <div style="display:flex; gap:8px; margin-top:12px;">
            <button class="btn-primary" onclick="openDispatchModal(${r.id}, '${primaryCat}', ${r.latitude || 'null'}, ${r.longitude || 'null'})" style="padding:8px 12px; font-size:11px; min-height:32px; background:linear-gradient(135deg, var(--accent), #1d4ed8); box-shadow:none;">⚙ Bàn giao việc</button>
          </div>
        `;
      }
      
      let assignmentInfoHTML = '';
      if (r.assigned_executor_id) {
        assignmentInfoHTML = `
          <div style="margin-top:10px; background:rgba(37,99,235,0.04); border:1px dashed rgba(37,99,235,0.2); border-radius:6px; padding:10px 12px; font-size:12px; color:var(--text-primary);">
            <p style="margin-bottom:4px; font-weight:700; color:var(--accent); display:flex; align-items:center; gap:4px;">👷 ĐƠN VỊ THỰC ĐỊA ĐANG PHỤ TRÁCH:</p>
            <p style="line-height:1.4;">• <b>ID Đơn vị:</b> Đội thi công #${r.assigned_executor_id}<br>• <b>Chỉ thị điều phối:</b> <i>${r.dispatch_notes || 'Không có ghi chú thêm.'}</i></p>
          </div>
        `;
      }
      
      container.innerHTML += `
        <div class="report-item">
          <div class="report-id">#${r.id}</div>
          <div class="report-body">
            <p class="report-text">${r.raw_text}</p>
            <p style="font-size:12px; color:var(--text-muted); margin-bottom:8px;">${reporterLabel}</p>
            <div class="report-meta">
              <span class="tag tag-category">${r.predicted_categories || 'Không rõ sự cố'}</span>
              <span class="tag tag-location">${r.extracted_locations || 'Không rõ địa điểm'}</span>
            </div>
            
            ${imageUrl ? `
              <div style="margin-top:10px; display:flex; gap:12px; align-items:start;">
                <img src="${imageUrl}" style="width:80px; height:80px; object-fit:cover; border-radius:8px; border:1px solid #e2e8f0;" onclick="window.open('${imageUrl}')" />
                <div>
                  <p style="font-size:11px; font-weight:700; color:var(--text-muted);">PHÂN TÍCH THỊ GIÁC AI:</p>
                  <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">${visionLabelsHTML || '<i>Trống</i>'}</div>
                </div>
              </div>
            ` : ''}
            
            ${assignmentInfoHTML}
            ${actionButtons}
          </div>
          <div class="report-right">
            <span class="status-badge ${badgeClass}"><span class="badge-dot"></span>${statusWord}</span>
            <span class="report-time">Độ tin cậy: <b>${((r.final_confidence || 0)*100).toFixed(0)}%</b></span>
          </div>
        </div>
      `;
    });
    
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p>Không thể tải dữ liệu: ${err.message}</p></div>`;
  }
}

async function moderatorDecision(id, action) {
  try {
    const res = await fetch(`${API}/api/moderator/reports/${id}/${action}`, {
      method: 'POST'
    });
    
    if (!res.ok) throw new Error(`Lỗi cập nhật ${action}`);
    
    showToast(`Đã duyệt lưu trữ báo cáo #${id} thành công!`, 'success');
    loadModeratorDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function updateModStats(reports, statusFilter) {
  document.getElementById('mod-stat-total').textContent = reports.length;
  
  const pending = reports.filter(r => r.status === 'Pending_Manual_Review' || r.status === 'Pending_Quick_Review').length;
  const approved = reports.filter(r => r.status === 'Approved_By_Mod' || r.status === 'Auto-Approved' || r.status === 'Auto-Dispatched' || r.status === 'Assigned_Manually' || r.status === 'In_Progress' || r.status === 'Resolved').length;
  const rejected = reports.filter(r => r.status === 'Rejected_By_Mod').length;
  
  document.getElementById('mod-stat-pending').textContent = pending;
  document.getElementById('mod-stat-approved').textContent = approved;
  document.getElementById('mod-stat-rejected').textContent = rejected;
}

// ── Resolver Dashboard Logic ────────────────────────
async function loadResolverDashboard() {
  const container = document.getElementById('res-reports-list');
  container.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Đang tải danh sách sự cố...</p></div>';
  
  const filterVal = document.getElementById('res-filter-status').value;
  const searchVal = document.getElementById('res-search-input').value.trim().toLowerCase();
  
  try {
    const res = await fetch(`${API}/reports/?limit=50&status=${filterVal}`);
    if (!res.ok) throw new Error('Không thể kết nối máy chủ');
    
    let reports = await res.json();
    
    if (searchVal) {
      reports = reports.filter(r => 
        r.raw_text.toLowerCase().includes(searchVal) || 
        (r.extracted_locations && r.extracted_locations.toLowerCase().includes(searchVal))
      );
    }
    
    if (reports.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <p>Không tìm thấy sự cố nào cần xử lý phù hợp.</p>
        </div>
      `;
      return;
    }
    
    container.innerHTML = '';
    reports.forEach(r => {
      const filename = r.image_path ? r.image_path.split('/').pop() : null;
      const imageUrl = filename ? `${API}/uploads/${filename}` : '';
      
      let badgeClass = 'badge-pending';
      let statusWord = 'Chờ xử lý';
      if (r.status === 'In_Progress') { badgeClass = 'badge-pending'; statusWord = 'Đang thi công 🚧'; }
      else if (r.status === 'Resolved') { badgeClass = 'badge-approved'; statusWord = 'Đã sửa xong ✔'; }
      
      let actionForm = '';
      if (r.status !== 'Resolved') {
        actionForm = `
          <div style="margin-top:12px; padding-top:12px; border-top:1px dashed #e2e8f0;">
            <div class="form-group" style="margin-bottom:8px;">
              <input type="text" id="res-note-${r.id}" class="form-input" style="min-height:36px; font-size:12px; padding:6px 12px;" placeholder="Nhập ghi chú thi công thực tế (Ví dụ: Đã vá ổ gà đường Lê Thiện Trị)..." value="${r.resolver_notes || ''}" />
            </div>
            <div style="display:flex; gap:8px;">
              ${r.status !== 'In_Progress' ? `
                <button class="btn-gps" onclick="resolverAction(${r.id}, 'In_Progress')" style="min-height:36px; padding:6px 12px; font-size:12px; border-color:#d97706; color:#d97706;">🚧 Bắt đầu sửa chữa</button>
              ` : ''}
              <button class="btn-primary" onclick="resolverAction(${r.id}, 'Resolved')" style="min-height:36px; padding:6px 12px; font-size:12px; background:linear-gradient(135deg, #059669, #047857); box-shadow:none;">✔ Báo cáo Đã sửa xong</button>
            </div>
          </div>
        `;
      } else {
        actionForm = `
          <div style="margin-top:8px; padding:8px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; font-size:12px; color:#15803d;">
            <b>Ghi chú hoàn thành:</b> ${r.resolver_notes || 'Không có ghi chú'}
          </div>
        `;
      }
      
      container.innerHTML += `
        <div class="report-item">
          <div class="report-id">#${r.id}</div>
          <div class="report-body">
            <p class="report-text" style="font-weight:600;">${r.raw_text}</p>
            <div class="report-meta" style="margin-top:6px;">
              <span class="tag tag-location" style="background:#f1f5f9; color:#475569; border-color:#e2e8f0;">📍 Địa điểm: ${r.extracted_locations || 'Không rõ'}</span>
            </div>
            
            ${imageUrl ? `
              <img src="${imageUrl}" style="width:100%; max-height:160px; object-fit:cover; border-radius:8px; margin-top:10px; border:1px solid #e2e8f0;" onclick="window.open('${imageUrl}')" />
            ` : ''}
            
            ${actionForm}
          </div>
          <div class="report-right">
            <span class="status-badge ${badgeClass}"><span class="badge-dot"></span>${statusWord}</span>
            <span class="report-time">Mã: RPT-${r.id}</span>
          </div>
        </div>
      `;
    });
    
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p>Lỗi đồng bộ dữ liệu: ${err.message}</p></div>`;
  }
}

async function resolverAction(id, targetStatus) {
  const noteVal = document.getElementById(`res-note-${id}`).value.trim();
  
  try {
    const formData = new FormData();
    formData.append('status', targetStatus);
    if (noteVal) formData.append('notes', noteVal);
    
    const res = await fetch(`${API}/api/resolver/reports/${id}/status`, {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) throw new Error('Cập nhật trạng thái thi công thất bại');
    
    showToast(`Đã cập nhật sự cố #${id} sang trạng thái thành công!`, 'success');
    loadResolverDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── Moderator Dispatch & Executor Management (Premium Giai đoạn 4) ──
async function loadExecutorsList() {
  try {
    const res = await fetch(`${API}/api/moderator/executors`);
    if (!res.ok) throw new Error('Không thể tải danh sách đơn vị');
    const executors = await res.json();
    
    const tbody = document.getElementById('moderator-executors-tbody');
    tbody.innerHTML = '';
    
    if (executors.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:15px; color:var(--text-muted);">Chưa có đơn vị thực địa nào đăng ký</td></tr>';
      return;
    }
    
    executors.forEach(exec => {
      tbody.innerHTML += `
        <tr style="border-bottom:1px solid var(--slate-100); color:var(--text-primary);">
          <td style="padding:12px 10px; font-weight:bold;">${exec.username}</td>
          <td style="padding:12px 10px;">${exec.full_name}</td>
          <td style="padding:12px 10px;"><span class="tag tag-category">${exec.specialty}</span></td>
          <td style="padding:12px 10px; font-family:monospace;">${exec.base_latitude?.toFixed(4)}, ${exec.base_longitude?.toFixed(4)}</td>
          <td style="padding:12px 10px; text-align:center;">
            <button class="btn-gps" style="border-color:#fca5a5; color:#b91c1c; background:#fef2f2; padding:4px 8px; font-size:0.75rem; cursor:pointer;" onclick="deleteExecutor(${exec.id})">Thu hồi</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error(err);
  }
}

function openCreateExecutorModal() {
  document.getElementById('create-executor-modal').style.display = 'grid';
}

function closeCreateExecutorModal() {
  document.getElementById('create-executor-modal').style.display = 'none';
  document.getElementById('new-exec-username').value = '';
  document.getElementById('new-exec-password').value = '';
  document.getElementById('new-exec-fullname').value = '';
  document.getElementById('new-exec-lat').value = '';
  document.getElementById('new-exec-lng').value = '';
}

async function submitCreateExecutor() {
  const username = document.getElementById('new-exec-username').value.trim();
  const password = document.getElementById('new-exec-password').value;
  const full_name = document.getElementById('new-exec-fullname').value.trim();
  const specialty = document.getElementById('new-exec-specialty').value;
  const lat = parseFloat(document.getElementById('new-exec-lat').value);
  const lng = parseFloat(document.getElementById('new-exec-lng').value);
  
  if (!username || !password || !full_name || isNaN(lat) || isNaN(lng)) {
    showToast('Vui lòng nhập đầy đủ tất cả các trường dữ liệu.', 'error');
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('full_name', full_name);
    formData.append('specialty', specialty);
    formData.append('base_latitude', lat);
    formData.append('base_longitude', lng);
    
    const res = await fetch(`${API}/api/moderator/executors/create`, {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Không thể tạo tài khoản');
    }
    
    showToast('Đã tạo tài khoản Đơn vị Thực địa thành công!', 'success');
    closeCreateExecutorModal();
    loadExecutorsList();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteExecutor(id) {
  if (!confirm('Bạn có chắc chắn muốn thu hồi tài khoản này không? Đơn vị này sẽ không thể làm việc nữa.')) return;
  try {
    const res = await fetch(`${API}/api/moderator/executors/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Không thể thu hồi tài khoản');
    showToast('Đã thu hồi tài khoản đơn vị thành công.', 'success');
    loadExecutorsList();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function openDispatchModal(reportId, primaryCategory, reportLat, reportLng) {
  document.getElementById('dispatch-report-id').value = reportId;
  document.getElementById('dispatch-notes-input').value = '';
  
  const select = document.getElementById('dispatch-executor-select');
  select.innerHTML = '<option>Đang tải danh sách đơn vị thi công...</option>';
  
  try {
    const res = await fetch(`${API}/api/moderator/executors?specialty=${encodeURIComponent(primaryCategory)}`);
    if (!res.ok) throw new Error('Không thể lấy danh sách Executor');
    const executors = await res.json();
    
    if (executors.length === 0) {
      select.innerHTML = '<option value="">Không có đơn vị nào chuyên môn phù hợp!</option>';
      document.getElementById('dispatch-modal').style.display = 'grid';
      return;
    }
    
    executors.forEach(exec => {
      if (reportLat && reportLng && exec.base_latitude && exec.base_longitude) {
        exec.distance = calculateHaversineDistance(reportLat, reportLng, exec.base_latitude, exec.base_longitude);
      } else {
        exec.distance = null;
      }
    });
    
    executors.sort((a, b) => {
      if (a.distance === null) return 1;
      if (b.distance === null) return -1;
      return a.distance - b.distance;
    });
    
    select.innerHTML = '';
    executors.forEach(exec => {
      const distLabel = exec.distance !== null ? `(Cách hiện trường: ${exec.distance.toFixed(2)} km)` : '(Không có GPS)';
      select.innerHTML += `<option value="${exec.id}">${exec.full_name} ${distLabel}</option>`;
    });
  } catch (err) {
    console.error(err);
    select.innerHTML = '<option value="">Có lỗi xảy ra khi tải đơn vị</option>';
  }
  
  document.getElementById('dispatch-modal').style.display = 'grid';
}

function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function closeDispatchModal() {
  document.getElementById('dispatch-modal').style.display = 'none';
}

async function submitManualDispatch() {
  const reportId = document.getElementById('dispatch-report-id').value;
  const execId = document.getElementById('dispatch-executor-select').value;
  const notes = document.getElementById('dispatch-notes-input').value.trim();
  
  if (!execId) {
    showToast('Vui lòng chọn đơn vị thi công phù hợp.', 'error');
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('executor_id', execId);
    if (notes) formData.append('notes', notes);
    
    const res = await fetch(`${API}/api/moderator/reports/${reportId}/dispatch`, {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) throw new Error('Có lỗi xảy ra khi bàn giao việc');
    
    showToast('Đã bàn giao sự cố thực địa thành công!', 'success');
    closeDispatchModal();
    loadModeratorDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── Toast Notifications ──────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  
  setTimeout(() => {
    t.classList.remove('show');
  }, 3500);
}
