from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from database import Base
import datetime

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    predicted_categories = Column(String(255), nullable=True) # VD: "Ngập nước, Ùn tắc"
    extracted_locations = Column(String(255), nullable=True)
    extracted_times = Column(String(255), nullable=True)
    status = Column(String(50), default="Pending") # Pending, Auto-Approved, Rejected
    
    # Image & Location fields
    image_path = Column(String(255), nullable=True)  # Đường dẫn file ảnh đã upload
    latitude = Column(Float, nullable=True)  # Tọa độ GPS
    longitude = Column(Float, nullable=True)
    
    # AI Confidence scoring
    nlp_confidence = Column(Float, nullable=True)  # Confidence từ text classification
    vision_confidence = Column(Float, nullable=True)  # Confidence từ image analysis
    final_confidence = Column(Float, nullable=True)  # Combined score
    vision_labels = Column(Text, nullable=True)  # JSON string các label từ Vision API
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
