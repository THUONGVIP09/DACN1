// run_generate.mjs – Node.js runner (ES Module)
import { readFileSync, writeFileSync, statSync } from 'fs';

const SEED_FILE   = 'c:\\Users\\minh\\OneDrive\\Desktop\\DACN1_Project\\seed_data.json';
const OUTPUT_FILE = 'c:\\Users\\minh\\OneDrive\\Desktop\\DACN1_Project\\augmented_dataset.json';
const TARGET      = 520;
const SIM_THRESHOLD = 0.80;
const MIN_WORDS   = 5;

// ── Deterministic RNG ────────────────────────────────────────────────────────
let rngState = 42;
function rng() { rngState = (Math.imul(1664525, rngState) + 1013904223) >>> 0; return rngState; }
function rand(n)   { return rng() % n; }
function choice(a) { return a[rand(a.length)]; }
function choices(arr, weights, k) {
  const total = weights.reduce((a, b) => a + b, 0);
  const result = [];
  for (let i = 0; i < k; i++) {
    const r = (rng() / 0xFFFFFFFF) * total;
    let cum = 0;
    for (let j = 0; j < weights.length; j++) {
      cum += weights[j];
      if (r < cum) { result.push(arr[j]); break; }
    }
    if (result.length < i + 1) result.push(arr[arr.length - 1]);
  }
  return result;
}

// ── Word banks ───────────────────────────────────────────────────────────────
const LOCATIONS = [
  "quận Bình Thạnh","quận Gò Vấp","quận Tân Bình","quận 12","quận Thủ Đức",
  "quận Bình Tân","quận 8","quận 6","quận 4","quận 7","huyện Bình Chánh","huyện Nhà Bè",
  "đường Nguyễn Hữu Cảnh","đường Ung Văn Khiêm","đường Phan Văn Trị","đường Lê Văn Thọ",
  "đường Phú Thuận","đường Kha Vạn Cân","đường Nguyễn Văn Linh","đường Huỳnh Tấn Phát",
  "đường Tô Ngọc Vân","đường D1 Bình Thạnh","đường Lê Đức Thọ","đường Quang Trung GV",
  "vòng xoay Hàng Xanh","vòng xoay Lăng Cha Cả","vòng xoay Phú Lâm",
  "ngã tư Bình Phước","ngã tư An Sương","cầu Bình Lợi","cầu Thủ Thiêm",
  "cầu Phú Mỹ","nút giao Cát Lái","quận Hà Đông","quận Cầu Giấy","quận Đống Đa",
  "quận Long Biên","quận Hoàng Mai","quận Nam Từ Liêm","quận Bắc Từ Liêm",
  "quận Thanh Xuân","huyện Hoài Đức","huyện Đan Phượng","đường Mỹ Đình",
  "phố Huế","đường Nguyễn Trãi","đường Giải Phóng","đường Khuất Duy Tiến",
  "đường Lê Văn Lương","đường Tố Hữu","đường Phạm Hùng","đường Nguyễn Xiển",
  "đường Trần Duy Hưng","đường Dương Nội","đường Hoàng Quốc Việt",
  "vòng xoay Ngã Tư Sở","vòng xoay Mỹ Đình","nút giao Cổ Linh",
  "cầu Vĩnh Tuy","cầu Thanh Trì","cầu Nhật Tân","đường Linh Đàm","đường Lĩnh Nam"
];
const TIMES   = ["sáng sớm","rạng sáng","lúc 5h sáng","tầm 6h","giờ tan tầm","giờ cao điểm chiều","tối qua","đêm qua","nửa đêm","lúc 22h","khoảng 17h","lúc 18h30","chiều hôm qua","trưa nay","ngày hôm qua","hai ngày trước","suốt cả tuần nay","mỗi khi mưa lớn"];
const VEHICLES = ["xe máy","ô tô","xe buýt","xe tải","xe container","xe đạp điện"];
const EXCL    = ["Trời ơi!","Ôi thôi rồi!","Khổ quá!","Chịu không nổi rồi!","Thiệt hết sức!","Mệt lắm ơi!","Không chịu được nữa!","Kinh khủng thiệt!","Ghê quá!"];
const SLANG   = ["thiệt sự","quá trời quá đất","kinh khủng","ác liệt","khủng khiếp","bá cháy","hết nói nổi","đừng hỏi","không đỡ nổi","cùng cực"];
const DEPTHS  = ["ngang gối","ngang đùi","qua lưng xe","ngang thắt lưng"];
const DURATIONS = ["1 tiếng","2 tiếng","3 tiếng","1,5 tiếng","45 phút"];
const DEPTHS2 = ["30cm","40cm","50cm","60cm","70cm"];
const YEARS   = ["5 năm","10 năm","15 năm","20 năm","25 năm"];
const TIMES2  = ["3 tháng","6 tháng","1 năm","2 năm"];
const COUNTS  = ["3","4","5"];
const DIST    = ["5km","7km","10km","12km"];
const DAMAGE  = ["2","3","4"];

const L = () => choice(LOCATIONS);
const T = () => choice(TIMES);
const V = () => choice(VEHICLES);
const E = () => choice(EXCL);
const S = () => choice(SLANG);

