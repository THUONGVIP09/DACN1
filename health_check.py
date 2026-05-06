import json
import re
import sys
import joblib
from pyvi import ViTokenizer

SEPARATOR = "=" * 60

def check_pass(label):
    print(f"  ✓ {label}")

def check_fail(label, reason=""):
    print(f"  ✗ {label} | {reason}")
    
def section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)

errors = []

# ──────────────────────────────────────────────────
# CHECK 1: Dữ liệu Augmented
# ──────────────────────────────────────────────────
section("CHECK 1: augmented_dataset.json")
try:
    with open("augmented_dataset.json", "r", encoding="utf-8-sig") as f:
        aug = json.load(f)
    
    cats = {}
    for item in aug:
        for c in item.get("category", []):
            cats[c] = cats.get(c, 0) + 1
    
    EXPECTED_CATS = {
        "Ùn tắc giao thông", "Tai nạn giao thông", "Ngập nước / Triều cường",
        "Sự cố hạ tầng & Đèn tín hiệu", "Chướng ngại vật & Sự cố bất ngờ",
        "Công trình thi công / Lô cốt", "Lấn chiếm vỉa hè & Lòng đường",
        "Vi phạm & Ý thức giao thông"
    }
    
    check_pass(f"Tải thành công | Tổng mẫu: {len(aug)}")
    
    missing_cats = EXPECTED_CATS - set(cats.keys())
    if missing_cats:
        check_fail(f"Thiếu nhãn: {missing_cats}")
        errors.append("missing_categories")
    else:
        check_pass("Đủ 8 Master Categories")
    
    for k, v in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {k:<50}: {v} mẫu")
    
    mising_text = sum(1 for i in aug if not i.get("text"))
    if mising_text:
        check_fail(f"Có {mising_text} mẫu thiếu trường 'text'")
        errors.append("missing_text_aug")
    else:
        check_pass("Mọi mẫu đều có trường 'text'")
        
except Exception as e:
    check_fail("Đọc file thất bại", str(e))
    errors.append("aug_load_fail")

# ──────────────────────────────────────────────────
# CHECK 2: Dữ liệu đã tiền xử lý
# ──────────────────────────────────────────────────
section("CHECK 2: preprocessed_dataset.json")
try:
    with open("preprocessed_dataset.json", "r", encoding="utf-8-sig") as f:
        pre = json.load(f)
    
    check_pass(f"Tải thành công | Tổng mẫu: {len(pre)}")
    
    missing_clean = sum(1 for i in pre if not i.get("clean_text"))
    if missing_clean:
        check_fail(f"Có {missing_clean} mẫu thiếu 'clean_text'")
        errors.append("missing_clean_text")
    else:
        check_pass("Mọi mẫu đều có 'clean_text'")
    
    sample = pre[0]
    print(f"    Ví dụ mẫu đầu tiên:")
    print(f"      raw : {sample.get('text','')[:60]}...")
    print(f"      clean: {sample.get('clean_text','')[:60]}...")
    
except Exception as e:
    check_fail("Đọc file thất bại", str(e))
    errors.append("pre_load_fail")

# ──────────────────────────────────────────────────
# CHECK 3: ML Models
# ──────────────────────────────────────────────────
section("CHECK 3: Models (TF-IDF + LinearSVC)")
try:
    vec = joblib.load("models/tfidf_vectorizer.pkl")
    mlb = joblib.load("models/label_binarizer.pkl")
    clf = joblib.load("models/traffic_classifier.pkl")
    
    check_pass(f"Nạp models thành công")
    check_pass(f"TF-IDF Vocab size: {len(vec.vocabulary_)} từ")
    check_pass(f"Nhãn ({len(mlb.classes_)}): {list(mlb.classes_)}")
    
except Exception as e:
    check_fail("Nạp models thất bại", str(e))
    errors.append("model_load_fail")

