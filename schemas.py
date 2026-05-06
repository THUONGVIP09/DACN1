from pydantic import BaseModel
from typing import Optional, List
import datetime

class ReportCreate(BaseModel):
    text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None

class ReportResponse(BaseModel):
    id: int
    raw_text: str
    predicted_categories: Optional[str]
    extracted_locations: Optional[str]
    extracted_times: Optional[str]
    status: str
    
    # Image & Location
    image_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # AI Scoring
    nlp_confidence: Optional[float] = None
    vision_confidence: Optional[float] = None
    final_confidence: Optional[float] = None
    vision_labels: Optional[str] = None
    
    # Reporter details
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    
    # Resolver actual processing details
    resolver_notes: Optional[str] = None
    resolved_at: Optional[datetime.datetime] = None
    
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class VisionAnalysisResult(BaseModel):
    """Schema cho kết quả phân tích ảnh"""
    labels: List[str]
    safe_search: dict
    image_quality: dict
    detected_text: str
    confidence_score: float

class CombinedAnalysisResponse(BaseModel):
    """Schema cho kết quả phân tích kết hợp NLP + Vision"""
    report_id: int
    nlp_category: str
    nlp_confidence: float
    vision_analysis: VisionAnalysisResult
    match_result: dict
    final_confidence: float
    auto_approve: bool
    status: str


# Authentication schemas
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: Optional[str] = None
    department: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

