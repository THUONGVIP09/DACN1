"""
Google Cloud Vision API Client
Uses REST API with API Key authentication
"""

import os
import base64
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import requests

# Load environment variables from .env file (absolute path)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Google Vision API endpoint
VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"

# Map các nhãn giao thông với Google Vision labels
TRAFFIC_LABEL_MAP = {
    "Ngập nước / Triều cường": ["flood", "water", "submerged", "rain", "storm", "puddle", "wet"],
    "Ùn tắc giao thông": ["traffic jam", "congestion", "traffic", "vehicle", "car", "motorcycle", "street"],
    "Tai nạn giao thông": ["accident", "collision", "crash", "emergency", "ambulance", "damage"],
    "Sự cố hạ tầng & Đèn tín hiệu": ["traffic light", "signal", "infrastructure", "road", "construction"],
    "Chướng ngại vật & Sự cố bất ngờ": ["obstacle", "debris", "tree", "block", "fallen"],
    "Công trình thi công / Lô cốt": ["construction", "roadwork", "barrier", "fence", "work zone"],
    "Lấn chiếm vỉa hè & Lòng đường": ["sidewalk", "encroachment", "vendor", "parking", "street food"],
    "Vi phạm & Ý thức giao thông": ["violation", "illegal", "wrong way", "red light", "helmet"]
}


