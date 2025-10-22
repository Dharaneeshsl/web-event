from datetime import datetime, timedelta
from bson import ObjectId
from .base import BaseModel
from ..services.game_service import GameManager

class Team(BaseModel):
    def __init__(self, db_manager):
        super().__init__('teams', db_manager)
    
    def get_by_code(self, code):
        return self.collection.find_one({'code': code})
    
    def get_all(self):
        return list(self.collection.find())
    
    def add_guess(self, team_id, word_guess):
        result = self.collection.update_one(
            {'_id': ObjectId(team_id)},
            {'$push': {'word_guesses': word_guess}}
        )
        return result.modified_count > 0
    
    def increment_noms(self, team_id):
        return self.collection.update_one({'_id': ObjectId(team_id)}, {'$inc': {'NOMs': 1}}).modified_count > 0

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
    
    def _calculate_yellows_for_guess(self, guess, word):
        """Calculate yellow letters for a single word guess"""
        yellows = 0
        word_letters = list(word)
        guess_letters = list(guess)
        
        # Count letters that are in the word but in wrong positions
        for i, letter in enumerate(guess_letters):
            if i < len(word_letters) and letter != word_letters[i]:
                if letter in word_letters:
                    yellows += 1
        
        return yellows

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

        if self.get_by_code(name):
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
            'current_word_state': ['_' for _ in GameManager.WORD],
            'last_activity': datetime.utcnow()
        }

        try:
            team_id = self.create(team_data)
            return True, team_id, None
        except Exception as e:
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