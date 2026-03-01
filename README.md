#  That's My Fish! (Python Multiplayer Game)

Welcome to **That's My Fish!**, a digital adaptation of the classic board game *Hey, That's My Fish!*. Built using Python, this project features a hexagonal grid board, a fully functional multiplayer client-server architecture, and an intelligent Minimax-based AI.

---

## Overview

In this game, players control a waddle of penguins searching for the tastiest fish on a shrinking ice floe. The goal is to collect the most fish before the ice completely melts away!

### Key Features
- **Interactive Hexagonal Grid**: Beautifully rendered using the `arcade` library.
- **Client-Server Architecture**: True networked multiplayer using TCP sockets.
- **Game Modes**: 
  - 🧍‍♂️ Local/Networked Multiplayer (Human vs Human)
  - 🤖 Single Player against AI (Human vs AI)
- **Intelligent AI**: Built-in Minimax algorithm with $\alpha-\beta$ pruning to challenge your fish-hunting skills!
- **Dynamic Board State**: The board shrinks dynamically as tiles are claimed, increasing the strategic depth of every move!

---

##  Technology Stack
- **Language**: Python 3.x
- **GUI Framework**: `arcade`
- **Networking**: Built-in Python `socket` & `threading`
- **Serialization**: `pickle` for robust game-state broadcasting

---

##  Getting Started

### Prerequisites

Ensure you have Python 3.x installed on your system.
You will need to install the `arcade` library for the graphical interface:

```bash
pip install arcade
```

### Running the Game

1. **Start the Server**
   Open a terminal and start the game server. It will prompt you to choose the game mode.
   ```bash
   python server.py
   ```
   *Mode Options:*
   - `1`: Human vs AI
   - `2`: Human vs Human

2. **Start the Client(s)**
   Open a new terminal (or two, if playing Human vs Human locally) and start the client.
   ```bash
   python client.py
   ```

---

##  How to Play

### 1. Placement Phase
- At the start of the game, players take turns placing their penguins on any hex tile that contains **exactly 1 fish** and is not currently occupied.
- Continue until all your penguins are placed.

### 2. Movement Phase
- On your turn, click one of your penguins and then click an empty tile in a straight line (hexagonal direction) to move it.
- **Rules of Movement**:
  - Penguins slide in straight lines until they are blocked by another penguin, a gap in the ice (a melted tile), or the edge of the board.
  - When a penguin moves, it collects the fish from the tile it started on, and that tile disappears, leaving a gap.
  
### 3. Winning the Game
- The game ends when no penguins can make a valid move.
- The player with the highest total number of fish wins!

---

##  Contributing

Feel free to fork this project, submit pull requests, or send suggestions. Whether it's enhancing the AI, creating new board layouts, or polishing the UI, contributions are always welcome!

---

Enjoy your ice fishing!
