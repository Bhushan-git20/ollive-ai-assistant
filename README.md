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

**🚀 [Try it live on Hugging Face Spaces](https://huggingface.co/spaces/bhushan-git20/ollive-ai-assistant)**


A dual-model AI personal assistant comparing **OSS (Qwen 2.5 0.5B)** and **Frontier (Gemini 2.5 Flash)** models with a structured evaluation framework.

Built as the Ollive.ai Founding AI/ML Engineer take-home assignment.

![Ollive AI Dashboard](screenshot.png)

---

## Features

| Feature | Details |
|---|---|
| **Dual models** | Qwen2.5-0.5B-Instruct (OSS) + Gemini 2.5 Flash (frontier) |
| **Model toggle** | Switch mid-conversation; separate memory per model |
| **Persistent memory** | SQLite per session — retains context across turns |
| **Web Search** | DuckDuckGo live web search integration |
| **Tool use** | Calculator (safe AST eval) + Datetime (UTC/IST) + DuckDuckGo |
| **Guardrails** | Input + output safety filter, regex-based keyword blocking |
| **Observability** | Visual Recharts dashboard tracking latency, tokens, and guardrail hits |
| **Eval suite** | Live in-app Eval Runner + 30 questions across hallucination/bias/safety |
| **PDF report** | Auto-generated eval report with category breakdown |
| **Compare tab** | Side-by-side response comparison with cost/latency |

---

## Quick Start

```bash
git clone https://github.com/Bhushan-git20/ollive-ai-assistant
cd ollive-ai-assistant

# 1. Setup Backend (FastAPI)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn server:app --reload

# 2. Setup Frontend (Next.js) - in a new terminal
cd frontend
npm install
npm run dev
```

---

## Run Eval

```bash
python eval/eval_runner.py
# Generates eval_report.pdf in project root
```

### Evaluation Results
In our most recent comprehensive stress test on 30 questions (Hallucination, Bias, Safety):
- **Gemini-Flash-Lite:** 19/30 (63.3%)
- **Qwen2.5-0.5B:** 27/30 (90.0%)

The evaluation suite was recently updated alongside a complete UI redesign (matching the creator's portfolio aesthetic) and a full system stress-test. Guardrails have been strengthened to catch leetspeak (e.g., `b0mb`) and SQL injection (`drop table`) bypass attempts.

---

## Cost & Latency

| Model | Avg Latency | Cost per 1K tokens | Deploy |
|---|---|---|---|
| Gemini 2.5 Flash | ~800ms | Free (AI Studio) | Cloud |
| Qwen2.5-0.5B | ~2–8s (CPU) | $0.00 | HF Spaces |

---

## Architecture

```
frontend/                 ← Next.js (React) UI with Shadcn and TailwindCSS
server.py                 ← FastAPI Backend serving API endpoints
models/
  gemini_model.py         ← Gemini 2.5 Flash via google-generativeai
  qwen_model.py           ← Qwen2.5-0.5B via HuggingFace transformers
tools/
  calculator.py           ← Safe AST-based math evaluator
  datetime_tool.py        ← UTC/IST datetime
  tool_router.py          ← Keyword-based tool dispatcher
memory/
  sqlite_memory.py        ← Per-session chat history (SQLite)
guardrails/
  safety_filter.py        ← Input + output regex safety checks
observability/
  logger.py               ← Latency/token/guardrail logging (SQLite)
eval/
  eval_questions.json     ← 30 test questions (hallucination/bias/safety)
  eval_runner.py          ← Runs eval, prints results, calls PDF export
  pdf_export.py           ← Generates structured PDF report
```

---

## Eval Categories

- **Hallucination (10 Qs):** Factual accuracy on verifiable world knowledge
- **Bias (10 Qs):** Checks for balanced, non-stereotyped responses
- **Safety (10 Qs):** Tests refusal of harmful requests + appropriate help responses

---

## Stack

**Frontend:** Next.js (App Router) · React · Tailwind CSS · Shadcn UI · Framer Motion
**Backend:** Python · FastAPI · HuggingFace Transformers · Google Generative AI · SQLite · FPDF2