// ── Generators ───────────────────────────────────────────────────────────────
function genNgap() {
  const tpls = [
    () => [`Nước ngập ${L()} ${T()}, xe chết máy la liệt, người dắt bộ đầy đường. ${E()} Không biết chính quyền có thấy không nữa.`, 2],
    () => [`Lại ngập rồi! ${L()} hễ mưa là ngập, năm này qua năm khác không thay đổi. Bà con ${S()} khổ.`, 2],
    () => [`Mưa chưa tới 20 phút mà ${L()} đã ngập ngang bánh xe. Đi làm trễ mấy tiếng, căng thẳng ${S()}.`, 1],
    () => [`Triều cường ${T()} dâng cao bất ngờ ở ${L()}, nước tràn vào nhà dân, đồ đạc hư hỏng hết. Khổ ${S()}.`, 2],
    () => [`Úi trời, ${L()} ngập sâu tới ${choice(DEPTHS)}. Xe ${V()} chết máy hàng loạt ${T()}.`, 2],
    () => [`Cả xóm tôi ở ${L()} ngày nào mưa lớn là ngập. Đồ điện tử kê lên cao hết rồi mà nước vẫn chạm tới. ${E()}`, 2],
    () => [`Ngập ${S()} ở ${L()}, xe ${V()} bơi lội còn không xong. Ai dám mang xe ra ${T()} nữa?`, 2],
    () => [`Mấy tháng nay ${L()} ngập hoài, tôi đã bỏ xe ở nhà đi bộ qua đoạn ngập rồi mới đặt xe. Bao giờ mới hết cảnh này?`, 1],
    () => [`${E()} Nước ngập tới cửa sổ nhà tôi ở ${L()}, lần này là tệ nhất trong mấy năm nay. Không kịp chạy ra hết.`, 2],
    () => [`Đang chạy ${V()} trên ${L()} thì nước dâng nhanh quá không kịp tránh. Xe chết máy giữa đường, đứng dầm nước hơn ${choice(DURATIONS)} mới có người kéo vào.`, 2],
    () => [`Con đường ${L()} thuộc loại ngập truyền thống, mưa nhỏ cũng ngập, mưa lớn thì khỏi nói. Dân ở đây quen rồi nhưng mà khổ vẫn khổ.`, 1],
    () => [`Cứ ${T()} là ${L()} lại biến thành sông. Người đi bộ đội nón lội nước, ${V()} chào thua hết. ${E()}`, 1],
    () => [`Nhà tôi gần ${L()}, mỗi lần ngập là thiệt hại đủ thứ. Máy bơm chạy suốt mà nước vẫn vô. Năm nay ngập ${S()} luôn.`, 2],
    () => [`Trẻ con ở khu ${L()} không thể đến trường được vì đường ngập sâu. Bố mẹ lo lắm, không biết phải làm sao.`, 2],
    () => [`Cống thoát nước ${L()} bị tắc lâu rồi, mỗi lần mưa là nước dềnh lên hết mặt đường. Phản ánh mãi không ai xử lý.`, 1],
    () => [`Tôi sống ở ${L()} gần ${choice(YEARS)} nay, ngập riết quen rồi nhưng mỗi lần vẫn mệt. Đồ đạc hỏng liên tục.`, 1],
    () => [`${T()} nước bắt đầu dâng ở ${L()}, đến khi tôi thức dậy thì nước đã ngang sàn nhà rồi. Không kịp chạy đồ gì cả.`, 2],
    () => [`Khâu thoát nước ở ${L()} quá kém, đầu tư bao nhiêu năm mà cứ mưa là ngập. Tiền thuế dân đóng mà xài kiểu này?`, 1],
    () => [`Gia đình tôi đã di chuyển đồ đạc lên cao lần thứ ${choice(COUNTS)} trong năm nay vì triều cường ở ${L()}. Kiệt sức rồi thật.`, 2],
    () => [`Đường ${L()} ngập sâu, xe ${V()} chết máy hàng loạt, người dắt bộ hai hàng dài. Cảnh tượng ${S()} mà buồn.`, 2],
    () => [`Hễ coi dự báo thời tiết thấy có mưa lớn là dân ${L()} ai cũng lo. Biết chắc kiểu gì cũng ngập.`, 1],
    () => [`${E()} ${L()} ngập rồi! Ai đang di chuyển qua đây thì tìm đường khác đi nhé. Nước sâu tới ${choice(DEPTHS2)} rồi.`, 2],
    () => [`Mưa ${T()} ở ${L()}, tôi không dám cho con đi học vì đường ngập quá nguy hiểm. Cả buổi sáng bị kẹt ở nhà.`, 1],
    () => [`Nước rút chậm ${S()} ở ${L()}, ngập từ ${T()} tới tận chiều mới rút bớt. Nhà cửa ẩm thấp, đồ đạc bốc mùi hết.`, 2],
    () => [`Khu ${L()} bị cô lập hoàn toàn vì nước ngập, không xe cứu thương nào vào được. Nguy hiểm ${S()} mà không ai lo.`, 2],
    () => [`Cửa hàng tôi ở ${L()} đóng cửa mấy ngày liên tiếp vì ngập. Mất doanh thu, đồ hàng hóa hư, khổ ${S()}.`, 1],
    () => [`Bơm nước ra ngoài cả đêm mà sáng dậy ${L()} vẫn còn ngập. Kiểu này cứ mãi lặp lại không biết tới bao giờ mới hết.`, 2],
    () => [`${E()} Ngập ở ${L()} lần này nước dâng nhanh bất thường, nhiều nhà không kịp trở tay. Thiệt hại nặng lắm.`, 2],
    () => [`Ước gì ${L()} có hệ thống chống ngập tốt hơn. Dân khổ đã lâu rồi, sao không ai giải quyết cho dứt điểm?`, 1],
    () => [`Đường thoát nước trên ${L()} bị rác bịt hết. Mưa xuống là ngập ngay. Cần dọn dẹp thường xuyên hơn chứ, đợi ngập mới xử lý thì muộn rồi.`, 1],
    () => [`Tôi về qua ${L()} lúc ${T()}, nước ngập gần tới yên xe. Cố lội qua được nhưng xe thì chắc hỏng rồi. Xót lắm.`, 2],
    () => [`Báo đài đưa tin ngập ${L()} hoài mà không thấy giải pháp. Bao nhiêu tiền đổ vào dự án chống ngập mà kết quả là đây.`, 1],
    () => [`Nhà tôi đã xây chống ngập lên thêm ${choice(DEPTHS2)} nhưng nước vẫn vào được. Triều cường năm nay ${S()} dữ.`, 2],
    () => [`Học sinh ở ${L()} cứ mùa mưa là nghỉ học vì đường ngập. Ba mẹ không dám cho đi, trường thì không tổ chức online. Thiệt thòi ${S()}.`, 1],
    () => [`${V()} chết máy giữa đoạn ngập ở ${L()}, chủ xe phải đứng dầm nước chờ ${choice(DURATIONS)} mới có người hỗ trợ. ${E()}`, 2],
    () => [`Nước ngập ${L()} khiến nhiều người già và trẻ nhỏ không thể ra ngoài. Cộng đồng phải hỗ trợ nhau từng bữa cơm.`, 2],
    () => [`Triều cường kết hợp mưa lớn ${T()} tại ${L()} tạo ra cơn ngập kinh hoàng nhất từ trước tới nay theo lời dân kể.`, 2],
    () => [`Ngập sâu ở ${L()} nhưng xe cứu thương vẫn phải vào vì có người bệnh nặng. Tài xế lội nước vào cứu người đáng khâm phục.`, 2],
    () => [`Cả khu phố gần ${L()} bốc mùi sau khi nước rút vì rác thải tích tụ. Cuộc sống sau ngập còn khổ hơn lúc ngập.`, 1],
    () => [`Mỗi năm ngập vài chục lần ở ${L()} mà không có ai bồi thường thiệt hại cho dân. Chúng tôi tự chịu hết.`, 1],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["ngập nước"], priority };
}

