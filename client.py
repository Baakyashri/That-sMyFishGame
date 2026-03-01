import socket, threading, pickle, math, arcade
from game_classes import TILE_RADIUS, ROWS, COLS, PLAYER_COLORS

HOST = '127.0.0.1'
PORT = 65432


class FishGameClient(arcade.Window):
    def __init__(self, state, player_idx, sock):
        super().__init__(800, 600, "Fish Game")
        self.state = state
        self.idx = player_idx
        self.sock = sock
        self.winner_text = None
        self.keep_open = True  # 👈 new flag
        arcade.set_background_color(arcade.color.LIGHT_BLUE)

    def on_draw(self):
        self.clear()
        for row in self.state["board"]:
            for t in row:
                t.draw()

        # Scoreboard
        arcade.draw_xywh_rectangle_filled(580, 10, 200, 580, arcade.color.WHITE_SMOKE)
        arcade.draw_text("Scores", 600, 550, arcade.color.BLACK, 18, bold=True)
        for i, p in enumerate(self.state["players"]):
            arcade.draw_text(f"P{i+1}: {p['score']}", 600, 520 - i * 30, PLAYER_COLORS[i], 15, bold=True)

        if self.winner_text:
            arcade.draw_text(self.winner_text, 400, 300, arcade.color.BROWN, 22,
                             anchor_x="center", anchor_y="center")
            arcade.draw_text("Press ESC to exit", 400, 260, arcade.color.YELLOW, 14,
                             anchor_x="center", anchor_y="center")

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state["game_over"]:
            return
        if self.state["current_player"] != self.idx:
            return
        r, c = self.pixel_to_tile(x, y) #click to board tile coord
        if r is not None:
            self.sock.sendall(pickle.dumps((r, c)))

    def on_key_press(self, key, modifiers):
        # ESC to exit manually
        if key == arcade.key.ESCAPE:
            print("Window closed by player.")
            self.keep_open = False
            arcade.exit()

    def pixel_to_tile(self, x, y):
        for r in range(ROWS):
            for c in range(COLS):
                tx = TILE_RADIUS * 1.5 * c + 100
                ty = TILE_RADIUS * math.sqrt(3) * (r + 0.5 * (c % 2)) + 100
                if math.sqrt((x - tx) ** 2 + (y - ty) ** 2) < TILE_RADIUS: 
                    #mouse click within tile
                    return r, c
        return None, None

    def update_state(self, new_state):
        self.state = new_state
        if new_state["game_over"]:
            scores = [p["score"] for p in new_state["players"]]
            max_score = max(scores)
            winners = [i + 1 for i, s in enumerate(scores) if s == max_score]
            if len(winners) == 1:
                self.winner_text = f"🏆 Winner: P{winners[0]} ({max_score})"
            else:
                self.winner_text = f"🤝 Tie between P{', P'.join(map(str, winners))}"


def listen(sock, window):
    while window.keep_open:
        try:
            data = sock.recv(8192)
            if not data:
                break
            state = pickle.loads(data)
            window.update_state(state) #refresh
        except Exception as e:
            print("Connection closed:", e)
            break


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    data = pickle.loads(s.recv(8192))
    window = FishGameClient(data["state"], data["player_idx"], s)

    # 👇 non-daemon thread (keeps window alive)
    t = threading.Thread(target=listen, args=(s, window))
    t.start()

    arcade.run()  # main thread stays active until player closes window

    # after player exits
    window.keep_open = False
    s.close()
    t.join()


if __name__ == "__main__":
    main()
