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
  document.getElementById('login-title').textContent = 'Đăng Nhập';
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
let capturedImages = [];

function handleImageCapture(event) {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;
  
  const validFiles = files.filter(f => f.type.startsWith('image/'));
  if (validFiles.length === 0) {
    showToast('Vui lòng chọn tệp ảnh hợp lệ.', 'error');
    return;
  }
  
  capturedImages = [...capturedImages, ...validFiles].slice(0, 4); // Giới hạn tối đa 4 ảnh
  renderPreviews();
}

function renderPreviews() {
  const preview = document.getElementById('camera-preview');
  preview.innerHTML = '';
  preview.style.display = 'flex';
  preview.style.flexWrap = 'wrap';
  preview.style.gap = '8px';
  
  capturedImages.forEach((file, index) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const container = document.createElement('div');
      container.className = 'preview-item';
      container.style.position = 'relative';
      container.style.width = '70px';
      container.style.height = '70px';
      container.style.borderRadius = '8px';
      container.style.overflow = 'hidden';
      container.style.border = '1px solid var(--slate-200)';
      
      container.innerHTML = `
        <img src="${e.target.result}" style="width:100%; height:100%; object-fit:cover;" />
        <button onclick="removeImage(${index}, event)" style="position:absolute; top:2px; right:2px; width:18px; height:18px; border-radius:50%; background:rgba(220,38,38,0.85); color:white; border:none; font-size:11px; display:grid; place-items:center; cursor:pointer; font-weight:bold;">&times;</button>
      `;
      preview.appendChild(container);
    };
    reader.readAsDataURL(file);
  });
  
  if (capturedImages.length < 4) {
    const addBtn = document.createElement('div');
    addBtn.style.width = '70px';
    addBtn.style.height = '70px';
    addBtn.style.borderRadius = '8px';
    addBtn.style.border = '2px dashed var(--slate-300)';
    addBtn.style.display = 'grid';
    addBtn.style.placeItems = 'center';
    addBtn.style.cursor = 'pointer';
    addBtn.innerHTML = '<span style="font-size:24px; color:var(--text-muted); font-weight:300;">+</span>';
    addBtn.onclick = () => document.getElementById('camera-input').click();
    preview.appendChild(addBtn);
  }
  
  document.getElementById('camera-actions').style.display = 'flex';
}

function removeImage(index, event) {
  event.stopPropagation();
  capturedImages.splice(index, 1);
  if (capturedImages.length === 0) {
    retakePhoto();
  } else {
    renderPreviews();
  }
}

