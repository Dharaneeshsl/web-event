import os
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
import structlog

from .config import config
from .utils.constants import TOTAL_PAGES
from .database import db_manager
from .routes import api_bp

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(config['default'])
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    logger = structlog.get_logger()
    
    # Initialize extensions
    db_manager.init_app(app)
    jwt = JWTManager(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    socketio = SocketIO(app, cors_allowed_origins=app.config.get('CORS_ORIGINS', '*'))

    # Validate critical env configuration
    if not app.config.get('SECRET_KEY'):
        logger.error("Missing SECRET_KEY in environment")
        raise RuntimeError("SECRET_KEY is required")
    if not app.config.get('JWT_SECRET_KEY'):
        logger.error("Missing JWT_SECRET_KEY in environment")
        raise RuntimeError("JWT_SECRET_KEY is required")
    
    app.register_blueprint(api_bp)
    
    # Initialize database using Page model
    try:
        from .models.page import Page
        page_model = Page(db_manager)
        if page_model.count() == 0:
            page_model.create_default_pages()
        
        game_state_collection = db_manager.get_collection('game_state')
        if game_state_collection.count_documents({'type': 'current'}) == 0:
            game_state = {
                'type': 'current',
                'current_page': 1,
                'revealed_letters': {},
                'game_status': 'waiting'
            }
            game_state_collection.insert_one(game_state)
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise RuntimeError(f"Database initialization failed: {str(e)}")
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'HashQuest Backend',
            'word': 'POWERHOUSE',
            'pages': TOTAL_PAGES,
            'max_teams': 20
        })
    
    # Register WebSocket handlers
    from .websocket_handlers import register_socketio_handlers
    register_socketio_handlers(socketio, db_manager)
    
    # Expose socketio via app extensions
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['socketio'] = socketio
    return app

app = create_app()
socketio = app.extensions['socketio']

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

