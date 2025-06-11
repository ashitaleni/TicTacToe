// static/script.js

// --- Global state variables ---
let board = [];
let gameActive = false;
let boardSize = 3; 

// --- DOM Element references ---
const startBtn = document.getElementById("start-btn");
const restartBtn = document.getElementById("restart-btn");
const boardContainer = document.getElementById("board-container");
const gameInfo = document.getElementById("game-info");
const moveHistoryContainer = document.getElementById("move-history");
const statsDisplay = document.getElementById("stats-display");

document.addEventListener("DOMContentLoaded", () => {
    startBtn.addEventListener("click", startGame);
    restartBtn.addEventListener("click", restartGame);
    updateStatsDisplay(); // Initial display
});

function startGame() {
    // Read new settings from the sidebar
    boardSize = parseInt(document.getElementById("board-size").value);
    const difficulty = document.getElementById("difficulty").value;
    const startPlayer = document.getElementById("start-player").value;
    
    gameActive = false; // Disable board clicks until server responds
    updateStatus("Initializing new game...");

    fetch("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            size: boardSize, 
            difficulty: difficulty,
            start_player: startPlayer // Send new setting to backend
        })
    })
    .then(res => res.json())
    .then(data => {
        board = data.board;
        moveHistoryContainer.innerHTML = '';
        renderBoard();
        
        if (data.initial_ai_move) {
            // AI made the first move
            const [aiRow, aiCol] = data.initial_ai_move;
            board[aiRow][aiCol] = 'O';
            addMoveToHistory('AI', aiRow, aiCol, data.ai_time);
            renderBoard();
        }
        
        gameActive = true;
        updateStatus("Your turn (X)");
        updateStatsDisplay(data.stats);
    })
    .catch(err => {
        console.error("Error starting game:", err);
        updateStatus("Failed to start game");
    });
}

function restartGame() {
    if (!gameActive && board.length === 0) {
        updateStatus("Start a game first!");
        return;
    }
    updateStatus("Restarting match...");
    fetch("/restart", { method: "POST" })
    .then(res => res.json())
    .then(data => {
        board = data.board;
        moveHistoryContainer.innerHTML = '';
        renderBoard();
        gameActive = true;
        updateStatus("Game restarted. Your turn (X)");
    })
    .catch(err => console.error("Error restarting game:", err));
}

function renderBoard() {
    boardContainer.innerHTML = "";
    // Dynamically set grid size and cell size for different boards
    const cellSize = boardSize > 3 ? (boardSize > 4 ? 70 : 85) : 100;
    boardContainer.style.gridTemplateColumns = `repeat(${boardSize}, ${cellSize}px)`;
    boardContainer.style.gridTemplateRows = `repeat(${boardSize}, ${cellSize}px)`;

    for (let i = 0; i < boardSize; i++) {
        for (let j = 0; j < boardSize; j++) {
            const cell = document.createElement("div");
            cell.classList.add("cell");
            cell.dataset.row = i;
            cell.dataset.col = j;
            
            const cellValue = board[i][j];
            if (cellValue) {
                cell.textContent = cellValue;
                cell.classList.add(cellValue === 'X' ? 'player-x' : 'player-o');
            }
            
            cell.style.width = `${cellSize}px`;
            cell.style.height = `${cellSize}px`;
            cell.style.fontSize = `${Math.floor(cellSize * 0.6)}px`;
            
            cell.addEventListener("click", handleCellClick);
            boardContainer.appendChild(cell);
        }
    }
}

function handleCellClick(e) {
    if (!gameActive) return;

    const row = parseInt(e.target.dataset.row);
    const col = parseInt(e.target.dataset.col);

    if (board[row][col] !== '') return;

    gameActive = false; // Prevent multiple clicks
    updateStatus("AI is thinking...");
    board[row][col] = 'X'; // Optimistically place the 'X'
    addMoveToHistory('You', row, col);
    renderBoard();

    fetch("/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row, col })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'invalid') {
            updateStatus("Invalid move. Try again.");
            board[row][col] = ''; // Revert optimistic move
            renderBoard();
            gameActive = true;
            return;
        }

        if (data.ai_move) {
            const [aiRow, aiCol] = data.ai_move;
            board[aiRow][aiCol] = 'O';
            addMoveToHistory('AI', aiRow, aiCol, data.ai_time);
        }
        
        renderBoard(); // Render final state of the turn

        if (data.status === 'win') {
            updateStatus(data.winner === 'X' ? "YOU WIN!" : "AI WINS!");
        } else if (data.status === 'draw') {
            updateStatus("IT'S A DRAW!");
        } else {
            updateStatus("Your turn (X)");
            gameActive = true;
        }
        
        // Fetch and update stats after every move
        fetch("/stats").then(res => res.json()).then(updateStatsDisplay);
    })
    .catch(err => {
        console.error("Error making move:", err);
        updateStatus("Error. Please restart.");
    });
}

function addMoveToHistory(player, row, col, time) {
    const moveText = document.createElement('div');
    moveText.textContent = `${player} -> (${row}, ${col})`;
    if (time) {
        moveText.textContent += ` [${time}s]`;
    }
    moveHistoryContainer.appendChild(moveText);
    moveHistoryContainer.scrollTop = moveHistoryContainer.scrollHeight;
}

function updateStatus(message) {
    gameInfo.textContent = message;
}

function updateStatsDisplay(stats) {
    if (!stats) {
        statsDisplay.textContent = "Player (X): 0\nAI (O): 0\nDraws: 0\nAvg AI Time: 0s";
        return;
    }
    statsDisplay.textContent = 
        `Player (X): ${stats.X}\n` +
        `AI (O):     ${stats.O}\n` +
        `Draws:      ${stats.Draws}\n` +
        `Avg AI Time: ${stats['Avg AI Time']}s`;
}