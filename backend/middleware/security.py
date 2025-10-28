from functools import wraps
from typing import Callable, List
from flask import request, jsonify
from decouple import config as env_config


def validate_required_fields(required_fields: List[str]):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            missing = [f for f in required_fields if f not in data or (isinstance(data.get(f), str) and not data.get(f).strip())]
            if missing:
                return jsonify({'success': False, 'error': 'Missing required fields', 'missing': missing}), 400
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        admin_token_header = request.headers.get('X-Admin-Token')
        expected = env_config('ADMIN_TOKEN', default='')
        if not expected:
            return jsonify({'success': False, 'error': 'Admin token not configured'}), 500
        if not admin_token_header or admin_token_header != expected:
            return jsonify({'success': False, 'error': 'Admin authorization required'}), 403
        return fn(*args, **kwargs)
    return wrapper
