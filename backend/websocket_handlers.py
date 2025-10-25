"""
WebSocket event handlers for HashQuest game
"""
from flask_socketio import emit, join_room, leave_room
from flask import request
from flask_jwt_extended import decode_token
from .models.team import Team
from .models.game_state import GameState
from .models.page import Page
from .services.game_service import GameManager
import structlog

logger = structlog.get_logger()

def register_socketio_handlers(socketio, db_manager):
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info("Client connected", client_id=request.sid)
        emit('connected', {'message': 'Connected to HashQuest server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected", client_id=request.sid)
    
    @socketio.on('join_game')
    def handle_join_game(data):
        """Handle team joining the game room"""
        try:
            token = data.get('token')
            if not token:
                emit('error', {'message': 'Authentication token required'})
                return
            
            # Decode JWT token to get team info
            decoded = decode_token(token)
            team_id = decoded.get('sub')
            
            if not team_id:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Get team info
            team_model = Team(db_manager)
            team = team_model.get_by_id(team_id)
            
            if not team:
                emit('error', {'message': 'Team not found'})
                return
            
            # Join the game room
            join_room('game')
            logger.info("Team joined game", team_id=team_id, team_code=team.get('code'))
            
            emit('joined_game', {
                'message': 'Successfully joined the game',
                'team_code': team.get('code'),
                'team_name': team.get('name')
            })
            
        except Exception as e:
            logger.error("Error joining game", error=str(e))
            emit('error', {'message': 'Failed to join game'})
    
    @socketio.on('leave_game')
    def handle_leave_game():
        """Handle team leaving the game room"""
        try:
            leave_room('game')
            logger.info("Team left game", client_id=request.sid)
            emit('left_game', {'message': 'Left the game'})
        except Exception as e:
            logger.error("Error leaving game", error=str(e))
    
    @socketio.on('get_game_status')
    def handle_get_game_status():
        """Send current game status to client"""
        try:
            game_state_model = GameState(db_manager)
            page_model = Page(db_manager)
            
            game_state = game_state_model.get_current()
            current_page = page_model.get_by_number(game_state['current_page'])
            
            emit('game_status', {
                'current_page': game_state['current_page'],
                'game_status': game_state['game_status'],
                'revealed_letters': game_state.get('revealed_letters', {}),
                'page_info': current_page,
                'word': GameManager.WORD
            })
            
        except Exception as e:
            logger.error("Error getting game status", error=str(e))
            emit('error', {'message': 'Failed to get game status'})
    
    @socketio.on('get_leaderboard')
    def handle_get_leaderboard():
        """Send current leaderboard to client"""
        try:
            team_model = Team(db_manager)
            teams = team_model.get_all()
            
            rankings = []
            for team in teams:
                greens, yellows = GameManager.best_team_scores(team)
                rankings.append({
                    'name': team.get('name'),
                    'code': team.get('code'),
                    'greens': greens,
                    'yellows': yellows,
                    'NOMs': team.get('NOMs', 0),
                    'word_guesses_count': len(team.get('word_guesses', [])),
                    'guesses_left': team.get('guesses_left', 3)
                })
            
            rankings.sort(key=lambda x: (-x['greens'], -x['NOMs'], -x['yellows']))
            
            emit('leaderboard', {'rankings': rankings})
            
        except Exception as e:
            logger.error("Error getting leaderboard", error=str(e))
            emit('error', {'message': 'Failed to get leaderboard'})
    
    @socketio.on('subscribe_updates')
    def handle_subscribe_updates():
        """Subscribe to real-time game updates"""
        try:
            join_room('updates')
            emit('subscribed', {'message': 'Subscribed to game updates'})
        except Exception as e:
            logger.error("Error subscribing to updates", error=str(e))
            emit('error', {'message': 'Failed to subscribe to updates'})
    
    @socketio.on('unsubscribe_updates')
    def handle_unsubscribe_updates():
        """Unsubscribe from real-time game updates"""
        try:
            leave_room('updates')
            emit('unsubscribed', {'message': 'Unsubscribed from game updates'})
        except Exception as e:
            logger.error("Error unsubscribing from updates", error=str(e))
            emit('error', {'message': 'Failed to unsubscribe from updates'})
