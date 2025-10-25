from datetime import datetime, timedelta
from bson import ObjectId
from .base import BaseModel
from ..services.game_service import GameManager
import structlog

logger = structlog.get_logger()

class Team(BaseModel):
    def __init__(self, db_manager):
        super().__init__('teams', db_manager)
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Index on team code for fast lookups
            self.collection.create_index('code', unique=True)
            # Index on team name for fast lookups
            self.collection.create_index('name', unique=True)
            # Index on last_activity for active team queries
            self.collection.create_index('last_activity')
            # Compound index for leaderboard queries
            self.collection.create_index([('NOMs', -1), ('last_activity', -1)])
            logger.info("Team indexes created successfully")
        except Exception as e:
            logger.warning("Failed to create team indexes", error=str(e))
    
    def get_by_code(self, code):
        return self.collection.find_one({'code': code})
    
    def get_by_name(self, name):
        return self.collection.find_one({'name': name})
    
    def get_all(self):
        return list(self.collection.find())
    
    def add_guess(self, team_id, word_guess):
        result = self.collection.update_one(
            {'_id': ObjectId(team_id)},
            {
                '$push': {'word_guesses': word_guess},
                '$set': {'last_activity': datetime.utcnow()}
            }
        )
        if result.modified_count > 0:
            logger.info("Team word guess added", team_id=team_id, guess=word_guess.get('guess'))
        return result.modified_count > 0
    
    def increment_noms(self, team_id):
        result = self.collection.update_one(
            {'_id': ObjectId(team_id)}, 
            {
                '$inc': {'NOMs': 1},
                '$set': {'last_activity': datetime.utcnow()}
            }
        ).modified_count > 0
        if result:
            logger.info("Team NOMs incremented", team_id=team_id)
        return result

    def add_letter_guess(self, team_id, letter, page_number):
        """Track a letter guess by this team"""
        result = self.collection.update_one(
            {'_id': ObjectId(team_id)},
            {
                '$push': {'letter_guesses': {
                    'letter': letter,
                    'page_number': page_number,
                    'timestamp': datetime.utcnow()
                }},
                '$set': {'last_activity': datetime.utcnow()}
            }
        )
        if result.modified_count > 0:
            logger.info("Team letter guess added", team_id=team_id, letter=letter, page=page_number)
        return result.modified_count > 0

    def has_guessed_letter(self, team_id, letter):
        """Check if team has already guessed this letter"""
        team = self.get_by_id(team_id)
        if not team:
            return False
        letter_guesses = team.get('letter_guesses', [])
        return any(guess['letter'] == letter for guess in letter_guesses)

    def decrement_guesses_left(self, team_id):
        team = self.get_by_id(team_id)
        current = team.get('guesses_left', 3) if team else 3
        new_val = max(0, current - 1)
        return self.update(team_id, {'guesses_left': new_val})
    
    def calculate_score(self, team, revealed_letters):
        # Use best guess against the target word to compute greens/yellows
        greens, yellows = GameManager.best_team_scores(team)
        return {
            'greens': greens,
            'yellows': yellows,
            'NOMs': team.get('NOMs', 0)
        }
    
    # Removed duplicate yellow calculation - using GameManager.evaluate_guess() instead

    def get_active_teams(self):
        """Get teams active in last 24 hours"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        return self.find_many({'last_activity': {'$gte': cutoff}})

    def clean_team_data(self, team):
        """Remove sensitive data from team"""
        if not team:
            return None
        cleaned = self.serialize_document(team)
        cleaned.pop('password_hash', None)
        return cleaned

    def create_team(self, name, password, code=None):
        """Create team with validation"""
        from ..services.auth_service import AuthService
        from ..config import config

        # Validate password length
        min_length = config['default'].PASSWORD_MIN_LENGTH
        if len(password) < min_length:
            return False, None, {'password': f'Password must be at least {min_length} characters'}

        # Check team cap atomically
        team_count = self.collection.count_documents({})
        if team_count >= 20:
            return False, None, {'error': 'Maximum number of teams (20) reached'}

        if self.get_by_name(name):
            return False, None, {'name': 'Name already exists'}

        if not code:
            code = AuthService.generate_team_code()
            while self.get_by_code(code):
                code = AuthService.generate_team_code()

        team_data = {
            'name': name,
            'code': code,
            'password_hash': AuthService.hash_password(password),
            'word_guesses': [],
            'guesses_left': 3,
            'greens': 0,
            'yellows': 0,
            'NOMs': 0,
            'solved_pages': [],
            'letter_guesses': [],  # Track letters guessed by this team
            'current_word_state': ['_' for _ in GameManager.WORD],
            'last_activity': datetime.utcnow()
        }

        try:
            team_id = self.create(team_data)
            logger.info("Team created successfully", team_id=team_id, name=name, code=code)
            return True, team_id, None
        except Exception as e:
            logger.error("Failed to create team", error=str(e), name=name)
            return False, None, {'error': str(e)}

    def get_team_stats(self, team_id):
        """Get team statistics"""
        team = self.get_by_id(team_id)
        if not team:
            return None

        return {
            'total_word_guesses': len(team.get('word_guesses', [])),
            'correct_guesses': len([g for g in team.get('word_guesses', []) if g.get('correct')]),
            'guesses_left': team.get('guesses_left', 3),
            'NOMs': team.get('NOMs', 0),
            'created_at': team.get('created_at'),
            'last_activity': team.get('last_activity')
        }