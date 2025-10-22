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
    def calc_score(team: Dict[str, Any]):
        greens = sum(len(v) if isinstance(v, list) else 1 for v in revealed_letters.values())
        yellows = 0
        guesses = team.get('word_guesses', []) or []
        for g in guesses:
            guess = (g.get('guess') or '').upper()
            if guess and not g.get('correct', False):
                yellows += _calculate_yellows_for_guess(guess, GAME_WORD)
        has_nonce = bool(team.get('has_nonce', False))
        return greens, yellows, has_nonce

    def _calculate_yellows_for_guess(guess: str, word: str) -> int:
        yellows = 0
        word_letters = list(word)
        for i, ch in enumerate(guess):
            if i < len(word_letters) and ch != word_letters[i] and ch in word_letters:
                yellows += 1
        return yellows

    leaderboard = []
    for team in teams:
        greens, yellows, has_nonce = calc_score(team)
        leaderboard.append({
            'name': team.get('name'),
            'code': team.get('code'),
            'greens': greens,
            'yellows': yellows,
            'has_nonce': has_nonce,
            'word_guesses_count': len(team.get('word_guesses', []) or [])
        })

    leaderboard.sort(key=lambda x: (-x['greens'], -int(x['has_nonce']), -x['yellows']))
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
