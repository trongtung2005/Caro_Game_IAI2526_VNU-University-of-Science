# Caro_Game_IAI2526_VNU-University-of-Science
Project cuối kỳ của môn học Nhập môn trí tuệ nhân tạo HUS - Giảng viên: CN.Vi Anh Quân, GS.Nguyễn Thế Toàn



# Cách sửa code
Cài đặt git https://git-scm.com/install/

Tạo file forder -> chuột phải -> git bash -> git clone https://github.com/trongtung2005/Caro_Game_IAI2526_VNU-University-of-Science.git

Hay (Vào VSCode -> Terminal ->git clone https://github.com/trongtung2005 Caro_Game_IAI2526_VNU-University-of-Science.git
Code trên phần mềm Visual Studio Code đăng nhập bằng tk github của mình đẫ liên kết trở thành người sửa )

Lấy code mới nhất: git pull origin main

Upload code:

Bước 1: git add .

Bước 2:  git commit -m "Lời nhắn ghi rõ mình vừa sửa cái gì"

Bước 3: git pull origin main

Bước 3: git push origin main


# 🎮 Giới thiệu chung
☆ Nếu bạn yêu thích các thể loại trò chơi trí tuệ hẳn bạn không hề xa lạ với cờ caro. Hầu hết những ai đã từng đến trường đều đã thử sức mình với môn cờ đơn giản những cũng giàu tính chiến thuật này. Để bắt đầu chơi cờ caro thì rất dễ chỉ cần một tờ giấy và 2 cây bút bất kỳ là có thể chơi được nhưng để chiến thắng và hiểu hết về nó thì không hề đơn giản.
☆ Chơi cờ Caro một Game trí tuệ đã rất quen thuộc với mỗi chúng ta. Với lối chơi đơn giản nhưng yếu tố trí tuệ lại rất cao nên Chơi Cờ Caro được rất nhiều người yêu thích đặc biệt là các bạn học sinh, sinh viên và dân văn phòng.
☆ Đây là Game Đại Chiến Cờ Caro AI giúp bạn có thể chơi chế độ 1 người với máy hoặc 2 máy với nhau trên bàn cờ caro 10x10, 12x12 hoặc 15x15, và bạn cũng sẽ có nhiều cơ hội thể hiện tài đấu trí của bản thân hơn! Hãy cố gắng đánh bại đối thủ trên bàn cờ caro hoặc so tài cùng bạn bè trong game đấu trí cờ caro này nhé!
☆ Game Đại Chiến Cờ Caro AI là ứng dụng giúp bạn có những phút giây giải trí đầy trí tuệ
☆ Game cờ caro là trò chơi điện tử đối kháng yêu cầu tư duy logic chiến thuật, tuy có lối chơi đơn giản nhưng rất trí tuệ. Hai cờ thủ đi lần lượt, bên nào sắp xếp được 5 quân cờ ca rô thẳng hàng trước không chặn hai đầu sẽ giành phần thắng. Trò chơi cờ ca-rô giúp rèn luyện tư duy trí tuệ và phát triển IQ rất tốt.
☆ Để dành chiến thắng bạn cần sở hữu kinh nghiệm chơi cờ, biết cách ra những đòn hiểm hóc, biết đánh lừa và khiến đối phương bị dẫn dụ. Về cơ bản thì việc đầu tiên bạn cần làm là thường xuyên luyện tập để nâng cao kỹ năng. Ngoài ra có thể quan sát người chơi có trình độ tốt hơn để học hỏi kinh nghiệm của họ. Ngoài ra đừng quên những mẹo chơi cờ để luôn dành chiến thắng:
Chúc bạn có những phút giây vui vẻ !

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
