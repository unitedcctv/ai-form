from pydantic import BaseModel, Field, field_validator
import re

class ValidatedLLMResponse(BaseModel):
    """Validates & formats user responses using Guardrails AI & Pydantic."""

    status: str = Field(..., pattern="^(valid|clarify|error)$")
    feedback: str
    formatted_answer: str

    @field_validator("formatted_answer", mode="before")
    @classmethod
    def validate_and_format(cls, value, values):
        """Formats & validates responses based on the question type."""

        if values.get("status") == "error":
            return value  # Skip validation for errors

        question = values.get("question", "").lower()

        # Validate Email Format
        if "email" in question:
            return cls.validate_email(value)

        # Validate Name Format (Capitalize First & Last Name)
        if "name" in question:
            return cls.validate_name(value)

        # Validate Phone Number (Format: (XXX) XXX-XXXX)
        if "phone" in question:
            return cls.validate_phone(value)

        # Validate Address (Must contain street, city, state, ZIP)
        if "address" in question:
            return cls.validate_address(value)

        return value  # Default: Return unchanged

    @staticmethod
    def validate_email(email: str) -> str:
        """Validates email format and converts to lowercase."""
        return (
            email.lower() if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) else "clarify"
        )

    @staticmethod
    def validate_name(name: str) -> str:
        """Capitalizes first & last name."""
        return " ".join(word.capitalize() for word in name.split())

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validates & formats phone numbers as (XXX) XXX-XXXX."""
        digits = re.sub(r"\D", "", phone)  # Remove non-numeric characters
        return (
            f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            if len(digits) == 10
            else "clarify"
        )

    @staticmethod
    def validate_address(address: str) -> str:
        """Ensures address includes street, city, state, ZIP & formats correctly."""
        components = address.split(",")
        if len(components) < 3:
            return "clarify"  # Address is incomplete

        formatted_address = ", ".join(comp.strip().title() for comp in components)
        return (
            formatted_address if re.search(r"\d{5}", formatted_address) else "clarify"
        )