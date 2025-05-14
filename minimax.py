import math
import random

class MinimaxAI:
    def __init__(self, size=3, difficulty='medium'):
        self.size = size
        self.difficulty = difficulty

    def find_best_move(self, board, player):
        if self.difficulty == 'easy':
            return self.random_move(board)
        elif self.difficulty == 'medium':
            # Introduce a small chance for medium to choose random moves
            if random.random() < 0.3:  # 30% chance to pick randomly, otherwise uses minimax
                return self.random_move(board)
            else:
                return self.minimax_move(board, player)
        return self.minimax_move(board, player)

    def random_move(self, board):
        empty = [(i, j) for i in range(self.size) for j in range(self.size) if board[i][j] == '']
        return random.choice(empty) if empty else None

    def minimax_move(self, board, player):
        best_score = -math.inf
        best_move = None

        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == '':
                    board[i][j] = player
                    score = self.minimax(board, 0, False, player)
                    board[i][j] = ''
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)

        return best_move

    def minimax(self, board, depth, is_maximizing, player):
        opponent = 'X' if player == 'O' else 'O'
        winner = self.check_winner(board)

        if winner == player:
            return 10 - depth
        elif winner == opponent:
            return depth - 10
        elif self.is_draw(board):
            return 0

        if is_maximizing:
            best_score = -math.inf
            for i in range(self.size):
                for j in range(self.size):
                    if board[i][j] == '':
                        board[i][j] = player
                        score = self.minimax(board, depth + 1, False, player)
                        board[i][j] = ''
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = math.inf
            for i in range(self.size):
                for j in range(self.size):
                    if board[i][j] == '':
                        board[i][j] = opponent
                        score = self.minimax(board, depth + 1, True, player)
                        board[i][j] = ''
                        best_score = min(score, best_score)
            return best_score

    def check_winner(self, board):
        # Check rows, columns, and diagonals for a winner
        for i in range(self.size):
            if board[i][0] != '' and all(board[i][j] == board[i][0] for j in range(self.size)):
                return board[i][0]
            if board[0][i] != '' and all(board[j][i] == board[0][i] for j in range(self.size)):
                return board[0][i]

        if board[0][0] != '' and all(board[i][i] == board[0][0] for i in range(self.size)):
            return board[0][0]
        if board[0][self.size - 1] != '' and all(board[i][self.size - i - 1] == board[0][self.size - 1] for i in range(self.size)):
            return board[0][self.size - 1]

        return None

    def is_draw(self, board):
        return all(cell != '' for row in board for cell in row)
