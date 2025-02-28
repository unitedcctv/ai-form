import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";
import {
    Box,
    Typography,
    Button,
    IconButton,
    TextField,
    Divider,
    Container,
    Paper,
} from "@mui/material";
import { useTheme, darken, lighten } from "@mui/material/styles";
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from "@mui/icons-material/Close";
import CheckIcon from '@mui/icons-material/Check';
import EditIcon from '@mui/icons-material/Edit';

interface RegistrationState {
    collected_data: Record<string, string>;
    current_question: string;
}

interface ResponseData {
    question: string;
    answer: string;
    formatted_answer: string;
    validation: string;
    validation_error: boolean;
}

function RegistrationForm() {
    const [state, setState] = useState<RegistrationState | null>(null);
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [responses, setResponses] = useState<ResponseData[]>([]);
    const [validationFeedback, setValidationFeedback] = useState<string | null>(null);
    const [registrationComplete, setRegistrationComplete] = useState<boolean>(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [skipSteps, setSkipSteps] = useState<string[]>([]);

    // For final review
    const [finalSummary, setFinalSummary] = useState<Record<string, string> | null>(null);

    // For editing a single field
    const [isEditingField, setIsEditingField] = useState<string | null>(null);
    const [editValue, setEditValue] = useState<string>("");
    const chatBoxRef = useRef<HTMLDivElement | null>(null);
    const editBoxRef = useRef<HTMLDivElement | null>(null);
    const inputRef = useRef<HTMLInputElement | null>(null);
    const hasStarted = useRef(false);
    const [isLoading, setIsLoading] = useState(false);
    const theme = useTheme();

    useEffect(() => {
        // Scroll to the bottom whenever responses change
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [responses]);

    useEffect(() => {
        // Scroll to the bottom whenever responses change
        if (editBoxRef.current) {
            editBoxRef.current.scrollTop = editBoxRef.current.scrollHeight;
        }
    }, [responses]);

    useEffect(() => {
        if (!hasStarted.current) {
            startRegistration();
            hasStarted.current = true;
        }
    }, []);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, [question]);

    async function startRegistration() {
        try {
            const res = await axios.post("http://localhost:8000/start_registration");
            setSessionId(res.data.session_id);
            setQuestion(res.data.message);
            setState(res.data.state);
        } catch (error) {
            console.error("Error starting registration:", error);
        }
    }

    async function submitResponse() {
        if (!sessionId || !question || !answer || !state) return;

        let newSkipSteps = [...skipSteps];
        const questionToNodeMap: Record<string, string> = {
            "What is your address?": "ask_address",
            "What is your phone number?": "ask_phone",
        };

        if (answer.trim().toLowerCase() === "skip") {
            const nodeKey = questionToNodeMap[question];
            if (nodeKey && !newSkipSteps.includes(nodeKey)) {
                newSkipSteps.push(nodeKey);
            }
        }

        try {
            setIsLoading(true);

            const res = await axios.post("http://localhost:8000/submit_response", {
                session_id: sessionId,
                answer,
                skip_steps: newSkipSteps,
            });
            
            setSkipSteps(newSkipSteps);

            // Check if complete
            if (res.data.message === "Registration complete!") {
                setIsLoading(false); 
                setRegistrationComplete(true);
                // If the backend returns summary, store it
                if (res.data.summary) {
                    setFinalSummary(res.data.summary);
                }
                return;
            }

            setResponses((prev) => [
                ...prev,
                {
                    question,
                    answer: res.data.user_answer,
                    formatted_answer: res.data.formatted_answer,
                    validation: res.data.validation_feedback,
                    validation_error: (res.data.next_question === question),
                },
            ]);

            // If there's a clarification needed
            if (res.data.next_question === question) {
                setIsLoading(false); 
                setValidationFeedback(res.data.validation_feedback);
                return;
            }

            setIsLoading(false); 
            setValidationFeedback(null);
            setQuestion(res.data.next_question || "");   // only now update the question
            setAnswer("");
            setState(res.data.state);
        
            // focus the input after question changes
            if (inputRef.current) {
                inputRef.current.focus();
            }

        } catch (error) {
            console.error("Error submitting response:", error);
            setIsLoading(false);
        }
    }

    async function handleSkipClick() {
        if (!sessionId || !question || !state) return;

        // Make a copy of the current skipSteps array
        const newSkipSteps = [...skipSteps];

        // Map the current question text to a node key
        const questionToNodeMap: Record<string, string> = {
            "What is your address?": "ask_address",
            "What is your phone number?": "ask_phone",
        };

        // Figure out which node is being skipped
        const nodeKey = questionToNodeMap[question];
        if (nodeKey && !newSkipSteps.includes(nodeKey)) {
            newSkipSteps.push(nodeKey);
        }

        // Update local skipSteps state so future calls know about it
        setSkipSteps(newSkipSteps);

        try {
            // Send a POST request to skip the node
            // We pass skip_steps + an empty answer (or "skip")
            const res = await axios.post("http://localhost:8000/submit_response", {
                session_id: sessionId,
                skip_steps: newSkipSteps,
                answer: "", // or "skip" if you prefer
            });

            // Check if registration is complete
            if (res.data.message === "Registration complete!") {
                setRegistrationComplete(true);
                if (res.data.summary) {
                    setFinalSummary(res.data.summary);
                }
                return;
            }

            // Otherwise, store the "skipped" response in your chat
            setResponses((prev) => [
                ...prev,
                {
                    question,
                    answer: "-",
                    formatted_answer: res.data.formatted_answer,
                    validation: res.data.validation_feedback,
                    validation_error: (res.data.next_question === question),
                },
            ]);

            // Refocus the input
            if (inputRef.current) {
                inputRef.current.focus();
            }

            // If there's a clarification needed
            if (res.data.next_question === question) {
                setValidationFeedback(res.data.validation_feedback);
                return;
            }

            // Otherwise, proceed to the next question
            setValidationFeedback(null);
            setQuestion(res.data.next_question || "");
            setAnswer("");
            setState(res.data.state);

        } catch (error) {
            console.error("Error skipping step:", error);
        }
    }

    function handleEditClick(fieldKey: string) {
        if (!finalSummary) return;
        setIsEditingField(fieldKey);
        setEditValue(finalSummary[fieldKey] || "");
    }

    async function handleSaveEdit() {
        if (!sessionId || !isEditingField) return;

        try {
            const res = await axios.post("http://localhost:8000/edit_field", {
                session_id: sessionId,
                field_to_edit: isEditingField,
                new_value: editValue,
            });

            if (res.data.summary) {
                setFinalSummary(res.data.summary);
            }
        } catch (error) {
            console.error("Failed to edit field:", error);
        } finally {
            setIsEditingField(null);
            setEditValue(""); // Clear input after submission
        }
    }

    function handleCancelEdit() {
        setIsEditingField(null);
        setEditValue("");
    }

    // Simple label for each field key
    function getLabel(key: string): string {
        switch (key) {
            case "ask_email": return "Email Address";
            case "ask_name": return "Full Name";
            case "ask_address": return "Address";
            case "ask_phone": return "Phone Number";
            case "ask_username": return "Username";
            case "ask_password": return "Password";
            default: return key;
        }
    }

    return (
        <Container fixed
            maxWidth="sm"
            sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                border: 1,
                borderColor: "divider",
                borderRadius: 2,
                padding: 3,
                boxShadow: 3,
                backgroundColor: "background.paper",
                height: "80vh", // Limits height to 90% of the viewport
                overflowY: "auto", // Enables scrolling when needed
            }}
        >
            <Typography variant="h5" color="primary" gutterBottom>
                <strong>Create an Account</strong>
            </Typography>
            <Divider sx={{ width: "100%", mb: 2 }} />

            {/* If registration not complete, show standard Q/A flow */}
            {!registrationComplete && (
                <>
                    <Box
                        ref={chatBoxRef}
                        sx={{
                            flex: 1, // Takes up available space
                            minHeight: 300,
                            minWidth: 400,
                            maxWidth: 400,
                            padding: 2,
                            backgroundColor: "background.paper",
                            borderRadius: 2,
                            overflowY: "auto",
                            textAlign: "left",
                            border: "1px solid",
                            borderColor: "divider",
                            boxShadow: 3,
                        }}
                    >
                        {responses.map((res, index) => {
                            const hasValidationError = res.validation_error;

                            if (res.answer === "-" && hasValidationError) {
                                return null; // No rendering for invalid skip
                            }

                            return (
                                <Box
                                    key={index}
                                    sx={{
                                        paddingBottom: 2,
                                        paddingLeft: 2,
                                        paddingRight: 4,
                                        borderRadius: 2,
                                        width: 400,
                                        flexShrink: 0,
                                        display: "flex",
                                        justifyContent: "flex-end"
                                    }}
                                >
                                    <Paper elevation={2} square={false} sx={{
                                        p: 0,
                                        transition: "all 0.3s ease-in-out", // Duration & easing
                                        "&:hover": {
                                            transform: "scale(1.05)",        // Slight zoom on hover
                                        },
                                        overflow: "hidden",
                                        width: "fit-content",
                                    }}>
                                        <Box
                                            sx={{
                                                backgroundColor: lighten(theme.palette.background.paper, 0.2),
                                                // e.g., 10% darker than default paper background
                                                color: theme.palette.getContrastText(
                                                    lighten(theme.palette.background.paper, 0.2)
                                                ),
                                                p: 1,
                                            }}
                                        >
                                            <Typography variant="body1">
                                                {res.question}
                                            </Typography>
                                        </Box>

                                        <Box
                                            sx={{
                                                p: 1,
                                            }}
                                        >
                                            {/* 1️⃣ If the answer is "Skipped", show a green check + "Skipped" text */}
                                            {res.answer === "-" && !hasValidationError ? (
                                                <Typography
                                                    variant="body2"
                                                    sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                                                >
                                                    <CheckIcon fontSize="small" sx={{ color: "success.main" }} />
                                                    Skipped
                                                </Typography>
                                            ) : (
                                                /* 2️⃣ Otherwise, the normal logic for validated or error responses */
                                                <>
                                                    {res.answer && (
                                                        <Typography
                                                            variant="body2"
                                                            sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                                                        >
                                                            {hasValidationError ? (
                                                                <CloseIcon fontSize="small" sx={{ color: "error.main" }} />
                                                            ) : (
                                                                <CheckIcon fontSize="small" sx={{ color: "success.main", transition: "opacity 0.5s ease-in-out" }} />
                                                            )}
                                                            {res.answer}
                                                        </Typography>
                                                    )}

                                                    {!hasValidationError && res.formatted_answer && (
                                                        <Typography
                                                            variant="body2"
                                                            sx={{ display: "flex", alignItems: "center", gap: 0.5, ml: 3, mt: 0.5 }}
                                                        >
                                                            <CheckCircleIcon fontSize="small" sx={{ color: "success.main" }} />
                                                            {res.formatted_answer}
                                                        </Typography>
                                                    )}
                                                </>
                                            )}
                                        </Box>
                                    </Paper>
                                </Box>
                            );
                        })}
                        {isLoading && (
                            <Box
                                sx={{
                                    paddingBottom: 2,
                                    paddingLeft: 2,
                                    borderRadius: 2,
                                    width: 400,
                                    flexShrink: 0,
                                }}
                            >
                                <Paper
                                    elevation={2}
                                    square={false}
                                    sx={{
                                        p: 1,
                                        width: "fit-content",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        animation: "fadeInOut 1.5s infinite",
                                    }}
                                >
                                    <Typography variant="body2" sx={{ fontStyle: "italic" }}>
                                        <span className="dots">...</span>
                                    </Typography>
                                </Paper>
                            </Box>
                        )}

                        {validationFeedback && (
                            <Typography
                                variant="body2"
                                sx={{ color: "error.main", fontWeight: "bold" }}
                            >
                                <strong>{validationFeedback}</strong>
                            </Typography>
                        )}

                        {/* Show next question */}
                        {question && (
                            <Typography variant="h6" sx={{ mt: 2, color: "primary.main" }}>
                                {question}
                            </Typography>
                        )}
                    </Box>

                    {/* Input + Send button */}
                    <Box sx={{ mt: 2, display: "flex", gap: 2, width: "100%" }}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            type="text"
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) { // Prevent Shift+Enter from submitting
                                    e.preventDefault(); // Prevent new line in multiline input
                                    submitResponse();
                                }
                            }}
                            label="Type your response..."
                            multiline
                            maxRows={4}
                            inputRef={inputRef}
                        />
                        <Button variant="contained" onClick={submitResponse}>
                            Send
                        </Button>
                        <Button variant="outlined" onClick={handleSkipClick}>
                            Skip
                        </Button>
                    </Box>
                </>
            )}

            {/* If registration complete, show final summary & optional edit */}
            {registrationComplete && finalSummary && (
                <Box sx={{
                    mt: 0, width: 400,
                    flexShrink: 0
                }} ref={editBoxRef}>
                    <Typography variant="overline" gutterBottom sx={{ mt: 0, textAlign: "left", display: 'block' }}>
                        <strong>Review Your Information</strong>
                    </Typography>

                    {Object.entries(finalSummary).map(([key, val]) => (
                        <Box key={key} sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                            <Typography sx={{ mr: 2 }}>
                                {val}
                            </Typography>
                            <IconButton
                                aria-label="edit"
                                color="primary"
                                onClick={() => handleEditClick(key)}
                                sx={{ ml: "auto" }}
                            >
                                <EditIcon />
                            </IconButton>
                        </Box>
                    ))}

                    {/* Edit form if user clicks Edit */}
                    {isEditingField && (
                        <Box sx={{ mt: 2 }}>
                            <Typography variant="overline">
                                <strong>Editing:</strong> {getLabel(isEditingField)}
                            </Typography>
                            <TextField
                                fullWidth
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                sx={{ mb: 2, mt: 1 }}
                            />
                            <Box sx={{ display: "flex", gap: 2 }}>
                                <Button variant="contained" onClick={handleSaveEdit}>
                                    Save
                                </Button>
                                <Button variant="text" onClick={handleCancelEdit}>
                                    Cancel
                                </Button>
                            </Box>
                        </Box>
                    )}

                    <Box sx={{ mt: 2 }}>
                        <Button
                            variant="contained"
                            color="success"
                            onClick={() => alert("All set!")}
                        >
                            Confirm & Finish
                        </Button>
                    </Box>
                </Box>
            )}
        </Container>
    );
}

export default RegistrationForm;
