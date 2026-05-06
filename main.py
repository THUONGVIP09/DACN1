from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import database, models, schemas
from extract_entities import extract_entities
from preprocess import clean_text
from pyvi import ViTokenizer
from vision_client import get_vision_client
import joblib
import os
import shutil
from pathlib import Path
import json
import datetime

# Tạo bảng trong Database nếu chưa có
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Traffic Incident API (Smart City)",
    description="Hệ thống tiếp nhận, phân loại và trích xuất thực thể phản ánh giao thông tự động.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("frontend/index.html")

# Load bộ não AI (Machine Learning Models)
try:
    vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
    mlb = joblib.load("models/label_binarizer.pkl")
    classifier = joblib.load("models/traffic_classifier.pkl")
    print("[AI] Models loaded successfully!")
except Exception as e:
    print(f"[Warning] Model files not found: {e}")
    vectorizer, mlb, classifier = None, None, None

def predict_categories(text: str) -> tuple:
    """
    Chạy câu qua Model AI để lấy danh sách nhãn và confidence score
    Returns: (labels_list, confidence_score)
    """
    if not classifier: 
        return [], 0.0
    
    cleaned = clean_text(text)
    tokenized = ViTokenizer.tokenize(cleaned)
    X = vectorizer.transform([tokenized])
    
    # Lấy prediction
    pred = classifier.predict(X)
    labels = list(mlb.inverse_transform(pred)[0])
    
    # Tính confidence dựa trên sigmoid của decision function
    try:
        import numpy as np
        decision_scores = classifier.decision_function(X)[0]
        
        # Fallback mechanism: Nếu không gán nhãn nào nhưng nhãn có điểm cao nhất rất gần ngưỡng (> -0.5)
        if len(labels) == 0:
            max_idx = np.argmax(decision_scores)
            max_score = decision_scores[max_idx]
            
            if max_score > -0.5:
                fallback_class = mlb.classes_[max_idx]
                labels = [fallback_class]
                # Chuyển điểm sang khoảng sigmoid [0.38, 0.50]
                confidence = 1 / (1 + np.exp(-max_score))
            else:
                confidence = 0.0
        else:
            # Lấy các điểm dương (đã được gán nhãn) để tính độ tự tin trung bình
            pos_scores = decision_scores[decision_scores > 0]
            if len(pos_scores) > 0:
                # Sigmoid của các điểm dương sẽ cho giá trị trong khoảng [0.5, 1.0]
                confidence = np.mean(1 / (1 + np.exp(-pos_scores)))
            else:
                confidence = 0.5
    except Exception as e:
        print(f"[AI Confidence Error] {e}")
        confidence = 0.7  # Default fallback
    
    return labels, round(float(confidence), 3)

import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách địa lý Haversine (km) giữa hai tọa độ địa lý
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    R = 6371.0  # Bán kính Trái Đất (km)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

