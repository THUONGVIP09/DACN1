import re
import json
from pathlib import Path

# ==========================================
# REGE EXPATTERNS FOR ENTITY EXTRACTION
# ==========================================

# Mẫu Regex cho Thời gian (Times)
# VD: 5h chiều, lúc 18h30, sáng nay, giờ tan tầm, 2 tiếng, 45 phút...
TIME_PATTERNS = [
    r"(?i)(?:lúc\s)?\d{1,2}h(?:\d{1,2})?(?:\s?(?:sáng|trưa|chiều|tối|đêm))?",
    r"(?i)(?:khoảng\s|tầm\s|lúc\s)?\d{1,2}\s?giờ(?:\s\d{1,2}\s?phút)?",
    r"(?i)(?:sáng|trưa|chiều|tối|đêm)\s(?:nay|qua|hôm\squa|sớm)",
    r"(?i)(?:giờ cao điểm|giờ tan tầm|rạng sáng|nửa đêm|sáng sớm)",
    r"(?i)\d{1,2}(?:\,\d)?\s?tiếng",
    r"(?i)\d{1,2}\s?phút"
]

# Mẫu Regex cho Địa điểm (Locations)
# Hệ thống ưu tiên bắt các từ khóa chỉ đường sá, khu vực đô thị
# VD: đường Nguyễn Hữu Cảnh, quận Bình Thạnh, vòng xoay Hàng Xanh, ngã tư...
LOCATION_PREFIXES = r"(?:đường|quận|huyện|phường|xã|đại lộ|tỉnh lộ|quốc lộ|cầu|vòng xoay|ngã tư|ngã ba|nút giao|hầm chui|phố|ngõ|hẻm|kiệt|ngách|khu vực|đoạn|khu)"
LOCATION_PATTERN = fr"(?i){LOCATION_PREFIXES}\s+[A-ZÀ-Ỹa-zà-ỹ0-9\s,]+?(?=\s(?:bị|có|rất|đang|vừa|từ|do|lúc|thì|là|thuộc|đã|\.|\?|!|$))"
# Fallback pattern nếu câu kết thúc luôn bằng địa điểm
LOCATION_PATTERN_FALLBACK = fr"(?i){LOCATION_PREFIXES}\s+[A-ZÀ-Ỹa-zà-ỹ0-9\s,]+"

def extract_entities(text: str) -> dict:
    """
    Trích xuất Thực thể Địa điểm (Location) và Thời gian (Time) từ văn bản tiếng Việt.
    Dùng Regex kết hợp Rule-based (Rất nhẹ, không cần GPU, tốc độ cao).
    """
    entities = {
        "locations": [],
        "times": []
    }
    
    # 1. Trích xuất Thời gian
    for pattern in TIME_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            clean_match = match.strip()
            if clean_match not in entities["times"]:
                entities["times"].append(clean_match)
                
    # 2. Trích xuất Địa điểm
    loc_matches = re.findall(LOCATION_PATTERN, text)
    if not loc_matches:
        # Thử fallback pattern (thường nằm ở cuối câu)
        fallback = re.findall(fr"(?i)({LOCATION_PREFIXES}\s+(?:[A-ZÀ-Ỹa-zà-ỹ0-9,]+\s*){{1,5}})", text)
        loc_matches = fallback

    raw_locations = []
    for match in loc_matches:
        clean_match = match.strip()
        # Loại bỏ các từ thừa đứng đầu/cuối sau khi regex bắt quá đà
        clean_match = re.sub(r'^(?:ở|tại|trên|dưới|trong|ngoài)\s+', '', clean_match, flags=re.IGNORECASE)
        clean_match = re.sub(r'\s+ở\s+đường\s+', ', đường ', clean_match, flags=re.IGNORECASE) # Ghép cụm lặp
        if len(clean_match) > 5:
            raw_locations.append(clean_match)
            
    # Lọc bỏ các thực thể lồng nhau (Sub-segment overlap resolution)
    # Ví dụ: Giữ lại "đường Lê Thiện Trị, phường Hòa Quý" và bỏ "đường Lê Thiện"
    raw_locations.sort(key=len, reverse=True)
    unique_locations = []
    for loc in raw_locations:
        # Kiểm tra xem loc có phải là một phần của bất kỳ địa điểm nào đã được chọn không
        if not any(loc.lower() in other.lower() and loc.lower() != other.lower() for other in unique_locations):
            if loc not in unique_locations:
                unique_locations.append(loc)
                
    entities["locations"] = unique_locations
    return entities

def main():
    print("=" * 60)
    print("  Entity Extraction (NER) - Rule-based & Regex")
    print("=" * 60)
    
    # Test thử trên vài mẫu văn bản
    test_sentences = [
        "Kẹt xe cứng ngắc ở đường Nguyễn Hữu Cảnh lúc 18h30 chiều nay.",
        "Ngập sâu tại quận Bình Thạnh sáng qua, xe chết máy rất nhiều.",
        "Va chạm giữa xe tải và xe máy ở vòng xoay Hàng Xanh lúc rạng sáng.",
        "Lô cốt rào chắn trên đường Phạm Văn Đồng chiếm hết làn xe máy.",
        "Đèn giao thông ngã tư Phú Nhuận bị hỏng từ 5h sáng."
    ]
    
    for idx, sentence in enumerate(test_sentences, 1):
        print(f"\n[Mẫu {idx}] {sentence}")
        entities = extract_entities(sentence)
        print(f"  📍 Địa điểm: {entities['locations']}")
        print(f"  ⏰ Thời gian: {entities['times']}")
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
