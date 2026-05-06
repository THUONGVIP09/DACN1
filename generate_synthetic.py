# -*- coding: utf-8 -*-
"""
generate_synthetic.py
=====================
Role   : Data Engineer – NLP
Task   : Sinh 60 % Synthetic Data chất lượng cao từ seed_data.json (20 % Real Data).

Kỹ thuật sử dụng:
  - Paraphrasing   : Viết lại câu từ các template đa dạng, có slang và cảm thán.
  - Entity Swapping: Thay thế địa danh / thời gian ngẫu nhiên.

Output:
  - augmented_dataset.json  (seed + synthetic đã lọc)
"""

import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

# ─── Cấu hình ────────────────────────────────────────────────────────────────
SEED_FILE   = Path("seed_data.json")
OUTPUT_FILE = Path("augmented_dataset.json")
TARGET_NEW_SAMPLES = 520
SIMILARITY_THRESHOLD = 0.80
MIN_WORD_COUNT = 5
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ─── 50 + Địa danh TP.HCM & Hà Nội ──────────────────────────────────────────
LOCATIONS = [
    # TP.HCM – Quận / Khu vực
    "quận Bình Thạnh", "quận Gò Vấp", "quận Tân Bình", "quận 12",
    "quận Thủ Đức", "quận Bình Tân", "quận 8", "quận 6",
    "quận 4", "quận 7", "huyện Bình Chánh", "huyện Nhà Bè",
    # TP.HCM – Tên đường / Vòng xoay / Cầu
    "đường Nguyễn Hữu Cảnh", "đường Ung Văn Khiêm", "đường Phan Văn Trị",
    "đường Lê Văn Thọ", "đường Phú Thuận", "đường Kha Vạn Cân",
    "đường Nguyễn Văn Linh", "đường Huỳnh Tấn Phát", "đường Tô Ngọc Vân",
    "đường D1 Bình Thạnh", "đường Lê Đức Thọ", "đường Quang Trung GV",
    "vòng xoay Hàng Xanh", "vòng xoay Lăng Cha Cả", "vòng xoay Phú Lâm",
    "ngã tư Bình Phước", "ngã tư An Sương", "cầu Bình Lợi",
    "cầu Thủ Thiêm", "cầu Phú Mỹ", "nút giao Cát Lái",
    # Hà Nội – Quận / Khu vực
    "quận Hà Đông", "quận Cầu Giấy", "quận Đống Đa", "quận Long Biên",
    "quận Hoàng Mai", "quận Nam Từ Liêm", "quận Bắc Từ Liêm", "quận Thanh Xuân",
    "huyện Hoài Đức", "huyện Đan Phượng",
    # Hà Nội – Tên đường / Vòng xoay / Cầu
    "đường Mỹ Đình", "phố Huế", "đường Nguyễn Trãi", "đường Giải Phóng",
    "đường Khuất Duy Tiến", "đường Lê Văn Lương", "đường Tố Hữu",
    "đường Phạm Hùng", "đường Nguyễn Xiển", "đường Trần Duy Hưng",
    "đường Dương Nội", "đường Hoàng Quốc Việt",
    "vòng xoay Ngã Tư Sở", "vòng xoay Mỹ Đình", "nút giao Cổ Linh",
    "cầu Vĩnh Tuy", "cầu Thanh Trì", "cầu Nhật Tân",
    "đường Linh Đàm", "đường Lĩnh Nam",
]

# ─── Từ điển thời gian ────────────────────────────────────────────────────────
TIMES = [
    "sáng sớm", "rạng sáng", "lúc 5h sáng", "tầm 6h", "giờ tan tầm",
    "giờ cao điểm chiều", "tối qua", "đêm qua", "nửa đêm", "lúc 22h",
    "khoảng 17h", "lúc 18h30", "chiều hôm qua", "trưa nay",
    "ngày hôm qua", "hai ngày trước", "suốt cả tuần nay",
    "mỗi khi mưa lớn", "liên tục mấy ngày nay",
]

# ─── Phương tiện ─────────────────────────────────────────────────────────────
VEHICLES = ["xe máy", "ô tô", "xe buýt", "xe tải", "xe container", "xe đạp điện"]

# ─── Từ cảm thán / Slang ─────────────────────────────────────────────────────
EXCLAMATIONS = [
    "Trời ơi!", "Ôi thôi rồi!", "Khổ quá!", "Chịu không nổi rồi!",
    "Thiệt hết sức!", "Mệt lắm ơi!", "Không chịu được nữa!",
    "Kinh khủng thiệt!", "Ghê quá!", "Thôi chết rồi!",
    "Bép xép kiểu này mà đi học sao kịp?", "Ăn không ngon ngủ không yên!",
]

SLANG_INTENSIFIERS = [
    "thiệt sự", "quá trời quá đất", "kinh khủng", "ác liệt",
    "khủng khiếp", "bá cháy", "hết nói nổi", "đừng hỏi",
    "không đỡ nổi", "cùng cực",
]

# ═══════════════════════════════════════════════════════════════════════════════
#  TEMPLATE BANK  (Paraphrasing templates cho từng category)
# ═══════════════════════════════════════════════════════════════════════════════

def _loc() -> str:
    return random.choice(LOCATIONS)

def _time() -> str:
    return random.choice(TIMES)

def _veh() -> str:
    return random.choice(VEHICLES)

def _exc() -> str:
    return random.choice(EXCLAMATIONS)

def _slang() -> str:
    return random.choice(SLANG_INTENSIFIERS)


