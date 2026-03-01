import math
import random
import arcade

# --- Board constants ---
ROWS = 5
COLS = 7
TILE_RADIUS = 40

# Fish & Player colors
FISH_COLORS = [
    (0, 0, 0),         # index 0 unused
    (90, 170, 255),
    (50, 210, 120),
    (255, 210, 80),
]
PLAYER_COLORS = [arcade.color.RED, arcade.color.BLUE, arcade.color.GREEN, arcade.color.ORANGE]

# Hex directions for movement (even vs odd columns)
DIRECTIONS_EVEN = [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]
DIRECTIONS_ODD  = [(-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]


class Tile:
    """One hex tile."""
    def __init__(self, row, col, fish):
        self.row = row
        self.col = col
        self.fish = fish
        self.occupied = None

    def get_position(self):
        x = TILE_RADIUS * 1.5 * self.col + 100
        y = TILE_RADIUS * math.sqrt(3) * (self.row + 0.5 * (self.col % 2)) + 100
        return x, y

    def draw(self):
        x, y = self.get_position()
        if self.fish == 0:
            arcade.draw_polygon_filled(self.hex_corners(x, y, TILE_RADIUS), (45, 45, 45))
        else:
            color = FISH_COLORS[self.fish]
            arcade.draw_polygon_filled(self.hex_corners(x, y, TILE_RADIUS), color)
            arcade.draw_text(str(self.fish), x-6, y-10, arcade.color.BLACK, 16)
        if self.occupied is not None:
            arcade.draw_circle_filled(x, y, TILE_RADIUS * 0.5, PLAYER_COLORS[self.occupied])

    @staticmethod
    def hex_corners(x, y, radius):
        return [(x + radius * math.cos(math.radians(60 * i + 30)),
                 y + radius * math.sin(math.radians(60 * i + 30))) for i in range(6)]


class GameState:
    """Main game state: placement, movement, scoring, AI."""
    def __init__(self, num_players, player_types):
        self.num_players = num_players
        self.player_types = list(player_types)
        self.penguins_per_player = 4 if num_players == 2 else 3
        self.board = [[Tile(r, c, random.randint(1, 3)) for c in range(COLS)] for r in range(ROWS)]
        self.players = [{"score": 0, "penguins": [], "type": t} for t in self.player_types]
        self.phase = "placement"
        self.current = 0
        self.total_placements = 0
        self.max_placements = self.num_players * self.penguins_per_player
        self.game_over_flag = False

    # --- Board utilities ---
    def in_bounds(self, r, c): return 0 <= r < ROWS and 0 <= c < COLS
    def tile(self, r, c): return self.board[r][c]
    def dirs(self, c): return DIRECTIONS_EVEN if c % 2 == 0 else DIRECTIONS_ODD

    #----Adjacent-only movement----
    def reachable_from(self, r, c):
        moves = []
        for dr, dc in self.dirs(c):
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                t = self.tile(nr, nc)
                if t.fish > 0 and t.occupied is None:
                    moves.append((nr, nc))
        return moves

    #player i plays or moves
    def has_moves(self, player_idx):
        if self.phase == "placement":
            return len(self.players[player_idx]["penguins"]) < self.penguins_per_player
        for (r, c) in self.players[player_idx]["penguins"]:
            if self.reachable_from(r, c): return True
        return False
    
    #no one can move anymore
    def game_over(self):
        if self.phase == "placement": return False
        if not any(self.has_moves(i) for i in range(self.num_players)):
            self.game_over_flag = True
        return self.game_over_flag
    
    #next player
    def next_turn(self):
        self.current = (self.current + 1) % self.num_players

    # --- Placement ---
    def place_penguin(self, i, r, c):
        if self.phase != "placement": return False
        if len(self.players[i]["penguins"]) >= self.penguins_per_player: return False
        t = self.tile(r, c)
        if t.fish == 0 or t.occupied is not None: return False
        t.occupied = i
        self.players[i]["penguins"].append((r, c))
        self.update_total_placements()
        return True

    def update_total_placements(self):
        self.total_placements = sum(len(p["penguins"]) for p in self.players)
        if self.total_placements >= self.max_placements:
            self.phase = "movement"

    # --- Movement ---
    def move_penguin(self, i, r2, c2):
        for (r1, c1) in list(self.players[i]["penguins"]):
            if (r2, c2) in self.reachable_from(r1, c1):
                from_t = self.tile(r1, c1)
                to_t = self.tile(r2, c2)
                self.players[i]["score"] += from_t.fish
                from_t.fish = 0
                from_t.occupied = None
                to_t.occupied = i
                self.players[i]["penguins"].remove((r1, c1))
                self.players[i]["penguins"].append((r2, c2))
                return True
        return False

    # --- AI Placement (strategic, one per turn) ---
    def ai_place(self, i):
        best_score = -1
        best_tile = None
        for r in range(ROWS):
            for c in range(COLS):
                t = self.tile(r, c)
                if t.occupied is None and t.fish > 0:
                    # Heuristic: tile fish + reachable fish
                    reachable_score = sum(self.tile(nr, nc).fish for nr, nc in self.reachable_from(r, c))
                    score = t.fish + reachable_score
                    if score > best_score:
                        best_score = score
                        best_tile = (r, c)
        if best_tile:
            self.place_penguin(i, *best_tile)
            return True
        return False

    # --- AI Movement using depth-limited minimax with alpha-beta ---
    def ai_move(self, i, depth=2):
        def minimax(state, player_idx, depth, alpha, beta, maximizing):
            if depth == 0 or state.game_over():
                return state.evaluate_state(player_idx), None

            moves = []
            for r, c in state.players[player_idx]["penguins"]:
                for nr, nc in state.reachable_from(r, c):
                    moves.append((r, c, nr, nc))
            if not moves:
                return state.evaluate_state(player_idx), None

            if maximizing: #AI turn
                best_val = -float("inf")
                best_move = None
                for r1, c1, r2, c2 in moves:
                    cloned = state.clone()
                    cloned.move_penguin(player_idx, r2, c2)
                    val, _ = minimax(cloned, player_idx, depth-1, alpha, beta, False)
                    if val > best_val:
                        best_val = val
                        best_move = (r2, c2)
                    alpha = max(alpha, best_val)
                    if beta <= alpha:
                        break  # pruning
                return best_val, best_move
            else: #Opponents turn
                opp_idx = (player_idx + 1) % state.num_players
                best_val = float("inf")
                for r1, c1, r2, c2 in moves:
                    cloned = state.clone()
                    cloned.move_penguin(opp_idx, r2, c2)
                    val, _ = minimax(cloned, player_idx, depth-1, alpha, beta, True)
                    best_val = min(best_val, val)
                    beta = min(beta, best_val)
                    if beta <= alpha:
                        break  # pruning
                return best_val, None

        _, best_move = minimax(self, i, depth, -float("inf"), float("inf"), True)
        if best_move:
            return self.move_penguin(i, *best_move)
        return False

    # --- Evaluation function: AI tries to maximize lead,heuristics ---
    def evaluate_state(self, player_idx):
        my_score = self.players[player_idx]["score"]
        opp_score = max(p["score"] for idx, p in enumerate(self.players) if idx != player_idx)
        return my_score - opp_score #positive good for ai 

    # --- Clone for minimax ---,not use same board
    def clone(self):
        new_state = GameState(self.num_players, self.player_types)
        new_state.phase = self.phase
        new_state.current = self.current
        new_state.game_over_flag = self.game_over_flag
        for r in range(ROWS):
            for c in range(COLS):
                t_old = self.board[r][c]
                t_new = new_state.board[r][c]
                t_new.fish = t_old.fish
                t_new.occupied = t_old.occupied
        for i, p in enumerate(self.players):
            new_state.players[i]["score"] = p["score"]
            new_state.players[i]["penguins"] = list(p["penguins"])
        return new_state