function retakePhoto() {
  capturedImages = [];
  const preview = document.getElementById('camera-preview');
  preview.innerHTML = `
    <div class="camera-placeholder" onclick="document.getElementById('camera-input').click()">
      <div class="camera-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
      </div>
      <p>Chạm để chụp / tải ảnh</p>
      <span class="camera-hint">Bạn có thể chọn tải lên nhiều ảnh</span>
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
function createCollageAndCompress(files) {
  return new Promise((resolve) => {
    if (files.length === 1) {
      compressImage(files[0]).then(resolve);
      return;
    }
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const promises = files.map(file => {
      return new Promise((resImg) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const img = new Image();
          img.onload = () => resImg(img);
          img.src = e.target.result;
        };
        reader.readAsDataURL(file);
      });
    });
    
    Promise.all(promises).then(images => {
      let cols = 2;
      let rows = images.length > 2 ? 2 : 1;
      
      const singleW = 500;
      const singleH = 500;
      
      canvas.width = cols * singleW;
      canvas.height = rows * singleH;
      
      images.forEach((img, index) => {
        const x = (index % cols) * singleW;
        const y = Math.floor(index / cols) * singleH;
        
        const imgRatio = img.width / img.height;
        const targetRatio = singleW / singleH;
        let drawW, drawH, sx = 0, sy = 0;
        
        if (imgRatio > targetRatio) {
          drawH = img.height;
          drawW = img.height * targetRatio;
          sx = (img.width - drawW) / 2;
        } else {
          drawW = img.width;
          drawH = img.width / targetRatio;
          sy = (img.height - drawH) / 2;
        }
        
        ctx.drawImage(img, sx, sy, drawW, drawH, x, y, singleW, singleH);
      });
      
      canvas.toBlob((blob) => {
        const file = new File([blob], "collage.jpg", { type: 'image/jpeg' });
        resolve(file);
      }, 'image/jpeg', 0.85);
    });
  });
}

async function submitReportWithImage() {
  const text = document.getElementById('report-text').value.trim();
  
  if (!text) {
    showToast('Vui lòng nhập mô tả sự cố.', 'error');
    return;
  }
  
  if (capturedImages.length === 0) {
    showToast('Vui lòng chụp hoặc chọn tải ảnh sự cố hiện trường.', 'error');
    return;
  }
  
  const btn = document.getElementById('submit-btn');
  const label = document.getElementById('btn-label');
  btn.disabled = true;
  
  try {
    label.textContent = 'Đang tối ưu dung lượng ảnh (4G)...';
    const compressedImage = await createCollageAndCompress(capturedImages);
    
    label.textContent = 'Đang gửi & Chờ xử lý...';
    
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
      let statusWord = 'đang chờ bàn giao';
      if (r.status === 'Pending_Manual_Review' || r.status === 'Pending_Quick_Review') { badgeClass = 'badge-pending'; statusWord = 'đang chờ bàn giao'; }
      else if (r.status === 'Auto-Dispatched') { badgeClass = 'badge-approved'; statusWord = 'đã bàn giao tự động (AI)'; }
      else if (r.status === 'Assigned_Manually') { badgeClass = 'badge-approved'; statusWord = 'đã bàn giao'; }
      else if (r.status === 'In_Progress') { badgeClass = 'badge-pending'; statusWord = 'đang chờ xử lý'; }
      else if (r.status === 'Resolved') { badgeClass = 'badge-approved'; statusWord = 'đã xử lý'; }
      
      const parsedLabels = r.vision_labels ? JSON.parse(r.vision_labels) : [];
      const visionLabelsHTML = parsedLabels.map(l => `<span class="vision-tag">${l}</span>`).join('');
      
      const primaryCat = r.predicted_categories ? r.predicted_categories.split(', ')[0] : 'hư hỏng đường xá';
      
      let actionButtons = `
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:12px;">
          ${(r.status !== 'Resolved') ? `
            <button class="btn-primary" onclick="openDispatchModal(${r.id}, '${primaryCat}', ${r.latitude || 'null'}, ${r.longitude || 'null'})" style="padding:8px 12px; font-size:11px; min-height:32px; background:linear-gradient(135deg, var(--accent), #1d4ed8); box-shadow:none; cursor:pointer;">⚙ Bàn giao việc</button>
          ` : ''}
          <button class="btn-primary" onclick="deleteReport(${r.id})" style="padding:8px 12px; font-size:11px; min-height:32px; background:linear-gradient(135deg, #dc2626, #b91c1c); box-shadow:none; cursor:pointer;">&times; Xóa</button>
        </div>
      `;
      
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

async function deleteReport(id) {
  if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn phản ánh #${id} khỏi hệ thống không?`)) {
    return;
  }
  try {
    const res = await fetch(`${API}/api/moderator/reports/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Không thể xóa phản ánh');
    showToast(`Đã xóa phản ánh #${id} thành công!`, 'success');
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
    let url = `${API}/reports/?limit=50`;
    if (filterVal && filterVal !== 'pending') url += `&status=${filterVal}`;
    if (currentUser && currentUser.user_id) {
      url += `&assigned_executor_id=${currentUser.user_id}`;
    }
    
    const res = await fetch(url);
    if (!res.ok) throw new Error('Không thể kết nối máy chủ');
    
    let reports = await res.json();
    
    if (filterVal === 'pending') {
      reports = reports.filter(r => r.status !== 'Resolved');
    }
    
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
          <p>Hiện tại bạn không có nhiệm vụ xử lý sự cố nào phù hợp.</p>
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
      else if (r.status === 'Auto-Dispatched') { badgeClass = 'badge-pending'; statusWord = 'Được giao tự động (AI)'; }
      else if (r.status === 'Assigned_Manually') { badgeClass = 'badge-pending'; statusWord = 'Cán bộ điều phối tay'; }
      
      let dispatchInfoHTML = '';
      if (r.dispatch_notes) {
        dispatchInfoHTML = `
          <div style="margin-top:10px; background:rgba(37,99,235,0.03); border-left:3px solid var(--accent); padding:8px 12px; font-size:12px; color:var(--text-primary); border-radius:0 6px 6px 0;">
            📢 <b>Chỉ thị từ Trung tâm:</b> <i>${r.dispatch_notes}</i>
          </div>
        `;
      }
      
      let actionForm = '';
      if (r.status !== 'Resolved') {
        actionForm = `
          <div style="margin-top:12px; padding-top:12px; border-top:1px dashed #e2e8f0;">
            <div class="form-group" style="margin-bottom:8px;">
              <input type="text" id="res-note-${r.id}" class="form-input" style="min-height:36px; font-size:12px; padding:6px 12px;" placeholder="Nhập ghi chú thi công thực tế (Ví dụ: Đã xử lý thông luồng, dọn cát)..." value="${r.resolver_notes || ''}" />
            </div>
            <div style="display:flex; gap:8px;">
              ${r.status !== 'In_Progress' ? `
                <button class="btn-gps" onclick="resolverAction(${r.id}, 'In_Progress')" style="min-height:36px; padding:6px 12px; font-size:12px; border-color:#d97706; color:#d97706; cursor:pointer;">🚧 Nhận việc & thi công</button>
              ` : ''}
              <button class="btn-primary" onclick="resolverAction(${r.id}, 'Resolved')" style="min-height:36px; padding:6px 12px; font-size:12px; background:linear-gradient(135deg, #059669, #047857); box-shadow:none; cursor:pointer;">✔ Đóng sự cố (Sửa xong)</button>
            </div>
          </div>
        `;
      } else {
        actionForm = `
          <div style="margin-top:8px; padding:8px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; font-size:12px; color:#15803d;">
            <b>Ghi chú hoàn thành thực tế:</b> ${r.resolver_notes || 'Không có ghi chú'}
          </div>
        `;
      }
      
      container.innerHTML += `
        <div class="report-item">
          <div class="report-id">#${r.id}</div>
          <div class="report-body">
            <p class="report-text" style="font-weight:600;">${r.raw_text}</p>
            <div class="report-meta" style="margin-top:6px;">
              <span class="tag tag-location" style="background:#f1f5f9; color:#475569; border-color:#e2e8f0;">📍 Hiện trường: ${r.extracted_locations || 'Không rõ'}</span>
            </div>
            
            ${imageUrl ? `
              <img src="${imageUrl}" style="width:100%; max-height:160px; object-fit:cover; border-radius:8px; margin-top:10px; border:1px solid #e2e8f0;" onclick="window.open('${imageUrl}')" />
            ` : ''}
            
            ${dispatchInfoHTML}
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
let editingExecutorId = null;

function viewExecutor(exec) {
  alert(`🔍 CHI TIẾT ĐƠN VỊ:\n\n• Tài khoản: ${exec.username}\n• Tên đội / Đơn vị: ${exec.full_name}\n• Chuyên môn dán nhãn: ${exec.specialty}\n• GPS Cơ sở: ${exec.base_latitude?.toFixed(5)}, ${exec.base_longitude?.toFixed(5)}\n• Ghi chú (SĐT, Địa chỉ): ${exec.department || 'Không có ghi chú'}`);
}

async function loadExecutorsList() {
  try {
    const res = await fetch(`${API}/api/moderator/executors`);
    if (!res.ok) throw new Error('Không thể tải danh sách đơn vị');
    const executors = await res.json();
    
    const tbody = document.getElementById('moderator-executors-tbody');
    tbody.innerHTML = '';
    
    if (executors.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:15px; color:var(--text-muted);">Chưa có đơn vị nào được đăng ký</td></tr>';
      return;
    }
    
    executors.forEach(exec => {
      const execStr = JSON.stringify(exec).replace(/'/g, "&apos;").replace(/"/g, "&quot;");
      tbody.innerHTML += `
        <tr style="border-bottom:1px solid var(--slate-100); color:var(--text-primary);">
          <td style="padding:12px 10px; font-weight:bold;">${exec.username}</td>
          <td style="padding:12px 10px;">${exec.full_name}</td>
          <td style="padding:12px 10px;"><span class="tag tag-category">${exec.specialty}</span></td>
          <td style="padding:12px 10px; font-family:monospace;">${exec.base_latitude?.toFixed(4)}, ${exec.base_longitude?.toFixed(4)}</td>
          <td style="padding:12px 10px; text-align:center;">
            <button class="btn-gps" style="border-color:var(--accent); color:var(--accent); background:rgba(37,99,235,0.05); padding:4px 8px; font-size:0.75rem; cursor:pointer;" onclick='viewExecutor(${execStr})'>Xem</button>
            <button class="btn-gps" style="border-color:#d97706; color:#d97706; background:rgba(217,119,6,0.05); padding:4px 8px; font-size:0.75rem; cursor:pointer; margin-left:4px;" onclick='openCreateExecutorModal(${execStr})'>Sửa</button>
            <button class="btn-gps" style="border-color:#ef4444; color:#ef4444; background:rgba(239,68,68,0.05); padding:4px 8px; font-size:0.75rem; cursor:pointer; margin-left:4px;" onclick='deleteExecutor(${exec.id})'>Xóa</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error(err);
  }
}