# ── Ngập nước ─────────────────────────────────────────────────────────────────
def _gen_ngap_nuoc() -> dict:
    templates = [
        lambda: (
            f"Nước ngập {_loc()} {_time()}, xe chết máy la liệt, người dắt bộ đầy đường. "
            f"{_exc()} Không biết chính quyền có thấy không nữa.",
            2
        ),
        lambda: (
            f"Lại ngập rồi! {_loc()} hễ mưa là ngập, năm này qua năm khác không thay đổi. "
            f"Bà con {_slang()} khổ.",
            2
        ),
        lambda: (
            f"Mưa chưa tới 20 phút mà {_loc()} đã ngập ngang bánh xe. "
            f"Đi làm trễ mấy tiếng đồng hồ, căng thẳng {_slang()}.",
            1
        ),
        lambda: (
            f"Triều cường {_time()} dâng cao bất ngờ ở {_loc()}, "
            f"nước tràn vào nhà dân, đồ đạc hư hỏng hết. Khổ {_slang()}.",
            2
        ),
        lambda: (
            f"Úi trời, {_loc()} ngập sâu tới {random.choice(['ngang gối', 'ngang đùi', 'qua lưng xe'])}. "
            f"Xe {_veh()} chết máy hàng loạt {_time()}.",
            2
        ),
        lambda: (
            f"Cả xóm tôi ở {_loc()} ngày nào mưa lớn là ngập. "
            f"Đồ điện tử kê lên cao hết rồi mà nước vẫn chạm tới, {_exc()}",
            2
        ),
        lambda: (
            f"Ngập {_slang()} ở {_loc()}, xe {_veh()} bơi lội còn không xong. "
            f"Ai dám mang xe ra {_time()} nữa?",
            2
        ),
        lambda: (
            f"Mấy tháng nay {_loc()} ngập hoài, tôi đã bỏ xe ở nhà đi bộ qua đoạn ngập "
            f"rồi mới đặt xe. Bao giờ mới hết cảnh này?",
            1
        ),
        lambda: (
            f"{_exc()} Nước ngập tới cửa sổ nhà tôi ở {_loc()}, "
            f"lần này là tệ nhất trong mấy năm nay. Không kịp chạy ra hết.",
            2
        ),
        lambda: (
            f"Đang chạy {_veh()} trên {_loc()} thì nước dâng nhanh quá không kịp tránh. "
            f"Xe chết máy giữa đường, đứng dầm nước hơn {random.choice(['1 tiếng', '2 tiếng', '3 tiếng'])} mới có người kéo vào.",
            2
        ),
        lambda: (
            f"Con đường {_loc()} thuộc loại ngập 'truyền thống', mưa nhỏ cũng ngập, "
            f"mưa lớn thì khỏi nói. Dân ở đây quen rồi nhưng mà khổ vẫn khổ.",
            1
        ),
        lambda: (
            f"Cứ {_time()} là {_loc()} lại biến thành sông. Người đi bộ đội nón lội nước, "
            f"{_veh()} chào thua hết. {_exc()}",
            1
        ),
        lambda: (
            f"Nhà tôi gần {_loc()}, mỗi lần ngập là thiệt hại đủ thứ. "
            f"Máy bơm chạy suốt mà nước vẫn vô. Năm nay ngập {_slang()} luôn.",
            2
        ),
        lambda: (
            f"Trẻ con ở khu {_loc()} không thể đến trường được vì đường ngập sâu. "
            f"Bố mẹ lo lắm, không biết phải làm sao.",
            2
        ),
        lambda: (
            f"Cống thoát nước {_loc()} bị tắc lâu rồi, mỗi lần mưa là nước không đi đâu được, "
            f"dềnh lên hết mặt đường. Phản ánh mãi không ai xử lý.",
            1
        ),
        lambda: (
            f"Tôi sống ở {_loc()} gần {random.choice(['5 năm', '10 năm', '15 năm', '20 năm'])} nay, "
            f"ngập riết quen rồi nhưng mỗi lần vẫn mệt. Đồ đạc hỏng liên tục.",
            1
        ),
        lambda: (
            f"{_time()} nước bắt đầu dâng ở {_loc()}, đến khi tôi thức dậy thì nước đã ngang sàn nhà rồi. "
            f"Không kịp chạy đồ gì cả.",
            2
        ),
        lambda: (
            f"Khâu thoát nước ở {_loc()} quá kém, đầu tư bao nhiêu năm mà cứ mưa là ngập. "
            f"Tiền thuế dân đóng mà xài kiểu này?",
            1
        ),
        lambda: (
            f"Gia đình tôi đã di chuyển đồ đạc lên cao lần thứ {random.choice(['3', '4', '5'])} trong năm nay "
            f"vì triều cường ở {_loc()}. Kiệt sức rồi thật.",
            2
        ),
        lambda: (
            f"Đường {_loc()} ngập sâu, xe {_veh()} chết máy hàng loạt, người dắt bộ hai hàng dài. "
            f"Cảnh tượng {_slang()} mà buồn.",
            2
        ),
        lambda: (
            f"Hễ coi dự báo thời tiết thấy có mưa lớn là dân {_loc()} ai cũng lo. "
            f"Vì biết chắc kiểu gì cũng ngập.",
            1
        ),
        lambda: (
            f"{_exc()} {_loc()} ngập rồi! Ai đang di chuyển qua đây thì tìm đường khác đi nhé. "
            f"Nước sâu tới {random.choice(['30cm', '40cm', '50cm', '60cm'])} rồi.",
            2
        ),
        lambda: (
            f"Mưa {_time()} ở {_loc()}, tôi không dám cho con đi học vì đường ngập quá nguy hiểm. "
            f"Cả buổi sáng bị kẹt ở nhà.",
            1
        ),
        lambda: (
            f"Nước rút chậm kinh khủng ở {_loc()}, ngập từ {_time()} tới tận chiều mới rút bớt. "
            f"Nhà cửa ẩm thấp, đồ đạc bốc mùi hết.",
            2
        ),
        lambda: (
            f"Khu {_loc()} bị cô lập hoàn toàn vì nước ngập, không xe cứu thương nào vào được. "
            f"Nguy hiểm {_slang()} mà không ai lo.",
            2
        ),
        lambda: (
            f"Cửa hàng tôi ở {_loc()} đóng cửa mấy ngày liên tiếp vì ngập. "
            f"Mất doanh thu, đồ hàng hóa hư, khổ {_slang()}.",
            1
        ),
        lambda: (
            f"Bơm nước ra ngoài cả đêm mà sáng dậy {_loc()} vẫn còn ngập. "
            f"Kiểu này cứ mãi lặp lại không biết tới bao giờ mới hết.",
            2
        ),
        lambda: (
            f"Ngập ở {_loc()} không phải chuyện lạ, nhưng lần này nước dâng nhanh bất thường, "
            f"nhiều nhà không kịp trở tay. Thiệt hại nặng lắm.",
            2
        ),
        lambda: (
            f"Ước gì {_loc()} có hệ thống chống ngập tốt hơn. Dân khổ đã lâu rồi, "
            f"sao không ai giải quyết cho dứt điểm?",
            1
        ),
        lambda: (
            f"Đường thoại nước trên {_loc()} bị rác bịt hết. Mưa xuống là ngập ngay. "
            f"Cần dọn dẹp thường xuyên hơn chứ, đợi ngập mới xử lý thì muộn rồi.",
            1
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Ngập nước / Triều cường"], "priority": priority}


# ── Kẹt xe ────────────────────────────────────────────────────────────────────
def _gen_ket_xe() -> dict:
    templates = [
        lambda: (
            f"Kẹt xe {_slang()} ở {_loc()} {_time()}, {_veh()} xếp hàng dài hàng cây số. "
            f"{_exc()} Không biết bao giờ mới thoát ra được.",
            1
        ),
        lambda: (
            f"Tôi mất gần {random.choice(['1 tiếng', '2 tiếng', '3 tiếng', '1,5 tiếng'])} "
            f"để qua khỏi {_loc()} vì kẹt xe {_time()}. Về tới nhà thì người cũng bã.",
            1
        ),
        lambda: (
            f"{_loc()} giờ cao điểm là ác mộng luôn. Xe {_veh()} chen nhau, "
            f"klaxon inh ỏi, không ai nhường ai. {_exc()}",
            1
        ),
        lambda: (
            f"Cứ {_time()} là {_loc()} lại tắc cứng. Đi làm mà về tới nhà tốn "
            f"hơn gấp đôi thời gian bình thường. Mệt {_slang()}.",
            1
        ),
        lambda: (
            f"Hôm qua kẹt xe tại {_loc()} do tai nạn chắn giữa đường, "
            f"cả dòng xe xếp hàng dài mấy km. Đứng chơi ngó trời luôn.",
            2
        ),
        lambda: (
            f"Từ nhà đến công ty chỉ {random.choice(['5km', '7km', '10km'])} mà đi mất "
            f"gần {random.choice(['45 phút', '1 tiếng', '1,5 tiếng'])} vì kẹt ở {_loc()}. "
            f"Kiểu này chắc phải dậy sớm thêm mấy tiếng.",
            1
        ),
        lambda: (
            f"Không hiểu sao {_loc()} vừa giải tỏa kẹt xe xong là lại kẹt chỗ khác. "
            f"Giao thông ở đây hỗn loạn {_slang()}.",
            1
        ),
        lambda: (
            f"Kẹt xe tứ phía ở {_loc()}, {_veh()} không nhúc nhích được. "
            f"{_exc()} Đứng giữa đường mà không biết đi hướng nào.",
            1
        ),
        lambda: (
            f"Ứng dụng bản đồ báo tắc đường ở {_loc()} nhưng đường vòng còn tệ hơn. "
            f"Kiểu gì cũng trễ làm, sếp nhìn mặt chán lắm.",
            1
        ),
        lambda: (
            f"Về quê dịp lễ mà ghé qua {_loc()} là kẹt không tưởng. "
            f"Người ta chen nhau vào làn ngược chiều, loạn hết. {_exc()}",
            2
        ),
        lambda: (
            f"Sài Gòn mà kẹt xe thì khỏi nói, nhưng {_loc()} là điểm nóng nhất. "
            f"{_time()} hôm nào cũng có vài vụ kẹt xe dài cả cây số.",
            1
        ),
        lambda: (
            f"Vừa nghe tin kẹt xe trên {_loc()} do xe {_veh()} bị hỏng giữa đường. "
            f"Anh em đi hướng đó chủ động tìm đường khác nha!",
            1
        ),
        lambda: (
            f"{_exc()} Cả buổi sáng kẹt xe ở {_loc()}, không ra khỏi nhà được. "
            f"Cuộc họp trễ cả tiếng, sếp gọi điện hỏi ầm ĩ.",
            1
        ),
        lambda: (
            f"Xe {_veh()} chen vào làn xe máy ở {_loc()} gây ra kẹt xe to. "
            f"Cảnh sát giao thông không thấy đâu cả.",
            1
        ),
        lambda: (
            f"Đường {_loc()} bị thu hẹp do công trình thi công, "
            f"kẹt xe suốt từ {_time()} tới tận tối mịt. Dân đi làm khổ điêu đứng.",
            1
        ),
        lambda: (
            f"Kẹt xe ở {_loc()} còn tệ hơn Tết luôn. {_time()} này không ai dám ra đường. "
            f"Đặt đồ ăn mà shipper cũng nói 'anh ơi đường tắc em không vô được'.",
            1
        ),
        lambda: (
            f"Metro chưa phủ hết tuyến nên dân {_loc()} vẫn phải đi {_veh()}. "
            f"Giờ cao điểm kẹt xe là bài học thuộc lòng mỗi ngày.",
            0
        ),
        lambda: (
            f"Vụ tai nạn trên {_loc()} {_time()} làm kẹt xe cả đoạn dài. "
            f"CSGT đến hướng dẫn nhưng vẫn {_slang()} chậm do lượng xe quá đông.",
            2
        ),
        lambda: (
            f"Nghe kể kẹt xe ở {_loc()} hơn {random.choice(['2 tiếng', '3 tiếng', '4 tiếng'])} "
            f"không nhúc nhích. Người ta tắt máy xuống ngồi hát hò luôn cho bớt căng thẳng.",
            1
        ),
        lambda: (
            f"Tuyến đường qua {_loc()} đang sửa chữa mà không phân luồng giao thông tử tế, "
            f"kẹt xe từ sáng đến tối. Khổ người dân {_slang()}.",
            1
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Ùn tắc giao thông"], "priority": priority}


# ── Ngập nước + Kẹt xe (Multi-label) ─────────────────────────────────────────
def _gen_ngap_ket() -> dict:
    templates = [
        lambda: (
            f"{_exc()} {_loc()} vừa ngập vừa kẹt xe {_time()}, "
            f"hai 'đặc sản' của {random.choice(['Sài Gòn', 'Hà Nội'])} về cùng một lúc. "
            f"Khổ {_slang()} không đỡ được.",
            2
        ),
        lambda: (
            f"Triều cường lên ở {_loc()} đúng giờ tan tầm, nước ngập kết hợp kẹt xe, "
            f"người dân khổ sở đủ đường. {_exc()}",
            2
        ),
        lambda: (
            f"Đường {_loc()} ngập sâu, xe {_veh()} chết máy giữa đường gây thêm kẹt xe. "
            f"Một mũi tên trúng hai cái khổ luôn.",
            2
        ),
        lambda: (
            f"Hôm nay {_loc()} vừa ngập vừa tắc. Tôi đứng đó {random.choice(['30 phút', '45 phút', '1 tiếng'])} "
            f"nước qua cổ chân mà xe không nhúc nhích. {_exc()}",
            2
        ),
        lambda: (
            f"Mưa lớn ở {_loc()} {_time()}: ngập sâu + kẹt xe = không đi đâu được. "
            f"Đây là combo chết người của mùa mưa.",
            2
        ),
        lambda: (
            f"Dân {_loc()} oán thán vì ngày nào cũng phải chịu cảnh ngập nước và kẹt xe. "
            f"Sống ở đây mà khỏe mạnh là kỳ tích.",
            1
        ),
        lambda: (
            f"Mưa + triều cường + giờ cao điểm = thảm họa tại {_loc()}. "
            f"Kẹt xe dài hàng km, nước ngập gần nửa bánh xe. {_exc()}",
            2
        ),
        lambda: (
            f"Đường về nhà qua {_loc()} vừa ngập vừa tắc. "
            f"Gọi xe không được, đặt shipper cũng lắc đầu. Kẹt {_slang()} luôn.",
            2
        ),
        lambda: (
            f"Cứ hễ mưa lớn là {_loc()} vừa ngập vừa kẹt xe cùng lúc. "
            f"Dân ở đây gọi đó là 'combo chào hỏi mùa mưa'.",
            1
        ),
        lambda: (
            f"Tôi phải đẩy {_veh()} qua đoạn ngập ở {_loc()} rồi sau đó lại mắc kẹt trong dòng xe. "
            f"Vừa ướt vừa trễ giờ, cực {_slang()}.",
            2
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Ngập nước / Triều cường", "Ùn tắc giao thông"], "priority": priority}


# ── Tai nạn ───────────────────────────────────────────────────────────────────
def _gen_tai_nan() -> dict:
    templates = [
        lambda: (
            f"Vừa xảy ra tai nạn nghiêm trọng trên {_loc()} {_time()}: "
            f"xe {_veh()} va chạm mạnh, {random.choice(['1 người', '2 người', '3 người'])} bị thương. "
            f"Giao thông ùn tắc nghiêm trọng.",
            2
        ),
        lambda: (
            f"{_exc()} Xe {_veh()} lao lên vỉa hè ở {_loc()}, may không có người đi bộ gần đó. "
            f"Nguy hiểm {_slang()} mà tài xế cứ phóng ẩu.",
            2
        ),
        lambda: (
            f"Khúc cua trên {_loc()} {_slang()} nguy hiểm, "
            f"đã xảy ra hàng chục vụ tai nạn nhưng vẫn chưa có biển cảnh báo hay gờ giảm tốc.",
            2
        ),
        lambda: (
            f"Xe {_veh()} vượt đèn đỏ ở ngã tư {_loc()} rồi tông vào người đi đường. "
            f"Hình ảnh camera an ninh ghi lại rõ mồn một mà tài xế còn cố chạy trốn.",
            2
        ),
        lambda: (
            f"Ổ gà to giữa {_loc()} không có biển báo, xe {_veh()} tránh không kịp ngã xuống đường. "
            f"Cần sửa chữa gấp trước khi thêm người nữa bị nạn.",
            2
        ),
        lambda: (
            f"Tin buồn: xảy ra tai nạn liên hoàn trên {_loc()} {_time()}, "
            f"nhiều xe {_veh()} hư hỏng nặng. CSGT đang phân luồng tại hiện trường.",
            2
        ),
        lambda: (
            f"Đường trơn sau mưa ở {_loc()}, {_veh()} trượt ngã liên tục {_time()}. "
            f"Bề mặt đường hỏng từ lâu mà không có ai vá. {_exc()}",
            2
        ),
        lambda: (
            f"Xe {_veh()} mất lái trên {_loc()} đâm vào dải phân cách, "
            f"lái xe may mắn thoát nhưng giao thông bị tắc nghẽn kéo dài.",
            2
        ),
        lambda: (
            f"Chỗ {_loc()} này không có vạch qua đường, người đi bộ rất dễ bị tai nạn. "
            f"Kiến nghị mãi mà chẳng ai nghe.",
            1
        ),
        lambda: (
            f"Đèn đường trên {_loc()} bị hỏng từ lâu, {_time()} tối mịt không thấy gì. "
            f"Đã xảy ra {random.choice(['2', '3', '4'])} vụ tai nạn mà vẫn chưa được sửa.",
            2
        ),
        lambda: (
            f"Học sinh bị ngã do vỉa hè bong tróc trên {_loc()}. "
            f"Cha mẹ đưa đi cấp cứu mà vẫn chưa thấy ai đứng ra nhận trách nhiệm.",
            2
        ),
        lambda: (
            f"Cảnh báo: đoạn {_loc()} đang có nhiều ổ gà sau mưa lớn, "
            f"{_veh()} đi cẩn thận kẻo ngã. Bà con đi qua đọc được thì giảm tốc nha!",
            1
        ),
        lambda: (
            f"Tôi thấy xe {_veh()} phóng nhanh trên {_loc()} rồi húc vào đuôi xe khác. "
            f"Cả hai tài xế xuống cãi nhau, không ai quan tâm giao thông đang bị tắc.",
            2
        ),
        lambda: (
            f"Tai nạn liên tiếp ở khu vực {_loc()} do đường hẹp, "
            f"thiếu biển báo và ánh sáng kém {_time()}. Cần can thiệp ngay.",
            2
        ),
        lambda: (
            f"{_slang()} nguy hiểm khi xe {_veh()} lao xuống từ {_loc()} lúc trời mưa trơn. "
            f"Cần làm lan can bảo vệ gấp.",
            2
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Tai nạn giao thông"], "priority": priority}


# ── Đèn tín hiệu ──────────────────────────────────────────────────────────────
def _gen_den_tin_hieu() -> dict:
    templates = [
        lambda: (
            f"Đèn tín hiệu tại {_loc()} bị hỏng từ {_time()}, xe cộ hỗn loạn không ai nhường ai. "
            f"Cảnh sát giao thông ở đâu hết rồi? {_exc()}",
            1
        ),
        lambda: (
            f"Chạy đến {_loc()} thì đèn đỏ đột nhiên nhảy thẳng sang xanh rồi lại đỏ không theo thứ tự. "
            f"Không hiểu phải xử lý thế nào, cứ đứng chờ cho an toàn.",
            1
        ),
        lambda: (
            f"Đèn xanh tại ngã tư {_loc()} chỉ bật được {random.choice(['3 giây', '5 giây', '7 giây'])}, "
            f"xe muốn qua cũng không kịp. Ai lập trình đèn này vậy?",
            1
        ),
        lambda: (
            f"Sau Nghị định 168, người ta không dám vượt đèn đỏ dù đèn hỏng ở {_loc()}. "
            f"Kết quả là kẹt xe cứng ngắc vì ai cũng đứng chờ.",
            1
        ),
        lambda: (
            f"Cột đèn giao thông ở {_loc()} bị xe {_veh()} húc ngã từ {_time()}, "
            f"chưa được sửa. Giao thông rối loạn {_slang()}.",
            1
        ),
        lambda: (
            f"Đèn tín hiệu {_loc()} chỉ còn 1 chiều sáng, 3 chiều kia đèn tắt ngóm. "
            f"Tài xế không biết đường nào được đi, đứng chờ mãi.",
            1
        ),
        lambda: (
            f"Phản ánh đèn tín hiệu hỏng ở {_loc()} lần thứ {random.choice(['3', '4', '5'])} rồi "
            f"mà vẫn chưa thấy ai sửa. Thiếu trách nhiệm {_slang()}.",
            1
        ),
        lambda: (
            f"Ngã tư {_loc()} không có đèn, mọi người tự điều phối với nhau nhưng "
            f"vẫn xảy ra va chạm nhỏ {_time()}. Cần lắp đèn tín hiệu gấp.",
            1
        ),
        lambda: (
            f"Đèn tín hiệu {_loc()} muốn đỏ hay xanh tùy hứng, không biết đường nào mà theo. "
            f"Dân chạy xe ở đây đã quen nhưng người lạ vào dễ bị tai nạn lắm.",
            1
        ),
        lambda: (
            f"{_exc()} Đèn tín hiệu tại {_loc()} bật đỏ cả 4 chiều cùng lúc, "
            f"ai cũng dừng, không ai đi được, kẹt xe {_slang()}.",
            1
        ),
        lambda: (
            f"Hệ thống đèn thông minh ở {_loc()} nghe nói tốn mấy chục tỷ đồng nhưng "
            f"cứ mưa lớn là tắt hoặc loạn nhịp. Hiệu quả {random.choice(['quá trời', 'thần sầu'])}, phải không?",
            1
        ),
        lambda: (
            f"Cảnh báo: đèn tín hiệu tại ngã tư {_loc()} đang hỏng pha xanh, "
            f"chỉ còn đỏ và vàng hoạt động. Bà con đi qua cẩn thận.",
            1
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Sự cố hạ tầng & Đèn tín hiệu"], "priority": priority}


# ── Vỉa hè ────────────────────────────────────────────────────────────────────
def _gen_via_he() -> dict:
    templates = [
        lambda: (
            f"Vỉa hè {_loc()} bị lấn chiếm hoàn toàn, người đi bộ phải xuống lòng đường. "
            f"Nguy hiểm {_slang()} mà không ai dọn dẹp.",
            1
        ),
        lambda: (
            f"Quán xá bày bàn ghế chiếm hết vỉa hè {_loc()}, "
            f"mẹ đẩy xe nôi cũng không có chỗ đi. {_exc()} Sao chịu nổi!",
            1
        ),
        lambda: (
            f"Vỉa hè {_loc()} bị để xe máy kín mít từ sáng đến tối. "
            f"Người đi bộ không còn chỗ, phải đi xuống lòng đường nguy hiểm.",
            1
        ),
        lambda: (
            f"Xe {_veh()} leo lên vỉa hè {_loc()} để tránh kẹt xe, "
            f"người đi bộ cứ phải né ra. Vỉa hè là của ai vậy?",
            1
        ),
        lambda: (
            f"Vỉa hè khu vực {_loc()} bong tróc, gạch vỡ nham nhở từ lâu. "
            f"Người già, trẻ em đi qua rất dễ vấp ngã. Cần sửa gấp.",
            1
        ),
        lambda: (
            f"Hàng quán lấn chiếm vỉa hè {_loc()} tới tận lòng đường, "
            f"không biết lực lượng chức năng đứng ở đâu mà để vậy.",
            1
        ),
        lambda: (
            f"Dây điện thòng xuống ngay vỉa hè {_loc()} {_slang()} nguy hiểm, "
            f"trẻ em chạy nhảy ở đó mà không ai cảnh báo.",
            2
        ),
        lambda: (
            f"Vỉa hè {_loc()} sạch đẹp được mấy hôm sau đợt ra quân thì lại bị chiếm lại. "
            f"Cần duy trì thường xuyên chứ không phải theo chiến dịch.",
            1
        ),
        lambda: (
            f"Ở {_loc()} vỉa hè bị đào lên để lắp đặt cáp ngầm mà không có biển cảnh báo. "
            f"Tôi suýt bị vấp ngã {_time()}. Thiếu an toàn {_slang()}.",
            1
        ),
        lambda: (
            f"Cây xanh trồng trên vỉa hè {_loc()} rễ trồi lên làm gạch bể lộm chộm. "
            f"Đi bộ phải nhìn xuống chân từng bước, {_exc()}",
            1
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Lấn chiếm vỉa hè & Lòng đường"], "priority": priority}


# ── Vi phạm luật ──────────────────────────────────────────────────────────────
def _gen_vi_pham() -> dict:
    templates = [
        lambda: (
            f"Xe {_veh()} chạy ngược chiều trên {_loc()} {_time()}, "
            f"người đi ngược chiều không ai xử lý hết. Luật giao thông ở đây vô nghĩa.",
            1
        ),
        lambda: (
            f"Cứ chiều {_time()} là có cả dòng {_veh()} leo lề {_loc()} để tránh kẹt. "
            f"CSGT đứng gần đó nhưng cũng không thổi phạt.",
            1
        ),
        lambda: (
            f"Phạt nặng theo Nghị định 168 mà tôi vẫn thấy người ta chạy ẩu ở {_loc()} {_time()}. "
            f"Phạt nặng mà không thực thi thì cũng như không.",
            0
        ),
        lambda: (
            f"Xe {_veh()} dừng đỗ tùy tiện trên {_loc()} chắn cả làn xe, "
            f"không ai nhắc nhở hay xử phạt. Ý thức như vậy mà thôi.",
            1
        ),
        lambda: (
            f"{_slang()} là cảnh xe {_veh()} bấm còi inh ỏi ở {_loc()} lúc nửa đêm. "
            f"Vi phạm quy định tiếng ồn mà cứ làm vô tư.",
            0
        ),
        lambda: (
            f"Mức phạt mới tăng gấp chục lần nhưng nhiều người ở {_loc()} vẫn vượt đèn đỏ. "
            f"Cần lắp camera nhiều hơn chứ không thì không hiệu quả.",
            0
        ),
        lambda: (
            f"Tài xế xe {_veh()} nhậu xong vẫn cầm lái trên {_loc()} {_time()}. "
            f"Kiểm tra nồng độ cồn cần tăng cường hơn nhiều.",
            2
        ),
        lambda: (
            f"Xe tải quá khổ quá tải vẫn chạy vô tư trên {_loc()}, "
            f"mặt đường bị hỏng liên tục. Ai cấp phép? Ai kiểm soát?",
            1
        ),
        lambda: (
            f"Người ta cứ nói phạt nặng nhưng kiểm tra ngẫu nhiên thì ít khi bị bắt. "
            f"Tỷ lệ bị phạt thấp nên nhiều người vẫn vi phạm ở {_loc()}.",
            0
        ),
        lambda: (
            f"Cảnh báo: CSGT đang đặt chốt ở {_loc()} {_time()}, "
            f"anh em nhớ đội mũ bảo hiểm và không sử dụng điện thoại khi lái xe.",
            0
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Vi phạm & Ý thức giao thông"], "priority": priority}


# ── Ý thức giao thông ─────────────────────────────────────────────────────────
def _gen_y_thuc() -> dict:
    templates = [
        lambda: (
            f"Xe {_veh()} cắt ngang đầu xe tôi ở {_loc()} mà không xi nhan. "
            f"Ý thức giao thông {_slang()} tệ, cứ như đường của riêng họ vậy.",
            1
        ),
        lambda: (
            f"Dừng đèn đỏ ở {_loc()}, xe phía sau cứ bấm còi inh ỏi. "
            f"Đèn đỏ mà bấm còi thì tôi biết làm gì? {_exc()}",
            1
        ),
        lambda: (
            f"Vừa thấy cảnh xe {_veh()} vượt ẩu ở {_loc()}, suýt húc vào mấy em học sinh. "
            f"Người ta cứ phóng nhanh như thể có người đang rượt đuổi.",
            2
        ),
        lambda: (
            f"{_exc()} Tài xế {_veh()} ở {_loc()} vừa lái vừa nhìn điện thoại. "
            f"Nguy hiểm không chỉ cho bản thân mà còn cả người xung quanh.",
            2
        ),
        lambda: (
            f"Xe {_veh()} dừng đỗ sai chỗ ở {_loc()}, chắn cả lề đường lẫn phần đường dành cho xe máy. "
            f"Ai cũng khổ vì mấy người thiếu ý thức này.",
            1
        ),
        lambda: (
            f"Chứng kiến ở {_loc()}: 3 chiếc xe {_veh()} cùng vượt đèn đỏ. "
            f"Rồi khi xảy ra tai nạn thì đổ lỗi cho hạ tầng. Tự mình xem lại đi!",
            1
        ),
        lambda: (
            f"Xe buýt ở {_loc()} vừa dừng ngay giữa đường để đón khách, "
            f"không ra bến. Hành khách phải nhảy xuống, {_slang()} nguy hiểm.",
            2
        ),
        lambda: (
            f"Người dân ở {_loc()} đã dần có ý thức hơn sau khi phạt nặng. "
            f"Nhưng vẫn còn nhiều người nhắm mắt leo lề tránh kẹt xe {_time()}.",
            0
        ),
        lambda: (
            f"Đi bộ sang đường ở {_loc()} mà cứ phải chạy né vì xe {_veh()} không nhường. "
            f"Đèn dành cho người đi bộ mà xe vẫn phóng thẳng vào.",
            1
        ),
        lambda: (
            f"{_exc()} Xe container trên {_loc()} không bật đèn xi nhan, "
            f"chuyển làn đột ngột gần như đẩy xe tôi vào giải phân cách. Ớn {_slang()}.",
            2
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Vi phạm & Ý thức giao thông"], "priority": priority}


# ── Hư hỏng hạ tầng ──────────────────────────────────────────────────────────
def _gen_ha_tang() -> dict:
    templates = [
        lambda: (
            f"Cầu {_loc()} bị nứt dọc mặt cầu từ lâu, mỗi lần xe {_veh()} qua là rung lắc {_slang()}. "
            f"Chờ tới khi sập mới sửa hay sao?",
            2
        ),
        lambda: (
            f"Ổ gà trên {_loc()} to tướng, lấp tạm rồi lại vỡ. "
            f"Xe {_veh()} qua đó liên tục hư lốp, tiền sửa xe còn nhiều hơn tiền đổ xăng.",
            1
        ),
        lambda: (
            f"Con đường {_loc()} mới sửa xong {random.choice(['3 tháng', '6 tháng', '1 năm'])} đã xuống cấp trở lại. "
            f"Chất lượng thi công kém {_slang()}, tiền ai đang ăn?",
            1
        ),
        lambda: (
            f"Biển báo giao thông trên {_loc()} bị che khuất bởi cây xanh, "
            f"không nhìn thấy tốc độ tối đa hay vạch kẻ đường. Nguy hiểm {_slang()}.",
            1
        ),
        lambda: (
            f"Hầm chui {_loc()} bị ngập mỗi khi mưa lớn dù mới xây xong. "
            f"Thiết kế kém hay thi công ẩu? Ai trả lời dân được không?",
            2
        ),
        lambda: (
            f"Đường {_loc()} hẹp mà hai chiều, xe {_veh()} qua nhau còn không có chỗ. "
            f"Ở đây thường xuyên xảy ra va chạm mà không ai mở rộng.",
            1
        ),
        lambda: (
            f"Dải phân cách trên {_loc()} bị xe {_veh()} đâm vào từ hôm qua, "
            f"nằm chắn giữa đường, nguy hiểm cực kỳ. Cần dọn dẹp ngay.",
            2
        ),
        lambda: (
            f"Hệ thống thoát nước dưới {_loc()} bị hỏng từ lâu, "
            f"mỗi lần mưa là ngập ngay. Đầu tư công trình kiểu gì vậy?",
            2
        ),
        lambda: (
            f"Cột đèn đường {_loc()} bị gãy một tuần nay chưa thay. "
            f"Đêm tối đen như mực, tai nạn liên tiếp xảy ra.",
            2
        ),
        lambda: (
            f"Metro {_loc()} vừa vận hành được mấy ngày đã gặp sự cố kỹ thuật. "
            f"Dự án nghìn tỷ mà chất lượng như vậy, ai dám đi?",
            1
        ),
    ]
    text, priority = random.choice(templates)()
    return {"text": text, "category": ["Sự cố hạ tầng & Đèn tín hiệu"], "priority": priority}


# ═══════════════════════════════════════════════════════════════════════════════
#  LỌC DỮ LIỆU
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """Chuẩn hóa: khoảng trắng, dấu câu, unicode NFC."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r" ([,.!?;:])", r"\1", text)
    return text


def _word_count(text: str) -> int:
    return len(text.split())


def _jaccard_similarity(a: str, b: str) -> float:
    """Tính Jaccard similarity giữa hai câu dựa trên tập các từ (bi-gram)."""
    def bigrams(s: str):
        tokens = s.lower().split()
        return set(zip(tokens, tokens[1:])) if len(tokens) > 1 else set(tokens)
    sa, sb = bigrams(a), bigrams(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def filter_data(records: list[dict]) -> list[dict]:
    """
    Áp dụng các bộ lọc chất lượng:
      1. Loại bỏ câu quá ngắn (< MIN_WORD_COUNT từ).
      2. Chuẩn hóa khoảng trắng và dấu câu.
      3. Loại bỏ bản trùng lặp / quá giống nhau (Jaccard similarity > SIMILARITY_THRESHOLD).
    """
    # Bước 1 + 2: chuẩn hóa và loại ngắn
    cleaned: list[dict] = []
    for rec in records:
        rec["text"] = _normalize(rec["text"])
        if _word_count(rec["text"]) >= MIN_WORD_COUNT:
            cleaned.append(rec)

    # Bước 3: loại trùng lặp / quá giống
    retained: list[dict] = []
    retained_texts: list[str] = []
    duplicates_removed = 0

    for rec in cleaned:
        t = rec["text"]
        is_duplicate = False
        for existing in retained_texts:
            if _jaccard_similarity(t, existing) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                duplicates_removed += 1
                break
        if not is_duplicate:
            retained.append(rec)
            retained_texts.append(t)

    print(f"  [filter] Input: {len(records)}  →  Sau lọc ngắn: {len(cleaned)}  →  Sau khử trùng: {len(retained)}  (đã xóa {duplicates_removed} bản trùng)")
    return retained


# ═══════════════════════════════════════════════════════════════════════════════
#  SINH DỮ LIỆU
# ═══════════════════════════════════════════════════════════════════════════════

# Bản đồ sinh: (generator_fn, trọng số theo phân phối seed)

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


GENERATORS = [
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
]

_fns, _weights = zip(*GENERATORS)


def generate_synthetic(n: int) -> list[dict]:
    """Sinh n mẫu tổng hợp có phân phối dựa trên trọng số category."""
    chosen_fns = random.choices(_fns, weights=_weights, k=n * 2)  # sinh dư để bù sau khi lọc
    raw: list[dict] = []
    for fn in chosen_fns:
        try:
            raw.append(fn())
        except Exception as e:
            print(f"  [warn] Generator error: {e}")
    return raw


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Synthetic Data Generator – Giao thông đô thị Việt Nam")
    print("=" * 60)

    # ── Bước 1: Đọc seed data ────────────────────────────────────
    print("\n[1] Đọc seed_data.json ...")
    with open(SEED_FILE, "r", encoding="utf-8-sig") as f:
        seed_data: list[dict] = json.load(f)

    # Thống kê seed
    seed_cats = []
    for item in seed_data:
        seed_cats.extend(item.get("category", []))
    cat_counts = Counter(seed_cats)
    print(f"    Tổng mẫu seed: {len(seed_data)}")
    print("    Phân phối category:")
    for cat, cnt in cat_counts.most_common():
        print(f"      {cat:<30s}: {cnt}")
    print(f"    Priority: {Counter(item.get('priority') for item in seed_data)}")

    # Đảm bảo seed data có field đúng
    for item in seed_data:
        item.setdefault("priority", 1)
        if isinstance(item.get("category"), str):
            item["category"] = [item["category"].strip()]

    # ── Bước 2: Sinh synthetic data ──────────────────────────────
    print(f"\n[2] Sinh {TARGET_NEW_SAMPLES}+ mẫu tổng hợp ...")
    raw_synthetic = generate_synthetic(TARGET_NEW_SAMPLES)
    print(f"    Đã sinh (thô): {len(raw_synthetic)} mẫu")

    # ── Bước 3: Lọc synthetic data ───────────────────────────────
    print("\n[3] Áp dụng filter_data() cho synthetic ...")
    filtered_synthetic = filter_data(raw_synthetic)

    # Đảm bảo đủ TARGET_NEW_SAMPLES sau lọc
    attempt = 1
    while len(filtered_synthetic) < TARGET_NEW_SAMPLES and attempt <= 5:
        print(f"    Sinh thêm (lần {attempt}) vì chưa đủ {TARGET_NEW_SAMPLES} mẫu ...")
        extra = generate_synthetic(TARGET_NEW_SAMPLES - len(filtered_synthetic))
        filtered_synthetic = filter_data(filtered_synthetic + extra)
        attempt += 1

    print(f"    Synthetic sau lọc : {len(filtered_synthetic)} mẫu")

    # ── Bước 4: Gộp và lọc toàn bộ dataset ──────────────────────
    print("\n[4] Gộp seed + synthetic và lọc lần cuối ...")
    all_data = seed_data + filtered_synthetic
    final_data = filter_data(all_data)
    print(f"    Tổng cộng: {len(final_data)} mẫu (seed: {len(seed_data)}, synthetic: {len(final_data) - len(seed_data)})")

    # Thống kê cuối
    final_cats = []
    for item in final_data:
        final_cats.extend(item.get("category", []))
    print("\n    Phân phối category cuối:")
    for cat, cnt in Counter(final_cats).most_common():
        print(f"      {cat:<30s}: {cnt}")
    print(f"    Priority: {Counter(item.get('priority') for item in final_data)}")

    # ── Bước 5: Xuất file ────────────────────────────────────────
    print(f"\n[5] Xuất ra {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"    Done! File: {OUTPUT_FILE}  ({OUTPUT_FILE.stat().st_size // 1024} KB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
