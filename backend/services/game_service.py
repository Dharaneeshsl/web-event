class GameManager:
    WORD = "RICARDIAN CONTRACT"

    @staticmethod
    def unique_letters():
        letters = set([c for c in GameManager.WORD if c.isalpha()])
        return sorted(list(letters))

    @staticmethod
    def get_letter_positions(letter):
        positions = []
        for i, char in enumerate(GameManager.WORD):
            if char == letter:
                positions.append(i)
        return positions

    @staticmethod
    def validate_word_guess(guess):
        return guess.upper().strip() == GameManager.WORD

    @staticmethod
    def evaluate_guess(guess):
        # Returns greens (correct position) and yellows (wrong position but present)
        guess = guess.upper().strip()
        target = GameManager.WORD

        # Align lengths by padding/truncation for safety
        n = min(len(guess), len(target))
        greens = 0
        yellows = 0

        # Track which positions are already green
        green_positions = set()
        
        # First pass: identify greens
        for i in range(n):
            if guess[i] == target[i]:
                greens += 1
                green_positions.add(i)

        # Count remaining letters in target (excluding greens)
        target_remaining = {}
        for i, char in enumerate(target):
            if i not in green_positions and char.isalpha():
                target_remaining[char] = target_remaining.get(char, 0) + 1

        # Count remaining letters in guess (excluding greens)
        guess_remaining = {}
        for i, char in enumerate(guess):
            if i not in green_positions and char.isalpha():
                guess_remaining[char] = guess_remaining.get(char, 0) + 1

        # Calculate yellows: for each letter in guess, count how many can be yellow
        for char, guess_count in guess_remaining.items():
            if char in target_remaining:
                yellows += min(guess_count, target_remaining[char])

        return greens, yellows

    @staticmethod
    def best_team_scores(team_doc):
        # Compute best greens/yellows across this team's word guesses
        best_g = 0
        best_y = 0
        for g in team_doc.get('word_guesses', []):
            guess = g.get('guess', '')
            greens, yellows = GameManager.evaluate_guess(guess)
            if (greens > best_g) or (greens == best_g and yellows > best_y):
                best_g, best_y = greens, yellows
        return best_g, best_y

    @staticmethod
    def calculate_team_rankings(teams):
        # Sort by greens desc, NOMs desc, yellows desc
        def ranking_key(team):
            g, y = GameManager.best_team_scores(team)
            noms = team.get('NOMs', 0)
            return (-g, -noms, -y)

        return sorted(teams, key=ranking_key)