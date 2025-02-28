from abc import ABC, abstractmethod
from typing import Dict

class BaseValidator(ABC):
    """Abstract base class for validation strategies."""

    @abstractmethod
    def validate(self, question: str, user_answer: str) -> Dict[str, str]:
        """Validate the user input and return a structured response."""
        pass