# Tạo thư mục lưu ảnh
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/reports/", response_model=schemas.ReportResponse, tags=["Reports"])
def submit_report(report: schemas.ReportCreate, db: Session = Depends(database.get_db)):
    """
    API gửi phản ánh TEXT-ONLY (Legacy). 
    Hệ thống sẽ tự động phân loại và trích xuất thực thể.
    """
    # 1. Phân loại (Classification)
    categories, nlp_confidence = predict_categories(report.text)
    cat_str = ", ".join(categories)
    
    # 2. Trích xuất Thực thể (NER)
    entities = extract_entities(report.text)
    loc_str = " | ".join(entities["locations"])
    time_str = " | ".join(entities["times"])
    
    # 3. Logic duyệt tự động (Auto-Approve) - Legacy logic
    if categories and entities["locations"]:
        final_status = "Auto-Approved"
    else:
        final_status = "Pending_Manual_Review"
        
    # 4. Lưu Database
    db_report = models.Report(
        raw_text=report.text,
        predicted_categories=cat_str,
        extracted_locations=loc_str,
        extracted_times=time_str,
        status=final_status,
        latitude=report.latitude,
        longitude=report.longitude,
        nlp_confidence=nlp_confidence,
        reporter_name=report.reporter_name,
        reporter_phone=report.reporter_phone
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report


@app.post("/reports/with-image", response_model=schemas.ReportResponse, tags=["Reports"])
async def submit_report_with_image(
    text: str = Form(..., description="Nội dung mô tả sự cố"),
    latitude: Optional[float] = Form(None, description="Vĩ độ GPS"),
    longitude: Optional[float] = Form(None, description="Kinh độ GPS"),
    reporter_name: Optional[str] = Form(None, description="Họ tên người dân"),
    reporter_phone: Optional[str] = Form(None, description="SĐT người dân"),
    image: UploadFile = File(..., description="Ảnh sự cố (chụp từ điện thoại)"),
    db: Session = Depends(database.get_db)
):
    """
    API gửi phản ánh KÈM ẢNH (Recommended cho Mobile).
    
    Hệ thống sẽ:
    1. Phân tích TEXT (NLP) → phân loại category, confidence
    2. Phân tích ẢNH (Google Vision API) → labels, quality check
    3. Kết hợp cả 2 → final confidence score
    4. Auto-Approve nếu score >= 0.85
    5. Lưu ảnh vào server
    
    Returns: Report đã tạo với đầy đủ AI analysis scores
    """
    try:
        # ===== 1. NLP ANALYSIS =====
        categories, nlp_confidence = predict_categories(text)
        primary_category = categories[0] if categories else "Unknown"
        cat_str = ", ".join(categories)
        
        # NER
        entities = extract_entities(text)
        loc_str = " | ".join(entities["locations"])
        time_str = " | ".join(entities["times"])
        
        # ===== 2. VISION ANALYSIS =====
        # Đọc file ảnh
        image_bytes = await image.read()
        
        # Kiểm tra file hợp lệ
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Ảnh upload bị rỗng")
        
        # Lưu file ảnh
        file_extension = image.filename.split(".")[-1] if "." in image.filename else "jpg"
        safe_filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text[:20])}.{file_extension}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        # Gọi Google Vision API
        try:
            vision_client = get_vision_client()
            vision_result = vision_client.analyze_image(image_bytes)
            
            # Tính combined score
            combined_result = vision_client.calculate_combined_confidence(
                nlp_category=primary_category,
                nlp_confidence=nlp_confidence,
                vision_result=vision_result
            )
            
            vision_labels_json = json.dumps(vision_result["labels"][:20])  # Lưu top 20 labels
            vision_confidence = combined_result["vision_score"]
            final_confidence = combined_result["final_score"]
            auto_approve = combined_result["auto_approve"]
            
        except Exception as e:
            print(f"[Vision Error] {e}")
            # Fallback: Chỉ dùng NLP nếu Vision fail
            vision_labels_json = json.dumps([])
            vision_confidence = 0.0
            final_confidence = nlp_confidence * 0.6  # Giảm confidence vì thiếu Vision
            auto_approve = False
            combined_result = {"match_verdict": "Vision API Error - Manual Review"}
        
        # ===== 3. DETERMINE STATUS & AUTO-DISPATCH (Grab model) =====
        assigned_executor_id = None
        dispatch_notes = None
        
        if final_confidence >= 0.85 and latitude is not None and longitude is not None:
            # Tìm Đơn vị thực thi (Executor) phù hợp theo chuyên môn
            executors = db.query(models.User).filter(
                models.User.role == "executor",
                models.User.specialty == primary_category
            ).all()
            
            if executors:
                nearest_exec = None
                min_dist = float('inf')
                for exec_user in executors:
                    dist = calculate_distance(latitude, longitude, exec_user.base_latitude, exec_user.base_longitude)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_exec = exec_user
                
                if nearest_exec:
                    assigned_executor_id = nearest_exec.id
                    final_status = "Auto-Dispatched"
                    dispatch_notes = f"Hệ thống AI tự động điều phối đến {nearest_exec.full_name} (Khoảng cách: {min_dist:.2f} km, Độ tin cậy: {(final_confidence*100):.0f}%)."
                else:
                    final_status = "Auto-Approved"
            else:
                final_status = "Auto-Approved"
        elif final_confidence >= 0.6:
            final_status = "Pending_Quick_Review"
        else:
            final_status = "Pending_Manual_Review"
        
        # ===== 4. SAVE TO DATABASE =====
        db_report = models.Report(
            raw_text=text,
            predicted_categories=cat_str,
            extracted_locations=loc_str,
            extracted_times=time_str,
            status=final_status,
            
            # Location
            latitude=latitude,
            longitude=longitude,
            
            # Image
            image_path=file_path.as_posix(),
            
            # AI Scores
            nlp_confidence=nlp_confidence,
            vision_confidence=vision_confidence,
            final_confidence=final_confidence,
            vision_labels=vision_labels_json,
            
            # Dispatch details
            assigned_executor_id=assigned_executor_id,
            dispatch_notes=dispatch_notes,
            
            # Reporter identity
            reporter_name=reporter_name,
            reporter_phone=reporter_phone
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        print(f"[Report Created] ID: {db_report.id}, Status: {final_status}, Confidence: {final_confidence}")
        
        return db_report
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Error] submit_report_with_image: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")


