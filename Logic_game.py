import math
import threading
import time

# CẤU HÌNH ĐIỂM SỐ HEURISTIC CHO AI
# 1: AI (Bot), -1: Người chơi (Human), 0: Ô trống

# 1. BỘ TRỌNG SỐ LẬP TRÌNH BẰNG TAY (MANUAL)
ATTACK_MATRIX_MANUAL = {
    (1, 1, 1, 1, 1): 200000,       
    (0, 1, 1, 1, 1, 0): 11000,     
    (0, 1, 1, 1, 1): 2700,         
    (1, 1, 1, 1, 0): 2700,         
    (0, 1, 1, 1, 0): 670,          
    (0, 1, 1, 0, 1, 0): 500,       
    (0, 1, 0, 1, 1, 0): 500,       
    (0, 1, 1, 1): 210,             
    (1, 1, 1, 0): 210,             
    (0, 1, 1, 0): 16,              
}

DEFEND_MATRIX_MANUAL = {
    (-1, -1, -1, -1, -1): -200000,     
    (0, -1, -1, -1, -1, 0): -45000,    
    (0, -1, -1, -1, -1): -2700,        
    (-1, -1, -1, -1, 0): -2700,
    (0, -1, -1, -1, 0): -1500,         
    (0, -1, -1, 0, -1, 0): -1000,      
    (0, -1, 0, -1, -1, 0): -1000,      
    (0, -1, -1, -1): -210,
    (-1, -1, -1, 0): -210,
    (0, -1, -1, 0): -16,
}
SCORE_MATRIX_MANUAL = {**ATTACK_MATRIX_MANUAL, **DEFEND_MATRIX_MANUAL}


# 2. BỘ TRỌNG SỐ TỪ HỌC MÁY (LOGISTIC REGRESSION)
ATTACK_MATRIX_LOGISTIC = {
    (1, 1, 1, 1, 1): 200000,
    (0, 1, 1, 1, 1, 0): 14105.50,
    (0, 1, 1, 1, 1): 76114.42,
    (1, 1, 1, 1, 0): 76114.42,
    (0, 1, 1, 1, 0): 4792.88,
    (0, 1, 1, 0, 1, 0): 10.00,
    (0, 1, 0, 1, 1, 0): 10.00,
    (0, 1, 1, 1): 71321.53,
    (1, 1, 1, 0): 71321.53,
    (0, 1, 1, 0): 37198.16,
}

DEFEND_MATRIX_LOGISTIC = {
    (-1, -1, -1, -1, -1): -200000,
    (0, -1, -1, -1, -1, 0): -88332.68,
    (0, -1, -1, -1, -1): -35333.07,
    (-1, -1, -1, -1, 0): -35333.07,
    (0, -1, -1, -1, 0): -43208.96,
    (0, -1, -1, 0, -1, 0): -10.00,
    (0, -1, 0, -1, -1, 0): -10.00,
    (0, -1, -1, -1): -78542.04,
    (-1, -1, -1, 0): -78542.04,
    (0, -1, -1, 0): -80000.00,
}
SCORE_MATRIX_LOGISTIC = {**ATTACK_MATRIX_LOGISTIC, **DEFEND_MATRIX_LOGISTIC}


