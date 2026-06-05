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
        self.scaled_menu_bg = None

        self.COLOR_BG = (20, 20, 25)           
        self.COLOR_BOARD = (30, 30, 35)        
        self.COLOR_GRID = (0, 255, 255)        
        self.COLOR_TEXT = (255, 255, 255)      
        self.COLOR_X = (255, 0, 128)           
        self.COLOR_O = (57, 255, 20)           
        self.COLOR_HIGHLIGHT = (255, 255, 200) 
        self.COLOR_HINT = (255, 165, 0)        
        
        self.GRID_SIZE = 40                             
        self.PADDING = 40  
        
        self.input_buffer = ""
        self.game_running = True

        self.game_mode = "PvE" 
        self.player_side = -1  
        self.bot_side = 1
        
        self.ai_1_depth = 1 
        self.ai_2_depth = 2 
        
        self.last_move = None
        self.hint_move = None 

        self.match_start_time = 0
        self.match_elapsed_time = 0
        self.is_paused = False

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

        try:
            orig_menu_bg = pygame.image.load("menu_bg.png")
            self.scaled_menu_bg = pygame.transform.scale(orig_menu_bg, (540, 540))
        except Exception:
            self.scaled_menu_bg = None

        try:
            self.orig_bg_image = pygame.image.load("game_bg.png")
        except Exception:
            self.orig_bg_image = None

        self.btn_home = pygame.Rect(0,0,0,0)
        self.btn_undo = pygame.Rect(0,0,0,0)
        self.btn_reset = pygame.Rect(0,0,0,0)
        self.btn_hint = pygame.Rect(0,0,0,0)
        self.btn_pause = pygame.Rect(0,0,0,0)

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
            if self.game_running and self.game_mode == "PvE" and not self.logic.game_over and self.logic.current_turn == self.player_side and not self.logic.bot_thinking:
                try:
                    user_input = input().strip()
                    if user_input: self.input_buffer = user_input
                except: pass
            time.sleep(0.1)

    def hint_calculation_worker(self):
        self.logic.bot_thinking = True 
        print("💡 AI đang quét tìm nước đi tối ưu...")
        with self.logic.lock:
            board_copy = [row[:] for row in self.logic.board]
        _, move = self.logic.minimax(board_copy, depth=self.logic.bot_depth, alpha=-math.inf, beta=math.inf, maximizing_player=(self.player_side == 1))
        if move:
            self.hint_move = move
            self.play_sfx(self.sound_move)
            print(f"👉 Trợ giúp: Khuyên bạn nên đánh vào ô {chr(move[1] + ord('A'))}{move[0]+1}!")
        self.logic.bot_thinking = False

    def bot_calculation_worker(self, side, depth):
        self.logic.bot_thinking = True
        
        if self.game_mode == "EvE":
            time.sleep(0.5) 
            
        with self.logic.lock:
            board_copy = [row[:] for row in self.logic.board]
            
        _, move = self.logic.minimax(board_copy, depth=depth, alpha=-math.inf, beta=math.inf, maximizing_player=(side == 1))
        
        if move and not self.logic.game_over:
            r, c = move
            success, is_win, move_str = self.logic.play_move(r, c, side)
            if success:
                self.play_sfx(self.sound_move) 
                self.last_move = (r, c)
                self.hint_move = None 
                
                # CẬP NHẬT LẠI TÊN HIỂN THỊ TRÊN TERMINAL
                bot_name = "Bot O (AI 1)" if side == -1 else "Bot X (AI 2)" if self.game_mode == "EvE" else "Bot Máy"
                print(f"-> {bot_name} đáp trả: {move_str}")
                if is_win: print(f"\n[KẾT THÚC] {bot_name.upper()} ĐÃ THẮNG!")
        self.logic.bot_thinking = False

    def draw_ui(self, screen, font):
        board_pixels = self.logic.board_size * self.GRID_SIZE
        
        if self.scaled_game_bg:
            screen.blit(self.scaled_game_bg, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
            pygame.draw.rect(screen, self.COLOR_BOARD, (self.PADDING, self.PADDING, board_pixels, board_pixels))
        
        for i in range(self.logic.board_size + 1):
            pygame.draw.line(screen, self.COLOR_GRID, (self.PADDING, self.PADDING + i * self.GRID_SIZE), (self.PADDING + board_pixels, self.PADDING + i * self.GRID_SIZE), 1)
            pygame.draw.line(screen, self.COLOR_GRID, (self.PADDING + i * self.GRID_SIZE, self.PADDING), (self.PADDING + i * self.GRID_SIZE, self.PADDING + board_pixels), 1)
        
        for i in range(self.logic.board_size):
            col_char = chr(i + ord('A'))
            text_surf = font.render(col_char, True, self.COLOR_TEXT)
            pos_x = self.PADDING + i * self.GRID_SIZE + (self.GRID_SIZE - text_surf.get_width()) // 2
            screen.blit(text_surf, (pos_x, self.PADDING // 3))                 
            
            row_num = str(i + 1)
            text_surf = font.render(row_num, True, self.COLOR_TEXT)
            pos_y = self.PADDING + i * self.GRID_SIZE + (self.GRID_SIZE - text_surf.get_height()) // 2
            screen.blit(text_surf, (self.PADDING // 3, pos_y))                 

        if self.last_move:
            lr, lc = self.last_move
            hx = self.PADDING + lc * self.GRID_SIZE
            hy = self.PADDING + lr * self.GRID_SIZE
            pygame.draw.rect(screen, self.COLOR_HIGHLIGHT, (hx, hy, self.GRID_SIZE, self.GRID_SIZE), 3)

        if self.hint_move:
            hr, hc = self.hint_move
            hx = self.PADDING + hc * self.GRID_SIZE + 2
            hy = self.PADDING + hr * self.GRID_SIZE + 2
            pygame.draw.rect(screen, self.COLOR_HINT, (hx, hy, self.GRID_SIZE-4, self.GRID_SIZE-4), 3, border_radius=5)

        step_count = 0
        with self.logic.lock:
            for r in range(self.logic.board_size):
                for c in range(self.logic.board_size):
                    if self.logic.board[r][c] != 0:
                        step_count += 1
                        
                    center_x = self.PADDING + c * self.GRID_SIZE + self.GRID_SIZE // 2
                    center_y = self.PADDING + r * self.GRID_SIZE + self.GRID_SIZE // 2
                    if self.logic.board[r][c] == 1: 
                        pygame.draw.line(screen, self.COLOR_X, (center_x - 12, center_y - 12), (center_x + 12, center_y + 12), 4)
                        pygame.draw.line(screen, self.COLOR_X, (center_x + 12, center_y - 12), (center_x - 12, center_y + 12), 4)
                    elif self.logic.board[r][c] == -1: 
                        pygame.draw.circle(screen, self.COLOR_O, (center_x, center_y), 14, 4)

        btn_font = pygame.font.SysFont("tahoma", 13, bold=True)
        
        pygame.draw.rect(screen, (231, 76, 60), self.btn_home, border_radius=6)
        txt_surf = btn_font.render("HOME", True, (255,255,255))
        screen.blit(txt_surf, (self.btn_home.centerx - txt_surf.get_width() // 2, self.btn_home.centery - txt_surf.get_height() // 2))

        if self.game_mode == "PvE":
            colors = [(52, 152, 219), (241, 196, 15), (46, 204, 113)] 
            rects = [self.btn_undo, self.btn_reset, self.btn_hint]
            texts = ["UNDO", "RESET", "TRỢ GIÚP"]
            for i in range(3):
                pygame.draw.rect(screen, colors[i], rects[i], border_radius=6)
                txt_surf = btn_font.render(texts[i], True, (0,0,0) if i==1 else (255,255,255))
                screen.blit(txt_surf, (rects[i].centerx - txt_surf.get_width() // 2, rects[i].centery - txt_surf.get_height() // 2))
        else:
            pause_text = "TIẾP TỤC" if self.is_paused else "TẠM DỪNG"
            pause_color = (46, 204, 113) if self.is_paused else (241, 196, 15)
            text_color = (255,255,255) if self.is_paused else (0,0,0)
            
            pygame.draw.rect(screen, pause_color, self.btn_pause, border_radius=6)
            txt_surf = btn_font.render(pause_text, True, text_color)
            screen.blit(txt_surf, (self.btn_pause.centerx - txt_surf.get_width() // 2, self.btn_pause.centery - txt_surf.get_height() // 2))

        turn_char = "X" if self.logic.current_turn == 1 else "O"
        turn_color = self.COLOR_X if self.logic.current_turn == 1 else self.COLOR_O
        
        # SỬA LẠI: AI 1 CẦM O (LƯỢT -1), AI 2 CẦM X (LƯỢT 1)
        if self.game_mode == "EvE":
            who_is_playing = "AI 1" if self.logic.current_turn == -1 else "AI 2"
        else:
            who_is_playing = "MÁY" if self.logic.current_turn == self.bot_side else "BẠN"
            
        if getattr(self.logic, 'game_over', False):
            status_text = "HẾT TRẬN"
        else:
            status_text = f"LƯỢT: {who_is_playing} ({turn_char})"

        if self.is_paused or getattr(self.logic, 'game_over', False):
            total_seconds = int(self.match_elapsed_time)
        else:
            total_seconds = int(self.match_elapsed_time + (time.time() - self.match_start_time))
            
        mins = total_seconds // 60
        secs = total_seconds % 60
        time_text = f"THỜI GIAN: {mins:02d}:{secs:02d}"

        info_font = pygame.font.SysFont("tahoma", 13, bold=True)
        step_text = f"TỔNG BƯỚC: {step_count}"
        
        txt_status_surf = info_font.render(status_text, True, turn_color)
        txt_step_surf = info_font.render(step_text, True, self.COLOR_TEXT)
        txt_time_surf = info_font.render(time_text, True, (0, 255, 255))
        
        text_start_y = self.PADDING + 280
        screen.blit(txt_status_surf, (self.btn_home.left, text_start_y))
        screen.blit(txt_step_surf, (self.btn_home.left, text_start_y + 30))
        screen.blit(txt_time_surf, (self.btn_home.left, text_start_y + 60))

    def show_mode_selection(self, screen, font):
        running = True
        title_font = pygame.font.SysFont("tahoma", 28, bold=True)
        sub_font = pygame.font.SysFont("tahoma", 18, bold=True)

        btn_pve = pygame.Rect(120, 200, 300, 60)
        btn_eve = pygame.Rect(120, 300, 300, 60)

        while running:
            if self.scaled_menu_bg:
                screen.blit(self.scaled_menu_bg, (0, 0))
            else:
                screen.fill(self.COLOR_BG)
            
            overlay = pygame.Surface((540, 540))
            overlay.set_alpha(190); overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            screen.blit(title_font.render("CHỌN CHẾ ĐỘ CHƠI", True, (0, 255, 255)), (screen.get_width() // 2 - 140, 100))

            pygame.draw.rect(screen, (52, 152, 219), btn_pve, border_radius=10)
            txt_pve = sub_font.render("1 NGƯỜI CHƠI (VS MÁY)", True, (255,255,255))
            screen.blit(txt_pve, (btn_pve.centerx - txt_pve.get_width()//2, btn_pve.centery - txt_pve.get_height()//2))

            pygame.draw.rect(screen, (231, 76, 60), btn_eve, border_radius=10)
            txt_eve = sub_font.render("AI ĐẤU VỚI AI (TỰ ĐỘNG)", True, (255,255,255))
            screen.blit(txt_eve, (btn_eve.centerx - txt_eve.get_width()//2, btn_eve.centery - txt_eve.get_height()//2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if btn_pve.collidepoint(pos):
                        self.game_mode = "PvE"
                        running = False
                    elif btn_eve.collidepoint(pos):
                        self.game_mode = "EvE"
                        running = False

    def show_menu(self, screen, font):
        menu_running = True
        title_font = pygame.font.SysFont("tahoma", 28, bold=True)
        sub_font = pygame.font.SysFont("tahoma", 18, bold=True)
        
        btn_back = pygame.Rect(415, 490, 110, 35) 
        
        btn_size_10 = pygame.Rect(100, 120, 100, 45)
        btn_size_12 = pygame.Rect(220, 120, 100, 45)
        btn_size_15 = pygame.Rect(340, 120, 100, 45)
        
        btn_easy = pygame.Rect(100, 230, 100, 45)
        btn_medium = pygame.Rect(220, 230, 100, 45)
        btn_hard = pygame.Rect(340, 230, 100, 45)
        
        btn_first_player = pygame.Rect(120, 340, 130, 45)
        btn_first_bot = pygame.Rect(290, 340, 130, 45)

        btn_ai2_easy = pygame.Rect(100, 340, 100, 45)
        btn_ai2_medium = pygame.Rect(220, 340, 100, 45)
        btn_ai2_hard = pygame.Rect(340, 340, 100, 45)

        btn_start = pygame.Rect(170, 440, 200, 55)

        while menu_running:
            if self.scaled_menu_bg:
                screen.blit(self.scaled_menu_bg, (0, 0))
            else:
                screen.fill(self.COLOR_BG)
            
            overlay = pygame.Surface((540, 540))
            overlay.set_alpha(170); overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, (231, 76, 60), btn_back, border_radius=6)
            txt_back = font.render("<- QUAY LẠI", True, (255,255,255))
            screen.blit(txt_back, (btn_back.centerx - txt_back.get_width()//2, btn_back.centery - txt_back.get_height()//2))

            screen.blit(title_font.render("CẤU HÌNH TRẬN ĐẤU", True, (0, 255, 255)), (screen.get_width() // 2 - 140, 30))

            screen.blit(sub_font.render("1. Kích thước bàn cờ:", True, self.COLOR_TEXT), (60, 80))
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 10 else (80, 80, 80), btn_size_10, border_radius=6)
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 12 else (80, 80, 80), btn_size_12, border_radius=6)
            pygame.draw.rect(screen, (255, 0, 128) if self.logic.board_size == 15 else (80, 80, 80), btn_size_15, border_radius=6)
            screen.blit(font.render("10 x 10", True, (255,255,255)), (btn_size_10.centerx-25, btn_size_10.centery-10))
            screen.blit(font.render("12 x 12", True, (255,255,255)), (btn_size_12.centerx-25, btn_size_12.centery-10))
            screen.blit(font.render("15 x 15", True, (255,255,255)), (btn_size_15.centerx-25, btn_size_15.centery-10))

            if self.game_mode == "PvE":
                screen.blit(sub_font.render("2. Trí tuệ AI (Độ khó):", True, self.COLOR_TEXT), (60, 190))
                pygame.draw.rect(screen, (46, 204, 113) if self.logic.bot_depth == 1 else (80, 80, 80), btn_easy, border_radius=6)
                pygame.draw.rect(screen, (241, 196, 15) if self.logic.bot_depth == 2 else (80, 80, 80), btn_medium, border_radius=6)
                pygame.draw.rect(screen, (231, 76, 60) if self.logic.bot_depth == 3 else (80, 80, 80), btn_hard, border_radius=6)
                screen.blit(font.render("DỄ", True, (255,255,255)), (btn_easy.centerx-10, btn_easy.centery-10))
                screen.blit(font.render("VỪA", True, (255,255,255)), (btn_medium.centerx-15, btn_medium.centery-10))
                screen.blit(font.render("KHÓ", True, (255,255,255)), (btn_hard.centerx-12, btn_hard.centery-10))

                screen.blit(sub_font.render("3. Quyền đi trước (Luôn cầm O):", True, self.COLOR_TEXT), (60, 300))
                pygame.draw.rect(screen, (0, 255, 255) if self.player_side == -1 else (80, 80, 80), btn_first_player, border_radius=6)
                pygame.draw.rect(screen, (0, 255, 255) if self.bot_side == -1 else (80, 80, 80), btn_first_bot, border_radius=6)
                screen.blit(font.render("NGƯỜI (O)", True, (0,0,0) if self.player_side == -1 else (255,255,255)), (btn_first_player.centerx-35, btn_first_player.centery-10))
                screen.blit(font.render("MÁY (O)", True, (0,0,0) if self.bot_side == -1 else (255,255,255)), (btn_first_bot.centerx-30, btn_first_bot.centery-10))
            
            else:
                # SỬA LẠI: AI 1 LUÔN CẦM O (ĐI TRƯỚC), AI 2 LUÔN CẦM X (ĐI SAU)
                screen.blit(sub_font.render("2. Độ khó AI 1 (Cầm O - Đi trước):", True, self.COLOR_O), (60, 190))
                pygame.draw.rect(screen, (46, 204, 113) if self.ai_1_depth == 1 else (80, 80, 80), btn_easy, border_radius=6)
                pygame.draw.rect(screen, (241, 196, 15) if self.ai_1_depth == 2 else (80, 80, 80), btn_medium, border_radius=6)
                pygame.draw.rect(screen, (231, 76, 60) if self.ai_1_depth == 3 else (80, 80, 80), btn_hard, border_radius=6)
                screen.blit(font.render("DỄ", True, (255,255,255)), (btn_easy.centerx-10, btn_easy.centery-10))
                screen.blit(font.render("VỪA", True, (255,255,255)), (btn_medium.centerx-15, btn_medium.centery-10))
                screen.blit(font.render("KHÓ", True, (255,255,255)), (btn_hard.centerx-12, btn_hard.centery-10))

                screen.blit(sub_font.render("3. Độ khó AI 2 (Cầm X - Đi sau):", True, self.COLOR_X), (60, 300))
                pygame.draw.rect(screen, (46, 204, 113) if self.ai_2_depth == 1 else (80, 80, 80), btn_ai2_easy, border_radius=6)
                pygame.draw.rect(screen, (241, 196, 15) if self.ai_2_depth == 2 else (80, 80, 80), btn_ai2_medium, border_radius=6)
                pygame.draw.rect(screen, (231, 76, 60) if self.ai_2_depth == 3 else (80, 80, 80), btn_ai2_hard, border_radius=6)
                screen.blit(font.render("DỄ", True, (255,255,255)), (btn_ai2_easy.centerx-10, btn_ai2_easy.centery-10))
                screen.blit(font.render("VỪA", True, (255,255,255)), (btn_ai2_medium.centerx-15, btn_ai2_medium.centery-10))
                screen.blit(font.render("KHÓ", True, (255,255,255)), (btn_ai2_hard.centerx-12, btn_ai2_hard.centery-10))

            pygame.draw.rect(screen, (0, 255, 255), btn_start, border_radius=10)
            text_start = sub_font.render("BẮT ĐẦU TRẬN", True, (0, 0, 0))
            screen.blit(text_start, (btn_start.centerx - text_start.get_width() // 2, btn_start.centery - text_start.get_height() // 2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    
                    if btn_back.collidepoint(pos):
                        return "BACK" 

                    if btn_size_10.collidepoint(pos): self.logic.board_size = 10
                    elif btn_size_12.collidepoint(pos): self.logic.board_size = 12
                    elif btn_size_15.collidepoint(pos): self.logic.board_size = 15
                    
                    elif self.game_mode == "PvE":
                        if btn_easy.collidepoint(pos): self.logic.bot_depth = 1
                        elif btn_medium.collidepoint(pos): self.logic.bot_depth = 2
                        elif btn_hard.collidepoint(pos): self.logic.bot_depth = 3
                        elif btn_first_player.collidepoint(pos): 
                            self.player_side = -1; self.bot_side = 1
                        elif btn_first_bot.collidepoint(pos): 
                            self.player_side = 1; self.bot_side = -1
                    
                    elif self.game_mode == "EvE":
                        if btn_easy.collidepoint(pos): self.ai_1_depth = 1
                        elif btn_medium.collidepoint(pos): self.ai_1_depth = 2
                        elif btn_hard.collidepoint(pos): self.ai_1_depth = 3
                        elif btn_ai2_easy.collidepoint(pos): self.ai_2_depth = 1
                        elif btn_ai2_medium.collidepoint(pos): self.ai_2_depth = 2
                        elif btn_ai2_hard.collidepoint(pos): self.ai_2_depth = 3

                    if btn_start.collidepoint(pos): 
                        return "START"

    def run(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'

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
            
            while True:
                self.show_mode_selection(screen, font)
                if self.show_menu(screen, font) == "START":
                    break 
            
            board_width = self.logic.board_size * self.GRID_SIZE + (self.PADDING * 2)
            panel_width = 160
            window_width = board_width + panel_width
            window_height = board_width 
            
            screen = pygame.display.set_mode((window_width, window_height))
            
            if self.orig_bg_image:
                self.scaled_game_bg = pygame.transform.scale(self.orig_bg_image, (window_width, window_height))

            btn_w = 120
            btn_h = 45
            start_x = board_width + (panel_width - btn_w) // 2 
            
            self.btn_home = pygame.Rect(start_x, self.PADDING, btn_w, btn_h)
            
            if self.game_mode == "PvE":
                self.btn_undo = pygame.Rect(start_x, self.PADDING + 70, btn_w, btn_h)
                self.btn_reset = pygame.Rect(start_x, self.PADDING + 140, btn_w, btn_h)
                self.btn_hint = pygame.Rect(start_x, self.PADDING + 210, btn_w, btn_h)
            else:
                self.btn_pause = pygame.Rect(start_x, self.PADDING + 70, btn_w, btn_h)

            self.logic.reset_game()
            # THIẾT LẬP ÉP BUỘC: O LUÔN LÀ NGƯỜI ĐI ĐẦU TIÊN (-1)
            self.logic.current_turn = -1 
            
            self.last_move = None 
            self.hint_move = None
            
            self.match_start_time = time.time()
            self.match_elapsed_time = 0
            self.is_paused = False
            
            if self.game_mode == "PvE":
                print(f"\n=== TRẬN ĐẤU MỚI: Người vs AI (Cấp {self.logic.bot_depth}) ===")
            else:
                print(f"\n=== TRẬN ĐẤU MỚI: AI 1 (O - Cấp {self.ai_1_depth}) vs AI 2 (X - Cấp {self.ai_2_depth}) ===")

            while self.game_running:
                
                if self.logic.game_over and not getattr(self, 'game_over_processed', False):
                    if not self.is_paused:
                        self.match_elapsed_time += time.time() - self.match_start_time
                        self.is_paused = True
                    self.game_over_processed = True

                if self.game_mode == "PvE":
                    if self.logic.current_turn == self.player_side and self.input_buffer != "" and not self.logic.bot_thinking:
                        cmd = self.input_buffer.upper()
                        self.input_buffer = ""
                        if cmd == 'U':
                            if self.logic.undo_move(): self.last_move = self.hint_move = None 
                        elif cmd == 'R':
                            self.logic.reset_game()
                            self.logic.current_turn = -1
                            self.last_move = self.hint_move = None
                            self.match_start_time = time.time()
                            self.match_elapsed_time = 0
                        else:
                            coords = self.parse_terminal_input(cmd)
                            if coords:
                                success, is_win, _ = self.logic.play_move(coords[0], coords[1], self.player_side)
                                if success: 
                                    self.play_sfx(self.sound_move)
                                    self.last_move = (coords[0], coords[1])
                                    self.hint_move = None

                    if self.logic.current_turn == self.bot_side and not self.logic.game_over and not self.logic.bot_thinking:
                        threading.Thread(target=self.bot_calculation_worker, args=(self.bot_side, self.logic.bot_depth), daemon=True).start()

                elif self.game_mode == "EvE" and not self.is_paused:
                    if not self.logic.game_over and not self.logic.bot_thinking:
                        current_side = self.logic.current_turn
                        current_depth = self.ai_1_depth if current_side == -1 else self.ai_2_depth
                        threading.Thread(target=self.bot_calculation_worker, args=(current_side, current_depth), daemon=True).start()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.logic.print_pgn_final()
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_u and self.game_mode == "PvE" and not self.logic.bot_thinking: 
                            if self.logic.undo_move(): self.last_move = self.hint_move = None
                        elif event.key == pygame.K_r and self.game_mode == "PvE" and not self.logic.bot_thinking:
                            self.logic.reset_game()
                            self.logic.current_turn = -1
                            self.last_move = self.hint_move = None
                            self.match_start_time = time.time()
                            self.match_elapsed_time = 0

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        
                        # XỬ LÝ CLICK XUYÊN QUA THỜI GIAN BOT SUY NGHĨ CHO CÁC NÚT ĐIỀU KIỂN
                        if self.btn_home.collidepoint(pos):
                            break 
                            
                        if self.game_mode == "EvE":
                            if self.btn_pause.collidepoint(pos) and not self.logic.game_over:
                                self.is_paused = not self.is_paused
                                if self.is_paused:
                                    self.match_elapsed_time += time.time() - self.match_start_time
                                else:
                                    self.match_start_time = time.time()
                                    
                        elif self.game_mode == "PvE" and not self.logic.bot_thinking:
                            if self.btn_undo.collidepoint(pos) and not self.logic.game_over:
                                if self.logic.undo_move(): self.last_move = self.hint_move = None
                            elif self.btn_reset.collidepoint(pos):
                                self.logic.reset_game()
                                self.logic.current_turn = -1
                                self.last_move = self.hint_move = None
                                self.match_start_time = time.time()
                                self.match_elapsed_time = 0
                            elif self.btn_hint.collidepoint(pos) and not self.logic.game_over:
                                if self.logic.current_turn == self.player_side:
                                    threading.Thread(target=self.hint_calculation_worker, daemon=True).start()
                            
                            elif not self.logic.game_over and self.logic.current_turn == self.player_side and pos[0] < board_width:
                                c = (pos[0] - self.PADDING) // self.GRID_SIZE
                                r = (pos[1] - self.PADDING) // self.GRID_SIZE
                                if 0 <= c < self.logic.board_size and 0 <= r < self.logic.board_size:
                                    success, is_win, _ = self.logic.play_move(r, c, self.player_side)
                                    if success: 
                                        self.play_sfx(self.sound_move)
                                        self.last_move = (r, c) 
                                        self.hint_move = None

                if not self.game_running or (event.type == pygame.MOUSEBUTTONDOWN and self.btn_home.collidepoint(pygame.mouse.get_pos())):
                    break

                if self.logic.game_over:
                    pygame.mixer.music.stop() 
                    if self.game_mode == "PvE":
                        self.play_sfx(self.sound_win if self.logic.current_turn == self.player_side else self.sound_lose)
                    else:
                        self.play_sfx(self.sound_win) 
                        
                    self.draw_ui(screen, font)
                    pygame.display.flip()
                    time.sleep(1.5)
                    
                    overlay = pygame.Surface((window_width, window_height))
                    overlay.set_alpha(200); overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    
                    if self.game_mode == "PvE":
                        msg, color = ("BẠN ĐÃ CHIẾN THẮNG!", (57, 255, 20)) if self.logic.current_turn == self.player_side else ("BẠN THUA RỒI!", (255, 0, 128))
                    else:
                        winner_name = "AI 1 (O)" if self.logic.current_turn == -1 else "AI 2 (X)"
                        msg, color = (f"{winner_name} CHIẾN THẮNG!", (0, 255, 255))

                    title_font = pygame.font.SysFont("tahoma", 24, bold=True)
                    text_surf = title_font.render(msg, True, color)
                    screen.blit(text_surf, (window_width//2 - text_surf.get_width()//2, window_height//2 - 30))
                    
                    sub_text = pygame.font.SysFont("tahoma", 14).render("(Nhấn chuột bất kỳ để quay lại Menu)", True, (255, 255, 255))
                    screen.blit(sub_text, (window_width//2 - sub_text.get_width()//2, window_height//2 + 20))
                    
                    pygame.display.flip()
                    
                    self.game_over_processed = False
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.logic.print_pgn_final()
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                waiting = False
                    break 

                self.draw_ui(screen, font)
                pygame.display.flip()
                clock.tick(30)

if __name__ == "__main__":
    app = CaroUI()
    app.run()