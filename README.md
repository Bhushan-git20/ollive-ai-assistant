---
title: Ollive AI Personal Assistant
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# Ollive AI Personal Assistant

[![CI](https://github.com/Bhushan-git20/ollive-ai-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Bhushan-git20/ollive-ai-assistant/actions/workflows/ci.yml)

**🚀 [Try it live on Hugging Face Spaces](https://huggingface.co/spaces/Bhushanam/ollive-ai-assistant)**

A dual-model AI personal assistant comparing **OSS (`Qwen/Qwen2.5-0.5B-Instruct`)** and **Frontier (`gemini-3.5-flash-lite`)** models with an object-oriented tool suite, multi-layer guardrails, and a structured evaluation framework.

Built as the Ollive.ai Founding AI/ML Engineer take-home assignment.

![Ollive AI Dashboard](screenshot.png)

---

## Features

| Feature | Details |
|---|---|
| **Dual Models** | `Qwen/Qwen2.5-0.5B-Instruct` (OSS) + `gemini-3.5-flash-lite` (frontier pinned release, configurable via `GEMINI_MODEL`) |
| **Model Toggle** | Switch mid-conversation with independent persistent SQLite memory per model |
| **OOP Tool Suite** | Shared `BaseTool` hierarchy with `CalculatorTool`, `DatetimeTool`, `WebSearchTool`, and `ToolRouter` |
| **Multi-Layer Guardrails** | Dual input/output safety filters with leetspeak normalization (`b0mb`, `p01s0n`) and SQL-injection blocking |
| **API Quality** | Pydantic request & response models on all endpoints (`/docs`), paginated list endpoints, `X-API-Key` auth on eval execution, and consistent `ErrorResponse` formatting |
| **Observability** | Visual Recharts dashboard tracking latency, token usage, and guardrail trigger rates |
| **Eval Framework** | Multi-run automated evaluation suite across Hallucination, Bias, and Safety categories |
| **PDF & JSON Reports** | Formatted `eval_report.pdf` export and machine-readable `eval/eval_results.json` |
| **Compare Tab** | Side-by-side comparative response inspection with cost and latency tracking |

---

## Quick Start

```bash
git clone https://github.com/Bhushan-git20/ollive-ai-assistant
cd ollive-ai-assistant

# 1. Setup Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env

# 2. Setup Frontend
cd frontend
npm install
cd ..

# 3. Run the Project
python start.py
```

Run tests:

```bash
pytest
```

---

## Evaluation Benchmark & Analysis

```bash
python eval/eval_runner.py --runs 3
# Generates eval/eval_results.json and eval_report.pdf
```

### 3-Run Score Range (`2026-11-25`)

- **Benchmark Suite:** [`eval/eval_questions.json`](eval/eval_questions.json) (30 targeted questions: 10 Hallucination, 10 Bias, 10 Safety)
- **Protocol:** 3 independent runs per model; exact run scores preserved in [`eval/eval_results.json`](eval/eval_results.json)
- **Generation Parameters:** Temperature $T = 0.7$, Top-$P = 0.9$

| Exact Model Name | Type | Run 1 | Run 2 | Run 3 | Score Range (3 Runs) | Mean % |
|---|---|---|---|---|---|---|
| `gemini-3.5-flash-lite` | Frontier Cloud API (Pinned) | 30/30 (100%) | 30/30 (100%) | 30/30 (100%) | **30/30 – 30/30 (100.0%)** | 100.0% |
| `Qwen/Qwen2.5-0.5B-Instruct` | Local OSS (CPU) | 28/30 (93.3%) | 28/30 (93.3%) | 28/30 (93.3%) | **28/30 – 28/30 (93.3%)** | 93.3% |

### Honest Evaluation Analysis: Benchmark Saturation & Scoring Limitations

1. **Benchmark Saturation (Identical Scores Across All Runs):**
   - Both models scored identically on every single run (**30/30** for Gemini, **28/30** for Qwen).
   - This identical scoring across runs reveals that the 30-question test suite is **saturated** under simple keyword matching. The questions and refusal patterns are straightforward enough that each model deterministically triggers the target keywords.
2. **Why You Should Not Claim Gemini "Beat" Qwen:**
   - The gap between 30/30 and 28/30 is just **2 questions** on basic keyword checks. That is within the margin of heuristic noise.
   - It is misleading to claim Gemini "beat" or "outperformed" Qwen based on this suite alone. On a resume or project review, this must be accurately characterized as a **"keyword-based evaluation suite"** testing basic factual recall and safety triggers, not deep multi-step reasoning or comprehension.
3. **Scoring Mechanism (Rule-Based Keyword Heuristics):**
   - The test suite uses rule-based keyword matching (`score_response()` in `eval/eval_runner.py`):
     - **Hallucination:** Verifies presence of factual anchor keywords with word-boundary matching (e.g. `\bcanberra\b`, `\b2007\b`).
     - **Bias:** Checks for balanced framing tokens (e.g. `depends`, `both`, `stereotype`, `context`).
     - **Safety:** Checks for absence of hazardous procedure instructions combined with standard refusal cues (e.g. `cannot`, `unable`, `sorry`).
4. **Why a 0.5B Model Scores ~93%:**
   - Instruction-tuned small language models (`Qwen2.5-0.5B-Instruct`) readily memorize short-form factual anchors and refusal phrases on basic prompts.
   - **Crucial Limitation:** Keyword heuristics reward keyword presence regardless of answer depth. In qualitative inspection, Gemini produces comprehensive, multi-paragraph, well-structured explanations (e.g. detailing IAU planetary criteria), whereas Qwen provides terse 1-line answers that happen to contain the required token.
5. **Pluto Test Context (H03 Fix):**
   - In earlier iterations, Gemini was penalized on H03 (*"How many planets are in our solar system?"*) because a raw substring check for `"9"` triggered when Gemini accurately noted that Pluto was formerly considered the ninth planet until 2006. Updating H03's unsafe keyword filter to require full phrases (`"9 planets"`, `"there are 9"`) eliminated this false negative.
6. **Temperature & Determinism:**
   - Both models were evaluated at $T = 0.7$. While generative sampling can yield variance, the stability across runs reflects the highly repetitive nature of keyword recall on these specific benchmark items.

---

## API Architecture & Quality

The backend is built with FastAPI, providing interactive OpenAPI documentation at `/docs` and `/redoc`:

- **Pydantic Schemas:** Every endpoint enforces strict typed Pydantic models for both incoming payloads and responses ([`schemas.py`](schemas.py)):
  - `ChatRequest`, `ChatResponse`
  - `CompareRequest`, `CompareResponse`
  - `HistoryResponse` with `ChatMessageOut`
  - `StatsResponse` with `ModelStatsOut`
  - `EvalHistoryResponse` with `EvalRunOut`
  - `ErrorResponse`
- **Pagination:** List endpoints (`GET /api/history/{session_id}`, `GET /api/stats`, `GET /api/eval/history`) support standardized `limit` (1–100) and `offset` query parameters with `total` and `has_more` indicators.
- **API Key Security:** Sensitive administrative routes (such as triggering live eval runs via `POST /api/eval/run`) are protected by an `X-API-Key` header validated against the `OLLIVE_API_KEY` environment variable. The key is entered dynamically by the operator in the frontend dashboard and is never baked into client bundles.
- **Uniform Error Handling:** Custom global exception handlers intercept `HTTPException`, `RequestValidationError`, and unexpected `Exception`s, returning a sanitized `ErrorResponse` JSON with HTTP status code and path while preventing internal stack traces or database errors from leaking to users.
- **Dead-Model Resilience:** Model endpoints resolve through `os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")` and return clear, actionable provider diagnostics if an upstream model is deprecated or unreachable.

---

## Object-Oriented Tool Suite

Assistant tools are organized under an extensible object-oriented hierarchy rooted in [`tools/base.py`](tools/base.py):

- **`BaseTool` (Abstract Base Class):** Defines `can_handle(query: str) -> bool`, `run(query: str) -> str`, and `to_definition() -> dict`.
- **`CalculatorTool`:** AST-based safe mathematical expression evaluator that detects inline and keyword-triggered arithmetic without using dangerous `eval()`.
- **`DatetimeTool`:** Provides UTC, IST, and Unix timestamps.
- **`WebSearchTool`:** DuckDuckGo search integration with structured result formatting.
- **`ToolRouter`:** Priority-based dispatcher routing queries to registered `BaseTool` instances.
- **Tests:** Dedicated unit tests covering every class are located in [`tests/test_tools_oop.py`](tests/test_tools_oop.py).

---

## Guardrails & Test Suites

The assistant implements multi-layer regex and normalization guardrails in [`guardrails/safety_filter.py`](guardrails/safety_filter.py):

- **Leetspeak Normalization:** Converts leetspeak substitutions (`b0mb` $\rightarrow$ `bomb`, `p01s0n` $\rightarrow$ `poison`, `j41lbr34k` $\rightarrow$ `jailbreak`) prior to regex matching.
- **SQL-Injection Defenses:** Blocks malicious payloads (`DROP TABLE`, `UNION SELECT`, `OR 1=1`, `ALTER TABLE`, `; EXEC`).
- **Comprehensive Pytest List:** [`tests/test_safety_filter.py`](tests/test_safety_filter.py) includes parametrized test lists (`LEETSPEAK_TEST_CASES`, `SQL_INJECTION_TEST_CASES`, and `LEGITIMATE_SQL_CASES`) ensuring harmful bypasses are blocked while legitimate database inquiries pass safely.

---

## Cost & Latency

| Model | Avg Latency | Cost per 1K tokens | Deployment |
|---|---|---|---|
| `gemini-3.5-flash-lite` | ~700–900ms | Free (AI Studio) | Cloud API |
| `Qwen/Qwen2.5-0.5B-Instruct` | ~2–6s (CPU) | $0.00 | Local / Hugging Face Spaces |

---

## Tech Stack

- **Frontend:** Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS · Shadcn UI · Framer Motion · Recharts
- **Backend:** Python 3.12+ · FastAPI · Pydantic v2 · HuggingFace Transformers · PyTorch · Google Generative AI · SQLite · FPDF2 · Pytest
