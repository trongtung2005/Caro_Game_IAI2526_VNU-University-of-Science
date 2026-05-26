# Caro_Game_IAI2526_VNU-University-of-Science
Project cuối kỳ của môn học Nhập môn trí tuệ nhân tạo HUS - Giảng viên: CN.Vi Anh Quân, GS.Nguyễn Thế Toàn

Code trên phần mềm Visual Studio Code đăng nhập bằng tk github của mình đẫ liên kết trở thành người sửa

Cài đặt git https://git-scm.com/install/

Vào VSCode -> Terminal
Gõ: git clone https://github.com/trongtung2005/Caro_Game_IAI2526_VNU-University-of-Science.git

Lấy code mới nhất: git pull origin main

Upload code:

Bước 1: git add .

Bước 2:  git commit -m "Lời nhắn ghi rõ mình vừa sửa cái gì"

Bước 3: git pull origin main

Bước 3: git push origin main



# 🎮 Caro Game with AI - Minimax Algorithm comebine with 

Dự án cuối kỳ môn: **Nhập môn Trí tuệ Nhân tạo**
Trường: Đại học Khoa học Tự nhiên, ĐHQGHN (HUS)
Giảng viên hướng dẫn:CN. Thầy Vi Anh Quân,GS. Thầy Nguyễn Thế Toàn

## 📝 Giới thiệu
Đây là tựa game Caro truyền thống được phát triển bằng Python (thư viện Pygame). Điểm nổi bật của dự án là việc tích hợp Trí tuệ nhân tạo (AI) sử dụng thuật toán **Minimax** kết hợp cắt tỉa **Alpha-Beta (Alpha-Beta Pruning)** và hàm Heuristic đánh giá thế cờ chuyên sâu.

## ✨ Tính năng nổi bật
* **Giao diện đồ họa (UI):**
* **Tùy biến linh hoạt:** Cho phép người chơi chọn kích thước bàn cờ (10x10, 12x12, 15x15).
* **AI thông minh:** 3 cấp độ khó khác nhau (Độ sâu Minimax: 1, 2, 3).
* **Hỗ trợ người chơi:** Tích hợp tính năng Undo (Đi lại) và Reset ván đấu trực tiếp bằng phím tắt hoặc nhập lệnh Terminal.
* **Xuất biên bản:** Tự động in biên bản ván đấu (PGN) ra Terminal khi kết thúc.

## 🚀 Hướng dẫn cài đặt và chạy game
**Bước 1:** Clone kho lưu trữ này về máy:
`git clone https://github.com/trongtung2005/Caro_Game_IAI2526_VNU-University-of-Science.git`

**Bước 2:** Cài đặt thư viện Pygame (nếu chưa có):
`pip install pygame`

**Bước 3:** Chạy file giao diện chính:
`python UI.py`

## 🛠️ Công nghệ sử dụng
* Ngôn ngữ: Python3
* Thư viện: Pygame, Threading, Math, Re
