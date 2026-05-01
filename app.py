import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)

# Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY.strip())

SYSTEM_PROMPT = """You are “The Keating Scale”, a structured writing analysis system inspired by expressive, authentic communication.

Your goal is NOT to judge grammar, intelligence, or correctness.

Your goal is to evaluate how human, meaningful, and self-expressive a piece of writing is.

You must be strict, consistent, and structured.

---

INPUT:
The user will provide a piece of text (sentence, paragraph, or short writing).

---

STEP 1: DETECT CLAIM TYPE
Classify the input into ONE:

- Generic Statement (common motivational / cliché / AI-like writing)
- Personal Expression (lived experience, emotions, self-reflection)
- Opinion / Argument (stance on a topic)
- Meme / Informal Expression (internet slang, humor, casual tone)
- Abstract / Vague Thought (philosophical but unclear)

---

STEP 2: SCORE USING 5 DIMENSIONS (0–10 each)

Be conservative. Do NOT inflate scores.

1. AUTHENTICITY
- 0–3: generic, cliché, AI-like, interchangeable
- 4–6: partially personal but still common phrasing
- 7–10: clearly lived, specific, personal voice

2. ORIGINALITY
- 0–3: cliché, commonly seen phrases
- 4–6: somewhat fresh but still familiar idea
- 7–10: unique angle or unusual phrasing

3. EMOTIONAL_WEIGHT
- 0–3: flat, informational
- 4–6: mild emotional undertone
- 7–10: strong emotional presence or vulnerability

4. CLARITY
- 0–3: confusing or overly vague
- 4–6: understandable but slightly unclear
- 7–10: clear intent and meaning

5. BOLDNESS
- 0–3: safe, neutral, avoids stance
- 4–6: moderate opinion or expression
- 7–10: strong stance, vulnerability, or risk-taking

---

STEP 3: GENERIC DENSITY
Rate how “replaceable” the text is:

- Low: unique voice
- Medium: somewhat generic
- High: could be said by almost anyone

---

STEP 4: OUTPUT FORMAT (STRICT)

Return exactly this structure:

---

CLAIM TYPE:
<classification>

---

SCORES:
AUTHENTICITY: X/10
ORIGINALITY: X/10
EMOTIONAL_WEIGHT: X/10
CLARITY: X/10
BOLDNESS: X/10

---

GENERIC DENSITY:
Low / Medium / High

---

OVERALL INTERPRETATION:
(one short sentence summarizing the writing)

---

FEEDBACK:
- Identify the weakest dimension
- Explain WHY in simple language
- Be direct, not polite or vague

---

KEATING PUSH (STRICT MODE):
DO NOT rewrite the text.

Instead, give ONLY:

1. Missing Core:
- one sentence describing what is missing emotionally or experientially

2. Distortion:
- one sentence explaining what feels generic or overused

3. Constraint:
- a strict rule the user must follow to rewrite it themselves
  (must include ONE specific detail requirement)

4. Starting Point (optional):
- ONE incomplete sentence starter only (max 12 words)
"""

def parse_response(text):
    data = {
        "claim_type": "",
        "scores": {},
        "generic_density": "",
        "overall": "",
        "feedback": "",
        "rewrite_challenge": ""
    }
    
    lines = text.strip().split('\n')
    mode = None
    feedback_lines = []
    rewrite_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('---'):
            continue
            
        if line.startswith('CLAIM TYPE:'):
            mode = "claim_type"
            data["claim_type"] = line.split(':', 1)[1].strip() if ':' in line and len(line) > 11 else ""
            continue
        elif line.startswith('SCORES:'):
            mode = "scores"
            continue
        elif line.startswith('GENERIC DENSITY:'):
            mode = "generic_density"
            data["generic_density"] = line.split(':', 1)[1].strip() if ':' in line and len(line) > 16 else ""
            continue
        elif line.startswith('OVERALL INTERPRETATION:'):
            mode = "overall"
            data["overall"] = line.split(':', 1)[1].strip() if ':' in line and len(line) > 23 else ""
            continue
        elif line.startswith('FEEDBACK:'):
            mode = "feedback"
            continue
        elif line.startswith('KEATING PUSH'):
            mode = "rewrite"
            continue
            
        if mode == "claim_type":
            if not data["claim_type"]:
                data["claim_type"] = line
        elif mode == "scores":
            if ':' in line:
                key, val = line.split(':', 1)
                try:
                    score = int(val.split('/')[0].strip())
                    data["scores"][key.strip()] = score
                except:
                    pass
        elif mode == "generic_density":
            if not data["generic_density"]:
                data["generic_density"] = line
        elif mode == "overall":
            if not data["overall"]:
                data["overall"] = line
        elif mode == "feedback":
            feedback_lines.append(line)
        elif mode == "rewrite":
            rewrite_lines.append(line)
            
    data["feedback"] = "\n".join(feedback_lines).strip()
    data["rewrite_challenge"] = "\n".join(rewrite_lines).strip()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    text = request.json.get('text', '')
    max_tokens = request.json.get('max_tokens', 1024)
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
        
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key is missing. Please add GEMINI_API_KEY to your .env file."}), 500
        
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        response = model.generate_content(
            text,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=int(max_tokens),
            )
        )
        
        ai_text = response.text
        result = parse_response(ai_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
