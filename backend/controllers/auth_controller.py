from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from ..services.auth_service import AuthService
from ..models.team import Team

class AuthController:
    def __init__(self, db_manager):
        self.team_model = Team(db_manager)
    
    def register(self):
        data = request.get_json()
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()
        
        if not name or not password:
            return jsonify({'error': 'Name and password required'}), 400
        
        if len(name) < 2 or len(name) > 50:
            return jsonify({'error': 'Team name must be 2-50 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Use team_model.create_team() for consistent team creation
        # The create_team method handles team cap validation atomically
        success, team_id, errors = self.team_model.create_team(name, password)
        if not success:
            if 'Maximum number of teams' in str(errors):
                return jsonify({'error': 'Maximum number of teams (20) reached'}), 400
            return jsonify({'error': errors}), 400
        
        # Get the created team to get the code
        team = self.team_model.get_by_id(team_id)
        token = create_access_token(identity=team_id)
        
        return jsonify({
            'team_id': team_id,
            'team_code': team['code'],
            'access_token': token
        }), 201
    
    def login(self):
        data = request.get_json()
        code = data.get('team_code', '').strip()
        password = data.get('password', '').strip()
        
        team = self.team_model.get_by_code(code)
        if not team or not AuthService.verify_password(password, team['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = create_access_token(identity=str(team['_id']))
        
        return jsonify({
            'team_id': str(team['_id']),
            'access_token': token
        }), 200
    
    @jwt_required()
    def profile(self):
        team_id = get_jwt_identity()
        team = self.team_model.get_by_id(team_id)
        
        return jsonify({
            'team_id': str(team['_id']),
            'name': team['name'],
            'code': team['code'],
            'word_guesses_count': len(team.get('word_guesses', [])),
            'has_nonce': team.get('has_nonce', False)
        }), 200