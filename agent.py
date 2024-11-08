import time
from typing import Dict, List
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from llms import TextGenerator


class Guess(BaseModel):
    words: List[str]
    reasoning: str = None
    correct: bool = None
    one_away: bool = None


class Puzzle(BaseModel):
    words: List[str]
    guesses: Dict[int, Guess] = {}
    mistakes_left: int = 4
    is_solved: bool = None


class Agent:
    def __init__(self):
        self.setup_driver()
        self.puzzle = self.get_todays_puzzle()
        self.text_generator = TextGenerator()

    def setup_driver(self):
        """Set up the Selenium WebDriver.

        Returns:
            WebDriver: Configured WebDriver instance.
        """
        driver = webdriver.Chrome()
        driver.maximize_window()
        self.driver = driver

    def navigate_to_puzzle(self):
        """Close banners and click buttons to navigate to the puzzle page.

        Raises:
            Exception: If an error occurs while navigating to the puzzle.
        """
        try:
            # Close the cookies banner if it is displayed
            cookies_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Reject all']"))
            )
            if cookies_button.is_displayed():
                cookies_button.click()

            # Click on the 'Play' button
            play_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Play']"))
            )
            play_button.click()

            # Close modal if it is displayed
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-testid='modal-close']")
                )
            )
            if close_button.is_displayed():
                close_button.click()

        except Exception as e:
            print("An error occurred while navigating to the puzzle:", e)
            raise Exception("Failed to navigate to the puzzle")

    def get_todays_puzzle(self) -> Puzzle:
        """Fetch today's puzzle words.

        Returns:
            dict: A dictionary where the key is the index (0-15) and the value is the text associated with that label.
        """
        try:
            self.driver.get("https://www.nytimes.com/games/connections")
            self.navigate_to_puzzle()

            # Wait until the first label is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "label[for='inner-card-0']")
                )
            )

            puzzle_words = []
            for index in range(16):
                for_value = f"inner-card-{index}"
                label = self.driver.find_element(
                    By.CSS_SELECTOR, f"label[for='{for_value}']"
                )
                text = label.text.strip()
                puzzle_words.append(text)

            return Puzzle(words=puzzle_words)

        except Exception as e:
            print("An error occurred while fetching today's puzzle words:", e)
            raise Exception("Failed to fetch today's puzzle words")

    def enter_guess(self, words: List[str]):
        """Enter the given words as a guess in the puzzle.

        Args:
            words (List[str]): The words to enter as a guess.
        """
        for word in words:
            index = self.puzzle.words.index(word)
            word_button = self.driver.find_element(
                By.CSS_SELECTOR, f"label[for='inner-card-{index}']"
            )
            word_button.click()
            time.sleep(0.5)

        submit_button = self.driver.find_element(
            By.CSS_SELECTOR, "button[data-testid='submit-btn']"
        )
        submit_button.click()

    def extract_feedback(self) -> tuple[bool, bool]:
        """Extract the feedback for the most recent guess.

        Returns:
            Tuple[bool, bool]: A tuple where the first element is a boolean indicating if the guess was correct,
                and the second element is a boolean indicating if the guess was one letter away from being correct.
        """
        correct, one_away = None, False

        try:
            # Check if one away
            toast_div = self.driver.find_element(By.ID, "portal-toast-system")
            feedback_text = toast_div.text.strip()
            if feedback_text and "one away" in feedback_text.lower():
                one_away = True

            # Check if correct
            mistakes_span = self.driver.find_element(
                By.CSS_SELECTOR, "span.Mistakes-module_mistakesRemainingBubbles__iTrFU"
            )
            mistakes_left = len(mistakes_span.find_elements(By.TAG_NAME, "span"))
            if mistakes_left == self.puzzle.mistakes_left:
                correct = True
                time.sleep(2)
            else:
                correct = False
                self.puzzle.mistakes_left -= 1
                if self.puzzle.mistakes_left > 0:
                    deselect_button = self.driver.find_element(
                        By.CSS_SELECTOR, "button[data-testid='deselect-btn']"
                    )
                    deselect_button.click()
            return correct, one_away
        except Exception as e:
            print("An error occurred while extracting feedback:", e)

    def make_guess(self):
        # Generate guess and enter it
        llm_answer = self.text_generator.generate_guess(
            self.puzzle.words, self.puzzle.guesses
        )
        guess = Guess(words=llm_answer.words, reasoning=llm_answer.reasoning)
        self.enter_guess(guess.words)
        # Wait for feedback and extract it
        time.sleep(2)
        correct, one_away = self.extract_feedback()
        guess.correct, guess.one_away = correct, one_away
        # Update history of guesses
        self.puzzle.guesses[len(self.puzzle.guesses) + 1] = guess

    def check_solved(self):
        """Check if the puzzle has been solved."""
        outcomes = {"Perfect!": 4, "Great!": 5, "Solid!": 6, "Phew!": 7}
        if self.puzzle.mistakes_left == 0:
            return False
        else:
            try:
                h2_element = self.driver.find_element(By.ID, "conn-congrats__title")
                outcome_text = h2_element.text.strip()
                if outcome_text == outcomes.get(outcome_text, None):
                    return True
            except Exception as e:
                print("An error occurred while checking if the puzzle is solved:", e)
        return False

    def solve_puzzle(self):
        """Solve the puzzle by making guesses based on the puzzle words."""
        puzzle = self.puzzle
        while not puzzle.is_solved and puzzle.mistakes_left > 0:
            # Make a guess
            self.make_guess()
            # Check if the puzzle is solved
            if len(self.puzzle.guesses) >= 4:
                puzzle.is_solved = self.check_solved()
            print(puzzle.model_dump())


if __name__ == "__main__":
    agent = Agent()
    agent.solve_puzzle()
