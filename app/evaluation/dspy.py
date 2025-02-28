import mlflow
from typing import List, Dict

# Import your custom DSPyValidator
from validation.dspy_validator import DSPyValidator

# Example test dataset
# Each sample has: question, user_answer, expected_status, expected_formatted_answer
test_data = [
    {
        "question": "What is your email address?",
        "user_answer": "paul@gmail.com",
        "expected_status": "valid",
        "expected_formatted": "paul@gmail.com",
    }
    # Add more test samples...
]

def run_evaluation():
    """
    Evaluates the DSPyValidator on a small dataset,
    logging metrics to MLflow.
    """
    # Initialize your validator
    validator = DSPyValidator()

    # Start a new MLflow run for the entire evaluation
    with mlflow.start_run(run_name="dspy_evaluation"):
        total_samples = len(test_data)
        correct_status = 0
        correct_format = 0

        for i, sample in enumerate(test_data):
            question = sample["question"]
            user_answer = sample["user_answer"]
            expected_status = sample["expected_status"]
            expected_formatted = sample["expected_formatted"]

            # Use the DSPyValidator to validate
            result = validator.validate(question, user_answer)
            predicted_status = result["status"]
            predicted_formatted = result["formatted_answer"]

            # Compare predictions with expected
            status_is_correct = (predicted_status == expected_status)
            format_is_correct = (predicted_formatted == expected_formatted)

            if status_is_correct:
                correct_status += 1
            if format_is_correct:
                correct_format += 1

            # Log each sample's details as a nested run or as a param
            with mlflow.start_run(
                nested=True, 
                run_name=f"sample_{i}", 
                description=f"Evaluation of sample #{i}"
            ):
                mlflow.log_param("question", question)
                mlflow.log_param("user_answer", user_answer)
                mlflow.log_param("predicted_status", predicted_status)
                mlflow.log_param("expected_status", expected_status)
                mlflow.log_param("predicted_formatted", predicted_formatted)
                mlflow.log_param("expected_formatted", expected_formatted)

                mlflow.log_metric("status_correct", 1 if status_is_correct else 0)
                mlflow.log_metric("format_correct", 1 if format_is_correct else 0)

        # After all samples, log aggregate metrics
        mlflow.log_metric("overall_status_accuracy", correct_status / total_samples)
        mlflow.log_metric("overall_format_accuracy", correct_format / total_samples)

        print(f"Evaluation complete on {total_samples} samples.")
        print(f"Status accuracy: {correct_status / total_samples:.2%}")
        print(f"Format accuracy: {correct_format / total_samples:.2%}")


if __name__ == "__main__":
    run_evaluation()
