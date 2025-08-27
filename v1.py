import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY) #type: ignore

MODEL_NAME = "models/gemini-2.0-flash-lite"

def make_prompt(syllabus_text, mark1, mark5, mark10):
    return f"""
Task: Create an answerable question paper aligned with India's NEP 2020 focusing on competency-based, formative assessment and balanced Bloom's levels.

Inputs:
- Syllabus (plaintext): {syllabus_text}
- Question counts: 1-mark MCQ = {mark1}; 5-mark short-answer = {mark5}; 10-mark short-answer = {mark10}

Constraints:
- Keep questions tightly grounded in the syllabus.
- Prefer competency-based prompts: real-life application, understanding, and clear skills demonstration.
- Ensure clarity, unambiguous wording, and answerability within marks.
- Avoid trick questions; no external curriculum content.
- Mix Bloom levels: mostly Remember/Understand/Apply, with occasional Analyze in 5-mark items if feasible.
- Output format:

Question Paper (NEP 2020–aligned)
Section A: 1-mark (MCQ) – {mark1} items
Q1–Q{mark1}: ...
Section B: 5-mark (short answer) – {mark5} items
Q1–Q{mark5}: ...
Section C: 10-mark (short answer) – {mark10} items
Q1–Q{mark10}: ...

Also include: Answers of MCQs after the paper.
"""
#Also include: An answer key after the paper.

def generate_question_paper(syllabus_text, mark1, mark5, mark10):
    prompt = make_prompt(syllabus_text, mark1, mark5, mark10)
    model = genai.GenerativeModel(MODEL_NAME) #type: ignore
    resp = model.generate_content(prompt)
    return resp.text if hasattr(resp, "text") else str(resp)

if __name__ == "__main__":
    syllabus = input("Paste syllabus text: ").strip()
    n1 = int(input("Number of 1-mark questions: ").strip() or "5")
    n2 = int(input("Number of 5-mark questions: ").strip() or "5")
    n3 = int(input("Number of 10-mark questions: ").strip() or "5")
    print(generate_question_paper(syllabus, n1, n2, n3))