from typing import Any, Dict, List
from flask import jsonify
from bson import ObjectId
from .constants import GAME_WORD


def create_response(data: Dict[str, Any] | List[Any] | None = None, message: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {'success': True}
    if message is not None:
        payload['message'] = message
    if data is not None:
        payload['data'] = serialize_object(data)
    return jsonify(payload)


def create_error_response(message: str, status_code: int, errors: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        'success': False,
        'error': message,
        'status_code': status_code
    }
    if errors:
        payload['errors'] = serialize_object(errors)
    return jsonify(payload)


def get_letter_positions(letter: str) -> List[int]:
    letter = letter.upper()
    positions: List[int] = []
    for i, ch in enumerate(GAME_WORD):
        if ch == letter:
            positions.append(i)
    return positions


def format_leaderboard(teams: List[Dict[str, Any]], revealed_letters: Dict[str, List[int]]):
    """Format leaderboard using consistent scoring from GameManager.best_team_scores"""
    from ..services.game_service import GameManager
    
    leaderboard = []
    for team in teams:
        # Use GameManager.best_team_scores for consistent scoring
        greens, yellows = GameManager.best_team_scores(team)
        has_nonce = bool(team.get('has_nonce', False))
        
        leaderboard.append({
            'name': team.get('name'),
            'code': team.get('code'),
            'greens': greens,
            'yellows': yellows,
            'has_nonce': has_nonce,
            'word_guesses_count': len(team.get('word_guesses', []) or [])
        })

    # Sort by greens desc, NOMs desc, yellows desc
    leaderboard.sort(key=lambda x: (-x['greens'], -x.get('NOMs', 0), -x['yellows']))
    return leaderboard


def serialize_object(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object(i) for i in obj]
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


def is_valid_object_id(value: str) -> bool:
    try:
        ObjectId(value)
        return True
    except Exception:
        return False
