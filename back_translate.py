# -*- coding: utf-8 -*-
"""
back_translate.py
=================
Role   : Data Engineer – NLP
Task   : Back-translation augmentation cho các mẫu priority: 2.

Luồng:  Tiếng Việt  ──►  Tiếng Anh  ──►  Tiếng Việt
Thư viện: deep-translator (GoogleTranslator) — pip install deep-translator

Kỹ thuật:
  - Trích xuất tất cả mẫu priority 2 từ augmented_dataset.json.
  - Chọn ngẫu nhiên TARGET_SAMPLES mẫu (phân tầng theo category để cân bằng).
  - Thực hiện back-translation qua GoogleTranslator (không cần API key).
  - Lọc chất lượng: loại kết quả quá giống bản gốc (Jaccard > 0.85) hoặc quá ngắn.
  - Thêm trường 'augmented': True và 'source_method': 'back_translation'.
  - Gộp vào augmented_dataset.json → ghi ra augmented_dataset.json (in-place).

Cài đặt phụ thuộc:
  pip install deep-translator tqdm

Chạy:
  python back_translate.py
"""

import json
import random
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

# ─── Thử import ────────────────────────────────────────────────────────────────
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_BACKEND = "deep_translator"
except ImportError:
    try:
        from googletrans import Translator as _GT
        _gt_instance = _GT()
        class GoogleTranslator:  # shim
            def __init__(self, source, target):
                self._src = source
                self._tgt = target
            def translate(self, text):
                result = _gt_instance.translate(text, src=self._src, dest=self._tgt)
                return result.text
        TRANSLATOR_BACKEND = "googletrans"
    except ImportError:
        raise ImportError(
            "Cần cài đặt thư viện dịch thuật:\n"
            "  pip install deep-translator\n"
            "hoặc:\n"
            "  pip install googletrans==4.0.0-rc1"
        )

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    def tqdm(iterable, **kwargs):
        return iterable

# ─── Cấu hình ─────────────────────────────────────────────────────────────────
INPUT_FILE  = Path("augmented_dataset.json")
OUTPUT_FILE = Path("augmented_dataset.json")   # ghi đè in-place
TARGET_SAMPLES     = 130          # số mẫu muốn back-translate
JACCARD_THRESHOLD  = 0.85         # loại nếu quá giống bản gốc
MIN_WORDS          = 6            # loại câu quá ngắn sau dịch
SLEEP_BETWEEN      = 0.8          # giây nghỉ giữa các lần gọi API (tránh rate-limit)
RANDOM_SEED        = 2025
random.seed(RANDOM_SEED)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r" ([,.!?;:])", r"\1", text)
    return text

def word_count(text: str) -> int:
    return len(text.split())

def bigrams(text: str) -> set:
    tokens = text.lower().split()
    if len(tokens) < 2:
        return set(tokens)
    return {(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)}