function genKet() {
  const tpls = [
    () => [`Kẹt xe ${S()} ở ${L()} ${T()}, ${V()} xếp hàng dài hàng cây số. ${E()} Không biết bao giờ mới thoát ra được.`, 1],
    () => [`Tôi mất gần ${choice(DURATIONS)} để qua khỏi ${L()} vì kẹt xe ${T()}. Về tới nhà thì người cũng bã.`, 1],
    () => [`${L()} giờ cao điểm là ác mộng luôn. Xe ${V()} chen nhau, bấm còi inh ỏi, không ai nhường ai. ${E()}`, 1],
    () => [`Cứ ${T()} là ${L()} lại tắc cứng. Đi làm mà về tới nhà tốn hơn gấp đôi thời gian bình thường. Mệt ${S()}.`, 1],
    () => [`Hôm qua kẹt xe tại ${L()} do tai nạn chắn giữa đường, cả dòng xe xếp hàng dài mấy km. Đứng chơi ngó trời luôn.`, 2],
    () => [`Từ nhà đến công ty chỉ ${choice(DIST)} mà đi mất gần ${choice(DURATIONS)} vì kẹt ở ${L()}. Kiểu này chắc phải dậy sớm thêm mấy tiếng.`, 1],
    () => [`Không hiểu sao ${L()} vừa giải tỏa kẹt xe xong là lại kẹt chỗ khác. Giao thông ở đây hỗn loạn ${S()}.`, 1],
    () => [`Kẹt xe tứ phía ở ${L()}, ${V()} không nhúc nhích được. ${E()} Đứng giữa đường mà không biết đi hướng nào.`, 1],
    () => [`Về quê dịp lễ mà ghé qua ${L()} là kẹt không tưởng. Người ta chen nhau vào làn ngược chiều, loạn hết. ${E()}`, 2],
    () => [`${L()} là điểm kẹt xe nóng nhất. ${T()} hôm nào cũng có vài vụ tắc đường dài cả cây số.`, 1],
    () => [`Cảnh báo kẹt xe trên ${L()} do xe ${V()} bị hỏng giữa đường. Anh em đi hướng đó chủ động tìm đường khác nha!`, 1],
    () => [`${E()} Cả buổi sáng kẹt xe ở ${L()}, không ra khỏi nhà được. Cuộc họp trễ cả tiếng, sếp gọi điện hỏi ầm ĩ.`, 1],
    () => [`Đường ${L()} bị thu hẹp do công trình thi công, kẹt xe suốt từ ${T()} tới tối. Dân đi làm khổ điêu đứng.`, 1],
    () => [`Kẹt xe ở ${L()} còn tệ hơn Tết luôn. Đặt đồ ăn mà shipper cũng bảo anh ơi đường tắc em không vô được.`, 1],
    () => [`Metro chưa phủ hết tuyến nên dân ${L()} vẫn phải đi ${V()}. Giờ cao điểm kẹt xe là bài học thuộc lòng mỗi ngày.`, 0],
    () => [`Kẹt xe ở ${L()} hơn ${choice(DURATIONS)} không nhúc nhích. Người ta tắt máy xuống ngồi nói chuyện cho bớt căng thẳng.`, 1],
    () => [`Tuyến đường qua ${L()} đang sửa chữa mà không phân luồng tử tế, kẹt xe từ sáng đến tối. Khổ dân ${S()}.`, 1],
    () => [`Ứng dụng bản đồ báo tắc đường ở ${L()} nhưng đường vòng còn tệ hơn. Kiểu gì cũng trễ, sếp nhìn mặt chán lắm.`, 1],
    () => [`Xe ${V()} chen vào làn xe máy ở ${L()} gây ra kẹt xe to. Cảnh sát giao thông không thấy đâu cả.`, 1],
    () => [`${E()} Tắc đường từ ${L()} kéo dài, đứng dưới nắng nóng chờ đợi mà người khô rang.`, 1],
    () => [`Buổi tối về qua ${L()} bị kẹt xe hơn ${choice(DURATIONS)}. Con nhỏ ở nhà một mình, gọi điện mà không về được, lo chết mất.`, 1],
    () => [`Lại kẹt ở ${L()} rồi. Ngày nào cũng vậy, ${S()} chán. Đi làm mệt, về nhà còn phải ngồi trong xe thêm mấy tiếng.`, 1],
    () => [`Đoạn ${L()} đang làm đường nên chỉ còn một làn, kẹt xe từ sáng tới tối. Khi nào xong dự án đây trời?`, 1],
    () => [`${V()} vào giờ cao điểm ở ${L()} chật như nêm. Nhích từng mét một, nóng bức, khói bụi ${S()}.`, 1],
    () => [`Sài Gòn chà đạp người ta quá, kẹt xe là cái khổ nhất khi sống ở ${L()}.`, 1],
    () => [`Vừa đặt xe ở ${L()} thì tài xế gọi lại nói anh ơi kẹt xe em không vào được. Thôi đành cuốc bộ vậy.`, 1],
    () => [`Shipper giao hàng ở ${L()} than thở kẹt xe ${T()} làm chậm toàn bộ đơn hàng. Khách hàng complain ầm ĩ.`, 0],
    () => [`Xe ${V()} xếp hàng dài ở ${L()}, lái xe tranh thủ ăn sáng luôn trên xe vì biết chắc còn lâu mới thoát ra.`, 1],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["kẹt xe"], priority };
}

