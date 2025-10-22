import os
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
from flask_socketio import SocketIO

from .config import config
from .database import db_manager
from .routes import api_bp

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(config['default'])
    
    db_manager.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    socketio = SocketIO(app, cors_allowed_origins=app.config.get('CORS_ORIGINS', '*'))
    
    app.register_blueprint(api_bp)
    
    # Initialize database
    pages_collection = db_manager.get_collection('pages')
    if pages_collection.count_documents({}) == 0:
        pages = [
            {'number': 1, 'letter': 'R', 'puzzle': 'Blockchain verification process', 'solution': 'PROOF_OF_WORK'},
            {'number': 2, 'letter': 'I', 'puzzle': 'Distributed ledger technology', 'solution': 'BLOCKCHAIN'},
            {'number': 3, 'letter': 'C', 'puzzle': 'Cryptographic hash function', 'solution': 'SHA256'},
            {'number': 4, 'letter': 'A', 'puzzle': 'Smart contract platform', 'solution': 'ETHEREUM'},
            {'number': 5, 'letter': 'D', 'puzzle': 'Digital asset ownership', 'solution': 'NFT'},
            {'number': 6, 'letter': 'N', 'puzzle': 'Consensus mechanism', 'solution': 'NONCE'},
            {'number': 7, 'letter': 'O', 'puzzle': 'Decentralized exchange', 'solution': 'DEX'},
            {'number': 8, 'letter': 'T', 'puzzle': 'Token standard', 'solution': 'ERC20'}
        ]
        
        for page in pages:
            page['is_solved'] = False
            page['solved_by'] = None
            page['solved_at'] = None
            page['created_at'] = datetime.utcnow()
            pages_collection.insert_one(page)
    
    game_state_collection = db_manager.get_collection('game_state')
    if game_state_collection.count_documents({'type': 'current'}) == 0:
        game_state = {
            'type': 'current',
            'current_page': 1,
            'revealed_letters': {},
            'game_status': 'waiting'
        }
        game_state_collection.insert_one(game_state)
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'HashQuest Backend',
            'word': 'RICARDIAN CONTRACT',
            'pages': 8,
            'max_teams': 20
        })
    
    # Expose socketio via app extensions
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['socketio'] = socketio
    return app

app = create_app()
socketio = app.extensions['socketio']

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