class CaroLogic:
    def __init__(self, board_size=15, bot_depth=3):
        self.lock = threading.Lock()
        self.board_size = board_size
        self.bot_depth = bot_depth
        self.nodes_evaluated = 0 
        self.reset_game()

    def reset_game(self, board_size=None, bot_depth=None):
        with self.lock:
            if board_size: self.board_size = board_size
            if bot_depth: self.bot_depth = bot_depth
            
            self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
            self.game_over = False
            self.current_turn = -1  
            self.pgn_history = []
            self.move_history = []
            self.bot_thinking = False
            self.nodes_evaluated = 0

    def play_move(self, r, c, player):
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

    # ================= ĐÁNH GIÁ HEURISTIC VÀ LUẬT CHƠI =================
    def evaluate_line(self, line, score_matrix):
        line_score = 0
        line_str = tuple(line)
        for length in [6, 5, 4]:
            for i in range(len(line_str) - length + 1):
                sub_line = line_str[i:i+length]
                if sub_line in score_matrix:
                    line_score += score_matrix[sub_line]
        return line_score

    def evaluate_board_heuristic(self, board_state, heuristic_type="LOGISTIC"):
        # Lựa chọn não bộ dựa trên tham số truyền vào
        score_matrix = SCORE_MATRIX_LOGISTIC if heuristic_type == "LOGISTIC" else SCORE_MATRIX_MANUAL
        
        total_score = 0
        for r in range(self.board_size):
            total_score += self.evaluate_line(board_state[r], score_matrix)
        for c in range(self.board_size):
            col = [board_state[r][c] for r in range(self.board_size)]
            total_score += self.evaluate_line(col, score_matrix)
        for d in range(-self.board_size + 1, self.board_size):
            diag1 = [board_state[i][i - d] for i in range(self.board_size) if 0 <= i - d < self.board_size]
            diag2 = [board_state[i][self.board_size - 1 - i - d] for i in range(self.board_size) if 0 <= self.board_size - 1 - i - d < self.board_size]
            if len(diag1) >= 4: total_score += self.evaluate_line(diag1, score_matrix)
            if len(diag2) >= 4: total_score += self.evaluate_line(diag2, score_matrix)
        return total_score

    def check_win(self, board_state, player):
        for r in range(self.board_size):
            for c in range(self.board_size):
                # Quét 4 hướng từ mọi ô cờ
                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    match = True
                    for i in range(5):
                        nr, nc = r + i * dr, c + i * dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if board_state[nr][nc] != player:
                                match = False
                                break
                        else:
                            match = False
                            break
                    
                    if match:
                        blocked_ends = 0
                        prev_r, prev_c = r - dr, c - dc
                        if prev_r < 0 or prev_r >= self.board_size or prev_c < 0 or prev_c >= self.board_size or board_state[prev_r][prev_c] == -player:
                            blocked_ends += 1
                            
                        next_r, next_c = r + 5 * dr, c + 5 * dc
                        if next_r < 0 or next_r >= self.board_size or next_c < 0 or next_c >= self.board_size or board_state[next_r][next_c] == -player:
                            blocked_ends += 1
                            
                        if blocked_ends < 2:
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


    def pure_minimax(self, board_state, maximizing_player):
        self.nodes_evaluated += 1
        
        if self.check_win(board_state, 1): return 1, None
        if self.check_win(board_state, -1): return -1, None
        
        is_full = all(board_state[r][c] != 0 for r in range(self.board_size) for c in range(self.board_size))
        if is_full: return 0, None

        moves = self.get_interesting_moves(board_state) 
        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for r, c in moves:
                board_state[r][c] = 1
                evaluation, _ = self.pure_minimax(board_state, False)
                board_state[r][c] = 0
                if evaluation > max_eval: max_eval = evaluation; best_move = (r, c)
            return max_eval, best_move
        else:
            min_eval = math.inf
            for r, c in moves:
                board_state[r][c] = -1
                evaluation, _ = self.pure_minimax(board_state, True)
                board_state[r][c] = 0
                if evaluation < min_eval: min_eval = evaluation; best_move = (r, c)
            return min_eval, best_move

    # Truyền thêm tham số heuristic_type (Mặc định = "LOGISTIC")
    def minimax_heuristic_only(self, board_state, depth, maximizing_player, heuristic_type="LOGISTIC"):
        self.nodes_evaluated += 1
        
        if self.check_win(board_state, 1): return 1000000 + depth, None
        if self.check_win(board_state, -1): return -1000000 - depth, None
        if depth == 0: return self.evaluate_board_heuristic(board_state, heuristic_type), None

        moves = self.get_interesting_moves(board_state)
        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for r, c in moves:
                board_state[r][c] = 1
                evaluation, _ = self.minimax_heuristic_only(board_state, depth - 1, False, heuristic_type)
                board_state[r][c] = 0
                if evaluation > max_eval: max_eval = evaluation; best_move = (r, c)
            return max_eval, best_move
        else:
            min_eval = math.inf
            for r, c in moves:
                board_state[r][c] = -1
                evaluation, _ = self.minimax_heuristic_only(board_state, depth - 1, True, heuristic_type)
                board_state[r][c] = 0
                if evaluation < min_eval: min_eval = evaluation; best_move = (r, c)
            return min_eval, best_move

    # Truyền thêm tham số heuristic_type (Mặc định = "LOGISTIC")
    def minimax(self, board_state, depth, alpha, beta, maximizing_player, heuristic_type="LOGISTIC"):
        self.nodes_evaluated += 1 
        
        if self.check_win(board_state, 1): return 1000000 + depth, None
        if self.check_win(board_state, -1): return -1000000 - depth, None
        if depth == 0: return self.evaluate_board_heuristic(board_state, heuristic_type), None

        moves = self.get_interesting_moves(board_state)
        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for r, c in moves:
                board_state[r][c] = 1
                evaluation, _ = self.minimax(board_state, depth - 1, alpha, beta, False, heuristic_type)
                board_state[r][c] = 0
                if evaluation > max_eval: max_eval = evaluation; best_move = (r, c)
                alpha = max(alpha, evaluation)
                if beta <= alpha: break 
            return max_eval, best_move
        else:
            min_eval = math.inf
            for r, c in moves:
                board_state[r][c] = -1
                evaluation, _ = self.minimax(board_state, depth - 1, alpha, beta, True, heuristic_type)
                board_state[r][c] = 0
                if evaluation < min_eval: min_eval = evaluation; best_move = (r, c)
                beta = min(beta, evaluation)
                if beta <= alpha: break 
            return min_eval, best_move


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