class VisionAnalyzer:
    """Client phan tich anh voi Google Vision API"""
    
    def __init__(self, key_path: str = None, api_key: str = None):
        """
        Khoi tao Vision client
        Args:
            key_path: Duong dan file service account JSON (optional)
            api_key: Google Vision API key (optional)
        """
        self.key_path = key_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "dacn1-495502-d16408026152.json"
        self.api_key = api_key or os.getenv("GOOGLE_VISION_API_KEY")
        
        # Check if service account JSON exists
        self.creds = None
        if os.path.exists(self.key_path):
            from google.oauth2 import service_account
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    self.key_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                print(f"[AI] Google Vision loaded Service Account from {self.key_path}")
            except Exception as e:
                print(f"[Warning] Failed to load Service Account from {self.key_path}: {e}")
        
        if not self.creds and not self.api_key:
            raise ValueError("Neither Service Account JSON nor GOOGLE_VISION_API_KEY was found")
    
    def analyze_image(self, image_bytes: bytes) -> Dict:
        """
        Phan tich anh va tra ve cac thong tin
        
        Args:
            image_bytes: Noi dung anh dang bytes
            
        Returns:
            Dict chua:
            - labels: List cac nhan phat hien
            - safe_search: Ket qua kiem tra noi dung
            - image_properties: Thuoc tinh anh (do sang, mau sac)
            - text_annotations: Text trong anh (OCR)
            - confidence_score: Diem danh gia chat luong anh (0-1)
        """
        # Encode image to base64
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build request payload
        payload = {
            "requests": [
                {
                    "image": {
                        "content": encoded_image
                    },
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 15},
                        {"type": "SAFE_SEARCH_DETECTION"},
                        {"type": "IMAGE_PROPERTIES"},
                        {"type": "TEXT_DETECTION"}
                    ]
                }
            ]
        }
        
        # Call Vision API
        if self.creds:
            import google.auth.transport.requests
            try:
                auth_req = google.auth.transport.requests.Request()
                self.creds.refresh(auth_req)
                headers = {
                    "Authorization": f"Bearer {self.creds.token}",
                    "Content-Type": "application/json"
                }
                url = VISION_API_URL
                response = requests.post(url, json=payload, headers=headers)
            except Exception as e:
                print(f"[Vision Auth Error] Failed to refresh with Service Account: {e}")
                if self.api_key:
                    url = f"{VISION_API_URL}?key={self.api_key}"
                    response = requests.post(url, json=payload)
                else:
                    raise e
        else:
            url = f"{VISION_API_URL}?key={self.api_key}"
            response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Vision API error: {response.status_code} - {response.text}")
        
        result_data = response.json()
        
        if "responses" not in result_data or not result_data["responses"]:
            raise Exception("No response from Vision API")
        
        response_data = result_data["responses"][0]
        
        # Xu ly ket qua
        result = {
            "labels": self._extract_labels(response_data.get("labelAnnotations", [])),
            "safe_search": self._extract_safe_search(response_data.get("safeSearchAnnotation", {})),
            "image_quality": self._assess_image_quality(response_data.get("imagePropertiesAnnotation", {})),
            "detected_text": self._extract_text(response_data.get("textAnnotations", [])),
            "confidence_score": 0.0
        }
        
        # Tinh diem chat luong anh tong the
        result["confidence_score"] = self._calculate_quality_score(result)
        
        return result
    
    def match_with_category(self, vision_result: Dict, category: str) -> Tuple[float, List[str]]:
        """
        So sánh kết quả Vision với category NLP để tính độ khớp
        
        Args:
            vision_result: Kết quả từ analyze_image()
            category: Category từ NLP (1 trong 8 Master Categories)
            
        Returns:
            Tuple: (match_score 0-1, matched_labels)
        """
        if category not in TRAFFIC_LABEL_MAP:
            return 0.0, []
        
        category_keywords = TRAFFIC_LABEL_MAP[category]
        detected_labels = [label.lower() for label in vision_result["labels"]]
        
        matched = []
        for keyword in category_keywords:
            for label in detected_labels:
                if keyword in label or label in keyword:
                    matched.append(label)
                    break
        
        # Tính điểm: số từ khớp / tổng số từ khóa của category
        score = len(matched) / len(category_keywords) if category_keywords else 0
        score = min(score * 2, 1.0)  # Scale up nhưng cap ở 1.0
        
        return score, list(set(matched))
    
    def calculate_combined_confidence(
        self, 
        nlp_category: str, 
        nlp_confidence: float,
        vision_result: Dict
    ) -> Dict:
        """
        Kết hợp NLP và Vision để tính confidence cuối cùng
        
        Args:
            nlp_category: Category từ NLP classifier
            nlp_confidence: Confidence score từ NLP (0-1)
            vision_result: Kết quả phân tích ảnh
            
        Returns:
            Dict: {
                "final_score": float 0-1,
                "nlp_score": float,
                "vision_score": float,
                "match_verdict": str,
                "auto_approve": bool
            }
        """
        # Vision match score
        vision_match, matched_labels = self.match_with_category(vision_result, nlp_category)
        vision_quality = vision_result["confidence_score"]
        
        # Vision score = match * quality
        vision_score = vision_match * vision_quality
        
        # Combined score: weighted average
        final_score = (nlp_confidence * 0.6) + (vision_score * 0.4)
        
        # Verdict
        if final_score >= 0.85:
            verdict = "High confidence - Auto approve"
            auto_approve = True
        elif final_score >= 0.6:
            verdict = "Medium confidence - Quick review"
            auto_approve = False
        else:
            verdict = "Low confidence - Manual review required"
            auto_approve = False
        
        return {
            "final_score": round(final_score, 3),
            "nlp_score": round(nlp_confidence, 3),
            "vision_score": round(vision_score, 3),
            "vision_match_score": round(vision_match, 3),
            "matched_labels": matched_labels,
            "match_verdict": verdict,
            "auto_approve": auto_approve
        }
    
    def _extract_labels(self, annotations) -> List[str]:
        """Trich xuat danh sach label tu annotation"""
        if not annotations:
            return []
        return [annotation.get("description", "") for annotation in annotations]
    
    def _extract_safe_search(self, annotation) -> Dict:
        """Trich xuat safe search results"""
        if not annotation:
            return {}
        
        return {
            "adult": annotation.get("adult", "UNKNOWN"),
            "violence": annotation.get("violence", "UNKNOWN"),
            "racy": annotation.get("racy", "UNKNOWN"),
            "spoof": annotation.get("spoof", "UNKNOWN"),
            "medical": annotation.get("medical", "UNKNOWN")
        }
    
    def _assess_image_quality(self, annotation) -> Dict:
        """Danh gia chat luong anh"""
        if not annotation:
            return {"brightness": 0.5, "color_count": 0}
        
        # Lay dominant colors de danh gia do sang
        colors = annotation.get("dominantColors", {}).get("colors", [])
        
        # Danh gia do sang (don gian hoa)
        brightness = 0.5
        if colors:
            # Tinh do sang trung binh tu RGB
            total_brightness = sum(
                (color.get("color", {}).get("red", 0) + 
                 color.get("color", {}).get("green", 0) + 
                 color.get("color", {}).get("blue", 0)) / 3 
                for color in colors
            ) / len(colors) / 255
            brightness = total_brightness
        
        return {
            "brightness": round(brightness, 3),
            "color_count": len(colors),
            "is_blurry": brightness < 0.1,
            "is_bright": brightness > 0.7
        }
    
    def _extract_text(self, annotations) -> str:
        """Trich xuat text tu anh (OCR)"""
        if not annotations:
            return ""
        # annotation[0] la toan bo text, con lai la tung tu
        return annotations[0].get("description", "") if annotations else ""
    
    def _calculate_quality_score(self, result: Dict) -> float:
        """Tính điểm chất lượng tổng thể của ảnh"""
        score = 1.0
        
        # Giảm điểm nếu ảnh tối
        if result["image_quality"].get("is_blurry"):
            score -= 0.3
        
        # Giảm điểm nếu có nội dung không phù hợp
        safe = result["safe_search"]
        if safe.get("adult") in ["LIKELY", "VERY_LIKELY"]:
            score -= 0.5
        if safe.get("violence") in ["LIKELY", "VERY_LIKELY"]:
            score -= 0.3
        
        return max(score, 0.0)


# Singleton instance để tái sử dụng
_vision_client = None

def get_vision_client() -> VisionAnalyzer:
    """Lấy instance VisionAnalyzer (singleton)"""
    global _vision_client
    if _vision_client is None:
        _vision_client = VisionAnalyzer()
    return _vision_client


if __name__ == "__main__":
    # Test script
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vision_client.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        client = get_vision_client()
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        result = client.analyze_image(image_bytes)
        
        print("=" * 60)
        print("GOOGLE VISION ANALYSIS RESULT")
        print("=" * 60)
        print(f"\nDetected Labels: {result['labels'][:10]}")
        print(f"Image Quality: {result['image_quality']}")
        print(f"Safe Search: {result['safe_search']}")
        print(f"Quality Score: {result['confidence_score']}")
        print(f"\nDetected Text (OCR): {result['detected_text'][:200]}...")
        
        # Test match với category
        test_cats = ["Ngập nước / Triều cường", "Ùn tắc giao thông"]
        for cat in test_cats:
            score, labels = client.match_with_category(result, cat)
            print(f"\nMatch with '{cat}': {score:.2f} (labels: {labels})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
