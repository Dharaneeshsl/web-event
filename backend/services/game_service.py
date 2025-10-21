import random

class GameService:
    WORD = "RICARDIAN CONTRACT"
    
    @staticmethod
    def get_letter_positions(letter):
        positions = []
        for i, char in enumerate(GameService.WORD):
            if char == letter:
                positions.append(i)
        return positions
    
    @staticmethod
    def validate_word_guess(guess):
        return guess.upper().strip() == GameService.WORD
    
    @staticmethod
    def calculate_team_rankings(teams, revealed_letters):
        def ranking_key(team):
            word = GameService.WORD
            greens = sum(1 for i, letter in enumerate(word) if letter in revealed_letters)
            yellows = 0  # Not used in this game
            has_nonce = team.get('has_nonce', False)
            
            return (-greens, -has_nonce, -yellows)
        
        return sorted(teams, key=ranking_key)
    
    @staticmethod
    def assign_nonce():
        return random.choice([True, False])