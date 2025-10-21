from datetime import datetime
from bson import ObjectId
from .base import BaseModel

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
    
    def update_nonce(self, team_id, has_nonce):
        return self.update(team_id, {'has_nonce': has_nonce})
    
    def calculate_score(self, team, revealed_letters):
        word = "RICARDIAN CONTRACT"
        greens = 0
        yellows = 0
        
        # Count actual revealed positions (greens)
        for letter, positions in revealed_letters.items():
            if isinstance(positions, list):
                greens += len(positions)
            else:
                greens += 1
        
        # Calculate yellows based on team's word guesses
        word_guesses = team.get('word_guesses', [])
        for guess_data in word_guesses:
            guess = guess_data.get('guess', '')
            if guess and not guess_data.get('correct', False):
                yellows += self._calculate_yellows_for_guess(guess, word)
        
        return {
            'greens': greens,
            'yellows': yellows,
            'has_nonce': team.get('has_nonce', False)
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