@app.get("/reports/map-data", tags=["Map"])
def get_reports_for_map(
    lat_min: float = None,
    lat_max: float = None,
    lng_min: float = None,
    lng_max: float = None,
    category: str = None,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """
    Lấy dữ liệu phản ánh cho bản đồ (GeoJSON format)
    
    Query params:
    - lat_min, lat_max, lng_min, lng_max: Bounding box
    - category: Lọc theo category (optional)
    - limit: Số lượng tối đa (default 100)
    
    Returns: Danh sách reports với lat/lng cho frontend map
    """
    query = db.query(models.Report).filter(
        models.Report.latitude != None,
        models.Report.longitude != None
    )
    
    # Bounding box filter
    if lat_min is not None and lat_max is not None:
        query = query.filter(models.Report.latitude.between(lat_min, lat_max))
    if lng_min is not None and lng_max is not None:
        query = query.filter(models.Report.longitude.between(lng_min, lng_max))
    
    # Category filter
    if category:
        query = query.filter(models.Report.predicted_categories.contains(category))
    
    reports = query.order_by(models.Report.created_at.desc()).limit(limit).all()
    
    # Convert to GeoJSON format
    features = []
    for r in reports:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(r.longitude) if r.longitude else 0, 
                               float(r.latitude) if r.latitude else 0]
            },
            "properties": {
                "id": r.id,
                "category": r.predicted_categories,
                "description": r.raw_text[:200] if r.raw_text else "",
                "location": r.extracted_locations,
                "status": r.status,
                "confidence": float(r.final_confidence) if r.final_confidence else 0,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "image_url": f"/uploads/{os.path.basename(r.image_path)}" if r.image_path else None
            }
        })
    
    return {"type": "FeatureCollection", "features": features}

