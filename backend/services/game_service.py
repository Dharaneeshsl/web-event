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

        target_counts = {}
        guess_counts = {}

        # First pass: greens
        for i in range(n):
            if guess[i] == target[i]:
                greens += 1
            else:
                if target[i].isalpha():
                    target_counts[target[i]] = target_counts.get(target[i], 0) + 1
                if guess[i].isalpha():
                    guess_counts[guess[i]] = guess_counts.get(guess[i], 0) + 1

        # Second pass: yellows
        for ch, cnt in guess_counts.items():
            if ch in target_counts:
                yellows += min(cnt, target_counts[ch])

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