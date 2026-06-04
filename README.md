---
title: Ollive AI Personal Assistant
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: false
license: mit
---

# Ollive AI Personal Assistant

**🚀 [Try it live on Hugging Face Spaces](https://huggingface.co/spaces/bhushan-git20/ollive-ai-assistant)**


A dual-model AI personal assistant comparing **OSS (Qwen 2.5 0.5B)** and **Frontier (Gemini 2.5 Flash)** models with a structured evaluation framework.

Built as the Ollive.ai Founding AI/ML Engineer take-home assignment.

---

## Features

| Feature | Details |
|---|---|
| **Dual models** | Qwen2.5-0.5B-Instruct (OSS) + Gemini 2.5 Flash (frontier) |
| **Model toggle** | Switch mid-conversation; separate memory per model |
| **Persistent memory** | SQLite per session — retains context across turns |
| **Tool use** | Calculator (safe AST eval) + Datetime (UTC/IST) |
| **Guardrails** | Input + output safety filter, regex-based keyword blocking |
| **Observability** | Logs latency, token counts, guardrail hits per request |
| **Eval suite** | 30 questions across hallucination / bias / safety categories |
| **PDF report** | Auto-generated eval report with category breakdown |
| **Compare tab** | Side-by-side response comparison with cost/latency |

---

## Quick Start

```bash
git clone https://github.com/Bhushan-git20/ollive-ai-assistant
cd ollive-ai-assistant

pip install -r requirements.txt

cp .env.example .env
# Add your GEMINI_API_KEY to .env

streamlit run app.py
```

---

## Run Eval

```bash
python eval/eval_runner.py
# Generates eval_report.pdf in project root
```

### Evaluation Results
In our most recent run on 30 test questions (Hallucination, Bias, Safety):
- **Gemini-Flash-Lite:** 30/30 (100.0%)
- **Qwen2.5-0.5B:** 26/30 (86.7%)

The evaluation suite has been recently updated to ensure proper parsing of unbiased responses and true refusals.

---

## Cost & Latency

| Model | Avg Latency | Cost per 1K tokens | Deploy |
|---|---|---|---|
| Gemini 2.5 Flash | ~800ms | Free (AI Studio) | Cloud |
| Qwen2.5-0.5B | ~2–8s (CPU) | $0.00 | HF Spaces |

---

## Architecture

```
app.py                    ← Streamlit UI (Chat / Compare / Eval tabs)
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

Python · Streamlit · HuggingFace Transformers · Google Generative AI · SQLite · FPDF2 · python-dotenv

