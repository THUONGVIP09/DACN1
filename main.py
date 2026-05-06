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
        nlp_confidence=nlp_confidence
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
        
        # ===== 3. DETERMINE STATUS =====
        if auto_approve and entities["locations"]:
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
            vision_labels=vision_labels_json
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
    db: Session = Depends(database.get_db)
):
    """
    Lấy danh sách các phản ánh đã lưu trong DB
    
    Query params:
    - status: Lọc theo trạng thái (Auto-Approved, Pending_Quick_Review, Pending_Manual_Review)
    - category: Lọc theo category
    """
    query = db.query(models.Report)
    
    if status:
        query = query.filter(models.Report.status == status)
    if category:
        query = query.filter(models.Report.predicted_categories.contains(category))
    
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


# Startup event - check Vision API
@app.on_event("startup")
async def startup_event():
    """Check Vision API on startup"""
    try:
        client = get_vision_client()
        print("[OK] Google Vision API connected successfully")
    except Exception as e:
        print(f"[WARN] Google Vision API connection failed: {e}")
        print("[INFO] Reports with images will fallback to NLP-only analysis")