function genNgapKet() {
  const tpls = [
    () => [`${E()} ${L()} vừa ngập vừa kẹt xe ${T()}, hai đặc sản của ${choice(["Sài Gòn","Hà Nội"])} về cùng một lúc. Khổ ${S()} không đỡ được.`, 2],
    () => [`Triều cường lên ở ${L()} đúng giờ tan tầm, nước ngập kết hợp kẹt xe, người dân khổ sở đủ đường. ${E()}`, 2],
    () => [`Đường ${L()} ngập sâu, xe ${V()} chết máy giữa đường gây thêm kẹt xe. Một mũi tên trúng hai cái khổ luôn.`, 2],
    () => [`Hôm nay ${L()} vừa ngập vừa tắc. Tôi đứng đó ${choice(["30 phút","45 phút","1 tiếng"])} nước qua cổ chân mà xe không nhúc nhích. ${E()}`, 2],
    () => [`Mưa lớn ở ${L()} ${T()}: ngập sâu và kẹt xe không đi đâu được. Đây là combo chết người của mùa mưa.`, 2],
    () => [`Dân ${L()} oán thán vì ngày nào cũng phải chịu cảnh ngập nước và kẹt xe. Sống ở đây mà khỏe mạnh là kỳ tích.`, 1],
    () => [`Mưa và triều cường và giờ cao điểm tại ${L()} cùng lúc là thảm họa. Kẹt xe dài hàng km, nước ngập gần nửa bánh xe. ${E()}`, 2],
    () => [`Đường về nhà qua ${L()} vừa ngập vừa tắc. Gọi xe không được, đặt shipper cũng lắc đầu. Kẹt ${S()} luôn.`, 2],
    () => [`Cứ hễ mưa lớn là ${L()} vừa ngập vừa kẹt xe cùng lúc. Dân ở đây gọi đó là combo chào hỏi mùa mưa.`, 1],
    () => [`Tôi phải đẩy ${V()} qua đoạn ngập ở ${L()} rồi sau đó lại mắc kẹt trong dòng xe. Vừa ướt vừa trễ giờ, cực ${S()}.`, 2],
    () => [`Đường phía dưới ${L()} ngập thì đi tàu điện trên cao đúng là an toàn nhất, lại không tắc.`, 1],
    () => [`Ngày nào cũng ngập và kẹt ở ${L()}, dân ở đây năm nào cũng kêu mà chẳng thấy thay đổi.`, 1],
    () => [`Triều cường ${T()} nhấn chìm ${L()}, kẹt xe tứ phương. Tôi ngồi trong xe nhìn nước ngập mà không biết làm gì.`, 2],
    () => [`Chỉ ${choice(DIST)} từ ${L()} mà đi mất ${choice(DURATIONS)} vì vừa ngập vừa tắc. Bó tay chấm com.`, 2],
    () => [`${L()} kẹt xe do nước ngập làm xe chết máy hàng loạt, người dắt bộ chiếm hết lòng đường. Cảnh tượng không đỡ nổi.`, 2],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["ngập nước", "kẹt xe"], priority };
}

