import math
import threading

# ==========================================
# HEURISTIC SCORING CONFIGURATION FOR AI
# ==========================================
# 1: AI (Bot), -1: Human (Player), 0: Empty cell

# 1. ATTACK MATRIX (Positive score - AI tries to create these patterns)
ATTACK_MATRIX = {
    (1, 1, 1, 1, 1): 200000,       # Guaranteed win (5 stones)
    (0, 1, 1, 1, 1, 0): 11000,     # Open both ends (4 stones) - About to win
    (0, 1, 1, 1, 1): 2700,         # Blocked one end (4 stones)
    (1, 1, 1, 1, 0): 2700,         # Blocked one end (4 stones)
    (0, 1, 1, 1, 0): 670,          # Open both ends (3 stones)
    (0, 1, 1, 0, 1, 0): 500,       # Broken 3 stones (X X _ X)
    (0, 1, 0, 1, 1, 0): 500,       # Broken 3 stones (X _ X X)
    (0, 1, 1, 1): 210,             # Blocked one end (3 stones)
    (1, 1, 1, 0): 210,             # Blocked one end (3 stones)
    (0, 1, 1, 0): 16,              # Open both ends (2 stones)
}

# 2. DEFENSE MATRIX (Negative score - AI tries to block/avoid these patterns)
DEFEND_MATRIX = {
    (-1, -1, -1, -1, -1): -200000,     # Opponent guaranteed win -> Absolute negative score
    (0, -1, -1, -1, -1, 0): -45000,    # Opponent has 4 open stones -> URGENT priority to block
    (0, -1, -1, -1, -1): -2700,        # Opponent has 4 blocked stones 
    (-1, -1, -1, -1, 0): -2700,
    (0, -1, -1, -1, 0): -1500,         # Opponent has 3 open stones -> Must block immediately
    (0, -1, -1, 0, -1, 0): -1000,      # Opponent has broken 3 stones (O O _ O)
    (0, -1, 0, -1, -1, 0): -1000,      # Opponent has broken 3 stones (O _ O O)
    (0, -1, -1, -1): -210,
    (-1, -1, -1, 0): -210,
    (0, -1, -1, 0): -16,
}

# 3. MERGE MATRICES FOR THE ALGORITHM TO READ
SCORE_MATRIX = {**ATTACK_MATRIX, **DEFEND_MATRIX}

class CaroLogic:
    def __init__(self, board_size=15, bot_depth=3):
        self.lock = threading.Lock()
        self.board_size = board_size
        self.bot_depth = bot_depth
        self.reset_game()

    def reset_game(self, board_size=None, bot_depth=None):
        """Initialize or reset the game"""
        with self.lock:
            if board_size: self.board_size = board_size
            if bot_depth: self.bot_depth = bot_depth
            
            self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
            self.game_over = False
            self.current_turn = -1  # -1: Player, 1: Bot
            self.pgn_history = []
            self.move_history = []
            self.bot_thinking = False

    def play_move(self, r, c, player):
        """Make a move on the board"""
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
        """Undo 1 turn (remove the last 2 moves)"""
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

    # === [UPDATED] DOUBLE-BLOCKED RULE ===
    def check_win(self, board_state, player):
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] != player: continue
                
                # Check 4 directions: Horizontal, Vertical, Main Diagonal, Anti-Diagonal
                for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    # ONLY count when this is the STARTING cell of the sequence
                    # (Meaning the previous cell does not belong to the same player)
                    prev_r, prev_c = r - dr, c - dc
                    if 0 <= prev_r < self.board_size and 0 <= prev_c < self.board_size and board_state[prev_r][prev_c] == player:
                        continue 
                    
                    count = 1
                    blocked_ends = 0
                    
                    # 1. Check if the front end is blocked (Blocked by opponent or board edge)
                    if prev_r < 0 or prev_r >= self.board_size or prev_c < 0 or prev_c >= self.board_size or board_state[prev_r][prev_c] == -player:
                        blocked_ends += 1
                        
                    # Count consecutive stones
                    curr_r, curr_c = r + dr, c + dc
                    while 0 <= curr_r < self.board_size and 0 <= curr_c < self.board_size and board_state[curr_r][curr_c] == player:
                        count += 1
                        curr_r += dr
                        curr_c += dc
                        
                    # 2. Check if the back end is blocked
                    if curr_r < 0 or curr_r >= self.board_size or curr_c < 0 or curr_c >= self.board_size or board_state[curr_r][curr_c] == -player:
                        blocked_ends += 1
                        
                    # WIN WHEN: Reach >= 5 stones AND blocked ends are less than 2
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

    # ================= UTILITIES =================
    def format_output(self, row, col):
        return f"{chr(col + ord('A'))}{row + 1}"

    def print_pgn_final(self):
        if not self.pgn_history: return
        print("\n" + "="*40)
        print("      PGN MATCH HISTORY      ")
        print("="*40)
        pgn_str = ""
        for i in range(0, len(self.pgn_history), 2):
            move_num = (i // 2) + 1
            p_move = self.pgn_history[i]
            b_move = self.pgn_history[i+1] if i+1 < len(self.pgn_history) else ""
            pgn_str += f"{move_num}. {p_move} {b_move}  "
        print(pgn_str)
        print("="*40 + "\n")