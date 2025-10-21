# HashQuest

Blockchain puzzle game with Flask backend.

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python app.py
```

## API Endpoints

- `POST /api/teams/register` - Register team
- `POST /api/teams/login` - Login team
- `GET /api/game/status` - Game status
- `POST /api/game/solve` - Solve page
- `POST /api/game/guess-letter` - Guess letter
- `POST /api/game/guess-word` - Guess word
- `GET /api/leaderboard` - Leaderboard

## Game Rules

- 20 teams, 8 pages
- Word: "RICARDIAN CONTRACT"
- 3 word guesses per team
- Winner: correct word → greens → NONCE → yellows
