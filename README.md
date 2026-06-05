# Caro_Game_IAI2526_VNU-University-of-Science
Dự án cuối kỳ của môn học: **Nhập môn Trí tuệ nhân tạo PHY1313**

Trường: **Trường Đại học Khoa học Tự nhiên, ĐHQGHN (VNU-HUS)**

Giảng viên: **CN. Vi Anh Quân, GS. Nguyễn Thế Toàn**

Sinh viên thực hiện: **Lại Huy Hoàng, Tô Quang Hân, Nguyễn Bá Tiến Phát, Nguyễn Trọng Tùng**

# 🎮 Giới thiệu chung

Cờ Caro (Gomoku) từ lâu đã là một trò chơi trí tuệ kinh điển, gắn liền với tuổi thơ và giảng đường của biết bao thế hệ. Chỉ với một tờ giấy và hai chiếc bút, bất kỳ ai cũng có thể dễ dàng bắt đầu một ván cờ. Tuy nhiên, đằng sau sự mộc mạc ấy lại là cả một nghệ thuật tư duy chiến thuật sâu sắc, khiến Caro luôn giữ được sức hút mãnh liệt đối với học sinh, sinh viên và giới văn phòng. Dễ chơi là vậy, nhưng để nắm giữ thế trận và giành chiến thắng lại là một thử thách không hề nhỏ.

Trò chơi là một cuộc đấu trí thực thụ đòi hỏi tư duy logic và tầm nhìn chiến lược. Hai kỳ thủ sẽ luân phiên đặt quân, người chiến thắng là người đầu tiên thiết lập thành công chuỗi **5 quân cờ liên tiếp (ngang, dọc hoặc chéo) và không bị chặn hai đầu**. Để vươn tới chiến thắng, bạn không chỉ cần một phòng tuyến vững chắc mà còn phải biết kiến tạo những đòn đánh hiểm hóc, giăng bẫy và dồn ép đối phương vào thế bí.

Dự án **Đại Chiến Cờ Caro AI** ra đời với mục tiêu số hóa trải nghiệm quen thuộc này, đồng thời mang đến một làn gió mới bằng việc tích hợp Trí tuệ nhân tạo (AI). Hệ thống AI không chỉ đơn thuần là những dòng code, mà đóng vai trò như một kỳ thủ ảo đáng gờm, sẵn sàng thử thách và giúp bạn mài giũa tư duy chiến thuật mỗi ngày.

***

Chúc bạn có những trận đấu thật bùng nổ và những phút giây giải trí tuyệt vời!

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
