from flask import Flask, render_template, request, jsonify, session
from minimax import MinimaxAI
from flask_session import Session
import time

app = Flask(__name__)
app.secret_key = 'secret!'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

class TicTacToe:
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
        for row in self.board:
            if row == win_line:
                return True
        for col in range(self.size):
            if [self.board[row][col] for row in range(self.size)] == win_line:
                return True
        if [self.board[i][i] for i in range(self.size)] == win_line:
            return True
        if [self.board[i][self.size - i - 1] for i in range(self.size)] == win_line:
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
    size = int(data['size'])
    difficulty = data['difficulty']
    session['game'] = TicTacToe(size, difficulty).__dict__
    return jsonify({'status': 'started'})

@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    row, col = data['row'], data['col']
    game_dict = session.get('game')
    game = TicTacToe(game_dict['size'], game_dict['difficulty'])
    game.__dict__.update(game_dict)

    if game.make_move(row, col):
        if game.is_winner('X'):
            game.stats['X'] += 1
            game.stats['Games'] += 1
            session['game'] = game.__dict__
            return jsonify({'status': 'win', 'winner': 'X'})

        if game.is_draw():
            game.stats['Draw'] += 1
            game.stats['Games'] += 1
            session['game'] = game.__dict__
            return jsonify({'status': 'draw'})

        game.switch_player()

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

    return jsonify({'status': 'invalid'})

@app.route('/ai-move', methods=['POST'])
def ai_move():
    data = request.json
    board = data['board']
    board_size = data['board_size']
    ai = MinimaxAI(board_size, 'medium')
    move = ai.find_best_move(board, 'O')
    return jsonify({'move': move})

@app.route('/restart', methods=['POST'])
def restart_game():
    game_dict = session.get('game')
    session['game'] = TicTacToe(game_dict['size'], game_dict['difficulty']).__dict__
    return jsonify({'status': 'restarted'})

@app.route('/stats', methods=['GET'])
def get_stats():
    game_dict = session.get('game')
    if game_dict:
        ai_times = game_dict['stats']['AI_time']
        avg_time = round(sum(ai_times) / len(ai_times), 3) if ai_times else 0
        return jsonify({
            'X': game_dict['stats']['X'],
            'O': game_dict['stats']['O'],
            'Draw': game_dict['stats']['Draw'],
            'Games': game_dict['stats']['Games'],
            'Avg AI Time': avg_time
        })
    return jsonify({})

@app.route('/state', methods=['GET'])
def get_state():
    game_dict = session.get('game')
    if game_dict:
        return jsonify({
            'board': game_dict['board'],
            'current_player': game_dict['current_player']
        })
    return jsonify({'board': [], 'current_player': 'X'})

if __name__ == '__main__':
    app.run(debug=True)
