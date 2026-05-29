import sys
sys.path.insert(0, 'd:/ANTI GRAVITY/ollive-ai-assistant/ollive-assistant')
from eval.eval_runner import load_questions, score_response
from models.gemini_model import generate

qs = load_questions()
for q in qs:
    if q['id'] in ['H07', 'B01', 'B06', 'S01']:
        resp, _, _, _ = generate(q['question'], [])
        passed, reason = score_response(q, resp)
        print(f"{q['id']}: {'PASS' if passed else 'FAIL'} - {reason}")
        print(f"  Response: {resp}")
