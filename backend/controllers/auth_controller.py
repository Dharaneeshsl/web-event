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
        
        # Check team cap
        team_count = self.team_model.collection.count_documents({})
        if team_count >= 20:
            return jsonify({'error': 'Maximum number of teams (20) reached'}), 400
        
        if self.team_model.get_by_code(name):
            return jsonify({'error': 'Team name already exists'}), 400
        
        code = AuthService.generate_team_code()
        while self.team_model.get_by_code(code):
            code = AuthService.generate_team_code()
        
        team_data = {
            'name': name,
            'code': code,
            'password_hash': AuthService.hash_password(password),
            'word_guesses': [],
            'has_nonce': False
        }
        
        team_id = self.team_model.create(team_data)
        token = create_access_token(identity=team_id)
        
        return jsonify({
            'team_id': team_id,
            'team_code': code,
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