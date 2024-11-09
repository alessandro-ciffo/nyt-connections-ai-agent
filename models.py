from typing import Dict, List
from pydantic import BaseModel


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


class LLMAnswer(BaseModel):
    words: List[str]
    reasoning: str