# ──────────────────────────────────────────────────
# CHECK 4: Prediction Sanity Test
# ──────────────────────────────────────────────────
section("CHECK 4: Prediction Test (5 câu mẫu thực tế)")
test_cases = [
    ("Tai nạn nghiêm trọng trên đường Điện Biên Phủ, xe tải húc ngã xe máy.", "Tai nạn giao thông"),
    ("Kẹt xe từ vòng xoay Lăng Cha Cả kéo dài đến sân bay Tân Sơn Nhất.", "Ùn tắc giao thông"),
    ("Cây to đổ chắn ngang đường Nguyễn Trãi do bão, ai đi qua nguy hiểm.", "Chướng ngại vật & Sự cố bất ngờ"),
    ("Lô cốt thi công chiếm đường Lê Lợi không có rào chắn cảnh báo.", "Công trình thi công / Lô cốt"),
    ("Nước ngập đến đầu gối ở quận 8, triều cường dâng cao đột ngột.", "Ngập nước / Triều cường"),
]

all_pass = True
for text, expected in test_cases:
    try:
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower()).strip()
        tok = ViTokenizer.tokenize(cleaned)
        X = vec.transform([tok])
        pred = clf.predict(X)
        labels = list(mlb.inverse_transform(pred)[0])
        ok = expected in labels
        if not ok:
            all_pass = False
            errors.append(f"predict_fail_{expected}")
        mark = "✓" if ok else "✗"
        print(f"  [{mark}] {text[:50]}...")
        print(f"       Dự đoán: {labels} | Kỳ vọng có: '{expected}'")
    except Exception as e:
        check_fail(f"Lỗi predict: {text[:30]}", str(e))
        errors.append("predict_error")
        all_pass = False

if all_pass:
    check_pass("TẤT CẢ 5 TEST CASES PASSED")

# ──────────────────────────────────────────────────
# CHECK 5: API (Database + FastAPI)
# ──────────────────────────────────────────────────
section("CHECK 5: API & Database")
try:
    import requests
    
    # Test GET endpoint
    r_get = requests.get("http://localhost:8000/reports/", timeout=5)
    check_pass(f"GET /reports/ -> HTTP {r_get.status_code} OK | {len(r_get.json())} bản ghi trong DB")
    
    # Test POST endpoint với câu mẫu mới
    payload = {"text": "Hố ga không nắp trên đường Trần Hưng Đạo đêm nay, xe máy có thể lọt bánh vào."}
    r_post = requests.post("http://localhost:8000/reports/", json=payload, timeout=5)
    if r_post.status_code == 200:
        result = r_post.json()
        check_pass(f"POST /reports/ -> HTTP 200 OK")
        check_pass(f"  Nhãn AI: '{result['predicted_categories']}'")
        check_pass(f"  Địa điểm: '{result['extracted_locations']}'")
        check_pass(f"  Thời gian: '{result['extracted_times']}'")
        check_pass(f"  Trạng thái: '{result['status']}'")
    else:
        check_fail(f"POST /reports/ thất bại | HTTP {r_post.status_code}", r_post.text[:200])
        errors.append("api_post_fail")
        
except requests.exceptions.ConnectionError:
    check_fail("Không kết nối được API", "Uvicorn có đang chạy không?")
    errors.append("api_offline")
except Exception as e:
    check_fail("Lỗi API test", str(e))
    errors.append("api_error")

# ──────────────────────────────────────────────────
# TỔNG KẾT
# ──────────────────────────────────────────────────
section("TỔNG KẾT KIỂM TRA")
if not errors:
    print("  ✅ TOÀN BỘ HỆ THỐNG HOẠT ĐỘNG BÌNH THƯỜNG")
    print("  ✅ SẴN SÀNG CHUYỂN SANG TUẦN 7: FRONTEND")
else:
    print(f"  ❌ Phát hiện {len(errors)} lỗi cần khắc phục:")
    for e in errors:
        print(f"     - {e}")
print(SEPARATOR)
