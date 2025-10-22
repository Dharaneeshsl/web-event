from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..services.game_service import GameService
from ..models.team import Team
from ..models.page import Page
from ..models.game_state import GameState
from ..utils.constants import GAME_STATUS_COMPLETED

class GameController:
    def __init__(self, db_manager):
        self.team_model = Team(db_manager)
        self.page_model = Page(db_manager)
        self.game_state_model = GameState(db_manager)
    
    def status(self):
        game_state = self.game_state_model.get_current()
        current_page = self.page_model.get_by_number(game_state['current_page'])
        
        return jsonify({
            'current_page': game_state['current_page'],
            'game_status': game_state['game_status'],
            'revealed_letters': game_state.get('revealed_letters', {}),
            'page_info': current_page,
            'word': GameService.WORD
        }), 200
    
    @jwt_required()
    def solve_page(self):
        team_id = get_jwt_identity()
        team = self.team_model.get_by_id(team_id)
        
        data = request.get_json()
        answer = data.get('answer', '').strip().upper()
        
        if not answer:
            return jsonify({'error': 'Answer required'}), 400
        
        game_state = self.game_state_model.get_current()
        current_page = self.page_model.get_by_number(game_state['current_page'])
        
        if current_page.get('is_solved'):
            return jsonify({'error': 'Page already solved'}), 400
        
        if answer != current_page.get('solution'):
            return jsonify({'error': 'Incorrect answer'}), 400
        
        # Atomically mark page as solved
        success = self.page_model.mark_solved(game_state['current_page'], team['code'], answer)
        if not success:
            return jsonify({'error': 'Page was solved by another team'}), 409
        
        # Award NONCE randomly
        if GameService.assign_nonce():
            self.team_model.update_nonce(team_id, True)
            nonce_awarded = True
        else:
            nonce_awarded = False
        
        # Advance to next page
        if game_state['current_page'] < 8:
            self.game_state_model.advance_page()
        else:
            self.game_state_model.update_state({'game_status': GAME_STATUS_COMPLETED})
        
        response_data = {
            'message': 'Page solved successfully! You can now guess a letter.',
            'can_guess_letter': True,
            'first_solver': True
        }
        
        if nonce_awarded:
            response_data['nonce_awarded'] = True
            response_data['message'] += ' You have been awarded a NONCE!'
        
        return jsonify(response_data), 200
    
    @jwt_required()
    def guess_letter(self):
        team_id = get_jwt_identity()
        team = self.team_model.get_by_id(team_id)
        data = request.get_json()
        letter = data.get('letter', '').strip().upper()
        
        if not letter or len(letter) != 1:
            return jsonify({'error': 'Invalid letter'}), 400
        
        game_state = self.game_state_model.get_current()
        current_page = self.page_model.get_by_number(game_state['current_page'])
        
        # Check if this team is the first solver
        if current_page.get('first_solver_team_code') != team['code']:
            return jsonify({'error': 'Only the first solver can guess a letter'}), 403
        
        # Check if letter already guessed for this page
        if current_page.get('letter_guessed'):
            return jsonify({'error': 'Letter already guessed for this page'}), 400
        
        # Check if letter already revealed
        if letter in game_state.get('revealed_letters', {}):
            return jsonify({'error': 'Letter already revealed'}), 400
        
        positions = GameService.get_letter_positions(letter)
        
        # Mark letter as guessed for this page
        self.page_model.collection.update_one(
            {'number': game_state['current_page']},
            {'$set': {'letter_guessed': True}}
        )
        
        if positions:
            self.game_state_model.reveal_letter(letter, positions)
            return jsonify({
                'correct': True,
                'letter': letter,
                'positions': positions,
                'message': f'Letter {letter} revealed in positions {positions}'
            }), 200
        else:
            return jsonify({
                'correct': False,
                'letter': letter,
                'message': f'Letter {letter} not found in the word'
            }), 200
    
    @jwt_required()
    def guess_word(self):
        team_id = get_jwt_identity()
        team = self.team_model.get_by_id(team_id)
        
        data = request.get_json()
        guess = data.get('guess', '').strip().upper()
        
        if not guess:
            return jsonify({'error': 'Word guess required'}), 400
        
        if len(team.get('word_guesses', [])) >= 3:
            return jsonify({'error': 'No more word guesses remaining'}), 400
        
        is_correct = GameService.validate_word_guess(guess)
        
        self.team_model.add_guess(team_id, {
            'guess': guess,
            'correct': is_correct,
            'timestamp': datetime.utcnow()
        })
        
        if is_correct:
            self.game_state_model.update_state({'game_status': GAME_STATUS_COMPLETED})
            return jsonify({
                'correct': True,
                'message': 'Congratulations! You guessed the word correctly!'
            }), 200
        else:
            remaining = 3 - len(team.get('word_guesses', [])) - 1
            return jsonify({
                'correct': False,
                'message': f'Incorrect guess. {remaining} guesses remaining.',
                'remaining_guesses': remaining
            }), 200
    
    def leaderboard(self):
        teams = self.team_model.get_all()
        game_state = self.game_state_model.get_current()
        revealed_letters = game_state.get('revealed_letters', {})
        
        rankings = []
        for team in teams:
            score = self.team_model.calculate_score(team, revealed_letters)
            rankings.append({
                'name': team['name'],
                'code': team['code'],
                'greens': score['greens'],
                'yellows': score['yellows'],
                'has_nonce': score['has_nonce'],
                'word_guesses_count': len(team.get('word_guesses', []))
            })
        
        rankings.sort(key=lambda x: (-x['greens'], -x['has_nonce'], -x['yellows']))
        return jsonify({'rankings': rankings}), 200
    
    def start_game(self):
        game_state = self.game_state_model.get_current()
        
        if game_state['game_status'] != 'waiting':
            return jsonify({'error': 'Game is not in waiting state'}), 400
        
        self.game_state_model.update_state({'game_status': 'in_progress'})
        return jsonify({'message': 'Game started successfully'}), 200
    
    def reset_game(self):
        # Reset all pages
        self.page_model.collection.update_many(
            {},
            {'$set': {
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'letter_guessed': False
            }}
        )
        
        # Reset game state
        self.game_state_model.update_state({
            'current_page': 1,
            'revealed_letters': {},
            'game_status': 'waiting'
        })
        
        # Reset teams' nonce status
        self.team_model.collection.update_many(
            {},
            {'$set': {'has_nonce': False}}
        )
        
        return jsonify({'message': 'Game reset successfully'}), 200