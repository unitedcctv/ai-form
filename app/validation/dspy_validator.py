import guardrails as gd
import dspy
from validation.base_validator import BaseValidator
from pydantic import ValidationError
from validation.validated_response import ValidatedLLMResponse
from typing import Literal
import logging
import json
import mlflow
from helpers.config import OPENAI_API_KEY, MLFLOW_ENABLED, MLFLOW_EXPERIMENT_NAME

dspy.settings.configure(lm=dspy.LM(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY))

if MLFLOW_ENABLED:
    mlflow.dspy.autolog()

guard = gd.Guard.for_pydantic(ValidatedLLMResponse)

# Define DSPy Signature
class ValidateUserAnswer(dspy.Signature):
    """Validates and formats user responses. Should return 'valid', 'clarify', or 'error'."""

    question: str = dspy.InputField()
    user_answer: str = dspy.InputField()

    status: Literal["valid", "clarify", "error"] = dspy.OutputField(
        desc="Validation status: 'valid', 'clarify', or 'error'. Return 'valid' if the input contains all necessary information."
    )
    feedback: str = dspy.OutputField(
        desc="Explanation if response is incorrect or needs details."
    )
    formatted_answer: str = dspy.OutputField(
        desc="Return the response with proper formatting. Example: "
        "- Emails: Lowercase (e.g., 'John@gmail.com' → 'john@gmail.com'). "
        "- Names: Capitalize first & last name (e.g., 'john doe' → 'John Doe'). "
        "- Addresses: Capitalize & ensure complete info (e.g., '123 main st,newyork,ny' → '123 Main St, New York, NY 10001'). "
        "- Phone numbers: Format as (XXX) XXX-XXXX (e.g., '1234567890' → '(123) 456-7890'). "
        "An address must include: street number, street name, city, state, and ZIP code. "
        "Reject responses that do not meet this format with status='clarify'."
        "If the response cannot be formatted, return the original answer."
    )


run_llm_validation = dspy.Predict(ValidateUserAnswer)


class DSPyValidator(BaseValidator):
    """Uses DSPy with Guardrails AI for structured validation."""

    def validate(self, question: str, user_answer: str):
        """Validates user response, applies guardrails, and logs to MLflow."""
        try:
            raw_result = run_llm_validation(question=question, user_answer=user_answer)
            structured_validation_output = guard.parse(json.dumps(raw_result.toDict()))
            validated_dict = dict(structured_validation_output.validated_output)

            if MLFLOW_ENABLED:
                mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
                with mlflow.start_run(nested=True):
                    mlflow.log_param("validation_engine", "DSPy + Guardrails AI")
                    mlflow.log_param("question", question)
                    mlflow.log_param("input_answer", user_answer)
                    mlflow.log_param("status", validated_dict["status"])
                    mlflow.log_param(
                        "formatted_answer", validated_dict["formatted_answer"]
                    )

            return {
                "status": validated_dict["status"],
                "feedback": validated_dict["feedback"],
                "formatted_answer": validated_dict["formatted_answer"],
            }

        except ValidationError as ve:
            logging.error(f"Validation error: {str(ve)}")
            return {
                "status": "error",
                "feedback": "Output validation failed.",
                "formatted_answer": user_answer,
            }
        except Exception as e:
            logging.error(f"Validation error: {str(e)}")
            return {
                "status": "error",
                "feedback": "An error occurred during validation.",
                "formatted_answer": user_answer,
            }
