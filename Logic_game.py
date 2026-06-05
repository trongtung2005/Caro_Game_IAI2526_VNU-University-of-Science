import math
import threading

# ==========================================
# CẤU HÌNH ĐIỂM SỐ HEURISTIC CHO AI
# ==========================================
# 1: AI (Bot), -1: Người chơi (Human), 0: Ô trống

# 1. MA TRẬN TẤN CÔNG (Điểm dương - AI tìm cách tạo ra thế này)
ATTACK_MATRIX = {
    (1, 1, 1, 1, 1): 200000,       # Thắng chắc (5 quân)
    (0, 1, 1, 1, 1, 0): 11000,     # Mở 2 đầu (4 quân) - Sắp thắng
    (0, 1, 1, 1, 1): 2700,         # Chặn 1 đầu (4 quân)
    (1, 1, 1, 1, 0): 2700,         # Chặn 1 đầu (4 quân)
    (0, 1, 1, 1, 0): 670,          # Mở 2 đầu (3 quân)
    (0, 1, 1, 0, 1, 0): 500,       # 3 quân đứt đoạn (X X _ X)
    (0, 1, 0, 1, 1, 0): 500,       # 3 quân đứt đoạn (X _ X X)
    (0, 1, 1, 1): 210,             # Chặn 1 đầu (3 quân)
    (1, 1, 1, 0): 210,             # Chặn 1 đầu (3 quân)
    (0, 1, 1, 0): 16,              # Mở 2 đầu (2 quân)
}

# 2. MA TRẬN PHÒNG THỦ (Điểm âm - AI tìm cách chặn/tránh thế này)
DEFEND_MATRIX = {
    (-1, -1, -1, -1, -1): -200000,     # Địch thắng chắc -> Điểm âm tuyệt đối
    (0, -1, -1, -1, -1, 0): -45000,    # Địch có 4 quân mở 2 đầu -> Ưu tiên chặn GẤP
    (0, -1, -1, -1, -1): -2700,        # Địch có 4 quân chặn 1 đầu 
    (-1, -1, -1, -1, 0): -2700,
    (0, -1, -1, -1, 0): -1500,         # Địch có 3 quân mở 2 đầu -> Phải chặn ngay
    (0, -1, -1, 0, -1, 0): -1000,      # Địch có 3 quân đứt đoạn (O O _ O)
    (0, -1, 0, -1, -1, 0): -1000,      # Địch có 3 quân đứt đoạn (O _ O O)
    (0, -1, -1, -1): -210,
    (-1, -1, -1, 0): -210,
    (0, -1, -1, 0): -16,
}

# 3. GỘP CHUNG (Merge) ĐỂ THUẬT TOÁN ĐỌC ĐƯỢC
SCORE_MATRIX = {**ATTACK_MATRIX, **DEFEND_MATRIX}

