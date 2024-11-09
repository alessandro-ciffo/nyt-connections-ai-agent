import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from models import LLMAnswer

load_dotenv()


class TextGenerator:
    """
    A class to generate a guess for the puzzle using GPT with Chain-of-Thought.
    """

    def __init__(self):
        """Initialize the TextGenerator class and load the prompts.

        Attributes:
            openai_client (OpenAI): The OpenAI client
            reasoning_sys_prompt (str): The system prompt for generating reasoning
            reasoning_user_prompt (str): The user prompt for generating reasoning
            parsing_sys_prompt (str): The system prompt for parsing the answer
        """
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.reasoning_sys_prompt = self.load_prompt("reasoning_sys_prompt.txt")
        self.reasoning_user_prompt = self.load_prompt("reasoning_user_prompt.txt")
        self.parsing_sys_prompt = self.load_prompt("parsing_sys_prompt.txt")

    @staticmethod
    def load_prompt(filename):
        """Load a prompt from the prompts directory.

        Args:
            filename (str): The name of the file to load

        Returns:
            str: The content of the file
        """
        filepath = os.path.join(os.path.dirname(__file__), "prompts", filename)
        with open(filepath, "r") as file:
            return file.read()

    def generate_reasoning(self, puzzle_input: List[str], guesses: Dict) -> str:
        """Analyze puzzle input and generate reasoning for the next guess.

        Args:
            puzzle_input (List[str]): words from the puzzle
            guesses (Dict): previous guesses and their outcomes

        Returns:
            str: reasoning for the next guess
        """
        user_content = self.reasoning_user_prompt.format(
            puzzle_input=puzzle_input, guesses=guesses
        )
        completion = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.reasoning_sys_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return completion.choices[0].message.content

    def generate_parsed_answer(self, reasoning: str) -> LLMAnswer:
        """Generate a parsed guess from the reasoning.

        Args:
            reasoning (str): AI-generated reasoning for the next guess.

        Returns:
            LLMAnswer: parsed guess
        """
        user_content = f"LONG_REASONING: {reasoning}\nOUTPUT:"
        completion = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": self.parsing_sys_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=LLMAnswer,
        )
        return completion.choices[0].message.parsed

    def generate_guess(self, puzzle_input: List[str], guesses: Dict) -> LLMAnswer:
        """Generate a guess based on the puzzle input and previous guesses using Chain-of-Thought.

        Args:
            puzzle_input (List[str]): words from the puzzle
            guesses (Dict): previous guesses and their outcomes

        Returns:
            LLMAnswer: parsed guess
        """
        reasoning = self.generate_reasoning(puzzle_input, guesses)
        return self.generate_parsed_answer(reasoning)


if __name__ == "__main__":
    text_generator = TextGenerator()
    puzzle_input = [
        "WHIRL",
        "DRAW",
        "NAVY",
        "LIVER",
        "CAR",
        "KIDNEY",
        "HOOK",
        "DRIVE",
        "PINTO",
        "PULL",
        "NEUTRAL",
        "DEAD",
        "LOW",
        "MUNG",
        "GRAB",
        "REVERSE",
    ]
    guesses = {
        1: {
            "last_guess": ["MUNG", "PINTO", "KIDNEY", "NAVY"],
            "correct": True,
            "one_away": False,
        },
        2: {
            "last_guess": ["WHIRL", "DRAW", "PULL", "GRAB"],
            "correct": False,
            "one_away": False,
        },
    }
    # reasoning = text_generator.generate_reasoning(puzzle_input, guesses)
    # print(reasoning)
    guess = text_generator.generate_guess(puzzle_input, guesses)
    print(guess)
