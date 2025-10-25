# HashQuest Backend

Flask backend for HashQuest blockchain puzzle game.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

## API Endpoints

### Public Endpoints
- `POST /api/teams/register` - Register team
- `POST /api/teams/login` - Login team
- `GET /api/health` - Health check

### Game Endpoints (JWT Required)
- `GET /api/game/status` - Game status
- `POST /api/game/solve` - Solve page
- `POST /api/game/guess-letter` - Guess letter
- `POST /api/game/guess-word` - Guess word
- `GET /api/leaderboard` - Leaderboard
- `POST /api/game/start` - Start game
- `POST /api/game/reset` - Reset game

### Admin Endpoints (JWT + Admin Token Required)
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/teams` - Get all teams (with pagination)
- `POST /api/admin/teams` - Create team (admin)
- `GET /api/admin/teams/<team_id>` - Get team details
- `DELETE /api/admin/teams/<team_id>` - Delete team
- `GET /api/admin/pages` - Get all pages with statistics
- `POST /api/admin/pages/<page_number>/reset` - Reset specific page
- `POST /api/admin/pages/reset-all` - Reset all pages
- `GET /api/admin/game/state` - Get game state
- `POST /api/admin/game/control` - Control game (start/stop/pause/resume/reset)
- `POST /api/admin/game/page/<page_number>` - Set current page
- `GET /api/admin/leaderboard` - Admin leaderboard with details
- `POST /api/admin/letters/reveal/<letter>` - Manually reveal letter

## Game Rules

- 20 teams, 8 pages
- Word: "RICARDIAN CONTRACT"
- 3 word guesses per team
- Winner: correct word → greens → NONCE → yellows