class CaroLogic:
    def __init__(self, board_size=15, bot_depth=3):
        self.lock = threading.Lock()
        self.board_size = board_size
        self.bot_depth = bot_depth
        self.reset_game()

    def reset_game(self, board_size=None, bot_depth=None):
        """Khởi tạo hoặc làm mới ván đấu"""
        with self.lock:
            if board_size: self.board_size = board_size
            if bot_depth: self.bot_depth = bot_depth
            
            self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
            self.game_over = False
            self.current_turn = -1  # -1: Người, 1: Bot
            self.pgn_history = []
            self.move_history = []
            self.bot_thinking = False

    def play_move(self, r, c, player):
        """Thực hiện một nước đi lên bàn cờ"""
        with self.lock:
            if self.board[r][c] == 0 and not self.game_over:
                self.board[r][c] = player
                self.move_history.append((r, c, player))
                
                is_win = self.check_win(self.board, player)
                move_str = self.format_output(r, c) + ("#" if is_win else "")
                self.pgn_history.append(move_str)
                
                if is_win:
                    self.game_over = True
                else:
                    self.current_turn = 1 if player == -1 else -1
                return True, is_win, move_str
        return False, False, ""

    def undo_move(self):
        """Lùi lại 1 lượt (xóa 2 nước đi gần nhất)"""
        with self.lock:
            if self.bot_thinking or len(self.move_history) < 2:
                return False
            
            r_bot, c_bot, _ = self.move_history.pop()
            self.board[r_bot][c_bot] = 0
            if self.pgn_history: self.pgn_history.pop()
            
            r_ply, c_ply, _ = self.move_history.pop()
            self.board[r_ply][c_ply] = 0
            if self.pgn_history: self.pgn_history.pop()
            
            self.game_over = False
            self.current_turn = -1
            return True

    # ================= AI & HEURISTIC =================
    def evaluate_line(self, line):
        line_score = 0
        line_str = tuple(line)
        for length in [6, 5, 4]:
            for i in range(len(line_str) - length + 1):
                sub_line = line_str[i:i+length]
                if sub_line in SCORE_MATRIX:
                    line_score += SCORE_MATRIX[sub_line]
        return line_score

    def evaluate_board_heuristic(self, board_state):
        total_score = 0
        for r in range(self.board_size):
            total_score += self.evaluate_line(board_state[r])
        for c in range(self.board_size):
            col = [board_state[r][c] for r in range(self.board_size)]
            total_score += self.evaluate_line(col)
        for d in range(-self.board_size + 1, self.board_size):
            diag1 = [board_state[i][i - d] for i in range(self.board_size) if 0 <= i - d < self.board_size]
            diag2 = [board_state[i][self.board_size - 1 - i - d] for i in range(self.board_size) if 0 <= self.board_size - 1 - i - d < self.board_size]
            if len(diag1) >= 4: total_score += self.evaluate_line(diag1)
            if len(diag2) >= 4: total_score += self.evaluate_line(diag2)
        return total_score

    # === [ĐÃ CẬP NHẬT] LUẬT CHẶN 2 ĐẦU ===
    def check_win(self, board_state, player):
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] != player: continue
                
                # Kiểm tra 4 hướng: Ngang, Dọc, Chéo xuôi, Chéo ngược
                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    # CHỈ đếm khi đây là ô BẮT ĐẦU của chuỗi
                    # (Tức là ô liền trước nó không phải của cùng người chơi)
                    prev_r, prev_c = r - dr, c - dc
                    if 0 <= prev_r < self.board_size and 0 <= prev_c < self.board_size and board_state[prev_r][prev_c] == player:
                        continue 
                    
                    count = 1
                    blocked_ends = 0
                    
                    # 1. Kiểm tra đầu phía trước bị chặn không? (Bị cản bởi địch hoặc Rìa bàn cờ)
                    if prev_r < 0 or prev_r >= self.board_size or prev_c < 0 or prev_c >= self.board_size or board_state[prev_r][prev_c] == -player:
                        blocked_ends += 1
                        
                    # Đếm số quân liên tiếp
                    curr_r, curr_c = r + dr, c + dc
                    while 0 <= curr_r < self.board_size and 0 <= curr_c < self.board_size and board_state[curr_r][curr_c] == player:
                        count += 1
                        curr_r += dr
                        curr_c += dc
                        
                    # 2. Kiểm tra đầu phía sau bị chặn không?
                    if curr_r < 0 or curr_r >= self.board_size or curr_c < 0 or curr_c >= self.board_size or board_state[curr_r][curr_c] == -player:
                        blocked_ends += 1
                        
                    # THẮNG KHI: Đạt >= 5 quân VÀ số đầu bị chặn ít hơn 2
                    if count >= 5 and blocked_ends < 2:
                        return True
        return False

    def get_interesting_moves(self, board_state):
        moves = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] != 0:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_state[nr][nc] == 0:
                                moves.add((nr, nc))
        
        move_list = list(moves)
        if self.bot_depth == 1:
            return move_list[:5] if move_list else [(self.board_size//2, self.board_size//2)]

        move_list.sort(key=lambda m: abs(m[0]-self.board_size//2) + abs(m[1]-self.board_size//2))
        return move_list[:30] if self.bot_depth == 2 else (move_list if move_list else [(self.board_size//2, self.board_size//2)])

    def minimax(self, board_state, depth, alpha, beta, maximizing_player):
        if self.check_win(board_state, 1): return 1000000 + depth, None
        if self.check_win(board_state, -1): return -1000000 - depth, None
        if depth == 0: return self.evaluate_board_heuristic(board_state), None

        moves = self.get_interesting_moves(board_state)
        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for r, c in moves:
                board_state[r][c] = 1
                evaluation, _ = self.minimax(board_state, depth - 1, alpha, beta, False)
                board_state[r][c] = 0
                if evaluation > max_eval: max_eval = evaluation; best_move = (r, c)
                alpha = max(alpha, evaluation)
                if beta <= alpha: break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for r, c in moves:
                board_state[r][c] = -1
                evaluation, _ = self.minimax(board_state, depth - 1, alpha, beta, True)
                board_state[r][c] = 0
                if evaluation < min_eval: min_eval = evaluation; best_move = (r, c)
                beta = min(beta, evaluation)
                if beta <= alpha: break
            return min_eval, best_move

    # ================= TIỆN ÍCH =================
    def format_output(self, row, col):
        return f"{chr(col + ord('A'))}{row + 1}"

    def print_pgn_final(self):
        if not self.pgn_history: return
        print("\n" + "="*40)
        print("      BIÊN BẢN TRẬN ĐẤU PGN      ")
        print("="*40)
        pgn_str = ""
        for i in range(0, len(self.pgn_history), 2):
            move_num = (i // 2) + 1
            p_move = self.pgn_history[i]
            b_move = self.pgn_history[i+1] if i+1 < len(self.pgn_history) else ""
            pgn_str += f"{move_num}. {p_move} {b_move}  "
        print(pgn_str)
        print("="*40 + "\n")