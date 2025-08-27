import os
from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY) #type: ignore

MODEL_NAME = "models/gemini-2.0-flash-lite"

def norm_choice(x, choices):
    x = (x or "").strip().lower()
    for c in choices:
        if x == c or x in c:  # accepts substrings like "med" -> "medium"
            return c
    return choices[0]

def map_difficulty(toughness, institute):

    base = {"easy":"low", "medium":"moderate", "hard":"high"}[toughness]
    level_bias = {"school":"foundational", "college":"intermediate", "postgrad":"advanced"}[institute]
    return f"{base} difficulty with {level_bias} cognitive demand"

def make_prompt(syllabus_text, mark1, mark5, mark10, toughness, institute):
    diff_desc = map_difficulty(toughness, institute)
    return f"""
Task: Create an answerable question paper aligned with India's NEP 2020 focusing on competency-based, formative assessment and balanced Bloom's levels.

Assessment profile:
- Intended institute level: {institute}
- Target toughness: {toughness} ({diff_desc})

Inputs:
- Syllabus (plaintext): {syllabus_text}
- Question counts: 1-mark MCQ = {mark1}; 5-mark short-answer = {mark5}; 10-mark short-answer = {mark10}

Constraints:
- Keep questions tightly grounded in the syllabus.
- Prefer competency-based prompts: real-life application, understanding, and clear skills demonstration.
- Ensure clarity, unambiguous wording, and answerability within marks.
- Avoid trick questions; no external curriculum content.
- Calibrate cognitive levels to {diff_desc}; emphasize Remember/Understand/Apply for lower marks; allow Analyze for 5-mark and Analyze/Evaluate (if feasible and still answerable) for 10-mark at higher levels.
- Keep the question short and to the point.
- 5 or 10 marks questions can be divided into 1, 2, 3, 4 marks questions,
- Output format:

Question Paper (NEP 2020–aligned)
Section A: 1-mark (MCQ) – {mark1} items
Q1–Q{mark1}: ...
Section B: 5-mark (short answer) – {mark5} items
Q1–Q{mark5}: ...
Section C: 10-mark (long answer) – {mark10} items
Q1–Q{mark10}: ...

Also include: Answers of MCQs after the paper.
"""

def generate_question_paper(syllabus_text, mark1, mark5, mark10, toughness, institute):
    prompt = make_prompt(syllabus_text, mark1, mark5, mark10, toughness, institute)
    model = genai.GenerativeModel(MODEL_NAME) #type: ignore
    resp = model.generate_content(prompt)
    return resp.text if hasattr(resp, "text") else str(resp)

if __name__ == "__main__":
    syllabus = input("Paste syllabus text: ").strip()
    n1 = int(input("Number of 1-mark questions: ").strip() or "5")
    n2 = int(input("Number of 5-mark questions: ").strip() or "5")
    n3 = int(input("Number of 10-mark questions: ").strip() or "5")
    toughness = norm_choice(input("Toughness (easy/medium/hard): "), ["easy","medium","hard"])
    institute = norm_choice(input("Institute level (school/college/postgrad): "), ["school","college","postgrad"])
    print(generate_question_paper(syllabus, n1, n2, n3, toughness, institute))
