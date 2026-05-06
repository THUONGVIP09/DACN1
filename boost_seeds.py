"""
Script bổ sung seed data cho 2 nhãn yếu:
  - Tai nạn giao thông
  - Chướng ngại vật & Sự cố bất ngờ
và re-train model với cấu hình tốt hơn.
"""

import json

SEED_FILE = "seed_data.json"

NEW_SEEDS = [
    # ── Tai nạn giao thông (15 mẫu đa dạng) ────────────────
    {"text": "Tai nạn nghiêm trọng trên đường Điện Biên Phủ, xe tải húc ngã xe máy, 1 người bất tỉnh.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Vừa chứng kiến vụ va chạm giữa 2 xe máy ở ngã tư Phú Nhuận, có người bị thương đang nằm giữa đường.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Xe container lật ngang trên quốc lộ 1A đoạn qua Bình Dương, chắn cả 2 chiều đường.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Ô tô con tông dải phân cách trên cầu Thủ Thiêm, kính vỡ văng đầy đường, lái xe có vẻ bị chấn thương.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Có vụ tai nạn ở đầu đường Phan Xích Long, xe máy ngã nhiều, giao thông ùn ứ từ đây.", "category": ["Tai nạn giao thông", "Ùn tắc giao thông"], "priority": 2},
    {"text": "2 xe máy đụng nhau trước cổng trường THPT Lê Quý Đôn, 1 em học sinh bị gãy chân.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Ô tô tông xe đạp điện ở đường Nguyễn Xí, người đi xe đạp văng ra giữa lòng đường.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Va chạm liên hoàn giữa 3 xe máy tại đường Hoàng Diệu 2 lúc tan tầm.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Xe khách mất phanh đâm vào ta luy đường Đèo Bảo Lộc, nhiều hành khách bị thương.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Ngã xe do né ổ gà trên đường Trần Xuân Soạn, đầu gối chảy máu, không ai dừng lại giúp.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Tai nạn xảy ra lúc 7 giờ sáng ở cổng KCN Tân Bình, xe máy va chạm xe ba gác.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Chứng kiến xe ô tô vượt đèn đỏ đâm thẳng vào bên hông xe buýt, có người bị thương.", "category": ["Tai nạn giao thông"], "priority": 2},
    {"text": "Va quẹt nhỏ ở hẻm Trần Não nhưng 2 bên cự cãi chắn đường không cho xe khác qua.", "category": ["Tai nạn giao thông"], "priority": 1},
    {"text": "Sáng nay có vụ xe tải cuốn xe máy vào gầm ở nút giao Bình Thái, kẹt xe rất nghiêm trọng.", "category": ["Tai nạn giao thông", "Ùn tắc giao thông"], "priority": 2},
    {"text": "Người đi bộ bị xe máy tông khi sang đường tại vạch kẻ đường đường Nguyễn Thị Minh Khai.", "category": ["Tai nạn giao thông"], "priority": 2},

    # ── Chướng ngại vật & Sự cố bất ngờ (15 mẫu đa dạng) ──
    {"text": "Cây to đổ chắn ngang đường Nguyễn Trãi do bão, ai đi qua nguy hiểm lắm.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Hố ga không có nắp trên đường Trần Hưng Đạo đêm nay, xe máy có thể lọt bánh vào bất cứ lúc nào.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Xe chở sắt thép rơi vãi đầy đường Xa lộ Hà Nội, nhiều xe phải đi tránh rất nguy hiểm.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Phát hiện đinh tặc rải dày ở đoạn đường Kinh Dương Vương gần cây xăng, sáng nay nhiều xe bị xẹp lốp.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Dầu nhớt đổ tràn ra mặt đường đường Phạm Văn Đồng, trơn trượt cực kỳ nguy hiểm.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Cột điện bị xe tải húc đổ ngang đường Hoàng Văn Thụ, dây điện cháy sáng rất nguy hiểm.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Xe container đứt thùng rơi đống hàng hóa giữa đường cao tốc TP.HCM - Long Thành, giao thông tê liệt.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Đống xà bần đổ trộm chiếm hết nửa lòng đường Bùi Thị Xuân từ tối qua, rất cản trở lưu thông.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 1},
    {"text": "Cây xanh mới trồng bật gốc đổ ra đường Lê Văn Sỹ sau cơn mưa, chưa có ai dọn.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Đoạn đường ngập sâu do vỡ ống cấp nước tại đường Đinh Tiên Hoàng, nước xì mạnh như vòi cứu hỏa.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Mảng bê tông cầu vượt bị bong tróc rơi xuống lòng đường Nguyễn Hữu Cảnh rất nguy hiểm.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Tôi vừa thấy cuộn cáp quang đứt thõng xuống giữa đường Võ Văn Ngân, xe máy cao rất dễ bị vướng.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Xe bồn chở hóa chất bị lật tại cầu Bình Triệu, có mùi hóa chất bốc lên rất khó chịu.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
    {"text": "Mảnh vỡ kính từ một vụ tai nạn chưa được dọn trên đường Lê Lai, bánh xe dễ bị thủng.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 1},
    {"text": "Sáng sớm ai đó đổ cát trộm xuống giữa đường hẻm Bà Hạt, người đi xe máy trơn bánh ngã liên tiếp.", "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": 2},
]

def main():
    with open(SEED_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    original_count = len(data)
    data.extend(NEW_SEEDS)
    
    with open(SEED_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Đã bổ sung {len(NEW_SEEDS)} mẫu seed mới.")
    print(f"     Seed data: {original_count} -> {len(data)} mẫu.")

if __name__ == "__main__":
    main()