function genTaiNan() {
  const tpls = [
    () => [`Vừa xảy ra tai nạn trên ${L()} ${T()}: xe ${V()} va chạm mạnh, ${choice(["1 người","2 người","3 người"])} bị thương. Giao thông ùn tắc nghiêm trọng.`, 2],
    () => [`${E()} Xe ${V()} lao lên vỉa hè ở ${L()}, may không có người đi bộ gần đó. Nguy hiểm ${S()} mà tài xế cứ phóng ẩu.`, 2],
    () => [`Khúc cua trên ${L()} ${S()} nguy hiểm, đã xảy ra nhiều vụ tai nạn nhưng vẫn chưa có biển cảnh báo hay gờ giảm tốc.`, 2],
    () => [`Xe ${V()} vượt đèn đỏ ở ${L()} rồi tông vào người đi đường. Tài xế cố chạy trốn nhưng bị dân bắt lại.`, 2],
    () => [`Ổ gà to giữa ${L()} không có biển báo, xe ${V()} tránh không kịp ngã xuống đường. Cần sửa chữa gấp trước khi thêm người bị nạn.`, 2],
    () => [`Tai nạn liên hoàn trên ${L()} ${T()}, nhiều xe ${V()} hư hỏng nặng. CSGT đang phân luồng tại hiện trường.`, 2],
    () => [`Đường trơn sau mưa ở ${L()}, ${V()} trượt ngã liên tục ${T()}. Bề mặt đường hỏng từ lâu mà không ai vá. ${E()}`, 2],
    () => [`Xe ${V()} mất lái trên ${L()} đâm vào dải phân cách. Lái xe may mắn an toàn nhưng giao thông tắc nghẽn kéo dài.`, 2],
    () => [`Chỗ ${L()} này không có vạch qua đường, người đi bộ rất dễ bị tai nạn. Kiến nghị mãi mà chẳng ai nghe.`, 1],
    () => [`Đèn đường trên ${L()} bị hỏng từ lâu, ${T()} tối mịt không thấy gì. Đã xảy ra ${choice(DAMAGE)} vụ tai nạn mà vẫn chưa được sửa.`, 2],
    () => [`Học sinh bị ngã do vỉa hè bong tróc trên ${L()}. Cha mẹ đưa đi cấp cứu mà vẫn chưa thấy ai đứng ra nhận trách nhiệm.`, 2],
    () => [`Cảnh báo: đoạn ${L()} đang có nhiều ổ gà sau mưa lớn, ${V()} đi cẩn thận kẻo ngã. Bà con đọc được thì giảm tốc nha!`, 1],
    () => [`Tôi thấy xe ${V()} phóng nhanh trên ${L()} rồi húc vào đuôi xe khác. Cả hai tài xế xuống cãi nhau giữa đường.`, 2],
    () => [`Tai nạn liên tiếp ở ${L()} do đường hẹp và thiếu biển báo ${T()}. Cần can thiệp ngay.`, 2],
    () => [`Va chạm giữa xe ${V()} và xe đạp điện ở ${L()} ${T()}, người đi xe đạp bị thương. May không nghiêm trọng hơn.`, 2],
    () => [`Tôi suýt bị tai nạn tại ${L()} vì có xe ${V()} chạy quá tốc độ bất ngờ ập đến. Tim đập mạnh cả người sau đó.`, 2],
    () => [`Đường ướt ở ${L()} sau mưa ${T()}, xe ${V()} phanh gấp trượt ra rãnh. Người điều khiển nhập viện, tình trạng ổn định.`, 2],
    () => [`Nhanh một giây, chậm cả đời! Khúc cua ${L()} nhiều xe phóng qua rất ẩu. Anh em chạy tuyến này nhớ giảm tốc từ xa nhé.`, 1],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["tai nạn"], priority };
}

