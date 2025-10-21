from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import BaseModel
from ..utils.constants import TOTAL_PAGES
import structlog

logger = structlog.get_logger()

class Page(BaseModel):
    def __init__(self, db_manager):
        super().__init__('pages', db_manager)
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for pages collection"""
        try:
            self.create_index('number', unique=True)
            self.create_index('is_solved')
            self.create_index('solved_by')
            self.create_index('solved_at')
        except Exception as e:
            logger.warning("Failed to create some indexes", collection='pages', error=str(e))
    
    def get_by_number(self, number: int) -> Optional[Dict[str, Any]]:
        """Get page by number"""
        return self.find_one({'number': number})
    
    def get_all(self, include_solved: bool = True) -> List[Dict[str, Any]]:
        """Get all pages with optional filtering"""
        query = {} if include_solved else {'is_solved': False}
        return self.find_many(query, sort=[('number', 1)])
    
    def get_solved_pages(self) -> List[Dict[str, Any]]:
        """Get all solved pages"""
        return self.find_many({'is_solved': True}, sort=[('solved_at', 1)])
    
    def get_unsolved_pages(self) -> List[Dict[str, Any]]:
        """Get all unsolved pages"""
        return self.find_many({'is_solved': False}, sort=[('number', 1)])
    
    def mark_solved(self, page_number: int, team_code: str, solution: str = None) -> bool:
        """Mark page as solved by team"""
        try:
            # Atomic update: only mark as solved if not already solved
            result = self.collection.update_one(
                {'number': page_number, 'is_solved': False},
                {
                    '$set': {
                'is_solved': True,
                'solved_by': team_code,
                        'solved_at': datetime.utcnow(),
                        'first_solver_team_code': team_code,
                        'solution_used': solution,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            success = result.modified_count > 0
            if success:
                logger.info("Page marked as solved", page_number=page_number, team_code=team_code)
            return success
        except Exception as e:
            logger.error("Failed to mark page as solved", page_number=page_number, team_code=team_code, error=str(e))
            return False
    
    def is_solved(self, page_number: int) -> bool:
        """Check if page is solved"""
        page = self.get_by_number(page_number)
        return page.get('is_solved', False) if page else False
    
    def get_solver(self, page_number: int) -> Optional[str]:
        """Get team code that solved the page"""
        page = self.get_by_number(page_number)
        return page.get('solved_by') if page else None
    
    def get_first_solver(self, page_number: int) -> Optional[str]:
        """Get team code that first solved the page"""
        page = self.get_by_number(page_number)
        return page.get('first_solver_team_code') if page else None
    
    def get_solve_time(self, page_number: int) -> Optional[datetime]:
        """Get time when page was solved"""
        page = self.get_by_number(page_number)
        return page.get('solved_at') if page else None
    
    def get_page_stats(self) -> Dict[str, Any]:
        """Get comprehensive page statistics"""
        total_pages = self.count()
        solved_pages = self.count({'is_solved': True})
        unsolved_pages = total_pages - solved_pages
        
        # Get solving teams
        solved_pages_data = self.get_solved_pages()
        solving_teams = list(set(page.get('solved_by') for page in solved_pages_data if page.get('solved_by')))
        
        return {
            'total_pages': total_pages,
            'solved_pages': solved_pages,
            'unsolved_pages': unsolved_pages,
            'completion_percentage': (solved_pages / total_pages * 100) if total_pages > 0 else 0,
            'solving_teams': len(solving_teams),
            'solving_teams_list': solving_teams
        }
    
    def get_team_solved_pages(self, team_code: str) -> List[Dict[str, Any]]:
        """Get pages solved by specific team"""
        return self.find_many({'solved_by': team_code}, sort=[('solved_at', 1)])
    
    def get_next_unsolved_page(self) -> Optional[Dict[str, Any]]:
        """Get the next unsolved page in sequence"""
        unsolved_pages = self.get_unsolved_pages()
        return unsolved_pages[0] if unsolved_pages else None
    
    def reset_page(self, page_number: int) -> bool:
        """Reset page to unsolved state"""
        try:
            result = self.collection.update_one(
                {'number': page_number},
                {
                    '$set': {
                        'is_solved': False,
                        'solved_by': None,
                        'solved_at': None,
                        'first_solver_team_code': None,
                        'solution_used': None,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            success = result.modified_count > 0
            if success:
                logger.info("Page reset", page_number=page_number)
            return success
        except Exception as e:
            logger.error("Failed to reset page", page_number=page_number, error=str(e))
            return False
    
    def reset_all_pages(self) -> int:
        """Reset all pages to unsolved state"""
        try:
            result = self.collection.update_many(
                {},
                {
                    '$set': {
                        'is_solved': False,
                        'solved_by': None,
                        'solved_at': None,
                        'first_solver_team_code': None,
                        'solution_used': None,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            logger.info("All pages reset", count=result.modified_count)
            return result.modified_count
        except Exception as e:
            logger.error("Failed to reset all pages", error=str(e))
            return 0
    
    def create_default_pages(self) -> List[str]:
        """Create default pages for the game"""
        pages_data = [
            {
                'number': 1,
                'letter': 'R',
                'puzzle': 'Blockchain verification process',
                'solution': 'PROOF_OF_WORK',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 2,
                'letter': 'I',
                'puzzle': 'Distributed ledger technology',
                'solution': 'BLOCKCHAIN',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 3,
                'letter': 'C',
                'puzzle': 'Cryptographic hash function',
                'solution': 'SHA256',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 4,
                'letter': 'A',
                'puzzle': 'Smart contract platform',
                'solution': 'ETHEREUM',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 5,
                'letter': 'D',
                'puzzle': 'Digital asset ownership',
                'solution': 'NFT',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 6,
                'letter': 'N',
                'puzzle': 'Consensus mechanism',
                'solution': 'NONCE',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 7,
                'letter': 'O',
                'puzzle': 'Decentralized exchange',
                'solution': 'DEX',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            },
            {
                'number': 8,
                'letter': 'T',
                'puzzle': 'Token standard',
                'solution': 'ERC20',
                'is_solved': False,
                'solved_by': None,
                'solved_at': None,
                'first_solver_team_code': None,
                'solution_used': None
            }
        ]
        
        try:
            # Clear existing pages
            self.collection.delete_many({})
            
            # Insert new pages
            page_ids = self.bulk_create(pages_data)
            logger.info("Default pages created", count=len(page_ids))
            return page_ids
        except Exception as e:
            logger.error("Failed to create default pages", error=str(e))
            return []
    
    def validate_page_number(self, page_number: int) -> bool:
        """Validate page number"""
        return isinstance(page_number, int) and 1 <= page_number <= TOTAL_PAGES
    
    def get_page_progress(self) -> Dict[str, Any]:
        """Get page completion progress"""
        stats = self.get_page_stats()
        return {
            'current_page': stats['solved_pages'] + 1,
            'total_pages': stats['total_pages'],
            'progress_percentage': stats['completion_percentage'],
            'is_complete': stats['solved_pages'] >= stats['total_pages']
        }