import json
import re

LABEL_MAP = {
    "ngập nước": "Ngập nước / Triều cường",
    "kẹt xe": "Ùn tắc giao thông",
    "ùn tắc giao thông": "Ùn tắc giao thông",
    "tai nạn": "Tai nạn giao thông",
    "đèn tín hiệu": "Sự cố hạ tầng & Đèn tín hiệu",
    "hư hỏng hạ tầng": "Sự cố hạ tầng & Đèn tín hiệu",
    "hư hỏng đường xá": "Sự cố hạ tầng & Đèn tín hiệu",
    "cầu": "Sự cố hạ tầng & Đèn tín hiệu",
    "cống rảnh": "Sự cố hạ tầng & Đèn tín hiệu",
    "cơ sở vật chất giao thông": "Sự cố hạ tầng & Đèn tín hiệu",
    "vỉa hè": "Lấn chiếm vỉa hè & Lòng đường",
    "lấn chiếm vỉa hè": "Lấn chiếm vỉa hè & Lòng đường",
    "vi phạm luật": "Vi phạm & Ý thức giao thông",
    "ý thức giao thông": "Vi phạm & Ý thức giao thông",
    "phân làn": "Vi phạm & Ý thức giao thông",
    "vạch kẻ đường": "Sự cố hạ tầng & Đèn tín hiệu",
    "thiếu biển báo": "Sự cố hạ tầng & Đèn tín hiệu",
    "Thiếu biển báo": "Sự cố hạ tầng & Đèn tín hiệu",
    "vật cản": "Chướng ngại vật & Sự cố bất ngờ",
    "cảnh quan đô thị": "Sự cố hạ tầng & Đèn tín hiệu"
}

def clean_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        for item in data:
            new_cats = []
            for c in item.get('category', []):
                mapped = LABEL_MAP.get(c.lower(), LABEL_MAP.get(c, c)) # Fallback if not in map
                if mapped not in new_cats:
                    new_cats.append(mapped)
            item['category'] = new_cats
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Cleaned {filepath}")
    except Exception as e:
        print(f"Error cleaning {filepath}: {e}")

clean_json("seed_data.json")

# 2. Modify generate_synthetic.py
with open("generate_synthetic.py", "r", encoding="utf-8-sig") as f:
    content = f.read()

# Replace category strings in generators
content = content.replace('category": ["ngập nước"]', 'category": ["Ngập nước / Triều cường"]')
content = content.replace('category": ["kẹt xe"]', 'category": ["Ùn tắc giao thông"]')
content = content.replace('category": ["ngập nước", "kẹt xe"]', 'category": ["Ngập nước / Triều cường", "Ùn tắc giao thông"]')
content = content.replace('category": ["tai nạn"]', 'category": ["Tai nạn giao thông"]')
content = content.replace('category": ["đèn tín hiệu"]', 'category": ["Sự cố hạ tầng & Đèn tín hiệu"]')
content = content.replace('category": ["hư hỏng hạ tầng"]', 'category": ["Sự cố hạ tầng & Đèn tín hiệu"]')
content = content.replace('category": ["vỉa hè"]', 'category": ["Lấn chiếm vỉa hè & Lòng đường"]')
content = content.replace('category": ["vi phạm luật"]', 'category": ["Vi phạm & Ý thức giao thông"]')
content = content.replace('category": ["ý thức giao thông"]', 'category": ["Vi phạm & Ý thức giao thông"]')

