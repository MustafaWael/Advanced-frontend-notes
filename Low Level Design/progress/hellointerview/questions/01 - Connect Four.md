# Connect Four — LLD Breakdown

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/connect-four
**Difficulty:** Easy · Author: Evan King (Hello Interview)

## Understanding the Problem

Connect Four is a two-player connection game where players take turns placing pieces in a 7x6 grid. The first player to connect four of their pieces in a row, column, or diagonal wins.

Prompt: *"Build the object-oriented design for a two-player Connect Four game. Players take turns dropping discs into a 7-column, 6-row board. The first to align four of their own discs vertically, horizontally, or diagonally wins."*

## Requirements (~5 min)

### Clarifying Questions

Structure questions around four areas: **core actions, error handling, system boundaries, and future extensions.**

Key clarifications from the interviewer dialogue:
- Players choose a column 0–6; the disc falls to the lowest available spot.
- Game ends on four-in-a-row (vertical, horizontal, diagonal) → win; full board with no winner → draw.
- Invalid moves (full column, out-of-turn, move after game over) → return false / raise an error; never corrupt game state.
- Single game at a time; no concurrency.
- Backend logic only, no UI. (This matters: with UI you'd want `getBoardState()` / `getValidMoves()`; backend-only keeps the API minimal.)
- No move history, no undo, board always 7x6.

### Final Requirements

```
Requirements:
1. Two players take turns dropping discs into a 7-column, 6-row board
2. A disc falls to the lowest available row in the chosen column
3. The game ends when:
    - A player gets four discs in a row (vertical, horizontal, or diagonal). They win.
    - The board is full. It's a draw.
4. Invalid moves should be rejected clearly:
    - Dropping in a full column.
    - Moving out of turn.
    - Moving after the game is over.

Out of scope:
- UI support
- Concurrent games
- Move history
- Undo
- Board size configuration
```

## Core Entities and Relationships (~5 min)

Look for nouns in the requirements. Common mistake: one giant class, or unnecessary splitting. Each class should have a single clear job.

| Entity | Responsibility |
|---|---|
| **Game** | The orchestrator. Holds the Board, tracks whose turn it is, manages game state (in progress, won, draw), enforces turn rules. On a move: validates, tells Board to place the disc, checks for win, switches turns. |
| **Board** | The 7x6 grid. Owns grid state and disc placement. Knows if a column is full, where a disc falls, and whether four discs are connected. Doesn't care about turns or winners. |
| **Player** | Simple data holder: name and disc color. No game logic. |

## Class Design (~10–15 min)

Take a **top-down approach**: design `Game` (the orchestrator/entry point) first, then `Board`, then `Player`. Derive state and behavior from the requirements ("What does the game need to remember to enforce this?").

### Game

| Requirement | What Game must track |
|---|---|
| "Two players take turns dropping discs..." | The two players, whose turn it is, the board |
| "The game ends when a player wins or the board is full" | Game state (in progress, won, draw) |
| "A player gets four discs in a row. They win." | Who won (if anyone) |

#### Bad solution: boolean flags for game state

```
class Game:
  - isOver: boolean
  - hasWinner: boolean
  - isDraw: boolean
  - winner: Player?
```

Works, but three coupled booleans must stay synchronized and can represent **invalid states** the domain doesn't allow (`isOver=false, hasWinner=true`; win and draw simultaneously; etc.). The domain has 3 states but the representation allows 8 combinations. Wrong abstraction; bugs appear on careless refactors.

#### Great solution: GameState enum

```
enum GameState:
    IN_PROGRESS
    WON
    DRAW
```

One field holds the entire game state; invalid states become impossible by construction. Callers check `state == WON` instead of `isOver && hasWinner`. Adding a state (PAUSED, ABANDONED) is one enum value.

**Principle: make invalid states unrepresentable.** When type structure matches domain structure, whole classes of bugs disappear.

Remaining gap: a separate nullable `winner` field can still desync (e.g., `IN_PROGRESS` with a winner set). The theoretically perfect fix is a sum type: `WON(winner: Player)` — supported natively in Rust, Swift, Kotlin (sealed classes), TypeScript (discriminated unions), but not elegantly in Java/Python/C#/Go. For interviews, enum + nullable winner is the right call; mention the ideal for depth.

#### Deriving methods

| Need from requirements | Method on Game |
|---|---|
| "Players take turns dropping discs" | `makeMove(player, column)` — the core action |
| "Reject moves out of turn" | `getCurrentPlayer()` |
| "The game ends when..." | `getGameState()` |
| "A player gets four discs in a row" | `getWinner()` |

Discovering methods mid-design (e.g., `getCurrentPlayer()` for display) is normal — iterative refinement shows good design thinking.

```
class Game:
    - board: Board
    - player1: Player
    - player2: Player
    - currentPlayer: Player
    - state: GameState        // IN_PROGRESS, WON, DRAW
    - winner: Player?         // null if no winner yet or draw

    + Game(player1, player2)
    + makeMove(player, column) -> bool
    + getCurrentPlayer() -> Player
    + getGameState() -> GameState
    + getWinner() -> Player?
    + getBoard() -> Board
```

Constructor:

```
Game(player1, player2)
    board = Board()
    this.player1 = player1
    this.player2 = player2
    currentPlayer = player1    // player1 goes first
    state = IN_PROGRESS
    winner = null
```

`makeMove` is the only mutating method; everything else is read-only.

### Board

| Requirement | What Board must track |
|---|---|
| "7-column, 6-row board" | Fixed dimensions (rows, cols) |
| "A disc falls to the lowest available row" | The grid (occupancy per column) |
| "The board is full. It's a draw." | Whether any empty cell remains |
| "Four discs in a row..." | Enough grid info to check contiguous discs |

```
class Board:
    - rows: int = 6
    - cols: int = 7
    - grid: DiscColor?[rows][cols]   // null if empty

    + Board()
    + getRows() -> int
    + getCols() -> int
    + canPlace(column) -> bool
    + placeDisc(column, color) -> int      // returns row where disc lands
    + isFull() -> bool
    + checkWin(row, column, color) -> bool
    + getCell(row, column) -> DiscColor?
```

Store `DiscColor` in the grid rather than `Player` — simpler type, keeps Board independently testable (no Player mocks). Board encapsulates all grid math and win detection; Game just asks.

### Player

| Requirement | What Player must track |
|---|---|
| "Two players take turns..." | A name/ID so Game can compare players |
| "their own discs" | The disc color for that player |

```
class Player:
    - name: string
    - color: DiscColor     // RED or YELLOW

    + Player(name, color)
    + getName() -> string
    + getColor() -> DiscColor
```

Deliberately simple — all game flow, validation, and win logic live elsewhere.

### Final Class Design

```
class Game:
    - board: Board
    - player1: Player
    - player2: Player
    - currentPlayer: Player
    - state: GameState
    - winner: Player?
    + Game(player1, player2)
    + makeMove(player, column) -> bool
    + getCurrentPlayer() -> Player
    + getGameState() -> GameState
    + getWinner() -> Player?
    + getBoard() -> Board

class Board:
    - rows: int = 6
    - cols: int = 7
    - grid: DiscColor?[rows][cols]
    + Board()
    + getRows() -> int
    + getCols() -> int
    + canPlace(column) -> bool
    + placeDisc(column, color) -> int
    + isFull() -> bool
    + checkWin(row, column, color) -> bool
    + getCell(row, column) -> DiscColor?

class Player:
    - name: string
    - color: DiscColor
    + Player(name, color)
    + getName() -> string
    + getColor() -> DiscColor

enum GameState: IN_PROGRESS, WON, DRAW
enum DiscColor: RED, YELLOW
```

Validation and orchestration in Game; physical board rules in Board; Player is pure data.

## Implementation (~10 min)

Ask the interviewer how much detail they want (pseudocode vs real code vs talk-through). For each method: (1) define the **core logic** (happy path), then (2) enumerate **edge cases**. Systematically identifying edge cases signals production-quality thinking.

Most interesting methods: `makeMove` (turn enforcement + game flow), `placeDisc` (discs falling), `checkWin` (directional scanning).

### Game.makeMove

Core logic:
1. Place disc via `board.placeDisc(column, player.getColor())` → returns row
2. Check win via `board.checkWin(row, column, color)`
3. If no win, check draw via `board.isFull()`
4. Switch turn if still in progress
5. Return true

Edge cases (reject before touching state): game already over; wrong player's turn; invalid/full column (delegated to Board).

```
makeMove(player, column)
    if state != IN_PROGRESS
        return false
    if player != currentPlayer
        return false

    row = board.placeDisc(column, player.getColor())
    if row == -1
        return false

    if board.checkWin(row, column, player.getColor())
        state = WON
        winner = player
    else if board.isFull()
        state = DRAW
    else
        currentPlayer = (player == player1) ? player2 : player1 // switch turn
    return true
```

Note: Game does **not** check column bounds/fullness — that's Board's responsibility (`placeDisc` returns -1 on invalid). Separation of concerns: Game handles game rules (turns, state), Board handles grid rules (bounds, placement).

Alternatives worth mentioning:
- Throw exceptions instead of returning false — fine in some languages; boolean often clearer in interviews. Ask.
- Have `makeMove` implicitly use `currentPlayer` (no player argument) — simpler for single-caller code; explicit player is useful in a networked setting where moves arrive tagged. Either is fine if you explain it.

### Board.placeDisc

Core logic: scan from `row = rows - 1` upward for the first `null` cell in the column, set it, return the row. Returning the row lets Game feed `checkWin` without re-scanning. (Optional optimization: a `heights[cols]` array of next-free rows — unnecessary for 7x6.)

Edge cases: column out of bounds → -1; column full → -1. Keep **all** grid validation inside `placeDisc` rather than making Game call `canPlace()` first.

```
placeDisc(column, color)
    if column < 0 || column >= cols
        return -1
    if !canPlace(column)
        return -1

    for row = rows - 1 down to 0
        if grid[row][column] == null
            grid[row][column] = color
            return row
    return -1
```

### Board.checkWin — the over-engineering trap

#### Bad solution: separate WinChecker classes (Strategy pattern abuse)

A `WinChecker` interface with `HorizontalWinChecker`, `VerticalWinChecker`, two diagonal checkers, iterated in a loop. Looks "properly object-oriented," but:

- Connect Four's win conditions **will never change** — exactly four directions, forever. Building runtime extensibility here violates **YAGNI**.
- All four checkers do the identical thing with different numbers: count contiguous discs from a point. The only difference is the `(dr, dc)` direction values.
- Strategy pattern makes sense when you genuinely need to swap behaviors at runtime (e.g., payment methods). Here the behavior is uniform and requirements fixed — this is pattern abuse, not design.

#### Great solution: unified directional vector approach

The direction is just **data** — a `(dr, dc)` pair. Separate data (direction vectors) from logic (the counting algorithm), written once.

```
checkWin(row, col, color)
    if row < 0 || row >= rows || col < 0 || col >= cols
        return false
    if grid[row][col] != color
        return false

    directions = [[0,1], [1,0], [1,1], [-1,1]]
    for dr, dc in directions:
        count = 1
        count += countInDirection(row, col, dr, dc, color)    // one direction
        count += countInDirection(row, col, -dr, -dc, color)  // opposite direction
        if count >= 4
            return true
    return false

countInDirection(row, col, dr, dc, color)
    count = 0
    r = row + dr
    c = col + dc
    while inBounds(r, c) && grid[r][c] == color
        count++
        r += dr
        c += dc
    return count
```

Horizontal = (0,1), vertical = (1,0), diagonals = (1,1) and (-1,1). Shorter, testable, one place to fix bugs, and trivially generalizes (e.g., five-in-a-row variant). In an interview this signals you know **when to use patterns and when not to** — flexibility via polymorphism vs simplicity via parameterization.

### Board helpers

```
canPlace(column)
    if column < 0 || column >= cols
        return false
    return grid[0][column] == null    // top row empty means column has space

isFull()
    for c = 0 to cols - 1
        if canPlace(c)
            return false
    return true

inBounds(row, col)
    return row >= 0 && row < rows && col >= 0 && col < cols
```

### Player

No interesting implementation — just getters. Skip unless asked.

### Verification

Trace a short game to catch logic errors before the interviewer does. The article traces: partially filled board → alternating drops → vertical win detected on move 5 (`count = 1 + 3 = 4`, `state = WON`) → move 6 rejected because `state != IN_PROGRESS`. Verbally walking test cases is usually enough; check with your interviewer rather than writing out every state.

## Extensibility (~5 min, if time and level allow)

Depth/quantity of follow-ups scales with level: juniors often get none, mid-level one or two, seniors more depth. You explain how classes adapt — full implementation usually not required.

### 1. Different board sizes?
Make `rows`/`cols` constructor parameters on `Board`. Placement and win logic already work for arbitrary dimensions (they rely on `rows`, `cols`, `inBounds`). Game barely changes — it just constructs the size it wants. The design already has a natural plug-in point.

### 2. Undo / move history?
Tests whether orchestration (Game) is cleanly separated from state (Board). All moves flow through `Game.makeMove` — a single choke point for recording.

```
class Move:
    - player: Player
    - row: int
    - col: int

class Game:
    - moveHistory: Stack<Move>   // push after each successful placeDisc

class Board:
    + clearCell(row, col)        // grid[row][col] = null

undoLastMove()
    if moveHistory.isEmpty()
        return false
    last = moveHistory.pop()
    board.clearCell(last.row, last.col)   // revert board
    currentPlayer = last.player           // revert turn
    state = IN_PROGRESS                   // recompute state (simplest version)
    winner = null
    return true
```

A production version might recompute win state more cleverly; this is enough for an interview.

### 3. Computer opponent?
Key insight: **rules don't change.** Game still enforces turns/validity; Board still owns grid logic. A bot just chooses a column.

```
class BotEngine:
    + chooseMove(game) -> int

chooseMove(game)
    board = game.getBoard()
    for col = 0 to board.getCols() - 1
        if board.canPlace(col)
            return col
    return -1

// game loop
while game.getGameState() == IN_PROGRESS
    current = game.getCurrentPlayer()
    column = (current == humanPlayer) ? readFromUI() : bot.chooseMove(game)
    game.makeMove(current, column)
```

No changes to Board, `makeMove`, or game rules — just a thin decision-making layer.

Alternative: make `Player` an interface with `HumanPlayer` / `BotPlayer` implementations. But the article argues **BotEngine is the better design**: a human player doesn't "do" anything — they're data. Making Player an interface adds abstraction without value; keeping identity separate from decision-making is cleaner.

## What Is Expected at Each Level?

### Junior
Decompose into logical pieces and implement a working game: board, players, turn orchestrator. Exact names matter less than sensible responsibilities. Working `placeDisc`; win checking at least horizontal + vertical (hints okay for diagonals). Basic edge-case handling (returning false is fine). A complete playable game that identifies winner/draw = doing well.

### Mid-level
Clean separation of concerns **without guidance**: Game = orchestration/turns, Board = grid + win detection, Player = minimal data. `makeMove` validates state before mutating (game state → turn order → column validity → place). Win checking handles all four directions cleanly — the `(dr, dc)` directional vector approach preferred over four separate methods. Able to discuss at least one extensibility scenario (undo, configurable size) and explain where changes would live without implementing.

### Senior
Production-review-quality design. Proactively justify decisions: why Player is just data, why GameState is an enum not booleans, why win checking lives on Board. Elegant `checkWin` (direction vectors + single `countInDirection` helper). Catch your own edge cases without prompting. Discuss multiple extensibility approaches with tradeoffs; recognize a bot changes only decision-making, not rules. Strong seniors finish early and can discuss networked multiplayer or spectator support.

## Key Takeaways

- Make invalid states unrepresentable (enum over boolean flags).
- YAGNI: don't apply Strategy pattern to fixed, uniform behavior — parameterize with data (direction vectors) instead.
- Separate concerns: Game = game rules, Board = grid rules, Player = data.
- Validate before mutating; keep validation where the knowledge lives (Board validates grid, Game validates turns/state).
