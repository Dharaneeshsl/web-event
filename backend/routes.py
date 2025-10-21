from flask import Blueprint
from flask_jwt_extended import JWTManager
from .controllers.auth_controller import AuthController
from .controllers.game_controller import GameController
from .database import db_manager

api_bp = Blueprint('api', __name__, url_prefix='/api')

auth_controller = AuthController(db_manager)
game_controller = GameController(db_manager)
jwt = JWTManager()

# Auth routes
@api_bp.route('/teams/register', methods=['POST'])
def register():
    return auth_controller.register()

@api_bp.route('/teams/login', methods=['POST'])
def login():
    return auth_controller.login()

@api_bp.route('/teams/profile', methods=['GET'])
def profile():
    return auth_controller.profile()

# Game routes
@api_bp.route('/game/status', methods=['GET'])
def game_status():
    return game_controller.status()

@api_bp.route('/game/solve', methods=['POST'])
def solve_page():
    return game_controller.solve_page()

@api_bp.route('/game/guess-letter', methods=['POST'])
def guess_letter():
    return game_controller.guess_letter()

@api_bp.route('/game/guess-word', methods=['POST'])
def guess_word():
    return game_controller.guess_word()

@api_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    return game_controller.leaderboard()

@api_bp.route('/game/start', methods=['POST'])
def start_game():
    return game_controller.start_game()

@api_bp.route('/game/reset', methods=['POST'])
def reset_game():
    return game_controller.reset_game()

@api_bp.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200