def jaccard_similarity(a: str, b: str) -> float:
    sa, sb = bigrams(a), bigrams(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def stratified_sample(records: list, n: int) -> list:
    """Lấy mẫu phân tầng theo category để đảm bảo đa dạng."""
    # Nhóm theo category đầu tiên
    groups: dict[str, list] = {}
    for rec in records:
        key = rec["category"][0] if rec.get("category") else "unknown"
        groups.setdefault(key, []).append(rec)
    
    # Shuffle từng nhóm
    for g in groups.values():
        random.shuffle(g)
    
    # Round-robin từ các nhóm cho đến đủ n
    result = []
    iters = {k: iter(v) for k, v in groups.items()}
    keys = list(groups.keys())
    i = 0
    while len(result) < n and iters:
        k = keys[i % len(keys)]
        try:
            result.append(next(iters[k]))
        except StopIteration:
            keys.remove(k)
            del iters[k]
        else:
            i += 1
    return result[:n]


# ─── Back-translation core ────────────────────────────────────────────────────
def back_translate(text: str, retries: int = 2) -> str | None:
    """
    Dịch: Tiếng Việt → Tiếng Anh → Tiếng Việt.
    Trả về None nếu thất bại hoặc kết quả không hợp lệ.
    """
    for attempt in range(retries + 1):
        try:
            # Vi → En
            en = GoogleTranslator(source="vi", target="en").translate(text)
            time.sleep(SLEEP_BETWEEN / 2)
            # En → Vi
            vi_back = GoogleTranslator(source="en", target="vi").translate(en)
            return normalize_text(vi_back)
        except Exception as e:
            if attempt < retries:
                wait = (attempt + 1) * 2
                print(f"  [warn] Lần {attempt+1} thất bại ({e}). Thử lại sau {wait}s...")
                time.sleep(wait)
            else:
                print(f"  [error] Bỏ qua mẫu sau {retries+1} lần thất bại: {e}")
                return None


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 62)
    print("  Back-Translation Augmentation – Priority 2 Samples")
    print(f"  Backend: {TRANSLATOR_BACKEND}")
    print("=" * 62)

    # Bước 1: Đọc dữ liệu
    print(f"\n[1] Đọc {INPUT_FILE} ...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dataset: list[dict] = json.load(f)
    print(f"    Tổng mẫu hiện có: {len(dataset)}")

    # Bước 2: Trích xuất mẫu priority 2
    p2_samples = [r for r in dataset if r.get("priority") == 2]
    print(f"    Mẫu priority 2: {len(p2_samples)}")
    cat_dist = Counter(c for r in p2_samples for c in r.get("category", []))
    print(f"    Phân phối: {dict(cat_dist.most_common())}")

    # Bước 3: Chọn mẫu phân tầng
    chosen = stratified_sample(p2_samples, TARGET_SAMPLES)
    print(f"\n[2] Chọn {len(chosen)} mẫu để back-translate (stratified) ...")
    chosen_dist = Counter(c for r in chosen for c in r.get("category", []))
    print(f"    Phân phối chosen: {dict(chosen_dist.most_common())}")

    # Bước 4: Back-translate
    print(f"\n[3] Thực hiện back-translation ({TRANSLATOR_BACKEND}) ...")
    augmented: list[dict] = []
    skipped_api  = 0
    skipped_sim  = 0
    skipped_short = 0

    iter_chosen = tqdm(chosen, desc="Back-translating", unit="sample") if HAS_TQDM \
                  else chosen

    for i, rec in enumerate(iter_chosen):
        original_text = rec["text"]
        
        bt_text = back_translate(original_text)
        time.sleep(SLEEP_BETWEEN)

        if bt_text is None:
            skipped_api += 1
            continue

        # Kiểm tra độ dài
        if word_count(bt_text) < MIN_WORDS:
            skipped_short += 1
            continue

        # Kiểm tra độ tương đồng với bản gốc
        sim = jaccard_similarity(original_text, bt_text)
        if sim > JACCARD_THRESHOLD:
            skipped_sim += 1
            continue

        # Tạo bản ghi mới
        new_rec = {
            "text": bt_text,
            "category": list(rec["category"]),  # đảm bảo deep copy
            "priority": rec["priority"],
            "augmented": True,
            "source_method": "back_translation",
            "original_text": original_text,
        }
        augmented.append(new_rec)

        if not HAS_TQDM and (i + 1) % 10 == 0:
            print(f"    [{i+1}/{len(chosen)}] OK: {len(augmented)} mẫu mới")

    print(f"\n    Kết quả:")
    print(f"      Thành công     : {len(augmented)}")
    print(f"      Bỏ qua (API)   : {skipped_api}")
    print(f"      Bỏ qua (ngắn)  : {skipped_short}")
    print(f"      Bỏ qua (giống) : {skipped_sim}")

    # Bước 5: Kiểm tra Multi-label integrity
    print("\n[4] Kiểm tra Multi-label integrity ...")
    for rec in augmented:
        assert isinstance(rec["category"], list), f"category không phải list: {rec}"
        assert len(rec["category"]) >= 1, f"category rỗng: {rec}"
    print(f"    OK – {len(augmented)} mẫu đều có category dạng list hợp lệ.")

    # Bước 6: Gộp và lưu
    print(f"\n[5] Gộp và lưu vào {OUTPUT_FILE} ...")
    final_dataset = dataset + augmented
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)

    print(f"    Trước: {len(dataset):>6} mẫu")
    print(f"    Mới  : {len(augmented):>6} mẫu (back-translation)")
    print(f"    Sau  : {len(final_dataset):>6} mẫu")
    print(f"    File : {OUTPUT_FILE}  ({OUTPUT_FILE.stat().st_size // 1024} KB)")

    # Thống kê cuối
    all_cats = Counter(c for r in final_dataset for c in r.get("category", []))
    print("\n    Phân phối category cuối:")
    for cat, cnt in all_cats.most_common():
        print(f"      {cat:<30s}: {cnt}")
    print("=" * 62)


if __name__ == "__main__":
    main()
