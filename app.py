# app.py

from flask import Flask, render_template, request, jsonify, session
from minimax import MinimaxAI
from flask_session import Session
import time

app = Flask(__name__)
# IMPORTANT: Change this secret key in a real application!
app.secret_key = 'a-super-secret-key-that-is-not-this' 
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# The TicTacToe class remains the same, it's already flexible!
class TicTacToe:
    # ... (no changes needed in this class, keep it as it is)
    def __init__(self, size=3, difficulty='medium'):
        self.size = size
        self.difficulty = difficulty
        self.board = [['' for _ in range(size)] for _ in range(size)]
        self.current_player = 'X'
        self.move_history = []
        self.stats = {'X': 0, 'O': 0, 'Draw': 0, 'Games': 0, 'AI_time': []}
        self.ai = MinimaxAI(size, difficulty)

    def make_move(self, row, col):
        if self.board[row][col] == '':
            self.board[row][col] = self.current_player
            self.move_history.append((self.current_player, row, col))
            return True
        return False

    def switch_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def is_winner(self, player):
        win_line = [player] * self.size
        # Check rows
        for row in self.board:
            if row == win_line:
                return True
        # Check columns
        for col in range(self.size):
            if [self.board[row][col] for row in range(self.size)] == win_line:
                return True
        # Check diagonals
        if self.size > 0 and [self.board[i][i] for i in range(self.size)] == win_line:
            return True
        if self.size > 0 and [self.board[i][self.size - i - 1] for i in range(self.size)] == win_line:
            return True
        return False

    def is_draw(self):
        return all(self.board[i][j] != '' for i in range(self.size) for j in range(self.size))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    data = request.json
    # Read the new settings from the frontend
    size = int(data.get('size', 3))
    difficulty = data.get('difficulty', 'medium')
    start_player = data.get('start_player', 'X')

    # Keep old stats if they exist in the session
    old_stats = session.get('game', {}).get('stats', {'X': 0, 'O': 0, 'Draw': 0, 'Games': 0, 'AI_time': []})
    
    game = TicTacToe(size, difficulty)
    game.stats = old_stats # Preserve stats across new games
    
    response = {
        'board': game.board,
        'initial_ai_move': None,
        'ai_time': None
    }
    
    # If AI is set to start, make its first move now
    if start_player == 'O':
        game.current_player = 'O'
        start_time = time.time()
        ai_move = game.ai.find_best_move(game.board, 'O')
        ai_time = round(time.time() - start_time, 3)
        
        if ai_move:
            game.make_move(ai_move[0], ai_move[1])
            game.switch_player() # Switch back to 'X' for the user's turn
            response['initial_ai_move'] = ai_move
            response['ai_time'] = ai_time
            game.stats['AI_time'].append(ai_time)

    session['game'] = game.__dict__
    
    # Also return current stats for the initial UI update
    ai_times = game.stats['AI_time']
    avg_time = round(sum(ai_times) / len(ai_times), 3) if ai_times else 0
    response['stats'] = {
        'X': game.stats['X'], 'O': game.stats['O'], 'Draw': game.stats['Draw'],
        'Avg AI Time': avg_time
    }

    return jsonify(response)


@app.route('/restart', methods=['POST'])
def restart_game():
    game_dict = session.get('game')
    if not game_dict:
        return jsonify({'status': 'error', 'message': 'No game in session'}), 400
    
    # Re-initialize the game but keep the stats
    size = game_dict['size']
    difficulty = game_dict['difficulty']
    stats = game_dict['stats']
    
    new_game = TicTacToe(size, difficulty)
    new_game.stats = stats
    
    session['game'] = new_game.__dict__
    return jsonify({'status': 'restarted', 'board': new_game.board})

# --- Other routes (`/move`, `/stats`, etc.) ---
# The rest of the routes are mostly okay, but we'll make a small tweak to `/move` to handle a winning move correctly
# and `/stats` to be more robust. The `/ai-move` and `/state` routes are not used by the new JS,
# but we can leave them for now.

@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    row, col = data['row'], data['col']
    game_dict = session.get('game')
    if not game_dict:
        return jsonify({'status': 'error', 'message': 'No game in session'}), 400
        
    game = TicTacToe(game_dict['size'], game_dict['difficulty'])
    game.__dict__.update(game_dict)

    # Player's move
    if not game.make_move(row, col):
        return jsonify({'status': 'invalid'})

    if game.is_winner('X'):
        game.stats['X'] += 1
        game.stats['Games'] += 1
        session['game'] = game.__dict__
        return jsonify({'status': 'win', 'winner': 'X', 'ai_move': None})

    if game.is_draw():
        game.stats['Draw'] += 1
        game.stats['Games'] += 1
        session['game'] = game.__dict__
        return jsonify({'status': 'draw', 'ai_move': None})

    game.switch_player()

    # AI's move
    start_time = time.time()
    ai_move = game.ai.find_best_move(game.board, 'O')
    ai_time = round(time.time() - start_time, 3)
    game.stats['AI_time'].append(ai_time)

    if ai_move:
        game.make_move(ai_move[0], ai_move[1])
        if game.is_winner('O'):
            game.stats['O'] += 1
            game.stats['Games'] += 1
            session['game'] = game.__dict__
            return jsonify({'status': 'win', 'winner': 'O', 'ai_move': ai_move, 'ai_time': ai_time})
        if game.is_draw():
            game.stats['Draw'] += 1
            game.stats['Games'] += 1
            session['game'] = game.__dict__
            return jsonify({'status': 'draw', 'ai_move': ai_move, 'ai_time': ai_time})
        game.switch_player()

    session['game'] = game.__dict__
    return jsonify({'status': 'continue', 'ai_move': ai_move, 'ai_time': ai_time})


@app.route('/stats', methods=['GET'])
def get_stats():
    game_dict = session.get('game')
    if game_dict:
        stats = game_dict.get('stats', {})
        ai_times = stats.get('AI_time', [])
        avg_time = round(sum(ai_times) / len(ai_times), 3) if ai_times else 0
        return jsonify({
            'X': stats.get('X', 0),
            'O': stats.get('O', 0),
            'Draw': stats.get('Draw', 0),
            'Games': stats.get('Games', 0),
            'Avg AI Time': avg_time
        })
    # Return default stats if no game is in session
    return jsonify({'X': 0, 'O': 0, 'Draw': 0, 'Games': 0, 'Avg AI Time': 0})

# The rest of the file (minimax.py, unused routes, if __name__ == '__main__':) can remain the same.
# Ensure you copy over the TicTacToe class and the other routes correctly.
if __name__ == '__main__':
    app.run(debug=True)