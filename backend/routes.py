from flask import Blueprint
from flask_jwt_extended import jwt_required
from .controllers.auth_controller import AuthController
from .controllers.game_controller import GameController
from .controllers.admin_controller import AdminController
from .database import db_manager

api_bp = Blueprint('api', __name__, url_prefix='/api')

auth_controller = AuthController(db_manager)
game_controller = GameController(db_manager)
admin_controller = AdminController(db_manager)

# Auth routes
@api_bp.route('/teams/register', methods=['POST'])
def register():
    return auth_controller.register()

@api_bp.route('/teams/login', methods=['POST'])
def login():
    return auth_controller.login()

## Profile route removed (JWT-dependent)

# Game routes (JWT protected)
@api_bp.route('/game/status', methods=['GET'])
@jwt_required()
def game_status():
    return game_controller.status()

@api_bp.route('/game/solve', methods=['POST'])
@jwt_required()
def solve_page():
    return game_controller.solve_page()

@api_bp.route('/game/guess-letter', methods=['POST'])
@jwt_required()
def guess_letter():
    return game_controller.guess_letter()

@api_bp.route('/game/guess-word', methods=['POST'])
@jwt_required()
def guess_word():
    return game_controller.guess_word()

@api_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def leaderboard():
    return game_controller.leaderboard()

@api_bp.route('/game/start', methods=['POST'])
@jwt_required()
def start_game():
    return game_controller.start_game()

@api_bp.route('/game/reset', methods=['POST'])
@jwt_required()
def reset_game():
    return game_controller.reset_game()

# Admin routes
@api_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    return admin_controller.get_dashboard_stats()

@api_bp.route('/admin/teams', methods=['GET'])
@jwt_required()
def admin_teams():
    return admin_controller.get_all_teams()

@api_bp.route('/admin/teams/<team_id>', methods=['GET'])
@jwt_required()
def admin_team_details(team_id):
    return admin_controller.get_team_details(team_id)

@api_bp.route('/admin/teams/<team_id>/reset', methods=['POST'])
@jwt_required()
def admin_reset_team(team_id):
    return admin_controller.reset_team(team_id)

@api_bp.route('/admin/game/start', methods=['POST'])
@jwt_required()
def admin_start_game():
    return admin_controller.start_game()

@api_bp.route('/admin/game/reset', methods=['POST'])
@jwt_required()
def admin_reset_game():
    return admin_controller.reset_game()

@api_bp.route('/admin/letters/reveal', methods=['POST'])
@jwt_required()
def admin_reveal_letter():
    return admin_controller.manually_reveal_letter()

@api_bp.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200
