import json
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
import warnings

# Tắt cảnh báo zero_division
warnings.filterwarnings('ignore')

INPUT_FILE = "preprocessed_dataset.json"
MODELS_DIR = Path("models")

def main():
    print("=" * 65)
    print("  Training Multi-Label Text Classifier (TF-IDF + LinearSVC)")
    print("=" * 65)
    
    # 1. Đọc dữ liệu
    print(f"[1] Load dữ liệu từ {INPUT_FILE} ...")
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        
    texts = [item.get("clean_text", "") for item in data]
    categories = [item.get("category", []) for item in data]
    
    # 2. Mã hóa Nhãn (Multi-Label Binarizer)
    print("\n[2] Mã hóa 8 Master Categories ...")
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(categories)
    
    for c in mlb.classes_:
        print(f"    - {c}")
        
    # 3. Trích xuất đặc trưng văn bản bằng TF-IDF
    # Sử dụng ngram_range=(1,2) để bắt cả các cụm từ như "kẹt xe", "ngập nước"
    print("\n[3] Xây dựng ma trận TF-IDF ...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    X = vectorizer.fit_transform(texts)
    
    # 4. Chia tập Train/Test (Tỷ lệ 80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"    Tập Training : {X_train.shape[0]} mẫu")
    print(f"    Tập Testing  : {X_test.shape[0]} mẫu")
    print(f"    Số chiều TF-IDF: {X_train.shape[1]}")
    
    # 5. Huấn luyện mô hình (One-vs-Rest với LinearSVC)
    # Rất phù hợp và cực nhanh cho văn bản
    print("\n[4] Đang huấn luyện LinearSVC ...")
    model = OneVsRestClassifier(LinearSVC(random_state=42, class_weight='balanced', max_iter=2000))
    model.fit(X_train, y_train)
    
    # 6. Đánh giá mô hình
    print("\n[5] Kết quả đánh giá trên tập Test (Classification Report):")
    predictions = model.predict(X_test)
    
    report = classification_report(y_test, predictions, target_names=mlb.classes_, zero_division=0)
    print(report)
    
    # 7. Lưu mô hình để tái sử dụng
    print("\n[6] Đang lưu models...")
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(vectorizer, MODELS_DIR / "tfidf_vectorizer.pkl")
    joblib.dump(mlb, MODELS_DIR / "label_binarizer.pkl")
    joblib.dump(model, MODELS_DIR / "traffic_classifier.pkl")
    
    print(f"    Đã lưu toàn bộ model vào thư mục '{MODELS_DIR}/'")
    print("=" * 65)

if __name__ == "__main__":
    main()