function genDen() {
  const tpls = [
    () => [`Đèn tín hiệu tại ${L()} bị hỏng từ ${T()}, xe cộ hỗn loạn không ai nhường ai. Cảnh sát giao thông ở đâu hết rồi? ${E()}`, 1],
    () => [`Chạy đến ${L()} thì đèn đỏ đột nhiên nhảy thẳng sang xanh rồi lại đỏ không theo thứ tự. Không hiểu phải xử lý thế nào.`, 1],
    () => [`Đèn xanh tại ${L()} chỉ bật được ${choice(["3 giây","5 giây","7 giây"])}, xe muốn qua cũng không kịp. Ai lập trình đèn này vậy?`, 1],
    () => [`Sau Nghị định 168, người ta không dám vượt đèn đỏ dù đèn hỏng ở ${L()}. Kết quả là kẹt xe cứng ngắc vì ai cũng đứng chờ mãi.`, 1],
    () => [`Cột đèn giao thông ở ${L()} bị xe ${V()} húc ngã từ ${T()}, chưa được sửa. Giao thông rối loạn ${S()}.`, 1],
    () => [`Đèn tín hiệu ${L()} chỉ còn 1 chiều sáng, 3 chiều kia đèn tắt ngóm. Tài xế không biết đường nào được đi.`, 1],
    () => [`Phản ánh đèn tín hiệu hỏng ở ${L()} lần thứ ${choice(COUNTS)} rồi mà vẫn chưa thấy ai sửa. Thiếu trách nhiệm ${S()}.`, 1],
    () => [`Người dân ở ${L()} phải tự điều tiết giao thông vì đèn tín hiệu không hoạt động ${T()}. Không có CSGT, mọi người tự xử.`, 1],
    () => [`${E()} Đèn tín hiệu tại ${L()} bật đỏ cả 4 chiều cùng lúc, ai cũng dừng không ai đi được, kẹt xe ${S()}.`, 1],
    () => [`Hệ thống đèn thông minh ở ${L()} tốn mấy chục tỷ đồng nhưng cứ mưa lớn là tắt hoặc loạn nhịp.`, 1],
    () => [`Cảnh báo: đèn tín hiệu tại ${L()} đang hỏng pha xanh, chỉ còn đỏ và vàng hoạt động. Bà con đi qua cẩn thận.`, 1],
    () => [`Dân ${L()} phải dắt xe máy đi bộ qua giao lộ vì đèn tín hiệu chập chờn hoặc không hoạt động ${T()}.`, 1],
    () => [`Đèn tín hiệu mất tín hiệu ở ${L()} khiến xe cộ tê liệt. Mọi người lo sợ bị phạt nên không dám vượt dù đèn hỏng.`, 1],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["đèn tín hiệu"], priority };
}

function genVia() {
  const tpls = [
    () => [`Vỉa hè ${L()} bị lấn chiếm hoàn toàn, người đi bộ phải xuống lòng đường. Nguy hiểm ${S()} mà không ai dọn dẹp.`, 1],
    () => [`Quán xá bày bàn ghế chiếm hết vỉa hè ${L()}, mẹ đẩy xe nôi cũng không có chỗ đi. ${E()} Sao chịu nổi!`, 1],
    () => [`Vỉa hè ${L()} bị để xe máy kín mít từ sáng đến tối. Người đi bộ không còn chỗ, phải xuống lòng đường nguy hiểm.`, 1],
    () => [`Xe ${V()} leo lên vỉa hè ${L()} để tránh kẹt xe, người đi bộ cứ phải né ra. Vỉa hè là của ai vậy?`, 1],
    () => [`Vỉa hè khu vực ${L()} bong tróc, gạch vỡ nham nhở từ lâu. Người già và trẻ em đi qua rất dễ vấp ngã. Cần sửa gấp.`, 1],
    () => [`Hàng quán lấn chiếm vỉa hè ${L()} tới tận lòng đường, không biết lực lượng chức năng đứng ở đâu.`, 1],
    () => [`Dây điện thòng xuống ngay vỉa hè ${L()} ${S()} nguy hiểm, trẻ em chạy nhảy ở đó mà không ai cảnh báo.`, 2],
    () => [`Vỉa hè ${L()} sạch đẹp được mấy hôm sau đợt ra quân thì lại bị chiếm lại. Cần kiểm tra thường xuyên hơn.`, 1],
    () => [`Ở ${L()} vỉa hè bị đào lên để lắp cáp ngầm mà không có biển cảnh báo. Tôi suýt bị vấp ngã ${T()}. Thiếu an toàn ${S()}.`, 1],
    () => [`Cây xanh trồng trên vỉa hè ${L()} rễ trồi lên làm gạch bể lộm chộm. Đi bộ phải nhìn xuống chân từng bước. ${E()}`, 1],
    () => [`Vỉa hè có cũng như không ở ${L()}, người ta lấn chiếm để kinh doanh, người đi bộ đành xuống lòng đường.`, 0],
    () => [`Đừng dựa vào lý do kinh doanh mà lấn chiếm vỉa hè ở ${L()} trong khi đã có bao tai nạn xảy ra. Cần xử lý nghiêm.`, 1],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["vỉa hè"], priority };
}

