import os
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

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
    - Keep questions clear and concise
    - No duplicate questions

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
            print(f"--- Requesting from {model_name}... ---")
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
                print(f"⚠️ {model_name} is busy. Trying fallback...")
                continue
            else:
                print(f"❌ Error with {model_name}: {e}")
                continue

    # ✅ FIX 1: fallback instead of empty list
    print("⚠️ Using fallback question.")
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


def run_quiz():
    print("="*40)
    print("      GEN-AI QUIZ MASTER")
    print("="*40)

    total_score = 0
    total_questions = 0

    while True:
        print("\n[Main Menu]")
        topic = input("Enter Topic (or 'q' to quit): ").strip()

        if topic.lower() == 'q':
            print("\nFinal Overall Score:", f"{total_score}/{total_questions}")
            print("Thanks for playing! Exiting...")
            break

        difficulty = input("Enter Difficulty (easy/medium/hard): ").strip().lower()
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'

        print(f"\nGenerating '{topic}' quiz. Please wait...")
        questions = get_quiz_questions(topic, difficulty)

        score = 0

        for i, q in enumerate(questions):
            print(f"\nQuestion {i+1}: {q['question']}")
            for key, val in q["options"].items():
                print(f"  {key}) {val}")

            # ✅ FIX 3: input validation
            while True:
                ans = input("Your answer (A/B/C/D or Q to quit): ").strip().upper()
                if ans in ["A", "B", "C", "D", "Q"]:
                    break
                print("Invalid input. Enter A, B, C, D or Q.")

            if ans == 'Q':
                print("Skipping remaining questions...")
                break

            if ans == q["answer"]:
                print("✅ Correct!")
                score += 1
            else:
                print(f"❌ Wrong! Correct answer: {q['answer']}")

        print(f"\n--- Round Score: {score}/{len(questions)} ---")

        # ✅ FIX 6: overall tracking
        total_score += score
        total_questions += len(questions)

        print(f"Overall Score So Far: {total_score}/{total_questions}")

        choice = input("\nTry another topic? (y/n): ").strip().lower()
        if choice != 'y':
            print("\nFinal Overall Score:", f"{total_score}/{total_questions}")
            print("Goodbye!")
            break


if __name__ == "__main__":
    run_quiz()