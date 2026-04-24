import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Load env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API key not found.")
    st.stop()

client = genai.Client(api_key=api_key)


def get_quiz_questions(topic, difficulty, count=5):
    models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]

    prompt = f"""
    Generate {count} multiple choice questions.

    Topic: {topic}
    Difficulty: {difficulty}

    Rules:
    - Exactly 4 options (A, B, C, D)
    - Only ONE correct answer
    - Clear and concise
    - No duplicates

    Return ONLY JSON.
    """

    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "question": {"type": "STRING"},
                "options": {
                    "type": "OBJECT",
                    "properties": {
                        "A": {"type": "STRING"},
                        "B": {"type": "STRING"},
                        "C": {"type": "STRING"},
                        "D": {"type": "STRING"},
                    },
                },
                "answer": {"type": "STRING"},
            },
            "required": ["question", "options", "answer"]
        },
    }

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )
            return json.loads(response.text)

        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                continue

    # fallback
    return [{
        "question": "What is the capital of France?",
        "options": {
            "A": "Berlin",
            "B": "Madrid",
            "C": "Paris",
            "D": "Rome"
        },
        "answer": "C"
    }]


# ---------------- UI ----------------

st.set_page_config(page_title="AI Quiz App", layout="centered")
st.title("🧠 AI Quiz App")

# Session state init
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current" not in st.session_state:
    st.session_state.current = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False
if "selected" not in st.session_state:
    st.session_state.selected = None


# ----------- START SCREEN -----------
if not st.session_state.questions:

    topic = st.text_input("Enter Topic")
    difficulty = st.selectbox("Select Difficulty", ["easy", "medium", "hard"])

    if st.button("Start Quiz"):
        if topic:
            with st.spinner("Generating questions..."):
                st.session_state.questions = get_quiz_questions(topic, difficulty)
                st.session_state.current = 0
                st.session_state.score = 0
                st.session_state.answered = False
        else:
            st.warning("Enter a topic")

# ----------- QUIZ SCREEN -----------
else:
    questions = st.session_state.questions
    idx = st.session_state.current

    if idx < len(questions):
        q = questions[idx]

        st.subheader(f"Question {idx + 1}")
        st.write(q["question"])

        options = q["options"]

        st.session_state.selected = st.radio(
            "Choose an option:",
            list(options.keys()),
            format_func=lambda x: f"{x}) {options[x]}"
        )

        # Submit button
        if not st.session_state.answered:
            if st.button("Submit"):
                st.session_state.answered = True

                if st.session_state.selected == q["answer"]:
                    st.session_state.score += 1

        # Show result (PERSISTENT)
        if st.session_state.answered:
            if st.session_state.selected == q["answer"]:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong! Correct answer: {q['answer']}")

            # Next button
            if st.button("Next Question"):
                st.session_state.current += 1
                st.session_state.answered = False
                st.session_state.selected = None
                st.rerun()

    else:
        # ----------- RESULT SCREEN -----------
        st.subheader("🎉 Quiz Completed!")
        st.write(f"Final Score: {st.session_state.score}/{len(questions)}")

        if st.button("Restart"):
            st.session_state.questions = []
            st.session_state.current = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.selected = None
            st.rerun()