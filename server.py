import socket, threading, pickle, time
from game_classes import GameState

HOST = '127.0.0.1'
PORT = 65432  # Changed from 5050 to avoid permission errors

clients = {}
client_list = []
lock = threading.Lock()

#game state to dictionary
def serialize_state(state):
    return {
        "board": state.board,  # Keep Tile objects
        "players": [{"score": p["score"], "penguins": list(p["penguins"])} for p in state.players],
        "current_player": state.current,
        "phase": state.phase, #placement or movement
        "game_over": state.game_over_flag
    }


def broadcast(state):
    data = pickle.dumps(state)
    for c in list(client_list):
        try: c.sendall(data)
        except: client_list.remove(c)

#who plays next
def advance_turn(state):
    while True:  # loop until we find a player with moves or game over
        i = state.current
        if state.game_over(): 
            return
        if not state.has_moves(i):
            # No moves for this player → skip
            state.next_turn()
            continue
        # If AI, make its move
        if state.players[i]["type"] == "ai":
            if state.phase == "placement":
                state.ai_place(i)
            else:
                state.ai_move(i)
            state.next_turn()
        break  # exit loop if human has moves or AI has played

#separate thread for each player
def handle_client(conn, idx, state):
    conn.send(pickle.dumps({"player_idx": idx, "state": serialize_state(state)}))
    while True:
        try:
            data = conn.recv(4096)
            if not data: break
            r, c = pickle.loads(data)
            with lock:
                if state.current != idx or state.game_over_flag: continue
                if state.phase == "placement":
                    if state.place_penguin(idx, r, c):
                        state.next_turn(); advance_turn(state); broadcast(serialize_state(state))
                else:
                    if state.move_penguin(idx, r, c):
                        state.next_turn(); advance_turn(state); broadcast(serialize_state(state))
        except: break
    conn.close()

def main():
    print("1. Human vs AI\n2. Two Humans")
    mode = int(input("Enter choice: "))
    if mode == 1:
        num_players = 2
        types = ["human", "ai"]
    else:
        num_players = 2
        types = ["human", "human"]

    state = GameState(num_players, types)
    
    #TCP server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server started on {HOST}:{PORT}")

        for i in range(sum(1 for t in types if t == "human")):
            conn, addr = s.accept()
            print(f"Player {i+1} connected from {addr}")
            clients[conn] = i
            client_list.append(conn)
            threading.Thread(target=handle_client, args=(conn, i, state), daemon=True).start()

    while True:
            if state.game_over():
                scores = [p["score"] for p in state.players]
                max_score = max(scores)
                winners = [i+1 for i,s in enumerate(scores) if s==max_score]
                if len(winners)==1:
                    print(f"\n🏆 Winner: Player {winners[0]} with {max_score} fish")
                else:
                    print(f"\n🤝 Tie between players {winners} with {max_score} fish")
                broadcast(serialize_state(state))
                
                print("\nGame over! Window will remain open. Close manually when ready.")
                # 👇 Keep server alive so client window stays open
                time.sleep(10)   # Wait 10 seconds before closing server
                break

            time.sleep(0.05)


if __name__ == "__main__":
    main()
