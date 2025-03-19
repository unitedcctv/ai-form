import openai
import guardrails as gd
import json
from typing import Dict
from validation.base_validator import BaseValidator
from validation.validated_response import ValidatedLLMResponse
from helpers.config import OPENAI_API_KEY, MLFLOW_ENABLED, MLFLOW_EXPERIMENT_NAME
import mlflow

if MLFLOW_ENABLED:
    mlflow.openai.autolog()

guard = gd.Guard.for_pydantic(ValidatedLLMResponse)


class ChatGPTValidator(BaseValidator):
    """ChatGPT-based implementation of the validation strategy."""

    def validate(self, question: str, user_answer: str) -> Dict[str, str]:
        """Uses OpenAI ChatGPT to validate responses."""
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that validates user responses. "
                        "You must respond in JSON format with a clear validation status. "
                        "If the response is valid, return: {'status': 'valid', 'feedback': '<feedback message>', 'formatted_answer': '<formatted response>'}. "
                        "If the response needs clarification, return: {'status': 'clarify', 'feedback': '<clarification message>', 'formatted_answer': '<original response>'}."
                        "Ensure proper formatting: lowercase emails, capitalized names, standardized phone numbers and addresses."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nUser Answer: {user_answer}\nValidate the answer.",
                },
            ],
            response_format={"type": "json_object"},
        )

        try:
            validation_str = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            validation_result = json.loads(validation_str)
            print(validation_result)

            # Apply Guardrails AI
            validated_result = guard.parse(json.dumps(validation_result))
            validated_dict = validated_result.validated_output
            print(validated_dict)
        except (json.JSONDecodeError, KeyError):
            validation_result = {
                "status": "error",
                "feedback": "Error processing validation response.",
                "formatted_answer": user_answer,
            }

        if MLFLOW_ENABLED:
            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
            with mlflow.start_run(nested=True):
                mlflow.log_param("validation_engine", "ChatGPT")
                mlflow.log_param("question", question)
                mlflow.log_param("input_answer", user_answer)
                mlflow.log_param("status", validated_dict.get("status", "error"))
                mlflow.log_param(
                    "feedback", validated_dict.get("feedback", "No feedback")
                )
                mlflow.log_param(
                    "formatted_answer",
                    validated_dict.get("formatted_answer", user_answer),
                )

        return validated_dict
