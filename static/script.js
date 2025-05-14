let board = [];
let gameActive = false;
let moveHistory = [];
let stats = {
    wins: 0,
    losses: 0,
    draws: 0,
    aiThinkingTimes: [],
    movesPerGame: [],
};

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("start-btn").addEventListener("click", startGame);
    document.getElementById("restart-btn").addEventListener("click", restartGame);
    document.getElementById("how-to-play-toggle").addEventListener("click", toggleHowToPlay);
});

function startGame() {
    const size = 3;
    const difficulty = document.getElementById("difficulty").value;

    fetch("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ size, difficulty })
    })
    .then(res => res.json())
    .then(() => {
        board = Array.from({ length: size }, () => Array(size).fill(''));
        gameActive = true;
        moveHistory = [];
        renderBoard();
        updateStatus("Your turn (X)");
        updateStatsDisplay();
    })
    .catch(err => {
        console.error("Error starting game:", err);
        updateStatus("Failed to start game");
    });
}

function restartGame() {
    fetch("/restart", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(() => {
        const size = board.length || 3;
        board = Array.from({ length: size }, () => Array(size).fill(''));
        gameActive = true;
        moveHistory = [];
        renderBoard();
        updateStatus("Game restarted. Your turn (X)");
    })
    .catch(err => {
        console.error("Error restarting game:", err);
        updateStatus("Failed to restart game");
    });
}

function toggleHowToPlay() {
    const howTo = document.getElementById("how-to-play");
    howTo.style.display = howTo.style.display === "none" ? "block" : "none";
}

function renderBoard() {
    const container = document.getElementById("board-container");
    container.innerHTML = "";
    container.style.gridTemplateColumns = `repeat(${board.length}, 60px)`;

    for (let i = 0; i < board.length; i++) {
        for (let j = 0; j < board[i].length; j++) {
            const cell = document.createElement("div");
            cell.classList.add("cell");
            cell.dataset.row = i;
            cell.dataset.col = j;
            cell.textContent = board[i][j];
            cell.addEventListener("click", handleCellClick);
            container.appendChild(cell);
        }
    }
}

function handleCellClick(e) {
    if (!gameActive) return;

    const row = parseInt(e.target.dataset.row);
    const col = parseInt(e.target.dataset.col);

    if (board[row][col] !== '') return;

    updateStatus("Processing move...");
    const moveStartTime = performance.now();

    fetch("/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row, col })
    })
    .then(res => res.json())
    .then(data => {
        const moveEndTime = performance.now();
        const moveTime = moveEndTime - moveStartTime;

        if (data.status === 'invalid') {
            updateStatus("Invalid move - try again");
            return;
        }

        board[row][col] = 'X';
        moveHistory.push(`You: (${row}, ${col})`);

        if (data.ai_move) {
            const [aiRow, aiCol] = data.ai_move;
            board[aiRow][aiCol] = 'O';
            moveHistory.push(`AI: (${aiRow}, ${aiCol}) [${data.ai_time}s]`);
            stats.aiThinkingTimes.push(parseFloat(data.ai_time));
        }

        renderBoard();

        if (data.status === 'win') {
            gameActive = false;
            const result = data.winner === 'X' ? "You win!" : "AI wins!";
            updateStatus(result);
            data.winner === 'X' ? stats.wins++ : stats.losses++;
            finalizeStats();
        } else if (data.status === 'draw') {
            gameActive = false;
            updateStatus("It's a draw!");
            stats.draws++;
            finalizeStats();
        } else {
            updateStatus("Your turn (X)");
        }
    })
    .catch(err => {
        console.error("Error making move:", err);
        updateStatus("Error processing move - try again");
    });
}

function updateStatus(message) {
    document.getElementById("game-info").textContent = message;
    document.getElementById("move-history").textContent = moveHistory.join('\n');
}

function finalizeStats() {
    stats.movesPerGame.push(moveHistory.length);
    updateStatsDisplay();
}

function updateStatsDisplay() {
    document.getElementById("stats").textContent =
        `Wins: ${stats.wins}\nLosses: ${stats.losses}\nDraws: ${stats.draws}\n` +
        `Avg AI Time: ${average(stats.aiThinkingTimes)}s\n` +
        `Avg Moves/Game: ${average(stats.movesPerGame)}`;
}

function average(arr) {
    return arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2) : '0.00';
}
