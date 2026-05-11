"""
Migration script: Convert old compound labels to new atomic labels
in all training datasets.
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Mapping from old compound labels to new atomic labels
LABEL_MIGRATION = {
    "Chướng ngại vật & Sự cố bất ngờ": ["chướng ngại vật"],
    "Công trình thi công / Lô cốt": ["công trình thi công"],
    "Lấn chiếm vỉa hè & Lòng đường": ["lấn chiếm vỉa hè"],
    "Ngập nước / Triều cường": ["ngập nước"],
    "Sự cố hạ tầng & Đèn tín hiệu": ["đèn tín hiệu", "hư hỏng đường xá"],  # Split into 2
    "Tai nạn giao thông": ["tai nạn giao thông"],
    "Vi phạm & Ý thức giao thông": ["ùn tắc giao thông"],  # Merge into closest
    "Ùn tắc giao thông": ["ùn tắc giao thông"],
}

def migrate_file(filepath):
    print(f"\n--- Processing: {filepath} ---")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    total_changed = 0
    for item in data:
        old_cats = item.get('category', [])
        if not old_cats:
            continue
        
        new_cats = []
        changed = False
        for cat in old_cats:
            if cat in LABEL_MIGRATION:
                new_cats.extend(LABEL_MIGRATION[cat])
                if LABEL_MIGRATION[cat] != [cat]:
                    changed = True
            else:
                new_cats.append(cat)
        
        # Deduplicate while preserving order
        seen = set()
        unique_cats = []
        for c in new_cats:
            if c not in seen:
                seen.add(c)
                unique_cats.append(c)
        
        if changed:
            total_changed += 1
        item['category'] = unique_cats
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Verify new labels
    all_labels = set()
    for item in data:
        all_labels.update(item.get('category', []))
    
    print(f"  Total samples: {len(data)}")
    print(f"  Changed: {total_changed}")
    print(f"  Final labels: {sorted(all_labels)}")
    return data

def migrate_seed(filepath):
    """seed_data.json uses 'category' key same as augmented"""
    print(f"\n--- Processing: {filepath} ---")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    total_changed = 0
    for item in data:
        old_cats = item.get('category', [])
        if not old_cats:
            continue
        
        new_cats = []
        changed = False
        for cat in old_cats:
            if cat in LABEL_MIGRATION:
                new_cats.extend(LABEL_MIGRATION[cat])
                if LABEL_MIGRATION[cat] != [cat]:
                    changed = True
            else:
                new_cats.append(cat)
        
        seen = set()
        unique_cats = []
        for c in new_cats:
            if c not in seen:
                seen.add(c)
                unique_cats.append(c)
        
        if changed:
            total_changed += 1
        item['category'] = unique_cats
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    all_labels = set()
    for item in data:
        all_labels.update(item.get('category', []))
    
    print(f"  Total samples: {len(data)}")
    print(f"  Changed: {total_changed}")
    print(f"  Final labels: {sorted(all_labels)}")

if __name__ == "__main__":
    print("=" * 60)
    print("  LABEL MIGRATION: Old Compound -> New Atomic")
    print("=" * 60)
    
    migrate_file("augmented_dataset.json")
    migrate_seed("seed_data.json")
    
    # Also migrate preprocessed_dataset.json (used by train_model.py)
    try:
        migrate_file("preprocessed_dataset.json")
    except Exception as e:
        print(f"  [SKIP] preprocessed_dataset.json: {e}")
    
    print("\n" + "=" * 60)
    print("  MIGRATION COMPLETE!")
    print("=" * 60)
