# Caro_Game_IAI2526_VNU-University-of-Science
Dự án cuối kỳ của môn học: **Nhập môn Trí tuệ nhân tạo PHY1313**
Trường: **Trường Đại học Khoa học Tự nhiên, ĐHQGHN (VNU-HUS)**
Giảng viên: **CN. Vi Anh Quân, GS. Nguyễn Thế Toàn**
Sinh viên thực hiện: **Lại Huy Hoàng, Tô Quang Hân, Nguyễn Bá Tiến Phát, Nguyễn Trọng Tùng**

# 🎮 Giới thiệu chung
Nếu bạn yêu thích các thể loại trò chơi trí tuệ hẳn bạn không hề xa lạ với cờ Caro (Gomoku). Hầu hết những ai đã từng đến trường đều đã thử sức mình với môn cờ đơn giản nhưng cũng giàu tính chiến thuật này. Lối chơi đơn giản, quen thuộc nhưng yếu tố trí tuệ lại rất cao khiến Cờ Caro được rất nhiều người yêu thích, đặc biệt là các bạn học sinh, sinh viên và dân văn phòng. Để bắt đầu thì rất dễ, chỉ cần một tờ giấy và 2 cây bút là có thể chơi được, nhưng để chiến thắng và hiểu hết về nó thì không hề đơn giản.

Trò chơi đòi hỏi tư duy logic chiến thuật. Hai cờ thủ đi lần lượt, bên nào sắp xếp được **5 quân cờ thẳng hàng (ngang, dọc, chéo) trước và KHÔNG BỊ CHẶN HAI ĐẦU** sẽ giành phần thắng. Để giành chiến thắng, bạn cần sở hữu kinh nghiệm, biết cách ra những đòn hiểm hóc, dẫn dụ đối phương. 

Dự án **Đại Chiến Cờ Caro AI** được phát triển nhằm đưa trải nghiệm quen thuộc này lên nền tảng kỹ thuật số, đồng thời tích hợp Trí tuệ nhân tạo (AI) sử dụng thuật toán **Minimax kết hợp Alpha-Beta Pruning**, giúp bạn có những phút giây giải trí rèn luyện IQ hoặc so tài cùng bạn bè!
---
Chúc bạn có những phút giây vui vẻ!

## ✨ Tính năng nổi bật

### 🧠 Trí tuệ nhân tạo (AI)
* **Thuật toán cốt lõi:** Minimax kết hợp cắt tỉa Alpha-Beta (Alpha-Beta Pruning).
* **Hàm Heuristic:** Đánh giá thế cờ theo ma trận Công - Thủ tinh vi, AI biết ưu tiên chặn các thế cờ nguy hiểm của người chơi trước khi tấn công.
* **Đa dạng độ khó:** 3 cấp độ AI (Độ sâu Minimax 1, 2, 3).

### 🕹️ Chế độ chơi & Tùy biến
* **3 Chế độ thi đấu:** * 1 Người chơi vs Máy (PvE).
  * 2 Người chơi (PvP - So tài trực tiếp trên cùng máy).
  * AI đấu với AI (EvE - Quan sát thuật toán tự đấu).
* **Kích thước bàn cờ:** Lựa chọn linh hoạt giữa `10x10`, `12x12`, và `15x15`.
* **Luật chơi Việt Nam:** Tích hợp chặt chẽ luật "Chặn 2 đầu không tính thắng".

### 🎨 Trải nghiệm người dùng (UX/UI)
* Giao diện Dark Mode/Cyberpunk hiện đại.
* **Hiệu ứng đặc biệt:** * *Particle:* Các hạt trôi nổi mượt mà ở màn hình Menu.
  * *Ripple:* Hiệu ứng gợn sóng nước sinh động mỗi khi click chuột.
  * *Ghost Piece:* Hiển thị trước quân cờ mờ khi di chuột vào ô trống.
  * *Blinking Win:* Nhấp nháy liên tục đường cờ chiến thắng trong 3 giây.
* **Đồng hồ bấm giờ:** Hiển thị tổng thời gian ván đấu và thời gian suy nghĩ của từng bên (O và X).
* **Âm thanh (SFX):** Nhạc nền, tiếng đặt cờ, tiếng click nút, âm báo thắng/thua. Hỗ trợ hệ thống điều chỉnh âm lượng độc lập (+ / -).

### ⚙️ Tính năng hỗ trợ
* Hỗ trợ thao tác Undo (Đi lại), Trợ giúp (Hint từ AI), Chơi lại (Reset), và Tạm dừng (Pause).
* Tự động xuất biên bản ván đấu (PGN) ra Terminal sau khi kết thúc.

## 🚀 Hướng dẫn cài đặt và chạy game
**Bước 1:** Clone kho lưu trữ này về máy:
`git clone https://github.com/trongtung2005/Caro_Game_IAI2526_VNU-University-of-Science.git`

**Bước 2:** Cài đặt thư viện Pygame (nếu chưa có):
`pip install pygame`

**Bước 3:** Chạy file giao diện chính:
`python UI.py`

## 🛠️ Công nghệ sử dụng
* Ngôn ngữ: Python3
* Thư viện: Pygame, Threading, Math, Re, OS, Random
