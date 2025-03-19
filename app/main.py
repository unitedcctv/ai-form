from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import logging
from validation.factory import validate_user_input
from db.sqlite_db import fetch_session_from_db, upsert_session_to_db, RegistrationState
from graph.registration_graph import RegistrationGraphManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registration_questions = {
    "ask_email": "What is your email address?",
    "ask_name": "What is your full name?",
    "ask_address": "What is your address?",
    "ask_phone": "What is your phone number?",
    "ask_username": "Choose a username.",
    "ask_password": "Choose a strong password.",
}

registration_graph = RegistrationGraphManager("registration", registration_questions)
registration_graph.generate_mermaid_diagram()


@app.post("/start_registration")
def start_registration():
    session_id = str(uuid.uuid4())

    # Our initial state
    initial_state: RegistrationState = {
        "collected_data": {},
        "current_question": "",
        "current_node": "ask_email",
        "session_id": session_id,
    }

    # Start the graph & get the first node
    execution = registration_graph.compiled_graph.stream(initial_state)
    try:
        steps = list(execution)  # Fully consume the generator
        if not steps:
            raise RuntimeError("Generator exited before producing any states.")
        first_step = steps[0]
    except GeneratorExit:
        raise RuntimeError("GeneratorExit detected before first transition!")

    # Extract state from the first node
    first_node_key = list(first_step.keys())[0]
    first_node_state = first_step[first_node_key]
    first_node_state["current_node"] = first_node_key
    first_node_state["session_id"] = session_id

    # Save to session
    upsert_session_to_db(
        session_id,
        first_node_state["collected_data"],
        first_node_state["current_question"],
        first_node_state["current_node"],
    )

    return {
        "session_id": session_id,
        "message": first_node_state["current_question"],
        "state": first_node_state,
    }


@app.post("/submit_response")
def submit_response(response: dict):
    session_id = response.get("session_id")
    if not session_id:
        return {"error": "Missing session_id"}

    current_state = fetch_session_from_db(session_id)
    if not current_state:
        return {"error": "Session not found. Please restart registration."}

    skip_steps = response.get("skip_steps", [])
    for node_key in skip_steps:
        logging.info(f"skip_{node_key}")
        current_state[f"skip_{node_key}"] = True

    user_answer = response.get("answer")
    if user_answer is None:
        return {"error": "Missing answer"}
    user_answer = str(user_answer)
    current_question = current_state["current_question"]
    current_node = current_state["current_node"]

    # Use dspy to validate the answer with fallbacks
    if current_node in skip_steps:
        # If user is skipping this question, create a dummy validation result
        validation_result = {
            "status": "valid",
            "feedback": "Skipped this question",
            "formatted_answer": "-",
        }
        logging.info(f"Skipping validation for {current_node}")
    else:
        # Normal validation
        validation_result = validate_user_input(current_question, user_answer)

        # If there's a clarify/error
        if validation_result["status"] in ("clarify", "error"):
            return {
                "next_question": current_question,
                "validation_feedback": validation_result["feedback"],
                "user_answer": user_answer,
                "formatted_answer": validation_result["formatted_answer"],
                "state": current_state,
            }

    current_state["collected_data"][current_state["current_node"]] = validation_result[
        "formatted_answer"
    ]

    if "current_node" not in current_state or not current_state.get("collected_data"):
        return {"error": "Corrupt session state, restart registration."}

    next_step = registration_graph.resume_and_step_graph(current_state)

    if not next_step or next_step == {}:
        # Means we've hit the END node or no more steps
        return {
            "message": "Registration complete!",
            "validation_feedback": validation_result["feedback"],
            "user_answer": user_answer,
            "formatted_answer": validation_result["formatted_answer"],
            "state": current_state,
            "summary": current_state["collected_data"],
        }

    next_node_key = list(next_step.keys())[0]
    next_node_state = next_step[next_node_key]
    next_node_state["current_node"] = next_node_key

    upsert_session_to_db(
        session_id,
        current_state["collected_data"],
        next_node_state["current_question"],
        next_node_state["current_node"],
    )

    return {
        "next_question": next_node_state["current_question"],
        "validation_feedback": validation_result["feedback"],
        "user_answer": user_answer,
        "formatted_answer": validation_result["formatted_answer"],
        "state": next_node_state,
        "summary": current_state["collected_data"],
    }


@app.post("/edit_field")
def edit_field(request: dict):
    session_id = request.get("session_id")
    if not session_id:
        return {"error": "Missing session_id"}

    field_to_edit = request.get("field_to_edit")
    new_value = request.get("new_value")

    current_state = fetch_session_from_db(session_id)
    if not current_state:
        logging.error("Session not found. Please restart registration.")
        return {"error": "Session not found. Please restart registration."}

    if not isinstance(field_to_edit, str):
        return {"error": "Invalid field_to_edit: must be a string"}
    question_text = registration_questions.get(field_to_edit)
    if not question_text:
        logging.error(f"Invalid field_to_edit: {field_to_edit}")
        return {"error": f"Invalid field_to_edit: {field_to_edit}"}

    validation_result = validate_user_input(
        question=question_text, user_answer=str(new_value)
    )

    if validation_result["status"] == "clarify":
        return {
            "message": "Needs clarification",
            "validation_feedback": validation_result["feedback"],
            "raw_answer": new_value,
            "formatted_answer": validation_result["formatted_answer"],
        }

    current_state["collected_data"][field_to_edit] = validation_result[
        "formatted_answer"
    ]

    upsert_session_to_db(
        session_id,
        current_state["collected_data"],
        current_state["current_question"],
        current_state["current_node"],
    )

    return {
        "message": "Field updated successfully!",
        "validation_feedback": validation_result["feedback"],
        "raw_answer": new_value,
        "formatted_answer": validation_result["formatted_answer"],
        "summary": current_state["collected_data"],
    }
