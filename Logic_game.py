import math
import threading
import time
import random

# CẤU HÌNH ĐIỂM SỐ HEURISTIC CHO AI
# 1: AI (Bot), -1: Người chơi (Human), 0: Ô trống

# =====================================================================
# 1. BỘ TRỌNG SỐ LẬP TRÌNH BẰNG TAY (MANUAL)
# =====================================================================
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


# =====================================================================
# 2. BỘ TRỌNG SỐ TỪ HỌC MÁY (LOGISTIC REGRESSION)
# =====================================================================
ATTACK_MATRIX_LOGISTIC = {
    (1, 1, 1, 1, 1): 200000,
    (0, 1, 1, 1, 1, 0): 14780.71,
    (0, 1, 1, 1, 1): 18888.35,
    (1, 1, 1, 1, 0): 10492.78,
    (0, 1, 1, 1, 0): 2908.58,
    (0, 1, 1, 0, 1, 0): 14685.24,
    (0, 1, 0, 1, 1, 0): 3073.37,
    (0, 1, 1, 1): 4031.58,
    (1, 1, 1, 0): 13436.97,
    (0, 1, 1, 0): 3736.87,
}

DEFEND_MATRIX_LOGISTIC = {
    (-1, -1, -1, -1, -1): -200000,
    (0, -1, -1, -1, -1, 0): -200000.00,
    (0, -1, -1, -1, -1): -3210.16,
    (-1, -1, -1, -1, 0): -23248.95,
    (0, -1, -1, -1, 0): -3550.76,
    (0, -1, -1, 0, -1, 0): -17230.09,
    (0, -1, 0, -1, -1, 0): -13548.83,
    (0, -1, -1, -1): -8589.42,
    (-1, -1, -1, 0): -14294.48,
    (0, -1, -1, 0): -2389.63,
}
SCORE_MATRIX_LOGISTIC = {**ATTACK_MATRIX_LOGISTIC, **DEFEND_MATRIX_LOGISTIC}


