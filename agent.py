import time
import logging
from llms import TextGenerator
from web_interface import WebInterface
from models import Guess, Puzzle

OUTCOME_TO_GUESSES = {"Perfect!": 4, "Great!": 5, "Solid!": 6, "Phew!": 7}

logging.basicConfig(level=logging.INFO)


class Agent:
    """
    A class to solve NYT Connections using GPT with Chain-of-Thought.
    """

    def __init__(self):
        """Initialize the Agent class.

        Attributes:
            web_interface (WebInterface): The WebInterface instance
            text_generator (TextGenerator): The TextGenerator instance
            puzzle (Puzzle): The Puzzle instance
        """
        self.web_interface = WebInterface()
        self.text_generator = TextGenerator()
        try:
            puzzle_words = self.web_interface.get_puzzle_words()
            self.puzzle = Puzzle(words=puzzle_words)
        except Exception as e:
            logging.error("An error occurred while initializing the puzzle: %s", e)
            raise

    def _generate_guess(self) -> Guess:
        """Generate guess using OpenAI's GPT

        Returns:
            Guess: The generated guess.
        """
        try:
            llm_answer = self.text_generator.generate_guess(
                self.puzzle.words, self.puzzle.guesses
            )
            return Guess(words=llm_answer.words, reasoning=llm_answer.reasoning)
        except Exception as e:
            logging.error("An error occurred while generating a guess: %s", e)
            raise

    def _get_guess_feedback(self, guess: Guess) -> Guess:
        """Extract the feedback for the most recent guess.

        Args:
            guess (Guess): The guess just entered.

        Returns:
            Guess: The guess updated with feedback.
        """
        try:
            # Check if one away
            time.sleep(2)
            guess.one_away = self.web_interface.check_one_away()
            # Check if correct
            mistakes_left = self.web_interface.get_mistakes_left()
            if mistakes_left == self.puzzle.mistakes_left:
                guess.correct = True
                time.sleep(2)
            else:
                guess.correct = False
                self.puzzle.mistakes_left -= 1
                if self.puzzle.mistakes_left > 0:
                    self.web_interface.deselect_all_words()
            return guess
        except Exception as e:
            logging.error("An error occurred while extracting feedback: %s", e)
            raise

    def _make_guess(self):
        """Generate guess using LLM, enter it, get feedback and update the puzzle history."""
        try:
            guess = self._generate_guess()
            self.web_interface.enter_guess(guess.words, self.puzzle.words)
            guess = self._get_guess_feedback(guess)
            self.puzzle.guesses[len(self.puzzle.guesses) + 1] = guess
        except Exception as e:
            logging.error("An error occurred while making a guess: %s", e)
            raise

    def _check_solved(self) -> bool:
        """Check if the puzzle has been solved.

        Returns:
            bool: True if the puzzle is solved, False otherwise.
        """
        if self.puzzle.mistakes_left == 0:
            return False
        else:
            try:
                outcome_text = self.web_interface.get_outcome_text()
                outcome_guesses = OUTCOME_TO_GUESSES.get(outcome_text, None)
                if outcome_guesses == len(self.puzzle.guesses):
                    return True
            except Exception as e:
                logging.error(
                    "An error occurred while checking if the puzzle is solved: %s", e
                )
                raise
        return False

    def solve_puzzle(self):
        """Solve the puzzle by making guesses based on the puzzle words."""
        puzzle = self.puzzle
        try:
            while not puzzle.is_solved and puzzle.mistakes_left > 0:
                self._make_guess()
                if len(self.puzzle.guesses) >= 4:
                    puzzle.is_solved = self._check_solved()
                logging.info("Puzzle state: %s", puzzle.model_dump())
        except Exception as e:
            logging.error("An error occurred while solving the puzzle: %s", e)
            raise
        finally:
            self.web_interface.driver.close()
        return puzzle.is_solved


if __name__ == "__main__":
    try:
        agent = Agent()
        solved = agent.solve_puzzle()
        if solved:
            logging.info("Puzzle solved successfully!")
        else:
            logging.info("Failed to solve the puzzle.")
    except Exception as e:
        logging.error("An error occurred in the main execution: %s", e)