function openCreateExecutorModal(exec = null) {
  if (exec) {
    editingExecutorId = exec.id;
    document.getElementById('exec-modal-title').textContent = 'Cập nhật đơn vị';
    document.getElementById('new-exec-username').value = exec.username;
    document.getElementById('new-exec-fullname').value = exec.full_name;
    document.getElementById('new-exec-specialty').value = exec.specialty;
    document.getElementById('new-exec-notes').value = exec.department === 'Đơn vị thực tế thực địa' ? '' : exec.department;
    document.getElementById('new-exec-lat').value = exec.base_latitude;
    document.getElementById('new-exec-lng').value = exec.base_longitude;
    
    document.getElementById('exec-username-group').style.display = 'none';
    document.getElementById('exec-password-group').style.display = 'none';
  } else {
    editingExecutorId = null;
    document.getElementById('exec-modal-title').textContent = 'Thêm Đơn Vị mới';
    document.getElementById('new-exec-username').value = '';
    document.getElementById('new-exec-password').value = '';
    document.getElementById('new-exec-fullname').value = '';
    document.getElementById('new-exec-notes').value = '';
    document.getElementById('new-exec-lat').value = '';
    document.getElementById('new-exec-lng').value = '';
    
    document.getElementById('exec-username-group').style.display = 'block';
    document.getElementById('exec-password-group').style.display = 'block';
  }
  document.getElementById('create-executor-modal').style.display = 'grid';
}

