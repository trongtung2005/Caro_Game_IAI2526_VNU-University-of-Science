import pygame
import sys
import threading
import time
import re
import math 
import os
import random 

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

        self.total_time = 0.0
        self.time_O = 0.0
        self.time_X = 0.0
        self.last_frame_time = 0.0
        self.is_paused = False
        self.game_over_processed = False

        self.vol_music = 0.3
        self.vol_sfx = 0.8

        pygame.mixer.init()
        try:
            pygame.mixer.music.load("background_music.mp3")
            pygame.mixer.music.set_volume(self.vol_music) 
        except Exception: pass

        try:
            self.sound_move = pygame.mixer.Sound("move.mp3")
            self.sound_win = pygame.mixer.Sound("win.mp3")
            self.sound_lose = pygame.mixer.Sound("lose.mp3")
            self.sound_draw = pygame.mixer.Sound("draw.mp3")
            
            if os.path.exists("click.mp3"):
                self.sound_click = pygame.mixer.Sound("click.mp3")
            elif os.path.exists("click.wav"):
                self.sound_click = pygame.mixer.Sound("click.wav")
            else:
                self.sound_click = None 
                
        except Exception:
            self.sound_move = self.sound_win = self.sound_lose = self.sound_draw = self.sound_click = None

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
        self.btn_pause = pygame.Rect(0,0,0,0)
        self.btn_undo = pygame.Rect(0,0,0,0)
        self.btn_reset = pygame.Rect(0,0,0,0)
        self.btn_hint = pygame.Rect(0,0,0,0)

        self.particles = [[random.randint(0, 540), random.randint(0, 540), random.uniform(-1, 1), random.uniform(-1, 1)] for _ in range(50)]
        self.ripples = []

    def add_ripple(self, pos):
        self.ripples.append({'x': pos[0], 'y': pos[1], 'radius': 0, 'alpha': 150})

    def draw_ripples(self, screen):
        for r in self.ripples[:]:
            r['radius'] += 2  
            r['alpha'] -= 10  
            if r['alpha'] <= 0:
                self.ripples.remove(r)
            else:
                radius = int(r['radius'])
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (0, 255, 255, int(r['alpha'])), (radius, radius), radius, 2)
                screen.blit(surf, (r['x'] - radius, r['y'] - radius))

    def play_sfx(self, sound_obj):
        if sound_obj: 
            sound_obj.set_volume(self.vol_sfx)
            sound_obj.play()
    
    def is_board_full(self):
        with self.logic.lock:
            for r in range(self.logic.board_size):
                for c in range(self.logic.board_size):
                    if self.logic.board[r][c] == 0:
                        return False
        return True
    
    def get_winning_line(self):
        for r in range(self.logic.board_size):
            for c in range(self.logic.board_size):
                if self.logic.board[r][c] == 0: continue
                player = self.logic.board[r][c]
                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    line = [(r, c)]
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < self.logic.board_size and 0 <= nc < self.logic.board_size and self.logic.board[nr][nc] == player:
                        line.append((nr, nc))
                        nr += dr
                        nc += dc
                    
                    if len(line) >= 5:
                        blocks = 0
                        br, bc = r - dr, c - dc
                        if br < 0 or br >= self.logic.board_size or bc < 0 or bc >= self.logic.board_size or self.logic.board[br][bc] == -player:
                            blocks += 1
                        if nr < 0 or nr >= self.logic.board_size or nc < 0 or nc >= self.logic.board_size or self.logic.board[nr][nc] == -player:
                            blocks += 1
                        
                        if blocks < 2:
                            return line[:5]
        return None

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
            if self.game_running and self.game_mode == "PvE" and not self.logic.game_over and self.logic.current_turn == self.player_side and not self.logic.bot_thinking and not self.is_paused:
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
        
        calc_side = self.player_side if self.game_mode == "PvE" else self.logic.current_turn
        depth = self.logic.bot_depth if self.game_mode == "PvE" else 2 
        
        _, move = self.logic.minimax(board_copy, depth=depth, alpha=-math.inf, beta=math.inf, maximizing_player=(calc_side == 1))
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
        
        if move and not self.logic.game_over and not self.is_paused:
            r, c = move
            success, is_win, move_str = self.logic.play_move(r, c, side)
            if success:
                self.play_sfx(self.sound_move) 
                self.last_move = (r, c)
                self.hint_move = None 
                
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

        if not getattr(self.logic, 'game_over', False) and not self.is_paused:
            is_human_turn = (self.game_mode == "PvP") or (self.game_mode == "PvE" and self.logic.current_turn == self.player_side)
            if is_human_turn:
                mx, my = pygame.mouse.get_pos()
                if mx < self.PADDING + board_pixels:
                    hc = (mx - self.PADDING) // self.GRID_SIZE
                    hr = (my - self.PADDING) // self.GRID_SIZE
                    if 0 <= hc < self.logic.board_size and 0 <= hr < self.logic.board_size:
                        if self.logic.board[hr][hc] == 0:
                            ghost_surf = pygame.Surface((self.GRID_SIZE, self.GRID_SIZE), pygame.SRCALPHA)
                            c_off = self.GRID_SIZE // 2
                            if self.logic.current_turn == 1:
                                pygame.draw.line(ghost_surf, (*self.COLOR_X, 100), (c_off - 12, c_off - 12), (c_off + 12, c_off + 12), 4)
                                pygame.draw.line(ghost_surf, (*self.COLOR_X, 100), (c_off + 12, c_off - 12), (c_off - 12, c_off + 12), 4)
                            else:
                                pygame.draw.circle(ghost_surf, (*self.COLOR_O, 100), (c_off, c_off), 14, 4)
                            screen.blit(ghost_surf, (self.PADDING + hc * self.GRID_SIZE, self.PADDING + hr * self.GRID_SIZE))

        btn_font = pygame.font.SysFont("tahoma", 13, bold=True)
        pygame.draw.rect(screen, (231, 76, 60), self.btn_home, border_radius=6)
        txt_surf = btn_font.render("HOME", True, (255,255,255))
        screen.blit(txt_surf, (self.btn_home.centerx - txt_surf.get_width() // 2, self.btn_home.centery - txt_surf.get_height() // 2))

        pause_text = "TIẾP TỤC" if self.is_paused else "TẠM DỪNG"
        pause_color = (46, 204, 113) if self.is_paused else (241, 196, 15)
        text_color = (255,255,255) if self.is_paused else (0,0,0)
        pygame.draw.rect(screen, pause_color, self.btn_pause, border_radius=6)
        txt_surf = btn_font.render(pause_text, True, text_color)
        screen.blit(txt_surf, (self.btn_pause.centerx - txt_surf.get_width() // 2, self.btn_pause.centery - txt_surf.get_height() // 2))

        if self.game_mode in ["PvE", "PvP"]:
            colors = [(52, 152, 219), (231, 76, 60), (46, 204, 113)] 
            rects = [self.btn_undo, self.btn_reset, self.btn_hint]
            texts = ["UNDO", "CHƠI LẠI", "TRỢ GIÚP"]
            for i in range(3):
                pygame.draw.rect(screen, colors[i], rects[i], border_radius=6)
                txt_surf = btn_font.render(texts[i], True, (255,255,255))
                screen.blit(txt_surf, (rects[i].centerx - txt_surf.get_width() // 2, rects[i].centery - txt_surf.get_height() // 2))
        elif self.game_mode == "EvE":
            pygame.draw.rect(screen, (231, 76, 60), self.btn_reset, border_radius=6)
            txt_surf = btn_font.render("CHƠI LẠI", True, (255,255,255))
            screen.blit(txt_surf, (self.btn_reset.centerx - txt_surf.get_width() // 2, self.btn_reset.centery - txt_surf.get_height() // 2))

        turn_char = "X" if self.logic.current_turn == 1 else "O"
        turn_color = self.COLOR_X if self.logic.current_turn == 1 else self.COLOR_O
        
        if self.game_mode == "EvE": who_is_playing = "AI 1" if self.logic.current_turn == -1 else "AI 2"
        elif self.game_mode == "PvP": who_is_playing = "NGƯỜI 1" if self.logic.current_turn == -1 else "NGƯỜI 2"
        else: who_is_playing = "MÁY" if self.logic.current_turn == self.bot_side else "BẠN"
            
        if getattr(self.logic, 'game_over', False): status_text = "HẾT TRẬN"
        else: status_text = f"LƯỢT: {who_is_playing} ({turn_char})"

        info_font = pygame.font.SysFont("tahoma", 13, bold=True)
        step_text = f"TỔNG BƯỚC: {step_count}"
        
        tm, ts = int(self.total_time // 60), int(self.total_time % 60)
        m_o, s_o = int(self.time_O // 60), int(self.time_O % 60)
        m_x, s_x = int(self.time_X // 60), int(self.time_X % 60)
        
        time_total_str = f"TỔNG T.GIAN: {tm:02d}:{ts:02d}"
        time_text_o = f"T.GIAN O: {m_o:02d}:{s_o:02d}"
        time_text_x = f"T.GIAN X: {m_x:02d}:{s_x:02d}"

        txt_status_surf = info_font.render(status_text, True, turn_color)
        txt_step_surf = info_font.render(step_text, True, self.COLOR_TEXT)
        txt_time_tot_surf = info_font.render(time_total_str, True, (255, 215, 0)) 
        txt_time_o_surf = info_font.render(time_text_o, True, self.COLOR_O)
        txt_time_x_surf = info_font.render(time_text_x, True, self.COLOR_X)
        
        text_start_y = self.btn_hint.bottom + 15 if self.game_mode in ["PvE", "PvP"] else self.btn_reset.bottom + 15

        screen.blit(txt_status_surf, (self.btn_home.left, text_start_y))
        screen.blit(txt_step_surf, (self.btn_home.left, text_start_y + 22))
        screen.blit(txt_time_tot_surf, (self.btn_home.left, text_start_y + 44))
        screen.blit(txt_time_o_surf, (self.btn_home.left, text_start_y + 66))
        screen.blit(txt_time_x_surf, (self.btn_home.left, text_start_y + 88))
        
        self.draw_ripples(screen)

    def show_mode_selection(self, screen, font):
        running = True
        title_font = pygame.font.SysFont("tahoma", 28, bold=True)
        sub_font = pygame.font.SysFont("tahoma", 18, bold=True)
        vol_font = pygame.font.SysFont("tahoma", 14, bold=True)

        btn_pvp = pygame.Rect(120, 120, 300, 60)
        btn_pve = pygame.Rect(120, 210, 300, 60)
        btn_eve = pygame.Rect(120, 300, 300, 60)

        btn_music_minus = pygame.Rect(130, 410, 35, 30)
        btn_music_plus = pygame.Rect(375, 410, 35, 30)
        btn_sfx_minus = pygame.Rect(130, 460, 35, 30)
        btn_sfx_plus = pygame.Rect(375, 460, 35, 30)

        clock = pygame.time.Clock()

        while running:
            if self.scaled_menu_bg: screen.blit(self.scaled_menu_bg, (0, 0))
            else: screen.fill(self.COLOR_BG)
            
            overlay = pygame.Surface((540, 540))
            overlay.set_alpha(190); overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            for p in self.particles:
                p[0] += p[2]
                p[1] += p[3]
                if p[0] < 0 or p[0] > 540: p[2] *= -1
                if p[1] < 0 or p[1] > 540: p[3] *= -1
                pygame.draw.circle(screen, (0, 150, 150), (int(p[0]), int(p[1])), 2)

            screen.blit(title_font.render("CHỌN CHẾ ĐỘ CHƠI", True, (0, 255, 255)), (screen.get_width() // 2 - 140, 50))

            pygame.draw.rect(screen, (155, 89, 182), btn_pvp, border_radius=10)
            txt_pvp = sub_font.render("2 NGƯỜI CHƠI (PvP)", True, (255,255,255))
            screen.blit(txt_pvp, (btn_pvp.centerx - txt_pvp.get_width()//2, btn_pvp.centery - txt_pvp.get_height()//2))

            pygame.draw.rect(screen, (52, 152, 219), btn_pve, border_radius=10)
            txt_pve = sub_font.render("1 NGƯỜI CHƠI (VS MÁY)", True, (255,255,255))
            screen.blit(txt_pve, (btn_pve.centerx - txt_pve.get_width()//2, btn_pve.centery - txt_pve.get_height()//2))

            pygame.draw.rect(screen, (231, 76, 60), btn_eve, border_radius=10)
            txt_eve = sub_font.render("AI ĐẤU VỚI AI (TỰ ĐỘNG)", True, (255,255,255))
            screen.blit(txt_eve, (btn_eve.centerx - txt_eve.get_width()//2, btn_eve.centery - txt_eve.get_height()//2))

            txt_music = vol_font.render(f"NHẠC NỀN: {int(self.vol_music*100):02d}%", True, (0, 255, 255))
            txt_sfx = vol_font.render(f"HIỆU ỨNG: {int(self.vol_sfx*100):02d}%", True, (0, 255, 255))
            
            center_x = (btn_music_minus.right + btn_music_plus.left) // 2
            screen.blit(txt_music, (center_x - txt_music.get_width()//2, 416))
            screen.blit(txt_sfx, (center_x - txt_sfx.get_width()//2, 466))

            for btn, txt in [(btn_music_minus, "-"), (btn_music_plus, "+"), (btn_sfx_minus, "-"), (btn_sfx_plus, "+")]:
                pygame.draw.rect(screen, (80, 80, 80), btn, border_radius=5)
                ts = vol_font.render(txt, True, (255,255,255))
                screen.blit(ts, (btn.centerx - ts.get_width()//2, btn.centery - ts.get_height()//2))

            self.draw_ripples(screen)

            pygame.display.flip()
            clock.tick(60) 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.add_ripple(pos)
                    
                    if btn_pvp.collidepoint(pos):
                        self.play_sfx(self.sound_click); self.game_mode = "PvP"; running = False
                    elif btn_pve.collidepoint(pos):
                        self.play_sfx(self.sound_click); self.game_mode = "PvE"; running = False
                    elif btn_eve.collidepoint(pos):
                        self.play_sfx(self.sound_click); self.game_mode = "EvE"; running = False
                        
                    elif btn_music_minus.collidepoint(pos):
                        self.play_sfx(self.sound_click); self.vol_music = max(0.0, self.vol_music - 0.1)
                        pygame.mixer.music.set_volume(self.vol_music)
                    elif btn_music_plus.collidepoint(pos):
                        self.play_sfx(self.sound_click); self.vol_music = min(1.0, self.vol_music + 0.1)
                        pygame.mixer.music.set_volume(self.vol_music)
                    elif btn_sfx_minus.collidepoint(pos):
                        self.vol_sfx = max(0.0, self.vol_sfx - 0.1)
                        self.play_sfx(self.sound_click)
                    elif btn_sfx_plus.collidepoint(pos):
                        self.vol_sfx = min(1.0, self.vol_sfx + 0.1)
                        self.play_sfx(self.sound_click)

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
        clock = pygame.time.Clock()

        while menu_running:
            if self.scaled_menu_bg: screen.blit(self.scaled_menu_bg, (0, 0))
            else: screen.fill(self.COLOR_BG)
            
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
            
            elif self.game_mode == "EvE":
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
            
            elif self.game_mode == "PvP":
                screen.blit(sub_font.render("2. Chế độ PvP: Người vs Người", True, (155, 89, 182)), (60, 220))
                screen.blit(font.render("Người 1 cầm O (Đi trước), Người 2 cầm X (Đi sau)", True, (255, 255, 255)), (60, 260))

            pygame.draw.rect(screen, (0, 255, 255), btn_start, border_radius=10)
            text_start = sub_font.render("BẮT ĐẦU TRẬN", True, (0, 0, 0))
            screen.blit(text_start, (btn_start.centerx - text_start.get_width() // 2, btn_start.centery - text_start.get_height() // 2))

            self.draw_ripples(screen)

            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.add_ripple(pos)
                    
                    if btn_back.collidepoint(pos):
                        self.play_sfx(self.sound_click)
                        return "BACK" 
                        
                    if btn_start.collidepoint(pos):
                        self.play_sfx(self.sound_click)
                        return "START"
                        
                    if btn_size_10.collidepoint(pos): self.play_sfx(self.sound_click); self.logic.board_size = 10
                    elif btn_size_12.collidepoint(pos): self.play_sfx(self.sound_click); self.logic.board_size = 12
                    elif btn_size_15.collidepoint(pos): self.play_sfx(self.sound_click); self.logic.board_size = 15
                    
                    if self.game_mode == "PvE":
                        if btn_easy.collidepoint(pos): self.play_sfx(self.sound_click); self.logic.bot_depth = 1
                        elif btn_medium.collidepoint(pos): self.play_sfx(self.sound_click); self.logic.bot_depth = 2
                        elif btn_hard.collidepoint(pos): self.play_sfx(self.sound_click); self.logic.bot_depth = 3
                        elif btn_first_player.collidepoint(pos): self.play_sfx(self.sound_click); self.player_side = -1; self.bot_side = 1
                        elif btn_first_bot.collidepoint(pos): self.play_sfx(self.sound_click); self.player_side = 1; self.bot_side = -1
                    
                    elif self.game_mode == "EvE":
                        if btn_easy.collidepoint(pos): self.play_sfx(self.sound_click); self.ai_1_depth = 1
                        elif btn_medium.collidepoint(pos): self.play_sfx(self.sound_click); self.ai_1_depth = 2
                        elif btn_hard.collidepoint(pos): self.play_sfx(self.sound_click); self.ai_1_depth = 3
                        elif btn_ai2_easy.collidepoint(pos): self.play_sfx(self.sound_click); self.ai_2_depth = 1
                        elif btn_ai2_medium.collidepoint(pos): self.play_sfx(self.sound_click); self.ai_2_depth = 2
                        elif btn_ai2_hard.collidepoint(pos): self.play_sfx(self.sound_click); self.ai_2_depth = 3

    def run(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        screen = pygame.display.set_mode((540, 540))
        pygame.display.set_caption("Đại chiến cờ Caro AI")
        
        try: pygame.display.set_icon(pygame.image.load("icon.png"))
        except: pass

        font = pygame.font.SysFont("tahoma", 14, bold=True)
        clock = pygame.time.Clock()
        
        input_thread = threading.Thread(target=self.terminal_input_loop, daemon=True)
        input_thread.start()

        while True:
            try:
                if not pygame.mixer.music.get_busy(): pygame.mixer.music.play(-1)
            except: pass

            screen = pygame.display.set_mode((540, 540))
            
            while True:
                self.show_mode_selection(screen, font)
                if self.show_menu(screen, font) == "START": break 
            
            board_width = self.logic.board_size * self.GRID_SIZE + (self.PADDING * 2)
            panel_width = 160
            window_width = board_width + panel_width
            window_height = board_width 
            
            screen = pygame.display.set_mode((window_width, window_height))
            if self.orig_bg_image: self.scaled_game_bg = pygame.transform.scale(self.orig_bg_image, (window_width, window_height))

            btn_w = 120
            btn_h = 45
            start_x = board_width + (panel_width - btn_w) // 2 
            btn_spacing = 55 
            
            self.btn_home = pygame.Rect(start_x, self.PADDING, btn_w, btn_h)
            self.btn_pause = pygame.Rect(start_x, self.PADDING + btn_spacing*1, btn_w, btn_h)
            self.btn_undo = pygame.Rect(start_x, self.PADDING + btn_spacing*2, btn_w, btn_h)
            self.btn_reset = pygame.Rect(start_x, self.PADDING + btn_spacing*3, btn_w, btn_h)
            self.btn_hint = pygame.Rect(start_x, self.PADDING + btn_spacing*4, btn_w, btn_h)
            
            if self.game_mode == "EvE":
                self.btn_reset = pygame.Rect(start_x, self.PADDING + btn_spacing*2, btn_w, btn_h)

            self.logic.reset_game()
            self.logic.current_turn = -1 
            self.last_move = self.hint_move = None
            
            self.total_time = 0.0
            self.time_O = 0.0
            self.time_X = 0.0
            self.last_frame_time = time.time()
            self.is_paused = False
            self.game_over_processed = False
            
            if self.game_mode == "PvE": print(f"\n=== TRẬN ĐẤU: Người vs AI (Cấp {self.logic.bot_depth}) ===")
            elif self.game_mode == "PvP": print(f"\n=== TRẬN ĐẤU: Người vs Người (PvP) ===")
            else: print(f"\n=== TRẬN ĐẤU: AI 1 (Cấp {self.ai_1_depth}) vs AI 2 (Cấp {self.ai_2_depth}) ===")

            while self.game_running:
                current_time = time.time()
                if not self.is_paused and not self.logic.game_over:
                    delta = current_time - self.last_frame_time
                    self.total_time += delta
                    if self.logic.current_turn == -1: self.time_O += delta
                    else: self.time_X += delta
                self.last_frame_time = current_time

                if self.game_mode == "PvE" and not self.is_paused:
                    if self.logic.current_turn == self.bot_side and not self.logic.game_over and not self.logic.bot_thinking:
                        threading.Thread(target=self.bot_calculation_worker, args=(self.bot_side, self.logic.bot_depth), daemon=True).start()
                elif self.game_mode == "EvE" and not self.is_paused:
                    if not self.logic.game_over and not self.logic.bot_thinking:
                        current_side = self.logic.current_turn
                        current_depth = self.ai_1_depth if current_side == -1 else self.ai_2_depth
                        threading.Thread(target=self.bot_calculation_worker, args=(current_side, current_depth), daemon=True).start()

                if self.game_mode == "PvE" and self.logic.current_turn == self.player_side and self.input_buffer != "" and not self.is_paused:
                    cmd = self.input_buffer.upper()
                    self.input_buffer = ""
                    if cmd == 'U':
                        if self.logic.undo_move(): self.last_move = self.hint_move = None 
                    elif cmd == 'R':
                        self.logic.reset_game(); self.logic.current_turn = -1
                        self.last_move = self.hint_move = None
                        self.total_time = self.time_O = self.time_X = 0.0
                    else:
                        coords = self.parse_terminal_input(cmd)
                        if coords:
                            success, is_win, _ = self.logic.play_move(coords[0], coords[1], self.player_side)
                            if success: 
                                self.play_sfx(self.sound_move); self.last_move = (coords[0], coords[1]); self.hint_move = None

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.logic.print_pgn_final(); pygame.quit(); sys.exit()

                    if event.type == pygame.KEYDOWN and not self.is_paused and not self.logic.bot_thinking:
                        if event.key == pygame.K_u and self.game_mode in ["PvE", "PvP"]: 
                            if self.logic.undo_move(): self.last_move = self.hint_move = None
                        elif event.key == pygame.K_r:
                            self.logic.reset_game(); self.logic.current_turn = -1
                            self.last_move = self.hint_move = None
                            self.total_time = self.time_O = self.time_X = 0.0

                if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        
                        if pos[0] >= board_width or self.logic.game_over:
                            self.add_ripple(pos)
                        
                        if self.btn_home.collidepoint(pos):
                            self.play_sfx(self.sound_click)
                            break 
                        
                        if self.btn_pause.collidepoint(pos) and not self.logic.game_over:
                            self.play_sfx(self.sound_click)
                            self.is_paused = not self.is_paused
                        
                        if not self.is_paused and not self.logic.bot_thinking:
                            if self.btn_reset.collidepoint(pos):
                                self.play_sfx(self.sound_click)
                                self.logic.reset_game(); self.logic.current_turn = -1
                                self.last_move = self.hint_move = None
                                self.total_time = self.time_O = self.time_X = 0.0
                                
                            if self.game_mode in ["PvE", "PvP"]:
                                if self.btn_undo.collidepoint(pos) and not self.logic.game_over:
                                    self.play_sfx(self.sound_click)
                                    if self.logic.undo_move(): self.last_move = self.hint_move = None
                                elif self.btn_hint.collidepoint(pos) and not self.logic.game_over:
                                    self.play_sfx(self.sound_click)
                                    threading.Thread(target=self.hint_calculation_worker, daemon=True).start()
                                
                                elif not self.logic.game_over and pos[0] < board_width:
                                    is_valid_turn = (self.game_mode == "PvP") or (self.game_mode == "PvE" and self.logic.current_turn == self.player_side)
                                    if is_valid_turn:
                                        c = (pos[0] - self.PADDING) // self.GRID_SIZE
                                        r = (pos[1] - self.PADDING) // self.GRID_SIZE
                                        if 0 <= c < self.logic.board_size and 0 <= r < self.logic.board_size:
                                            current_p = self.logic.current_turn
                                            success, is_win, move_str = self.logic.play_move(r, c, current_p)
                                            if success: 
                                                print(f"-> Bạn đi: {move_str}")
                                                self.play_sfx(self.sound_move)
                                                self.last_move = (r, c) 
                                                self.hint_move = None

                if not self.game_running or (event.type == pygame.MOUSEBUTTONDOWN and self.btn_home.collidepoint(pygame.mouse.get_pos())):
                    break

                is_full = self.is_board_full()
                if self.logic.game_over or is_full:
                    if is_full and not self.logic.game_over:
                        self.logic.game_over = True
                        
                    pygame.mixer.music.stop() 
                    if not self.game_over_processed:
                        self.game_over_processed = True
                        
                        win_line = self.get_winning_line()
                        if win_line:
                            for _ in range(6):
                                self.draw_ui(screen, font)
                                pygame.display.flip()
                                time.sleep(0.25)
                                
                                for r, c in win_line:
                                    hx, hy = self.PADDING + c * self.GRID_SIZE, self.PADDING + r * self.GRID_SIZE
                                    pygame.draw.rect(screen, (255, 255, 0), (hx, hy, self.GRID_SIZE, self.GRID_SIZE), 4, border_radius=4)
                                pygame.display.flip()
                                time.sleep(0.25)
                            
                            if self.game_mode == "PvE": self.play_sfx(self.sound_win if self.logic.current_turn == self.player_side else self.sound_lose)
                            else: self.play_sfx(self.sound_win) 
                        else:
                            # Nếu không có win_line mà bàn cờ đầy -> HÒA
                            self.play_sfx(getattr(self, 'sound_draw', None))
                        
                    self.draw_ui(screen, font)
                    pygame.display.flip()
                    
                    overlay = pygame.Surface((window_width, window_height))
                    overlay.set_alpha(200); overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    
                    # XỬ LÝ TEXT THÔNG BÁO DỰA TRÊN KẾT QUẢ
                    if win_line is None:
                        msg, color = ("TRẬN ĐẤU HÒA!", (255, 255, 0))
                    elif self.game_mode == "PvE":
                        msg, color = ("BẠN ĐÃ CHIẾN THẮNG!", (57, 255, 20)) if self.logic.current_turn == self.player_side else ("BẠN THUA RỒI!", (255, 0, 128))
                    elif self.game_mode == "PvP":
                        winner_name = "NGƯỜI 1 (O)" if self.logic.current_turn == -1 else "NGƯỜI 2 (X)"
                        msg, color = (f"{winner_name} CHIẾN THẮNG!", (0, 255, 255))
                    else:
                        winner_name = "AI 1 (O)" if self.logic.current_turn == -1 else "AI 2 (X)"
                        msg, color = (f"{winner_name} CHIẾN THẮNG!", (0, 255, 255))

                    title_font = pygame.font.SysFont("tahoma", 24, bold=True)
                    text_surf = title_font.render(msg, True, color)
                    screen.blit(text_surf, (window_width//2 - text_surf.get_width()//2, window_height//2 - 30))
                    
                    sub_text = pygame.font.SysFont("tahoma", 14).render("(Nhấn chuột bất kỳ để quay lại Menu)", True, (255, 255, 255))
                    screen.blit(sub_text, (window_width//2 - sub_text.get_width()//2, window_height//2 + 20))
                    
                    pygame.display.flip()
                    
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.logic.print_pgn_final(); pygame.quit(); sys.exit()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                self.add_ripple(pygame.mouse.get_pos())
                                waiting = False
                    self.logic.print_pgn_final()
                    break 

                self.draw_ui(screen, font)
                pygame.display.flip()
                clock.tick(60)

if __name__ == "__main__":
    app = CaroUI()
    app.run()