if __name__ == "__main__":
    game = CaroLogic(board_size=15)
    
    # Giả lập một thế cờ ở giữa trận đấu để AI suy nghĩ
    game.board[7][7] = -1  # X
    game.board[7][8] = 1   # O
    game.board[8][7] = -1  # X
    
    depth_test = 3 # Thử đo lường ở Depth = 3
    print(f"--- ĐÁNH GIÁ HIỆU NĂNG THUẬT TOÁN (DEPTH = {depth_test}) ---")
    
    # Mặc định sử dụng heuristic_type = "LOGISTIC"
    
    # 1. Test: Minimax + Heuristic (KHÔNG Cắt tỉa)
    game.nodes_evaluated = 0
    start_time = time.time()
    score1, move1 = game.minimax_heuristic_only(game.board, depth_test, True, heuristic_type="LOGISTIC")
    time1 = time.time() - start_time
    print(f"1. Minimax + Heuristic (Không Alpha-Beta):")
    print(f"   - Nước đi tốt nhất: {move1}")
    print(f"   - Số nút phải duyệt: {game.nodes_evaluated:,} nodes")
    print(f"   - Thời gian tính toán: {time1:.4f} giây\n")
    
    # 2. Test: Minimax + Heuristic + Alpha-Beta 
    game.nodes_evaluated = 0
    start_time = time.time()
    score2, move2 = game.minimax(game.board, depth_test, -math.inf, math.inf, True, heuristic_type="LOGISTIC")
    time2 = time.time() - start_time
    print(f"2. Minimax + Heuristic + Alpha-Beta Pruning (Tối ưu):")
    print(f"   - Nước đi tốt nhất: {move2}")
    print(f"   - Số nút phải duyệt: {game.nodes_evaluated:,} nodes")
    print(f"   - Thời gian tính toán: {time2:.4f} giây")
    
    if game.nodes_evaluated > 0:
        percent_saved = 100 - (game.nodes_evaluated / game.nodes_evaluated) * 100 
        print(f"   => Kỹ thuật Alpha-Beta giúp AI chạy nhanh hơn cực kỳ nhiều lần!")