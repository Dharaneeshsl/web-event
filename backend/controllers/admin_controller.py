from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, Any
import structlog

from ..services.auth_service import AuthService
from ..models.team import Team
from ..models.page import Page
from ..models.game_state import GameState
from ..utils.helpers import create_response, create_error_response, format_leaderboard
from ..utils.constants import ERROR_MESSAGES, SUCCESS_MESSAGES
from ..middleware.security import validate_required_fields, admin_required

logger = structlog.get_logger()

class AdminController:
    def __init__(self, db_manager):
        self.team_model = Team(db_manager)
        self.page_model = Page(db_manager)
        self.game_state_model = GameState(db_manager)
    
    @jwt_required()
    @admin_required
    def get_dashboard_stats(self) -> tuple[Dict[str, Any], int]:
        """Get comprehensive dashboard statistics"""
        try:
            # Get team statistics
            teams = self.team_model.get_all()
            active_teams = self.team_model.get_active_teams()
            
            # Get page statistics
            page_stats = self.page_model.get_page_stats()
            
            # Get game state
            game_state = self.game_state_model.get_current()
            game_progress = self.game_state_model.get_game_progress()
            
            # Calculate additional stats
            total_word_guesses = sum(len(team.get('word_guesses', [])) for team in teams)
            correct_guesses = sum(
                len([g for g in team.get('word_guesses', []) if g.get('correct', False)])
                for team in teams
            )
            
            stats = {
                'teams': {
                    'total': len(teams),
                    'active': len(active_teams),
                    'inactive': len(teams) - len(active_teams)
                },
                'pages': page_stats,
                'game': {
                    'status': game_state.get('game_status', 'waiting'),
                    'current_page': game_state.get('current_page', 1),
                    'progress': game_progress,
                    'duration_seconds': self.game_state_model.get_game_duration()
                },
                'guesses': {
                    'total': total_word_guesses,
                    'correct': correct_guesses,
                    'accuracy': (correct_guesses / total_word_guesses * 100) if total_word_guesses > 0 else 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return create_response(data=stats), 200
            
        except Exception as e:
            logger.error("Failed to get dashboard stats", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def get_teams(self) -> tuple[Dict[str, Any], int]:
        """Get all teams with pagination and filtering"""
        try:
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            search = request.args.get('search', '').strip()
            status = request.args.get('status', 'all')
            
            # Build query
            query = {}
            if search:
                query['$or'] = [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'code': {'$regex': search, '$options': 'i'}}
                ]
            
            if status == 'active':
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                query['last_activity'] = {'$gte': cutoff_time}
            elif status == 'inactive':
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                query['$or'] = [
                    {'last_activity': {'$lt': cutoff_time}},
                    {'last_activity': {'$exists': False}}
                ]
            
            # Get teams
            teams = self.team_model.find_many(
                query=query,
                sort=[('created_at', -1)],
                skip=(page - 1) * per_page,
                limit=per_page
            )
            
            total = self.team_model.count(query)
            
            # Clean team data
            cleaned_teams = [self.team_model.clean_team_data(team) for team in teams]
            
            response_data = {
                'teams': cleaned_teams,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
            return create_response(data=response_data), 200
            
        except Exception as e:
            logger.error("Failed to get teams", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    @validate_required_fields(['name', 'password'])
    def create_team(self) -> tuple[Dict[str, Any], int]:
        """Create a new team"""
        try:
            data = request.get_json()
            name = data['name'].strip()
            password = data['password']
            code = data.get('code', '').strip().upper()
            
            # Create team
            success, team_id, errors = self.team_model.create_team(name, password, code or None)
            
            if not success:
                return create_error_response('Failed to create team', 400, errors), 400
            
            # Get created team
            team = self.team_model.get_by_id(team_id)
            cleaned_team = self.team_model.clean_team_data(team)
            
            return create_response(
                data=cleaned_team,
                message=SUCCESS_MESSAGES['TEAM_REGISTERED']
            ), 201
            
        except Exception as e:
            logger.error("Failed to create team", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def delete_team(self, team_id: str) -> tuple[Dict[str, Any], int]:
        """Delete a team"""
        try:
            if not self.team_model.get_by_id(team_id):
                return create_error_response(ERROR_MESSAGES['TEAM_NOT_FOUND'], 404), 404
            
            success = self.team_model.delete(team_id)
            if not success:
                return create_error_response('Failed to delete team', 500), 500
            
            return create_response(message='Team deleted successfully'), 200
            
        except Exception as e:
            logger.error("Failed to delete team", team_id=team_id, error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def get_pages(self) -> tuple[Dict[str, Any], int]:
        """Get all pages with statistics"""
        try:
            pages = self.page_model.get_all()
            page_stats = self.page_model.get_page_stats()
            
            response_data = {
                'pages': pages,
                'statistics': page_stats
            }
            
            return create_response(data=response_data), 200
            
        except Exception as e:
            logger.error("Failed to get pages", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def reset_page(self, page_number: int) -> tuple[Dict[str, Any], int]:
        """Reset a specific page"""
        try:
            if not self.page_model.validate_page_number(page_number):
                return create_error_response('Invalid page number', 400), 400
            
            success = self.page_model.reset_page(page_number)
            if not success:
                return create_error_response('Failed to reset page', 500), 500
            
            return create_response(message=f'Page {page_number} reset successfully'), 200
            
        except Exception as e:
            logger.error("Failed to reset page", page_number=page_number, error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def reset_all_pages(self) -> tuple[Dict[str, Any], int]:
        """Reset all pages"""
        try:
            count = self.page_model.reset_all_pages()
            return create_response(
                data={'reset_count': count},
                message=f'Reset {count} pages successfully'
            ), 200
            
        except Exception as e:
            logger.error("Failed to reset all pages", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def get_game_state(self) -> tuple[Dict[str, Any], int]:
        """Get current game state"""
        try:
            game_state = self.game_state_model.get_current()
            game_progress = self.game_state_model.get_game_progress()
            game_stats = self.game_state_model.get_game_statistics()
            
            response_data = {
                'game_state': game_state,
                'progress': game_progress,
                'statistics': game_stats
            }
            
            return create_response(data=response_data), 200
            
        except Exception as e:
            logger.error("Failed to get game state", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    @validate_required_fields(['action'])
    def control_game(self) -> tuple[Dict[str, Any], int]:
        """Control game state (start, stop, pause, resume, reset)"""
        try:
            data = request.get_json()
            action = data['action'].lower()
            
            if action == 'start':
                success = self.game_state_model.start_game()
                message = 'Game started successfully'
            elif action == 'stop':
                success = self.game_state_model.end_game()
                message = 'Game stopped successfully'
            elif action == 'pause':
                success = self.game_state_model.pause_game()
                message = 'Game paused successfully'
            elif action == 'resume':
                success = self.game_state_model.resume_game()
                message = 'Game resumed successfully'
            elif action == 'reset':
                success = self.game_state_model.reset_game()
                message = 'Game reset successfully'
            else:
                return create_error_response('Invalid action', 400), 400
            
            if not success:
                return create_error_response('Failed to control game', 500), 500
            
            return create_response(message=message), 200
            
        except Exception as e:
            logger.error("Failed to control game", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def set_current_page(self, page_number: int) -> tuple[Dict[str, Any], int]:
        """Set current page number"""
        try:
            if not self.page_model.validate_page_number(page_number):
                return create_error_response('Invalid page number', 400), 400
            
            success = self.game_state_model.set_page(page_number)
            if not success:
                return create_error_response('Failed to set page', 500), 500
            
            return create_response(message=f'Current page set to {page_number}'), 200
            
        except Exception as e:
            logger.error("Failed to set current page", page_number=page_number, error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def get_leaderboard(self) -> tuple[Dict[str, Any], int]:
        """Get leaderboard with admin details"""
        try:
            game_state = self.game_state_model.get_current()
            revealed_letters = game_state.get('revealed_letters', {})
            
            teams = self.team_model.get_all()
            leaderboard = format_leaderboard(teams, revealed_letters)
            
            response_data = {
                'leaderboard': leaderboard,
                'game_state': game_state,
                'total_teams': len(teams)
            }
            
            return create_response(data=response_data), 200
            
        except Exception as e:
            logger.error("Failed to get leaderboard", error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def reveal_letter(self, letter: str) -> tuple[Dict[str, Any], int]:
        """Manually reveal a letter"""
        try:
            letter = letter.upper().strip()
            if len(letter) != 1 or not letter.isalpha():
                return create_error_response('Invalid letter', 400), 400
            
            if self.game_state_model.is_letter_revealed(letter):
                return create_error_response('Letter already revealed', 400), 400
            
            from ..utils.helpers import get_letter_positions
            positions = get_letter_positions(letter)
            
            if not positions:
                return create_error_response('Letter not found in word', 400), 400
            
            success = self.game_state_model.reveal_letter(letter, positions)
            if not success:
                return create_error_response('Failed to reveal letter', 500), 500
            
            return create_response(
                data={'letter': letter, 'positions': positions},
                message=f'Letter {letter} revealed successfully'
            ), 200
            
        except Exception as e:
            logger.error("Failed to reveal letter", letter=letter, error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500
    
    @jwt_required()
    @admin_required
    def get_team_details(self, team_id: str) -> tuple[Dict[str, Any], int]:
        """Get detailed information about a specific team"""
        try:
            team = self.team_model.get_by_id(team_id)
            if not team:
                return create_error_response(ERROR_MESSAGES['TEAM_NOT_FOUND'], 404), 404
            
            # Get team stats
            team_stats = self.team_model.get_team_stats(team_id)
            
            # Get solved pages
            solved_pages = self.page_model.get_team_solved_pages(team['code'])
            
            # Get game state for score calculation
            game_state = self.game_state_model.get_current()
            revealed_letters = game_state.get('revealed_letters', {})
            score = self.team_model.calculate_score(team, revealed_letters)
            
            response_data = {
                'team': self.team_model.clean_team_data(team),
                'stats': team_stats,
                'solved_pages': solved_pages,
                'score': score
            }
            
            return create_response(data=response_data), 200
            
        except Exception as e:
            logger.error("Failed to get team details", team_id=team_id, error=str(e))
            return create_error_response(ERROR_MESSAGES['INTERNAL_ERROR'], 500), 500



