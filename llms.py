import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class LLMGuess(BaseModel):
    words: List[str]
    reasoning: str


class TextGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.reasoning_sys_prompt = self.load_prompt("reasoning_sys_prompt.txt")
        self.reasoning_user_prompt = self.load_prompt("reasoning_user_prompt.txt")
        self.parsing_sys_prompt = self.load_prompt("parsing_sys_prompt.txt")

    @staticmethod
    def load_prompt(filename):
        filepath = os.path.join(os.path.dirname(__file__), "prompts", filename)
        with open(filepath, "r") as file:
            return file.read()

    def generate_reasoning(self, puzzle_input: List[str], guesses: Dict) -> str:
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

    def generate_parsed_answer(self, reasoning: str) -> LLMGuess:
        user_content = f"LONG_REASONING: {reasoning}\nOUTPUT:"
        completion = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": self.parsing_sys_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=LLMGuess,
        )
        return completion.choices[0].message.parsed

    def generate_guess(self, puzzle_input: List[str], guesses: Dict) -> LLMGuess:
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
