from decouple import config as env_config

# Default word aligned with current frontend implementation
GAME_WORD = env_config('GAME_WORD', default='POWERHOUSE')
TOTAL_PAGES = env_config('TOTAL_PAGES', default=10, cast=int)

GAME_STATUS_WAITING = 'waiting'
GAME_STATUS_ACTIVE = 'in_progress'
GAME_STATUS_COMPLETED = 'completed'

ERROR_MESSAGES = {
    'INTERNAL_ERROR': 'An unexpected error occurred',
    'TEAM_NOT_FOUND': 'Team not found'
}

SUCCESS_MESSAGES = {
    'TEAM_REGISTERED': 'Team registered successfully'
}