@app.get("/reports/", response_model=list[schemas.ReportResponse], tags=["Reports"])
def get_all_reports(
    skip: int = 0, 
    limit: int = 50, 
    status: str = None,
    category: str = None,
    assigned_executor_id: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """
    Lấy danh sách các phản ánh đã lưu trong DB
    
    Query params:
    - status: Lọc theo trạng thái
    - category: Lọc theo category
    - assigned_executor_id: Lọc theo đơn vị thi công phụ trách
    """
    query = db.query(models.Report)
    
    if status:
        query = query.filter(models.Report.status == status)
    if category:
        query = query.filter(models.Report.predicted_categories.contains(category))
    if assigned_executor_id is not None:
        query = query.filter(models.Report.assigned_executor_id == assigned_executor_id)
    
    return query.order_by(models.Report.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/analytics/summary", tags=["Analytics"])
def get_analytics_summary(db: Session = Depends(database.get_db)):
    """
    Dashboard analytics: Tổng hợp thống kê cho frontend charts
    """
    from sqlalchemy import func
    
    total = db.query(models.Report).count()
    
    # By status
    status_counts = db.query(models.Report.status, func.count(models.Report.id)).group_by(models.Report.status).all()
    
    # By category (need to parse the comma-separated categories)
    all_reports = db.query(models.Report.predicted_categories).all()
    category_counts = {}
    for (cats,) in all_reports:
        if cats:
            for cat in cats.split(", "):
                category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Average confidence
    avg_confidence = db.query(func.avg(models.Report.final_confidence)).scalar() or 0
    
    # Recent trend (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = db.query(models.Report).filter(models.Report.created_at >= week_ago).count()
    
    return {
        "total_reports": total,
        "by_status": {status: count for status, count in status_counts},
        "by_category": category_counts,
        "avg_confidence": round(float(avg_confidence), 3),
        "recent_7_days": recent_count
    }


# Serve uploaded images
@app.get("/uploads/{filename}")
def serve_uploaded_image(filename: str):
    """Serve uploaded images"""
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Image not found")


# Password hashing helper (Simple SHA256)
import hashlib
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ===== AUTHENTICATION & LOGIN =====
@app.post("/api/auth/login", tags=["Auth"])
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    """Đăng nhập hệ thống cho Moderator và Admin/Resolver"""
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user or user.hashed_password != hash_password(user_data.password):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    
    return {
        "status": "success",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "department": user.department,
        "token": f"mock-token-for-{user.username}"
    }

# ===== MODERATION ENDPOINTS =====
@app.post("/api/moderator/reports/{id}/approve", response_model=schemas.ReportResponse, tags=["Moderator"])
def approve_report(id: int, db: Session = Depends(database.get_db)):
    """Moderator duyệt phản ánh thủ công"""
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản ánh")
    
    report.status = "Approved_By_Mod"
    db.commit()
    db.refresh(report)
    return report

@app.post("/api/moderator/reports/{id}/reject", response_model=schemas.ReportResponse, tags=["Moderator"])
def reject_report(id: int, db: Session = Depends(database.get_db)):
    """Moderator từ chối phản ánh thủ công"""
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản ánh")
    
    report.status = "Rejected_By_Mod"
    db.commit()
    db.refresh(report)
    return report

@app.delete("/api/moderator/reports/{id}", tags=["Moderator"])
def delete_report(id: int, db: Session = Depends(database.get_db)):
    """Cán bộ xóa hoàn toàn sự cố/báo cáo từ hệ thống"""
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản ánh")
    db.delete(report)
    db.commit()
    return {"status": "success", "message": "Đã xóa phản ánh thành công"}

@app.post("/api/moderator/reports/{id}/dispatch", response_model=schemas.ReportResponse, tags=["Moderator"])
def manual_dispatch_report(
    id: int,
    executor_id: int = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(database.get_db)
):
    """
    Cán bộ điều phối thủ công bàn giao sự cố cho Executor phù hợp kèm ghi chú chỉ đạo thực tế
    """
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản ánh")
    
    executor = db.query(models.User).filter(models.User.id == executor_id, models.User.role == "executor").first()
    if not executor:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị thực thi phù hợp")
    
    report.assigned_executor_id = executor.id
    report.status = "Assigned_Manually"
    report.dispatch_notes = notes or f"Cán bộ điều phối thủ công bàn giao cho {executor.full_name}."
    db.commit()
    db.refresh(report)
    return report

@app.get("/api/moderator/executors", response_model=List[schemas.UserResponse], tags=["Moderator"])
def get_executors_list(
    specialty: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """
    Lấy danh sách các Đơn vị thực thi (Executor) phục vụ tính toán và hiển thị cho cán bộ điều phối
    """
    query = db.query(models.User).filter(models.User.role == "executor")
    if specialty:
        query = query.filter(models.User.specialty == specialty)
    return query.all()

@app.post("/api/moderator/executors/create", response_model=schemas.UserResponse, tags=["Moderator"])
def create_executor(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    specialty: str = Form(...),
    base_latitude: float = Form(...),
    base_longitude: float = Form(...),
    department: Optional[str] = Form(None),
    db: Session = Depends(database.get_db)
):
    """
    Tạo mới tài khoản Executor (Chỉ Cán bộ điều phối tối cao mới có quyền)
    """
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập này đã tồn tại")
    
    new_user = models.User(
        username=username,
        hashed_password=hash_password(password),
        role="executor",
        specialty=specialty,
        base_latitude=base_latitude,
        base_longitude=base_longitude,
        full_name=full_name,
        department=department or "Đơn vị thực thi thực địa"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/moderator/executors/{id}/update", response_model=schemas.UserResponse, tags=["Moderator"])
def update_executor(
    id: int,
    full_name: str = Form(...),
    specialty: str = Form(...),
    base_latitude: float = Form(...),
    base_longitude: float = Form(...),
    department: Optional[str] = Form(None),
    db: Session = Depends(database.get_db)
):
    """Cập nhật thông tin tài khoản đơn vị thi công"""
    executor = db.query(models.User).filter(models.User.id == id, models.User.role == "executor").first()
    if not executor:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản đơn vị")
    executor.full_name = full_name
    executor.specialty = specialty
    executor.base_latitude = base_latitude
    executor.base_longitude = base_longitude
    executor.department = department or "Đơn vị thực tế thực địa"
    db.commit()
    db.refresh(executor)
    return executor

@app.delete("/api/moderator/executors/{id}", tags=["Moderator"])
def delete_executor(id: int, db: Session = Depends(database.get_db)):
    """
    Xóa tài khoản Executor (Chỉ Cán bộ điều phối tối cao mới có quyền)
    """
    executor = db.query(models.User).filter(models.User.id == id, models.User.role == "executor").first()
    if not executor:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản đơn vị")
    db.delete(executor)
    db.commit()
    return {"status": "success", "message": "Đã xóa tài khoản đơn vị thi công thành công"}

# ===== RESOLUTION ENDPOINTS =====
@app.post("/api/resolver/reports/{id}/status", response_model=schemas.ReportResponse, tags=["Resolver"])
def update_resolver_status(
    id: int, 
    status: str = Form(...), # "In_Progress" hoặc "Resolved"
    notes: Optional[str] = Form(None), 
    db: Session = Depends(database.get_db)
):
    """Đơn vị xử lý cập nhật tiến độ khắc phục thực tế"""
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản ánh")
    
    if status not in ["In_Progress", "Resolved"]:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
    
    report.status = status
    if notes:
        report.resolver_notes = notes
    
    if status == "Resolved":
        report.resolved_at = datetime.datetime.utcnow()
        
    db.commit()
    db.refresh(report)
    return report


# Startup event - check Vision API & seed accounts
@app.on_event("startup")
async def startup_event():
    """Check Vision API on startup & seed Moderator and Admin accounts"""
    # 1. Check Vision API
    try:
        client = get_vision_client()
        print("[OK] Google Vision API connected successfully")
    except Exception as e:
        print(f"[WARN] Google Vision API connection failed: {e}")
        print("[INFO] Reports with images will fallback to NLP-only analysis")

    # 2. Seed Default Accounts
    try:
        db = database.SessionLocal()
        # Seed Moderator (Cán bộ điều phối)
        mod_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not mod_user:
            mod_user = models.User(
                username="admin",
                hashed_password=hash_password("admin"),
                role="moderator",
                full_name="Cán bộ điều phối",
                department="Trung tâm Điều hành Đô thị"
            )
            db.add(mod_user)
            print("[Seed] Created default moderator account: admin / admin")
            
        # Seed Executor 1: đèn tín hiệu
        exec_light = db.query(models.User).filter(models.User.username == "exec_light").first()
        if not exec_light:
            exec_light = models.User(
                username="exec_light",
                hashed_password=hash_password("exec123"),
                role="executor",
                specialty="đèn tín hiệu",
                base_latitude=16.0245,
                base_longitude=108.2435,
                full_name="Đội Thi công Cầu đường Ngũ Hành Sơn",
                department="Xí nghiệp Chiếu sáng & Cầu đường Đà Nẵng"
            )
            db.add(exec_light)
            print("[Seed] Created executor account: exec_light / exec123")

        # Seed Executor 2: ngập nước
        exec_water = db.query(models.User).filter(models.User.username == "exec_water").first()
        if not exec_water:
            exec_water = models.User(
                username="exec_water",
                hashed_password=hash_password("exec123"),
                role="executor",
                specialty="ngập nước",
                base_latitude=16.0612,
                base_longitude=108.1921,
                full_name="Đội Công trình Thoát nước Thanh Khê",
                department="Công ty Thoát nước và Xử lý Nước thải Đà Nẵng"
            )
            db.add(exec_water)
            print("[Seed] Created executor account: exec_water / exec123")

        # Seed Executor 3: ùn tắc giao thông
        exec_traffic = db.query(models.User).filter(models.User.username == "exec_traffic").first()
        if not exec_traffic:
            exec_traffic = models.User(
                username="exec_traffic",
                hashed_password=hash_password("exec123"),
                role="executor",
                specialty="ùn tắc giao thông",
                base_latitude=16.0595,
                base_longitude=108.2215,
                full_name="Đội Điều phối Đô thị Hải Châu",
                department="Trung tâm Điều hành Giao thông Đô thị Đà Nẵng"
            )
            db.add(exec_traffic)
            print("[Seed] Created executor account: exec_traffic / exec123")
            
        db.commit()
        db.close()
    except Exception as e:
        print(f"[WARN] Failed to seed default accounts: {e}")

