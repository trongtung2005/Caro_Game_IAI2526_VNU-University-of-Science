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

        self.COLOR_BG = (20, 20, 25)           
        self.COLOR_BOARD = (30, 30, 35)        
        self.COLOR_GRID = (0, 255, 255)        
        self.COLOR_TEXT = (255, 255, 255)      
        self.COLOR_X = (255, 0, 128)           
        self.COLOR_O = (57, 255, 20)           
        self.COLOR_HIGHLIGHT = (255, 255, 200) 
        self.COLOR_HINT = (255, 165, 0)        # Màu Cam viền nét đứt cho ô Trợ giúp
        
        self.GRID_SIZE = 40                             
        self.PADDING = 40  
        
        self.input_buffer = ""
        self.game_running = True

        self.player_side = -1  
        self.bot_side = 1
        
        self.last_move = None
        self.hint_move = None # Biến lưu trữ tọa độ do AI trợ giúp

        # Khởi tạo âm thanh
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("background_music.mp3")
            pygame.mixer.music.set_volume(0.3) 
        except Exception: pass

        try:
            self.sound_move = pygame.mixer.Sound("move.mp3")
            self.sound_win = pygame.mixer.Sound("win.mp3")
            self.sound_lose = pygame.mixer.Sound("lose.mp3")
            self.sound_move.set_volume(0.8)
            self.sound_win.set_volume(0.7)
            self.sound_lose.set_volume(0.7)
        except Exception:
            self.sound_move = self.sound_win = self.sound_lose = None

        # Khai báo các nút bấm
        self.btn_home = pygame.Rect(0,0,0,0)
        self.btn_undo = pygame.Rect(0,0,0,0)
        self.btn_reset = pygame.Rect(0,0,0,0)
        self.btn_hint = pygame.Rect(0,0,0,0)

    def play_sfx(self, sound_obj):
        if sound_obj: sound_obj.play()

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

    def hint_calculation_worker(self):
        """Luồng chạy ngầm: Dùng AI tìm nước đi tốt nhất cho người chơi"""
        self.logic.bot_thinking = True # Khóa bàn cờ trong lúc suy nghĩ
        print("💡 AI đang quét tìm nước đi tối ưu...")
        
        with self.logic.lock:
            board_copy = [row[:] for row in self.logic.board]
        
        # Gọi thuật toán Minimax để mớm nước đi cho người chơi (maximizing_player phụ thuộc vào phe người)
        _, move = self.logic.minimax(board_copy, depth=self.logic.bot_depth, alpha=-math.inf, beta=math.inf, maximizing_player=(self.player_side == 1))
        
        if move:
            self.hint_move = move
            self.play_sfx(self.sound_move)
            print(f"👉 Trợ giúp: Khuyên bạn nên đánh vào ô {chr(move[1] + ord('A'))}{move[0]+1}!")
            
        self.logic.bot_thinking = False

    def bot_calculation_worker(self):
        self.logic.bot_thinking = True
        with self.logic.lock:
            board_copy = [row[:] for row in self.logic.board]
            
        _, move = self.logic.minimax(board_copy, depth=self.logic.bot_depth, alpha=-math.inf, beta=math.inf, maximizing_player=(self.bot_side == 1))
        
        if move and not self.logic.game_over:
            r, c = move
            success, is_win, move_str = self.logic.play_move(r, c, self.bot_side)
            if success:
                self.play_sfx(self.sound_move) 
                self.last_move = (r, c)
                self.hint_move = None # Xóa gợi ý cũ đi
                print(f"-> Bot đáp trả: {move_str}")
                if is_win: print("\n[KẾT THÚC] BOT ĐÃ THẮNG!")
                
        self.logic.bot_thinking = False

    def draw_ui(self, screen, font):
        board_pixels = self.logic.board_size * self.GRID_SIZE
        
        # Nền chính
        screen.fill(self.COLOR_BG)
        pygame.draw.rect(screen, self.COLOR_BOARD, (self.PADDING, self.PADDING, board_pixels, board_pixels))
        
        # Vẽ lưới cờ
        for i in range(self.logic.board_size + 1):
            pygame.draw.line(screen, self.COLOR_GRID, (self.PADDING, self.PADDING + i * self.GRID_SIZE), (self.PADDING + board_pixels, self.PADDING + i * self.GRID_SIZE), 1)
            pygame.draw.line(screen, self.COLOR_GRID, (self.PADDING + i * self.GRID_SIZE, self.PADDING), (self.PADDING + i * self.GRID_SIZE, self.PADDING + board_pixels), 1)
        
        # Vẽ tọa độ chữ/số
        for i in range(self.logic.board_size):
            col_char = chr(i + ord('A'))
            text_surf = font.render(col_char, True, self.COLOR_TEXT)
            pos_x = self.PADDING + i * self.GRID_SIZE + (self.GRID_SIZE - text_surf.get_width()) // 2
            screen.blit(text_surf, (pos_x, self.PADDING // 3))                 
            
            row_num = str(i + 1)
            text_surf = font.render(row_num, True, self.COLOR_TEXT)
            pos_y = self.PADDING + i * self.GRID_SIZE + (self.GRID_SIZE - text_surf.get_height()) // 2
            screen.blit(text_surf, (self.PADDING // 3, pos_y))                 

        # Viền Highlight nước vừa đi
        if self.last_move:
            lr, lc = self.last_move
            hx = self.PADDING + lc * self.GRID_SIZE
            hy = self.PADDING + lr * self.GRID_SIZE
            pygame.draw.rect(screen, self.COLOR_HIGHLIGHT, (hx, hy, self.GRID_SIZE, self.GRID_SIZE), 3)

        # Viền Highlight ô Trợ Giúp
        if self.hint_move:
            hr, hc = self.hint_move
            hx = self.PADDING + hc * self.GRID_SIZE + 2
            hy = self.PADDING + hr * self.GRID_SIZE + 2
            pygame.draw.rect(screen, self.COLOR_HINT, (hx, hy, self.GRID_SIZE-4, self.GRID_SIZE-4), 3, border_radius=5)

        # Vẽ các quân cờ
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

        # VẼ KHU VỰC BẢNG ĐIỀU KHIỂN BÊN DƯỚI (Control Panel)
        btn_font = pygame.font.SysFont("tahoma", 13, bold=True)
        colors = [(231, 76, 60), (52, 152, 219), (241, 196, 15), (46, 204, 113)] # Đỏ, Xanh lam, Vàng, Xanh lục
        texts = ["HOME", "UNDO", "RESET", "TRỢ GIÚP"]
        rects = [self.btn_home, self.btn_undo, self.btn_reset, self.btn_hint]

        for i in range(4):
            # Vẽ nền nút bấm
            pygame.draw.rect(screen, colors[i], rects[i], border_radius=6)
            # Vẽ chữ căn giữa nút
            txt_surf = btn_font.render(texts[i], True, (0,0,0) if i==2 else (255,255,255))
            screen.blit(txt_surf, (rects[i].centerx - txt_surf.get_width() // 2, rects[i].centery - txt_surf.get_height() // 2))

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

            # Kích thước
            screen.blit(sub_font.render("1. Kích thước bàn cờ:", True, self.COLOR_TEXT), (60, 80))
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 10 else (80, 80, 80), btn_size_10, border_radius=6)
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 12 else (80, 80, 80), btn_size_12, border_radius=6)
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 15 else (80, 80, 80), btn_size_15, border_radius=6)
            screen.blit(font.render("10 x 10", True, (255,255,255)), (btn_size_10.centerx-25, btn_size_10.centery-10))
            screen.blit(font.render("12 x 12", True, (255,255,255)), (btn_size_12.centerx-25, btn_size_12.centery-10))
            screen.blit(font.render("15 x 15", True, (255,255,255)), (btn_size_15.centerx-25, btn_size_15.centery-10))

            # Độ khó
            screen.blit(sub_font.render("2. Trí tuệ AI (Độ khó):", True, self.COLOR_TEXT), (60, 190))
            pygame.draw.rect(screen, (46, 204, 113) if self.logic.bot_depth == 1 else (80, 80, 80), btn_easy, border_radius=6)
            pygame.draw.rect(screen, (241, 196, 15) if self.logic.bot_depth == 2 else (80, 80, 80), btn_medium, border_radius=6)
            pygame.draw.rect(screen, (231, 76, 60) if self.logic.bot_depth == 3 else (80, 80, 80), btn_hard, border_radius=6)
            screen.blit(font.render("DỄ", True, (255,255,255)), (btn_easy.centerx-10, btn_easy.centery-10))
            screen.blit(font.render("VỪA", True, (255,255,255)), (btn_medium.centerx-15, btn_medium.centery-10))
            screen.blit(font.render("KHÓ", True, (255,255,255)), (btn_hard.centerx-12, btn_hard.centery-10))

            # Quyền đi trước
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
                        self.player_side = -1; self.bot_side = 1
                    elif btn_first_bot.collidepoint(pos): 
                        self.player_side = 1; self.bot_side = -1
                    elif btn_start.collidepoint(pos): menu_running = False

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((540, 540))
        pygame.display.set_caption("Đại chiến cờ Caro AI")
        
        try:
            pygame.display.set_icon(pygame.image.load("icon.png"))
        except Exception: pass

        font = pygame.font.SysFont("tahoma", 14, bold=True)
        clock = pygame.time.Clock()
        
        input_thread = threading.Thread(target=self.terminal_input_loop, daemon=True)
        input_thread.start()

        while True:
            try:
                if not pygame.mixer.music.get_busy(): pygame.mixer.music.play(-1)
            except Exception: pass

            screen = pygame.display.set_mode((540, 540))
            self.show_menu(screen, font)
            
            # TÍNH TOÁN KÍCH THƯỚC CỬA SỔ & NÚT BẤM KHI VÀO TRẬN
            board_width = self.logic.board_size * self.GRID_SIZE + (self.PADDING * 2)
            window_width = board_width
            window_height = board_width + 70 # Nới thêm 70 pixel cho Control Panel
            screen = pygame.display.set_mode((window_width, window_height))
            
            # Gán tọa độ cho 4 nút bấm
            btn_w = (window_width - 50) // 4
            btn_y = board_width + 10
            self.btn_home = pygame.Rect(10, btn_y, btn_w, 40)
            self.btn_undo = pygame.Rect(20 + btn_w, btn_y, btn_w, 40)
            self.btn_reset = pygame.Rect(30 + 2*btn_w, btn_y, btn_w, 40)
            self.btn_hint = pygame.Rect(40 + 3*btn_w, btn_y, btn_w, 40)

            self.logic.reset_game()
            self.last_move = None 
            self.hint_move = None
            
            print(f"\n=== TRẬN ĐẤU MỚI: BÀN CỜ {self.logic.board_size}x{self.logic.board_size} - AI CẤP ĐỘ {self.logic.bot_depth} ===")

            while self.game_running:
                # Xử lý nhập Terminal... (giữ nguyên logic cũ)
                if self.logic.current_turn == self.player_side and self.input_buffer != "" and not self.logic.bot_thinking:
                    cmd = self.input_buffer.upper()
                    self.input_buffer = ""
                    if cmd == 'U':
                        if self.logic.undo_move(): self.last_move = self.hint_move = None 
                    elif cmd == 'R':
                        self.logic.reset_game()
                        self.last_move = self.hint_move = None
                    else:
                        coords = self.parse_terminal_input(cmd)
                        if coords:
                            success, is_win, _ = self.logic.play_move(coords[0], coords[1], self.player_side)
                            if success: 
                                self.play_sfx(self.sound_move)
                                self.last_move = (coords[0], coords[1])
                                self.hint_move = None

                # Lượt của Máy
                if self.logic.current_turn == self.bot_side and not self.logic.game_over and not self.logic.bot_thinking:
                    threading.Thread(target=self.bot_calculation_worker, daemon=True).start()

                # Xử lý sự kiện Pygame (Chuột & Bàn phím)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.logic.print_pgn_final()
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_u and self.logic.undo_move(): 
                            self.last_move = self.hint_move = None
                        elif event.key == pygame.K_r:
                            self.logic.reset_game()
                            self.last_move = self.hint_move = None

                    if event.type == pygame.MOUSEBUTTONDOWN and not self.logic.bot_thinking:
                        pos = pygame.mouse.get_pos()
                        
                        # KIỂM TRA CLICK NÚT TRÊN CONTROL PANEL
                        if self.btn_home.collidepoint(pos):
                            break # Cắt đứt vòng lặp game hiện tại, quay ra vòng lặp Menu
                        
                        elif self.btn_undo.collidepoint(pos) and not self.logic.game_over:
                            if self.logic.undo_move(): self.last_move = self.hint_move = None
                                
                        elif self.btn_reset.collidepoint(pos):
                            self.logic.reset_game()
                            self.last_move = self.hint_move = None
                            
                        elif self.btn_hint.collidepoint(pos) and not self.logic.game_over:
                            if self.logic.current_turn == self.player_side:
                                # Gọi luồng Trợ giúp riêng để không làm treo giao diện
                                threading.Thread(target=self.hint_calculation_worker, daemon=True).start()

                        # KIỂM TRA CLICK BÀN CỜ
                        elif not self.logic.game_over and self.logic.current_turn == self.player_side:
                            c = (pos[0] - self.PADDING) // self.GRID_SIZE
                            r = (pos[1] - self.PADDING) // self.GRID_SIZE
                            
                            if 0 <= c < self.logic.board_size and 0 <= r < self.logic.board_size:
                                success, is_win, _ = self.logic.play_move(r, c, self.player_side)
                                if success: 
                                    self.play_sfx(self.sound_move)
                                    self.last_move = (r, c) 
                                    self.hint_move = None

                # Break out to Menu loop if Home was pressed
                if not self.game_running or (event.type == pygame.MOUSEBUTTONDOWN and self.btn_home.collidepoint(pygame.mouse.get_pos())):
                    break

                # Animation Kết thúc Game
                if self.logic.game_over:
                    pygame.mixer.music.stop() 
                    self.play_sfx(self.sound_win if self.logic.current_turn == self.player_side else self.sound_lose)
                        
                    self.draw_ui(screen, font)
                    pygame.display.flip()
                    time.sleep(1.5)
                    
                    overlay = pygame.Surface((window_width, window_height))
                    overlay.set_alpha(200); overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    
                    msg, color = ("BẠN ĐÃ CHIẾN THẮNG!", (57, 255, 20)) if self.logic.current_turn == self.player_side else ("BẠN THUA RỒI!", (255, 0, 128))
                    title_font = pygame.font.SysFont("tahoma", 24, bold=True)
                    screen.blit(title_font.render(msg, True, color), (window_width//2 - 120, window_height//2 - 30))
                    screen.blit(pygame.font.SysFont("tahoma", 14).render("(Nhấn chuột bất kỳ để quay lại Menu)", True, (255, 255, 255)), (window_width//2 - 130, window_height//2 + 20))
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
                    break # Quay về menu

                self.draw_ui(screen, font)
                pygame.display.flip()
                clock.tick(30)

if __name__ == "__main__":
    app = CaroUI()
    app.run()