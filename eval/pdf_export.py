from fpdf import FPDF
from datetime import datetime
import textwrap


class EvalReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(30, 30, 60)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "Ollive AI Assistant - Evaluation Report", ln=True, fill=True, align="C")
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 7, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(240, 240, 255)
        self.cell(0, 9, title, ln=True, fill=True)
        self.ln(2)

    def summary_table(self, results_by_model: dict):
        self.section_title("Executive Summary")
        self.set_font("Helvetica", "B", 9)

        col_w = [50, 35, 35, 35, 35]
        headers = ["Model", "Total", "Passed", "Failed", "Score %"]
        for i, h in enumerate(headers):
            self.cell(col_w[i], 8, h, border=1, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        for model_name, data in results_by_model.items():
            total = data["total"]
            passed = data["passed"]
            failed = total - passed
            score = round((passed / total) * 100, 1) if total else 0
            row = [model_name, str(total), str(passed), str(failed), f"{score}%"]
            for i, val in enumerate(row):
                self.cell(col_w[i], 7, val, border=1, align="C")
            self.ln()
        self.ln(4)

    def category_breakdown(self, results_by_model: dict):
        self.section_title("Category Breakdown")
        categories = ["hallucination", "bias", "safety"]

        self.set_font("Helvetica", "B", 9)
        col_w = [50, 45, 45, 50]
        headers = ["Model", "Hallucination", "Bias", "Safety"]
        for i, h in enumerate(headers):
            self.cell(col_w[i], 8, h, border=1, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        for model_name, data in results_by_model.items():
            cat_scores = data.get("category_scores", {})
            row = [model_name]
            for cat in categories:
                s = cat_scores.get(cat, {})
                p = s.get("passed", 0)
                t = s.get("total", 0)
                row.append(f"{p}/{t} ({round(p/t*100) if t else 0}%)")
            for i, val in enumerate(row):
                self.cell(col_w[i], 7, val, border=1, align="C")
            self.ln()
        self.ln(4)

    def detailed_results(self, model_name: str, results: list):
        self.section_title(f"Detailed Results - {model_name}")
        self.set_font("Helvetica", "", 8)

        def safe_wrap(prefix, text, width=80):
            # Encode and decode ascii to remove unprintable unicode that can also crash fpdf widths
            safe_text = str(text).encode("ascii", "ignore").decode("ascii")
            full_text = f"{prefix}{safe_text}"
            return "\n".join(full_text[i:i+width] for i in range(0, len(full_text), width))

        for r in results:
            status_icon = "PASS" if r["passed"] else "FAIL"
            color = (0, 140, 0) if r["passed"] else (180, 0, 0)
            self.set_text_color(*color)
            self.set_font("Helvetica", "B", 8)
            self.cell(0, 6, f"[{r['id']}] {r['category'].upper()} - {status_icon}", ln=True)
            self.set_text_color(0, 0, 0)
            self.set_font("Helvetica", "", 8)
            
            self.multi_cell(0, 5, safe_wrap("Q: ", r['question']))
            
            # Truncate response for PDF
            resp_preview = r["response"][:300] + "..." if len(r["response"]) > 300 else r["response"]
            self.multi_cell(0, 5, safe_wrap("A: ", resp_preview))
            
            if r.get("fail_reason"):
                self.set_text_color(180, 0, 0)
                self.multi_cell(0, 5, safe_wrap("Fail reason: ", r['fail_reason']))
                self.set_text_color(0, 0, 0)
            self.ln(2)

    def latency_table(self, stats: list):
        self.section_title("Cost & Latency Summary")
        if not stats:
            self.set_font("Helvetica", "I", 9)
            self.cell(0, 7, "No runtime data available. Start chatting to populate.", ln=True)
            return

        self.set_font("Helvetica", "B", 9)
        col_w = [50, 30, 35, 35, 40]
        headers = ["Model", "Requests", "Avg Latency ms", "Total Tokens", "Guardrail Hits"]
        for i, h in enumerate(headers):
            self.cell(col_w[i], 8, h, border=1, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        for row in stats:
            total_tok = (row.get("total_prompt_tokens") or 0) + (row.get("total_completion_tokens") or 0)
            vals = [
                row.get("model", ""),
                str(row.get("requests", 0)),
                str(row.get("avg_latency_ms", 0)),
                str(total_tok),
                str(row.get("guardrail_hits", 0)),
            ]
            for i, val in enumerate(vals):
                self.cell(col_w[i], 7, val, border=1, align="C")
            self.ln()


def generate_pdf(results_by_model: dict, stats: list, output_path: str = "eval_report.pdf"):
    pdf = EvalReportPDF()
    pdf.add_page()

    pdf.summary_table(results_by_model)
    pdf.category_breakdown(results_by_model)
    pdf.latency_table(stats)

    for model_name, data in results_by_model.items():
        pdf.add_page()
        pdf.detailed_results(model_name, data["results"])

    pdf.output(output_path)
    print(f"✅ PDF saved to: {output_path}")
