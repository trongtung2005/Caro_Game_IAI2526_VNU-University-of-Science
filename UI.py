import pygame
import sys
import threading
import time
import re
import math 
import os

from Logic_game import CaroLogic

class CaroUI:
    def __init__(self):
        self.logic = CaroLogic()

        self.orig_bg_image = None
        self.scaled_game_bg = None

        self.COLOR_BG = (20, 20, 25)           # Màu nền dự phòng (Đen xám)
        self.COLOR_BOARD = (30, 30, 35)        # Màu bảng dự phòng
        self.COLOR_GRID = (0, 255, 255)        # Lưới màu Xanh Cyan phát sáng
        self.COLOR_TEXT = (255, 255, 255)      # Chữ tọa độ màu Trắng
        self.COLOR_X = (255, 0, 128)           # Quân X màu Hồng Neon
        self.COLOR_O = (57, 255, 20)           # Quân O màu Xanh lá Neon
        self.COLOR_HIGHLIGHT = (255, 255, 200) # Khung viền Vàng cho nước đi vừa đánh
        
        self.GRID_SIZE = 40                             
        self.PADDING = 40  
        
        self.input_buffer = ""
        self.game_running = True

        # BIẾN QUẢN LÝ QUYỀN ĐI TRƯỚC: -1 mặc định là O (đi trước), 1 là X (đi sau)
        self.player_side = -1  
        self.bot_side = 1
        
        # Biến lưu vị trí vừa đánh để highlight
        self.last_move = None

        # === KHỞI TẠO ÂM THANH & NHẠC NỀN ===
        pygame.mixer.init()
        
        # 1. Nhạc nền (Cập nhật theo tên file của Tùng)
        try:
            pygame.mixer.music.load("background_music.mp3")
            pygame.mixer.music.set_volume(0.3) # Nhạc nền để nhỏ (30%)
            pygame.mixer.music.play(-1)        # -1 để lặp vô hạn
        except Exception as e:
            print(f"⚠️ Không tìm thấy nhạc nền (background_music.mp3). Lỗi: {e}")

        # 2. Hiệu ứng âm thanh SFX (Cập nhật sang đuôi .mp3 theo file của Tùng)
        try:
            self.sound_move = pygame.mixer.Sound("move.mp3")
            self.sound_win = pygame.mixer.Sound("win.mp3")
            self.sound_lose = pygame.mixer.Sound("lose.mp3")
            
            self.sound_move.set_volume(0.8)
            self.sound_win.set_volume(0.7)
            self.sound_lose.set_volume(0.7)
        except Exception as e:
            print(f"⚠️ Không tìm thấy file âm thanh hiệu ứng (.mp3). Lỗi: {e}")
            self.sound_move = self.sound_win = self.sound_lose = None

    def play_sfx(self, sound_obj):
        """Hàm hỗ trợ phát âm thanh an toàn"""
        if sound_obj:
            sound_obj.play()

    def parse_terminal_input(self, move_str):
        move_str = move_str.strip().upper()
        max_char = chr(ord('A') + self.logic.board_size - 1)
        match = re.match(r"^([A-" + max_char + r"])([1-9][0-5]?)$", move_str)
        if not match: return None
        col_char, row_str = match.groups()
        col = ord(col_char) - ord('A')
        row = int(row_str) - 1
        if 0 <= row < self.logic.board_size and 0 <= col < self.logic.board_size:
            return row, col
        return None

    def terminal_input_loop(self):
        while True:
            if self.game_running and not self.logic.game_over and self.logic.current_turn == self.player_side and not self.logic.bot_thinking:
                try:
                    user_input = input().strip()
                    if user_input: self.input_buffer = user_input
                except: pass
            time.sleep(0.1)

    def bot_calculation_worker(self):
        self.logic.bot_thinking = True
        
        with self.logic.lock:
            board_copy = [row[:] for row in self.logic.board]
        
        # Báo cho hàm minimax biết Bot đang đóng vai trò nào
        _, move = self.logic.minimax(board_copy, depth=self.logic.bot_depth, alpha=-math.inf, beta=math.inf, maximizing_player=(self.bot_side == 1))
        
        if move and not self.logic.game_over:
            r, c = move
            success, is_win, move_str = self.logic.play_move(r, c, self.bot_side)
            if success:
                self.play_sfx(self.sound_move) # Tiếng Bot hạ quân
                self.last_move = (r, c)
                print(f"-> Bot đáp trả: {move_str}")
                if is_win: print("\n[KẾT THÚC] BOT ĐÃ THẮNG!")
                else: print("Nhập nước đi (Ví dụ: H8) hoặc [U: Undo], [R: Reset]: ")
                
        self.logic.bot_thinking = False

    def draw_ui(self, screen, font):
        board_pixels = self.logic.board_size * self.GRID_SIZE
        window_size = board_pixels + (self.PADDING * 2)
        
        if self.orig_bg_image:
            screen.blit(self.scaled_game_bg, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
            pygame.draw.rect(screen, self.COLOR_BOARD, (self.PADDING, self.PADDING, board_pixels, board_pixels))
        
        for i in range(self.logic.board_size + 1):
            pygame.draw.line(screen, self.COLOR_GRID, (self.PADDING, self.PADDING + i * self.GRID_SIZE), (self.PADDING + board_pixels, self.PADDING + i * self.GRID_SIZE), 1)
            pygame.draw.line(screen, self.COLOR_GRID, (self.PADDING + i * self.GRID_SIZE, self.PADDING), (self.PADDING + i * self.GRID_SIZE, self.PADDING + board_pixels), 1)
        
        for i in range(self.logic.board_size):
            col_char = chr(i + ord('A'))
            text_surface = font.render(col_char, True, self.COLOR_TEXT)
            pos_x = self.PADDING + i * self.GRID_SIZE + (self.GRID_SIZE - text_surface.get_width()) // 2
            screen.blit(text_surface, (pos_x, self.PADDING // 3))                 
            screen.blit(text_surface, (pos_x, window_size - self.PADDING + 10))   
            
            row_num = str(i + 1)
            text_surface = font.render(row_num, True, self.COLOR_TEXT)
            pos_y = self.PADDING + i * self.GRID_SIZE + (self.GRID_SIZE - text_surface.get_height()) // 2
            screen.blit(text_surface, (self.PADDING // 3, pos_y))                 
            screen.blit(text_surface, (window_size - self.PADDING + 15, pos_y))   

        # Highlight ô vừa đánh
        if self.last_move:
            lr, lc = self.last_move
            hx = self.PADDING + lc * self.GRID_SIZE
            hy = self.PADDING + lr * self.GRID_SIZE
            pygame.draw.rect(screen, self.COLOR_HIGHLIGHT, (hx, hy, self.GRID_SIZE, self.GRID_SIZE), 3)

        with self.logic.lock:
            for r in range(self.logic.board_size):
                for c in range(self.logic.board_size):
                    center_x = self.PADDING + c * self.GRID_SIZE + self.GRID_SIZE // 2
                    center_y = self.PADDING + r * self.GRID_SIZE + self.GRID_SIZE // 2
                    if self.logic.board[r][c] == 1: 
                        pygame.draw.line(screen, self.COLOR_X, (center_x - 12, center_y - 12), (center_x + 12, center_y + 12), 4)
                        pygame.draw.line(screen, self.COLOR_X, (center_x + 12, center_y - 12), (center_x - 12, center_y + 12), 4)
                    elif self.logic.board[r][c] == -1: 
                        pygame.draw.circle(screen, self.COLOR_O, (center_x, center_y), 14, 4)

    def show_menu(self, screen, font):
        menu_running = True
        title_font = pygame.font.SysFont("tahoma", 28, bold=True)
        sub_font = pygame.font.SysFont("tahoma", 18, bold=True)
        
        btn_size_10 = pygame.Rect(100, 120, 100, 45)
        btn_size_12 = pygame.Rect(220, 120, 100, 45)
        btn_size_15 = pygame.Rect(340, 120, 100, 45)
        
        btn_easy = pygame.Rect(100, 230, 100, 45)
        btn_medium = pygame.Rect(220, 230, 100, 45)
        btn_hard = pygame.Rect(340, 230, 100, 45)
        
        btn_first_player = pygame.Rect(120, 340, 130, 45)
        btn_first_bot = pygame.Rect(290, 340, 130, 45)

        btn_start = pygame.Rect(170, 440, 200, 55)

        while menu_running:
            screen.fill(self.COLOR_BG)
            
            overlay = pygame.Surface((540, 540))
            overlay.set_alpha(150) 
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            screen.blit(title_font.render("CẤU HÌNH TRẬN ĐẤU", True, (0, 255, 255)), (screen.get_width() // 2 - 140, 30))

            # 1. Kích thước
            screen.blit(sub_font.render("1. Kích thước bàn cờ:", True, self.COLOR_TEXT), (60, 80))
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 10 else (80, 80, 80), btn_size_10, border_radius=6)
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 12 else (80, 80, 80), btn_size_12, border_radius=6)
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 15 else (80, 80, 80), btn_size_15, border_radius=6)
            screen.blit(font.render("10 x 10", True, (255,255,255)), (btn_size_10.centerx-25, btn_size_10.centery-10))
            screen.blit(font.render("12 x 12", True, (255,255,255)), (btn_size_12.centerx-25, btn_size_12.centery-10))
            screen.blit(font.render("15 x 15", True, (255,255,255)), (btn_size_15.centerx-25, btn_size_15.centery-10))

            # 2. Độ khó
            screen.blit(sub_font.render("2. Trí tuệ AI (Độ khó):", True, self.COLOR_TEXT), (60, 190))
            pygame.draw.rect(screen, (46, 204, 113) if self.logic.bot_depth == 1 else (80, 80, 80), btn_easy, border_radius=6)
            pygame.draw.rect(screen, (241, 196, 15) if self.logic.bot_depth == 2 else (80, 80, 80), btn_medium, border_radius=6)
            pygame.draw.rect(screen, (231, 76, 60) if self.logic.bot_depth == 3 else (80, 80, 80), btn_hard, border_radius=6)
            screen.blit(font.render("DỄ", True, (255,255,255)), (btn_easy.centerx-10, btn_easy.centery-10))
            screen.blit(font.render("VỪA", True, (255,255,255)), (btn_medium.centerx-15, btn_medium.centery-10))
            screen.blit(font.render("KHÓ", True, (255,255,255)), (btn_hard.centerx-12, btn_hard.centery-10))

            # 3. Quyền đi trước
            screen.blit(sub_font.render("3. Quyền đi trước (Luôn cầm O):", True, self.COLOR_TEXT), (60, 300))
            pygame.draw.rect(screen, (0, 255, 255) if self.player_side == -1 else (80, 80, 80), btn_first_player, border_radius=6)
            pygame.draw.rect(screen, (0, 255, 255) if self.bot_side == -1 else (80, 80, 80), btn_first_bot, border_radius=6)
            screen.blit(font.render("NGƯỜI (O)", True, (0,0,0) if self.player_side == -1 else (255,255,255)), (btn_first_player.centerx-35, btn_first_player.centery-10))
            screen.blit(font.render("MÁY (O)", True, (0,0,0) if self.bot_side == -1 else (255,255,255)), (btn_first_bot.centerx-30, btn_first_bot.centery-10))

            # Nút VÀO TRẬN
            pygame.draw.rect(screen, (0, 255, 255), btn_start, border_radius=10)
            text_start = sub_font.render("VÀO TRẬN ĐẤU", True, (0, 0, 0))
            screen.blit(text_start, (btn_start.centerx - text_start.get_width() // 2, btn_start.centery - text_start.get_height() // 2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if btn_size_10.collidepoint(pos): self.logic.board_size = 10
                    elif btn_size_12.collidepoint(pos): self.logic.board_size = 12
                    elif btn_size_15.collidepoint(pos): self.logic.board_size = 15
                    elif btn_easy.collidepoint(pos): self.logic.bot_depth = 1
                    elif btn_medium.collidepoint(pos): self.logic.bot_depth = 2
                    elif btn_hard.collidepoint(pos): self.logic.bot_depth = 3
                    elif btn_first_player.collidepoint(pos): 
                        self.player_side = -1
                        self.bot_side = 1
                    elif btn_first_bot.collidepoint(pos): 
                        self.player_side = 1
                        self.bot_side = -1
                    elif btn_start.collidepoint(pos): menu_running = False

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((540, 540))
        pygame.display.set_caption("Đại chiến cờ Caro AI")
        
        # === ĐỔI ICON CỬA SỔ ===
        try:
            icon_image = pygame.image.load("icon.png")
            pygame.display.set_icon(icon_image)
        except Exception as e:
            pass

        font = pygame.font.SysFont("tahoma", 14, bold=True)
        clock = pygame.time.Clock()
        
        input_thread = threading.Thread(target=self.terminal_input_loop)
        input_thread.daemon = True
        input_thread.start()

        while True:
            # === SỬA LỖI: PHÁT LẠI NHẠC NỀN KHI QUAY VỀ MENU / CHƠI VÁN MỚI ===
            try:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
            except Exception as e:
                pass
            # =================================================================

            self.show_menu(screen, font)
            
            board_pixels = self.logic.board_size * self.GRID_SIZE
            window_size = board_pixels + (self.PADDING * 2)
            screen = pygame.display.set_mode((window_size, window_size))
            
            if self.orig_bg_image:
                self.scaled_game_bg = pygame.transform.scale(self.orig_bg_image, (window_size, window_size))

            self.logic.reset_game()
            self.last_move = None 
            
            print(f"\n=== TRẬN ĐẤU MỚI: BÀN CỜ {self.logic.board_size}x{self.logic.board_size} - AI CẤP ĐỘ {self.logic.bot_depth} ===")
            print(" * [U]: Undo đi lại  |  [R]: Reset làm mới")

            while self.game_running:
                # Xử lý Terminal Input cho Người chơi
                if self.logic.current_turn == self.player_side and self.input_buffer != "" and not self.logic.bot_thinking:
                    cmd = self.input_buffer.upper()
                    self.input_buffer = ""
                    
                    if cmd == 'U':
                        if self.logic.undo_move(): 
                            self.last_move = None 
                            print("Đã lùi lại 1 lượt đi!")
                        else: print("Không thể Undo lúc này!")
                    elif cmd == 'R':
                        self.logic.reset_game()
                        self.last_move = None
                        print("Trận đấu đã được làm mới!")
                    else:
                        coords = self.parse_terminal_input(cmd)
                        if coords is None: print("❌ Định dạng sai! Nhập lại: ")
                        else:
                            success, is_win, move_str = self.logic.play_move(coords[0], coords[1], self.player_side)
                            if success: 
                                self.play_sfx(self.sound_move) # Tiếng Người hạ quân
                                self.last_move = (coords[0], coords[1]) 
                                print(f"-> Bạn đi (Terminal): {move_str}")
                            else: print("❌ Ô đã có quân! Chọn ô khác: ")

                # Lượt của Máy (Khởi động luồng AI)
                if self.logic.current_turn == self.bot_side and not self.logic.game_over and not self.logic.bot_thinking:
                    bot_thread = threading.Thread(target=self.bot_calculation_worker)
                    bot_thread.daemon = True
                    bot_thread.start()

                # Xử lý UI Pygame
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.logic.print_pgn_final()
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_u:
                            if self.logic.undo_move(): 
                                self.last_move = None
                                print(" Đã lùi lại 1 lượt đi!")
                        elif event.key == pygame.K_r:
                            self.logic.reset_game()
                            self.last_move = None
                            print("Trận đấu đã được làm mới!")

                    # Xử lý Click chuột cho Người chơi
                    if event.type == pygame.MOUSEBUTTONDOWN and not self.logic.game_over and self.logic.current_turn == self.player_side and not self.logic.bot_thinking:
                        mouseX, mouseY = pygame.mouse.get_pos()
                        c = (mouseX - self.PADDING) // self.GRID_SIZE
                        r = (mouseY - self.PADDING) // self.GRID_SIZE
                        
                        if 0 <= c < self.logic.board_size and 0 <= r < self.logic.board_size:
                            success, is_win, move_str = self.logic.play_move(r, c, self.player_side)
                            if success: 
                                self.play_sfx(self.sound_move) # Tiếng Người hạ quân
                                self.last_move = (r, c) 
                                print(f"-> Bạn đi (UI Mouse): {move_str}")

                # Game Over Animation
                if self.logic.game_over:
                    # === KIỂM TRA ĐỂ PHÁT NHẠC THẮNG/THUA ===
                    pygame.mixer.music.stop() # Tắt nhạc nền để bật nhạc Win/Lose rõ hơn
                    if self.logic.current_turn == self.player_side:
                        self.play_sfx(self.sound_win)
                    else:
                        self.play_sfx(self.sound_lose)
                        
                    self.draw_ui(screen, font)
                    pygame.display.flip()
                    time.sleep(1.5)
                    
                    overlay = pygame.Surface((window_size, window_size))
                    overlay.set_alpha(200)
                    overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    
                    msg, color = ("BẠN ĐÃ CHIẾN THẮNG!", (57, 255, 20)) if self.logic.current_turn == self.player_side else ("BẠN THUA RỒI!", (255, 0, 128))
                    title_font = pygame.font.SysFont("tahoma", 24, bold=True)
                    hint_font = pygame.font.SysFont("tahoma", 14)
                    
                    screen.blit(title_font.render(msg, True, color), (window_size//2 - 120, window_size//2 - 30))
                    screen.blit(hint_font.render("(Nhấn chuột bất kỳ để quay lại Menu)", True, (255, 255, 255)), (window_size//2 - 130, window_size//2 + 20))
                    pygame.display.flip()
                    
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.logic.print_pgn_final()
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                waiting = False
                    
                    self.logic.print_pgn_final()
                    break 

                if self.game_running:
                    self.draw_ui(screen, font)
                    pygame.display.flip()
                clock.tick(30)

if __name__ == "__main__":
    app = CaroUI()
    app.run()