function closeCreateExecutorModal() {
  document.getElementById('create-executor-modal').style.display = 'none';
}

async function submitCreateExecutor() {
  const username = document.getElementById('new-exec-username').value.trim();
  const password = document.getElementById('new-exec-password').value;
  const full_name = document.getElementById('new-exec-fullname').value.trim();
  const specialty = document.getElementById('new-exec-specialty').value;
  const notes = document.getElementById('new-exec-notes').value.trim();
  const lat = parseFloat(document.getElementById('new-exec-lat').value);
  const lng = parseFloat(document.getElementById('new-exec-lng').value);
  
  if (!full_name || isNaN(lat) || isNaN(lng)) {
    showToast('Vui lòng điền đầy đủ các thông tin bắt buộc.', 'error');
    return;
  }
  
  if (!editingExecutorId && (!username || !password)) {
    showToast('Tên đăng nhập và mật khẩu khởi tạo là bắt buộc khi tạo mới.', 'error');
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('full_name', full_name);
    formData.append('specialty', specialty);
    formData.append('department', notes || 'Đơn vị thực tế thực địa');
    formData.append('base_latitude', lat);
    formData.append('base_longitude', lng);
    
    let url = `${API}/api/moderator/executors/create`;
    if (editingExecutorId) {
      url = `${API}/api/moderator/executors/${editingExecutorId}/update`;
    } else {
      formData.append('username', username);
      formData.append('password', password);
    }
    
    const res = await fetch(url, {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Không thể lưu thông tin đơn vị');
    }
    
    showToast(editingExecutorId ? 'Cập nhật thông tin đơn vị thành công!' : 'Tạo mới tài khoản Đơn vị thành công!', 'success');
    closeCreateExecutorModal();
    loadExecutorsList();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteExecutor(id) {
  if (!confirm('Bạn có chắc chắn muốn xóa vĩnh viễn đơn vị thi công này không? Hành động này không thể hoàn tác.')) return;
  try {
    const res = await fetch(`${API}/api/moderator/executors/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Không thể xóa đơn vị');
    showToast('Đã xóa đơn vị thành công!', 'success');
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