# Inject new generators
NEW_GENERATORS_CODE = """
def _gen_chuong_ngai_vat() -> dict:
    tpls = [
        lambda: (f"Cây bàng cổ thụ ở {_loc()} vừa bị gió lốc quật ngã chắn ngang đường. Rất may không trúng người đi đường.", 2),
        lambda: (f"Một lượng lớn dầu nhớt đổ lênh láng trên mặt đường {_loc()}, nãy giờ có mấy xe máy bị trượt ngã rồi, nguy hiểm quá!", 2),
        lambda: (f"Xe bồn chở gạch làm rơi vãi đầy đường {_loc()} lúc {random.choice(_TIMES)}. Xe cộ qua lại phải né rất cực.", 2),
        lambda: (f"Ai đó rải đinh ở khu vực {_loc()}, sáng nay tôi thấy hàng loạt xe phải dắt bộ vì lủng lốp. Quá bức xúc!", 2),
        lambda: (f"Một cuộn cáp quang đứt thòng xuống giữa đường {_loc()}, xe tải qua lại vướng vào rất dễ gây tai nạn liên hoàn.", 2),
        lambda: (f"Đống xà bần, rác thải xây dựng bị đổ trộm chiếm nửa lòng đường {_loc()} từ đêm qua. Đề nghị cơ quan chức năng dọn dẹp gấp.", 1),
    ]
    text, priority = random.choice(tpls)()
    return {"text": text, "category": ["Chướng ngại vật & Sự cố bất ngờ"], "priority": priority}

def _gen_cong_trinh() -> dict:
    tpls = [
        lambda: (f"Lô cốt thi công cống hộp ở {_loc()} đào đường lên mà không có rào chắn cứng, chỉ giăng dây thừng mỏng manh. Ban đêm ai không thấy là lọt xuống hố sâu.", 2),
        lambda: (f"Công trình trên đường {_loc()} thi công ban đêm bụi mù mịt, tiếng ồn đinh tai nhức óc không ai ngủ được.", 1),
        lambda: (f"Họ rào đường chiếm hết 2/3 diện tích ở {_loc()} nhưng bỏ không đó mấy tháng trời không thi công. Kẹt xe kéo dài triền miên.", 2),
        lambda: (f"Sắt thép từ công trình xây dựng ở {_loc()} thò ra ngoài đường sát người đi xe máy. Nguy hiểm chết người!", 2),
        lambda: (f"Đơn vị thi công cáp ngầm ở {_loc()} đào đường xong lấp lại bằng cát sơ sài, mưa xuống tạo thành hố bùn trơn trượt.", 2),
        lambda: (f"Đèn cảnh báo của rào chắn thi công ở {_loc()} bị hỏng, tối thui. Tối qua có người đi xe máy đâm thẳng vào rào chắn.", 2),
    ]
    text, priority = random.choice(tpls)()
    return {"text": text, "category": ["Công trình thi công / Lô cốt"], "priority": priority}

def _gen_lan_chiem() -> dict:
    tpls = [
        lambda: (f"Ô tô đỗ trái phép thành hàng dài 2 bên đường {_loc()} khiến xe cứu hỏa không thể tiến vào khu dân cư. Tình trạng này tồn tại quá lâu.", 2),
        lambda: (f"Quán nhậu ở {_loc()} bày bàn ghế ra tận giữa lòng đường. Người đi bộ bị ép phải đi ra làn xe ô tô chạy.", 1),
        lambda: (f"Bãi giữ xe tự phát thu tiền cắt cổ, chiếm trọn vỉa hè {_loc()}. Dân phản ánh mãi mà phường không xuống dẹp.", 1),
        lambda: (f"Xe khách giường nằm đậu đỗ đón khách sai quy định ngay đầu {_loc()} gây cản trở giao thông và mất trật tự đô thị.", 1),
        lambda: (f"Một đống hàng hóa của siêu thị điện máy chất đống trên vỉa hè {_loc()} không chừa một khe hở cho người đi bộ.", 1),
    ]
    text, priority = random.choice(tpls)()
    return {"text": text, "category": ["Lấn chiếm vỉa hè & Lòng đường"], "priority": priority}

"""

if "_gen_chuong_ngai_vat" not in content:
    # Insert new generators before GENERATORS = [
    content = content.replace("GENERATORS = [", NEW_GENERATORS_CODE + "\nGENERATORS = [")

# Rewrite GENERATORS list with new weights
new_generators_list = """GENERATORS = [
    (_gen_ngap_nuoc,   20),
    (_gen_ket_xe,      18),
    (_gen_ngap_ket,    8),
    (_gen_tai_nan,     12),
    (_gen_den_tin_hieu, 6),
    (_gen_ha_tang,      6),
    (_gen_via_he,       6),
    (_gen_vi_pham,      6),
    (_gen_y_thuc,       6),
    (_gen_chuong_ngai_vat, 6),
    (_gen_cong_trinh,      6),
    (_gen_lan_chiem,       6),
]"""

# Replace the block GENERATORS = [...]
content = re.sub(r'GENERATORS = \[\s+.*?\s+\]', new_generators_list, content, flags=re.DOTALL)

with open("generate_synthetic.py", "w", encoding="utf-8-sig") as f:
    f.write(content)

print("Updated generate_synthetic.py with 8 Master Categories and 3 New Generators.")
