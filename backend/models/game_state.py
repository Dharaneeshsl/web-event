from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import BaseModel
from ..utils.constants import GAME_WORD, GAME_STATUS_WAITING, GAME_STATUS_ACTIVE, GAME_STATUS_COMPLETED
import structlog

logger = structlog.get_logger()

class GameState(BaseModel):
    def __init__(self, db_manager):
        super().__init__('game_state', db_manager)
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for game_state collection"""
        try:
            self.create_index('type', unique=True)
            self.create_index('game_status')
            self.create_index('current_page')
        except Exception as e:
            logger.warning("Failed to create some indexes", collection='game_state', error=str(e))
    
    def get_current(self) -> Dict[str, Any]:
        """Get current game state"""
        state = self.find_one({'type': 'current'})
        if not state:
            state = self._create_default_state()
        return state
    
    def _create_default_state(self) -> Dict[str, Any]:
        """Create default game state"""
        state = {
            'type': 'current',
            'current_page': 1,
            'revealed_letters': {},
            'game_status': GAME_STATUS_WAITING,
            'game_start_time': None,
            'game_end_time': None,
            'total_teams': 0,
            'active_teams': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            self.create(state)
            logger.info("Default game state created")
        except Exception as e:
            logger.error("Failed to create default game state", error=str(e))
        
        return state
    
    def update_state(self, data: Dict[str, Any]) -> bool:
        """Update game state"""
        try:
            data['updated_at'] = datetime.utcnow()
            result = self.collection.update_one(
                {'type': 'current'},
                {'$set': data}
            )
            success = result.modified_count > 0
            if success:
                logger.info("Game state updated", data=data)
            return success
        except Exception as e:
            logger.error("Failed to update game state", data=data, error=str(e))
            return False
    
    def advance_page(self) -> bool:
        """Advance to next page"""
        current = self.get_current()
        new_page = current['current_page'] + 1
        return self.update_state({'current_page': new_page})
    
    def set_page(self, page_number: int) -> bool:
        """Set current page to specific number"""
        return self.update_state({'current_page': page_number})
    
    def reveal_letter(self, letter: str, positions: List[int]) -> bool:
        """Reveal letter at specific positions"""
        try:
            current = self.get_current()
            revealed = current.get('revealed_letters', {}).copy()
            
            if letter not in revealed:
                revealed[letter] = []
            
            # Add new positions
            for pos in positions:
                if pos not in revealed[letter]:
                    revealed[letter].append(pos)
            
            # Sort positions for consistency
            revealed[letter].sort()
            
            return self.update_state({'revealed_letters': revealed})
        except Exception as e:
            logger.error("Failed to reveal letter", letter=letter, positions=positions, error=str(e))
            return False
    
    def is_letter_revealed(self, letter: str) -> bool:
        """Check if letter is already revealed"""
        current = self.get_current()
        revealed_letters = current.get('revealed_letters', {})
        return letter in revealed_letters and len(revealed_letters[letter]) > 0
    
    def get_revealed_positions(self, letter: str) -> List[int]:
        """Get revealed positions for a letter"""
        current = self.get_current()
        revealed_letters = current.get('revealed_letters', {})
        return revealed_letters.get(letter, [])
    
    def set_game_status(self, status: str) -> bool:
        """Set game status"""
        valid_statuses = [GAME_STATUS_WAITING, GAME_STATUS_ACTIVE, GAME_STATUS_COMPLETED]
        if status not in valid_statuses:
            logger.warning("Invalid game status", status=status)
            return False
        
        update_data = {'game_status': status}
        
        if status == GAME_STATUS_ACTIVE and not self.get_current().get('game_start_time'):
            update_data['game_start_time'] = datetime.utcnow()
        elif status == GAME_STATUS_COMPLETED and not self.get_current().get('game_end_time'):
            update_data['game_end_time'] = datetime.utcnow()
        
        return self.update_state(update_data)
    
    def start_game(self) -> bool:
        """Start the game"""
        return self.set_game_status(GAME_STATUS_ACTIVE)
    
    def end_game(self) -> bool:
        """End the game"""
        return self.set_game_status(GAME_STATUS_COMPLETED)
    
    def pause_game(self) -> bool:
        """Pause the game"""
        return self.set_game_status('paused')
    
    def resume_game(self) -> bool:
        """Resume the game"""
        return self.set_game_status(GAME_STATUS_ACTIVE)
    
    def reset_game(self) -> bool:
        """Reset game to initial state"""
        try:
            reset_data = {
                'current_page': 1,
                'revealed_letters': {},
                'game_status': GAME_STATUS_WAITING,
                'game_start_time': None,
                'game_end_time': None,
                'total_teams': 0,
                'active_teams': 0
            }
            
            success = self.update_state(reset_data)
            if success:
                logger.info("Game reset successfully")
            return success
        except Exception as e:
            logger.error("Failed to reset game", error=str(e))
            return False
    
    def get_game_progress(self) -> Dict[str, Any]:
        """Get game progress information"""
        current = self.get_current()
        revealed_letters = current.get('revealed_letters', {})
        
        # Calculate revealed positions
        total_revealed = sum(len(positions) for positions in revealed_letters.values())
        total_positions = len(GAME_WORD)
        
        progress_percentage = (total_revealed / total_positions * 100) if total_positions > 0 else 0
        
        return {
            'current_page': current.get('current_page', 1),
            'game_status': current.get('game_status', GAME_STATUS_WAITING),
            'revealed_letters_count': len(revealed_letters),
            'total_revealed_positions': total_revealed,
            'total_positions': total_positions,
            'progress_percentage': round(progress_percentage, 2),
            'is_complete': progress_percentage >= 100,
            'game_start_time': current.get('game_start_time'),
            'game_end_time': current.get('game_end_time'),
            'total_teams': current.get('total_teams', 0),
            'active_teams': current.get('active_teams', 0)
        }
    
    def update_team_counts(self, total_teams: int, active_teams: int) -> bool:
        """Update team counts"""
        return self.update_state({
            'total_teams': total_teams,
            'active_teams': active_teams
        })
    
    def get_game_duration(self) -> Optional[int]:
        """Get game duration in seconds"""
        current = self.get_current()
        start_time = current.get('game_start_time')
        end_time = current.get('game_end_time') or datetime.utcnow()
        
        if not start_time:
            return None
        
        duration = (end_time - start_time).total_seconds()
        return int(duration)
    
    def is_game_active(self) -> bool:
        """Check if game is currently active"""
        current = self.get_current()
        return current.get('game_status') == GAME_STATUS_ACTIVE
    
    def is_game_completed(self) -> bool:
        """Check if game is completed"""
        current = self.get_current()
        return current.get('game_status') == GAME_STATUS_COMPLETED
    
    def can_advance_page(self) -> bool:
        """Check if game can advance to next page"""
        current = self.get_current()
        return (current.get('current_page', 1) < 8 and 
                current.get('game_status') == GAME_STATUS_ACTIVE)
    
    def get_game_statistics(self) -> Dict[str, Any]:
        """Get comprehensive game statistics"""
        current = self.get_current()
        progress = self.get_game_progress()
        
        return {
            'game_state': current,
            'progress': progress,
            'duration_seconds': self.get_game_duration(),
            'is_active': self.is_game_active(),
            'is_completed': self.is_game_completed(),
            'can_advance': self.can_advance_page()
        }