# =====================================================================
# CLASS LOGIC GAME CARO
# =====================================================================
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

    def undo_move(self, steps=1):
        with self.lock:
            # Nếu bot đang nghĩ hoặc không đủ số bước để undo
            if self.bot_thinking or len(self.move_history) < steps:
                return False
            
            for _ in range(steps):
                r, c, _ = self.move_history.pop()
                self.board[r][c] = 0
                if self.pgn_history: 
                    self.pgn_history.pop()
            
            self.game_over = False
            
            # Cập nhật lại lượt chơi hiện tại dựa trên nước đi cuối cùng trong lịch sử
            if self.move_history:
                last_player = self.move_history[-1][2]
                self.current_turn = 1 if last_player == -1 else -1
            else:
                self.current_turn = -1 # Nếu mảng rỗng, X (người đi trước) đánh lại
                
            return True

    def random_opening(self):
        """Khởi tạo 3 nước đi đầu tiên (X, O, X) ngẫu nhiên quanh tâm bàn cờ."""
        self.reset_game()
        center = self.board_size // 2
        
        # Nước 1: X (Người đi trước) - Thường đánh ở trung tâm
        r1, c1 = center, center
        self.play_move(r1, c1, -1)
        
        # Nước 2: O - Đánh ngẫu nhiên 1 trong 8 ô xung quanh tâm
        moves_2 = [(r1+dr, c1+dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr==0 and dc==0)]
        r2, c2 = random.choice(moves_2)
        self.play_move(r2, c2, 1)
        
        # Nước 3: X - Đánh ngẫu nhiên xung quanh nước 1 hoặc nước 2 (phạm vi 5x5 giữa bàn cờ)
        moves_3 = set()
        for r, c in [(r1, c1), (r2, c2)]:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr][nc] == 0:
                        moves_3.add((nr, nc))
        r3, c3 = random.choice(list(moves_3))
        self.play_move(r3, c3, -1)
        
        self.current_turn = 1 # Chuyển lượt cho O

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
        
        # THÊM ĐOẠN NÀY: Xử lý an toàn khi bàn cờ trống hoàn toàn
        if not move_list:
            return [(self.board_size // 2, self.board_size // 2)]
            
        if self.bot_depth == 1:
            return move_list[:5]

        move_list.sort(key=lambda m: abs(m[0]-self.board_size//2) + abs(m[1]-self.board_size//2))
        return move_list[:30] if self.bot_depth == 2 else move_list

    import math

    def pure_minimax(self, board_state, depth, maximizing_player):
        self.nodes_evaluated += 1
    
        # 1. Trạng thái kết thúc: Trả về 1 hoặc -1 nếu có người thắng cuộc rõ ràng
        if self.check_win(board_state, 1): return 1, None
        if self.check_win(board_state, -1): return -1, None
    
        # 2. ĐẠT GIỚI HẠN ĐỘ SÂU: Trả về 0 (Coi như hòa/trung lập), QUYẾT KHÔNG DÙNG HEURISTIC
        if depth == 0: 
           return 0, None
        
        # 3. Bàn cờ đầy (Hòa cờ thực sự)
        is_full = all(board_state[r][c] != 0 for r in range(self.board_size) for c in range(self.board_size))
        if is_full: return 0, None

      # Lấy danh sách các nước đi tiềm năng
        moves = self.get_interesting_moves(board_state) 
        best_move = None

    # Lượt của AI (Tìm giá trị Max)
        if maximizing_player:
            max_eval = -math.inf
            for r, c in moves:
                board_state[r][c] = 1  # Thử nước đi
                # Truyền depth - 1 vào đệ quy
                evaluation, _ = self.pure_minimax(board_state, depth - 1, False)
                board_state[r][c] = 0  # Trả lại trạng thái bàn cờ (Backtracking)
            
                if evaluation > max_eval: 
                    max_eval = evaluation
                    best_move = (r, c)
            return max_eval, best_move
        
    # Lượt của người chơi (Tìm giá trị Min)
        else:
            min_eval = math.inf
            for r, c in moves:
                board_state[r][c] = -1 # Thử nước đi
            # Truyền depth - 1 vào đệ quy
                evaluation, _ = self.pure_minimax(board_state, depth - 1, True)
                board_state[r][c] = 0  # Trả lại trạng thái bàn cờ (Backtracking)
            
                if evaluation < min_eval: 
                    min_eval = evaluation
                    best_move = (r, c)
            return min_eval, best_move

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


# =====================================================================
# KIỂM THỬ CHẾ ĐỘ AI VS AI (KHAI CUỘC NGẪU NHIÊN)
# =====================================================================
if __name__ == "__main__":
    game = CaroLogic(board_size=15)
    
    print("--- CHẾ ĐỘ AI VS AI: KHAI CUỘC NGẪU NHIÊN ---")
    game.random_opening()
    print("Khai cuộc 3 nước đầu:")
    game.print_pgn_final()
    
    # Cho 2 AI đánh nhau (mô phỏng tối đa 16 nước đi để xem demo)
    max_moves = 16
    move_count = 0
    depth_ai1 = 2 # AI X (Logistic)
    depth_ai2 = 2 # AI O (Manual)
    
    while not game.game_over and move_count < max_moves:
        player = game.current_turn
        player_name = "X (Máy - Logistic)" if player == -1 else "O (Máy - Manual)"
        heuristic = "LOGISTIC" if player == -1 else "MANUAL"
        depth = depth_ai1 if player == -1 else depth_ai2
        
        print(f"Lượt của {player_name} đang suy nghĩ...")
        
        game.nodes_evaluated = 0
        start_time = time.time()
        
        # Cả 2 AI đều dùng Alpha-Beta Pruning cho tối ưu
        score, best_move = game.minimax(
            game.board, depth, -math.inf, math.inf, 
            maximizing_player=(player == 1), 
            heuristic_type=heuristic
        )
        time_taken = time.time() - start_time
        
        if best_move:
            game.play_move(best_move[0], best_move[1], player)
            print(f"-> Đánh: {game.format_output(best_move[0], best_move[1])} | TG: {time_taken:.4f}s | Nút đã duyệt: {game.nodes_evaluated}")
        else:
            print("Hòa! Không còn nước đi hợp lệ.")
            break
            
        move_count += 1

    # In ra biên bản PGN tổng hợp sau khi trận đấu dừng
    print("\n[Trận đấu kết thúc hoặc đạt giới hạn số nước test]")
    game.print_pgn_final()