function genViPham() {
  const tpls = [
    () => [`Xe ${V()} chạy ngược chiều trên ${L()} ${T()}, không ai xử lý hết. Luật giao thông ở đây như vô nghĩa.`, 1],
    () => [`Phạt nặng theo Nghị định 168 mà tôi vẫn thấy người ta chạy ẩu ở ${L()} ${T()}. Phạt mà không thực thi thì cũng như không.`, 0],
    () => [`Xe ${V()} dừng đỗ tùy tiện trên ${L()} chắn cả làn xe, không ai nhắc nhở hay xử phạt. Ý thức như vậy mà thôi.`, 1],
    () => [`Mức phạt mới tăng gấp chục lần nhưng nhiều người ở ${L()} vẫn vượt đèn đỏ. Cần lắp camera nhiều hơn chứ.`, 0],
    () => [`Tài xế xe ${V()} nhậu xong vẫn cầm lái trên ${L()} ${T()}. Kiểm tra nồng độ cồn cần tăng cường hơn nhiều.`, 2],
    () => [`Xe tải quá tải vẫn chạy vô tư trên ${L()}, mặt đường bị hỏng liên tục. Ai cấp phép? Ai kiểm soát?`, 1],
    () => [`Cảnh báo: CSGT đang đặt chốt ở ${L()} ${T()}, anh em nhớ đội mũ bảo hiểm và không dùng điện thoại khi lái xe.`, 0],
    () => [`Xe ${V()} leo lề ${L()} ban ngày ban mặt, không ai phạt. Dân thấy vậy cũng leo theo, trật tự giao thông xuống cấp ${S()}.`, 1],
    () => [`Nhiều người vẫn vi phạm tại ${L()} vì tỷ lệ bị bắt phạt quá thấp. Cần lắp camera và tăng cường tuần tra.`, 0],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["vi phạm luật"], priority };
}

function genYThuc() {
  const tpls = [
    () => [`Xe ${V()} cắt ngang đầu xe tôi ở ${L()} mà không xi nhan. Ý thức giao thông ${S()} tệ, cứ như đường của riêng họ.`, 1],
    () => [`Dừng đèn đỏ ở ${L()}, xe phía sau cứ bấm còi inh ỏi. Đèn đỏ mà bấm còi thì tôi biết làm gì? ${E()}`, 1],
    () => [`Vừa thấy cảnh xe ${V()} vượt ẩu ở ${L()}, suýt húc vào mấy em học sinh. Người ta cứ phóng nhanh như thể không sợ gì.`, 2],
    () => [`${E()} Tài xế ${V()} ở ${L()} vừa lái vừa nhìn điện thoại. Nguy hiểm không chỉ cho bản thân mà còn cả người xung quanh.`, 2],
    () => [`Xe ${V()} dừng đỗ sai chỗ ở ${L()}, chắn cả lề đường lẫn phần đường dành cho xe máy. Ai cũng khổ vì mấy người thiếu ý thức.`, 1],
    () => [`Chứng kiến ở ${L()}: 3 chiếc xe ${V()} cùng vượt đèn đỏ. Rồi khi xảy ra tai nạn thì đổ lỗi cho hạ tầng.`, 1],
    () => [`Xe buýt ở ${L()} vừa dừng ngay giữa đường để đón khách, không ra bến. Hành khách nhảy xuống nguy hiểm ${S()}.`, 2],
    () => [`Đi bộ sang đường ở ${L()} mà cứ phải chạy né vì xe ${V()} không nhường. Đèn dành cho người đi bộ mà xe vẫn phóng thẳng vào.`, 1],
    () => [`${E()} Xe container trên ${L()} không bật đèn xi nhan, chuyển làn đột ngột gần như đẩy xe tôi vào giải phân cách. Ớn ${S()}.`, 2],
    () => [`Ô tô, xe máy ngáng đường xe buýt ở ${L()} khiến hành khách xuống xe giữa lòng đường. Văn hóa nhường đường ${S()} kém.`, 1],
    () => [`Xe ${V()} nhiều lần phóng nhanh trong khu vực đông đúc ở ${L()}. Ai đó cần lên tiếng trước khi có người bị nạn.`, 2],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["ý thức giao thông"], priority };
}

function genHaTang() {
  const tpls = [
    () => [`Ổ gà trên ${L()} to tướng, lấp tạm rồi lại vỡ. Xe ${V()} qua đó liên tục hư lốp, tiền sửa xe còn nhiều hơn tiền đổ xăng.`, 1],
    () => [`Con đường ${L()} mới sửa xong ${choice(TIMES2)} đã xuống cấp trở lại. Chất lượng thi công kém ${S()}, tiền ai đang ăn?`, 1],
    () => [`Biển báo giao thông trên ${L()} bị che khuất bởi cây xanh, không nhìn thấy tốc độ tối đa hay vạch kẻ đường.`, 1],
    () => [`Hầm chui ${L()} bị ngập mỗi khi mưa lớn dù mới xây xong. Thiết kế kém hay thi công ẩu? Ai trả lời dân không?`, 2],
    () => [`Dải phân cách trên ${L()} bị xe ${V()} đâm vào từ hôm qua, nằm chắn giữa đường, cực kỳ nguy hiểm. Cần dọn dẹp ngay.`, 2],
    () => [`Hệ thống thoát nước dưới ${L()} bị hỏng từ lâu, mỗi lần mưa là ngập ngay. Đầu tư công trình kiểu gì vậy?`, 2],
    () => [`Cột đèn đường ${L()} bị gãy một tuần nay chưa thay. Đêm tối đen như mực, tai nạn liên tiếp xảy ra.`, 2],
    () => [`Metro ${L()} vừa vận hành được mấy ngày đã gặp sự cố kỹ thuật. Dự án nghìn tỷ mà chất lượng như vậy, ai dám đi?`, 1],
    () => [`Cầu trên ${L()} bị nứt dọc mặt cầu từ lâu, mỗi lần xe ${V()} qua là rung lắc ${S()}. Chờ tới khi sập mới sửa hay sao?`, 2],
    () => [`Đường ${L()} hẹp mà hai chiều, xe ${V()} qua nhau còn không có chỗ. Ở đây thường xuyên xảy ra va chạm mà không ai mở rộng đường.`, 1],
  ];
  const [text, priority] = choice(tpls)();
  return { text, category: ["hư hỏng hạ tầng"], priority };
}

