import json
import re
import multiprocessing
from pyvi import ViTokenizer
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import time

INPUT_FILE = "augmented_dataset.json"
OUTPUT_FILE = "preprocessed_dataset.json"
STOPWORDS_FILE = "stopwords.txt"

# 1. Load Stopwords
try:
    with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
        # Stopwords frequently use '_' instead of spaces for compound words if pyvi tokenizes them
        stopwords = set(line.strip().lower() for line in f if line.strip())
except FileNotFoundError:
    print(f"[Warn] Cannot find {STOPWORDS_FILE}, running without stopwords.")
    stopwords = set()

def clean_text(text: str) -> str:
    """Làm sạch văn bản thô"""
    text = text.lower()
    # Loại bỏ URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Loại bỏ ký tự đặc biệt, dấu câu (chỉ giữ lại chữ cái và số)
    text = re.sub(r'[^\w\s]', ' ', text)
    # Loại bỏ khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_sample(sample: dict) -> dict:
    """Hàm chạy độc lập trên từng luồng (Core) để tiền xử lý 1 mẫu dữ liệu"""
    original_text = sample.get("text", "")
    
    # Bước 1: Làm sạch
    cleaned = clean_text(original_text)
    
    # Bước 2: Tokenize (Tách từ Tiếng Việt bằng pyvi)
    # Ví dụ: "kẹt xe quá" -> "kẹt_xe quá"
    tokenized = ViTokenizer.tokenize(cleaned)
    
    # Bước 3: Loại bỏ Stopwords
    words = tokenized.split()
    filtered_words = [w for w in words if w not in stopwords]
    final_text = " ".join(filtered_words)
    
    # Lưu kết quả vào dict mới
    new_sample = sample.copy()
    new_sample["clean_text"] = final_text
    return new_sample

def main():
    print("=" * 65)
    print("  Data Preprocessing – Xử lý đa luồng (Multi-Processing)")
    print("=" * 65)
    
    start_time = time.time()
    
    # Đọc dữ liệu
    print(f"\n[1] Đọc dữ liệu từ {INPUT_FILE} ...")
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    print(f"    Tổng cộng: {len(data)} mẫu.")
    
    # Lấy số luồng CPU (ví dụ i7-12700H có 20 luồng)
    cpu_cores = multiprocessing.cpu_count()
    print(f"\n[2] Tiền xử lý song song với {cpu_cores} luồng CPU ...")
    
    # Chạy đa luồng bằng ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=cpu_cores) as executor:
        processed_data = list(executor.map(preprocess_sample, data))
        
    # Ghi dữ liệu ra file
    print(f"\n[3] Lưu kết quả vào {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    print(f"\n[4] XONG! Thời gian xử lý: {elapsed:.3f} giây.")
    print("    Dữ liệu đã sẵn sàng để đưa vào Model Học máy.")
    print("=" * 65)

if __name__ == '__main__':
    # Bắt buộc phải có dòng này trên Windows khi dùng multiprocessing
    multiprocessing.freeze_support()
    main()
