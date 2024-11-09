import time
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebInterface:
    """
    A class to interact with the New York Times Connections website.
    """

    def __init__(self):
        """Initialize the WebInterface class.

        Attributes:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        self.driver = self.setup_driver()

    def setup_driver(self) -> webdriver.Chrome:
        """Set up the Selenium WebDriver.

        Returns:
            WebDriver: Configured WebDriver instance.
        """
        driver = webdriver.Chrome()
        driver.maximize_window()
        return driver

    def _navigate_to_puzzle(self):
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

    def get_puzzle_words(self) -> List[str]:
        """Fetch today's puzzle words.

        Returns:
            List[str]: The words in today's puzzle.
        """
        try:
            self.driver.get("https://www.nytimes.com/games/connections")
            self._navigate_to_puzzle()

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

            return puzzle_words

        except Exception as e:
            print("An error occurred while fetching today's puzzle words:", e)
            raise Exception("Failed to fetch today's puzzle words")

    def enter_guess(self, guess_words: List[str], puzzle_words: List[str]):
        """Enter the given words as a guess in the puzzle.

        Args:
            guess_words (List[str]): The words to enter as a guess.
            puzzle_words (List[str]): All the words in the puzzle.
        """
        for word in guess_words:
            index = puzzle_words.index(word)
            word_button = self.driver.find_element(
                By.CSS_SELECTOR, f"label[for='inner-card-{index}']"
            )
            word_button.click()
            time.sleep(0.5)

        submit_button = self.driver.find_element(
            By.CSS_SELECTOR, "button[data-testid='submit-btn']"
        )
        submit_button.click()

    def check_one_away(self) -> bool:
        """Check if the most recent guess was one word away from being correct.

        Returns:
            bool: True if the guess was one word away, False otherwise.
        """
        try:
            toast_div = self.driver.find_element(By.ID, "portal-toast-system")
            feedback_text = toast_div.text.strip()
            if feedback_text and "one away" in feedback_text.lower():
                return True
            return False
        except Exception as e:
            print("An error occurred while checking if the guess was one away:", e)
            return None

    def get_mistakes_left(self) -> int:
        """Get the number of mistakes left before the puzzle is failed.

        Returns:
            int: The number of mistakes left.
        """
        try:
            mistakes_span = self.driver.find_element(
                By.CSS_SELECTOR, "span.Mistakes-module_mistakesRemainingBubbles__iTrFU"
            )
            return len(mistakes_span.find_elements(By.TAG_NAME, "span"))
        except Exception as e:
            print("An error occurred while getting the number of mistakes left:", e)
            return None

    def deselect_all_words(self):
        """Deselect all words in the puzzle"""
        try:
            deselect_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[data-testid='deselect-btn']"
            )
            deselect_button.click()
        except Exception as e:
            print("An error occurred while deselecting all words:", e)

    def get_outcome_text(self) -> str:
        """Get the outcome text to check if the puzzle is solved.

        Returns:
            str: The outcome text.
        """
        try:
            h2_element = self.driver.find_element(By.ID, "conn-congrats__title")
            outcome_text = h2_element.text.strip()
            return outcome_text
        except Exception as e:
            print("An error occurred while getting the outcome text:", e)
            return None