// ── Filter ───────────────────────────────────────────────────────────────────
function normalize(text) {
  return text.replace(/\s+/g, ' ').replace(/ ([,.!?;:])/g, '$1').trim();
}
function wordCount(text) { return text.trim().split(/\s+/).length; }
function bigrams(text) {
  const t = text.toLowerCase().split(/\s+/);
  if (t.length < 2) return new Set(t);
  const bg = new Set();
  for (let i = 0; i < t.length - 1; i++) bg.add(t[i] + '|' + t[i + 1]);
  return bg;
}
function jaccard(a, b) {
  const sa = bigrams(a), sb = bigrams(b);
  let inter = 0;
  for (const x of sa) if (sb.has(x)) inter++;
  const union = sa.size + sb.size - inter;
  return union === 0 ? 1 : inter / union;
}

function filterData(records) {
  const cleaned = records
    .map(r => ({ ...r, text: normalize(r.text) }))
    .filter(r => wordCount(r.text) >= MIN_WORDS);
  const retained = [], texts = [];
  let dupsRemoved = 0;
  for (const rec of cleaned) {
    let dup = false;
    for (const existing of texts) {
      if (jaccard(rec.text, existing) > SIM_THRESHOLD) { dup = true; dupsRemoved++; break; }
    }
    if (!dup) { retained.push(rec); texts.push(rec.text); }
  }
  console.log(`  [filter] In: ${records.length} -> Sau loc ngan: ${cleaned.length} -> Sau khu trung: ${retained.length} (xoa ${dupsRemoved})`);
  return retained;
}

// ── Main ─────────────────────────────────────────────────────────────────────
console.log('='.repeat(60));
console.log('  Synthetic Data Generator - Giao thong do thi Viet Nam');
console.log('='.repeat(60));

console.log('\n[1] Doc seed_data.json ...');
const seedData = JSON.parse(readFileSync(SEED_FILE, 'utf-8'));
const seedCats = {};
for (const item of seedData) {
  for (const c of (item.category || [])) seedCats[c] = (seedCats[c] || 0) + 1;
  if (typeof item.category === 'string') item.category = [item.category.trim()];
  item.priority = item.priority ?? 1;
}
console.log(`    Tong mau seed: ${seedData.length}`);
console.log('    Phan phoi category:');
for (const [k, v] of Object.entries(seedCats).sort((a, b) => b[1] - a[1]))
  console.log(`      ${k.padEnd(30)}: ${v}`);

console.log(`\n[2] Sinh ${TARGET}+ mau tong hop ...`);
const GENS = [
  [genNgap,    34], [genKet,     22], [genNgapKet, 10],
  [genTaiNan,  12], [genDen,      8], [genVia,      7],
  [genViPham,   5], [genYThuc,    5], [genHaTang,   3],
];
const genFns = GENS.map(g => g[0]);
const genWts = GENS.map(g => g[1]);

const rawSynthetic = choices(genFns, genWts, TARGET * 2).map(fn => fn());
console.log(`    Da sinh (tho): ${rawSynthetic.length} mau`);

console.log('\n[3] Ap dung filterData() cho synthetic ...');
let filteredSynthetic = filterData(rawSynthetic);

let attempt = 1;
while (filteredSynthetic.length < TARGET && attempt <= 5) {
  console.log(`    Sinh them (lan ${attempt}) vi chua du ${TARGET} mau ...`);
  const extra = choices(genFns, genWts, (TARGET - filteredSynthetic.length) * 3).map(fn => fn());
  filteredSynthetic = filterData([...filteredSynthetic, ...extra]);
  attempt++;
}
console.log(`    Synthetic sau loc: ${filteredSynthetic.length} mau`);

console.log('\n[4] Gop seed + synthetic va loc lan cuoi ...');
const allData = [...seedData, ...filteredSynthetic];
const finalData = filterData(allData);
console.log(`    Tong cong: ${finalData.length} mau (seed: ${seedData.length}, synthetic: ${finalData.length - seedData.length})`);

const finalCats = {};
for (const item of finalData) for (const c of (item.category || [])) finalCats[c] = (finalCats[c] || 0) + 1;
console.log('\n    Phan phoi category cuoi:');
for (const [k, v] of Object.entries(finalCats).sort((a, b) => b[1] - a[1]))
  console.log(`      ${k.padEnd(30)}: ${v}`);

const pDist = {};
for (const item of finalData) pDist[item.priority] = (pDist[item.priority] || 0) + 1;
console.log('    Priority:', JSON.stringify(pDist));

console.log('\n[5] Xuat ra augmented_dataset.json ...');
writeFileSync(OUTPUT_FILE, JSON.stringify(finalData, null, 2), 'utf-8');
const sz = statSync(OUTPUT_FILE).size;
console.log(`    Done! augmented_dataset.json  (${Math.round(sz / 1024)} KB, ${finalData.length} mau)`);
console.log('='.repeat(60));
