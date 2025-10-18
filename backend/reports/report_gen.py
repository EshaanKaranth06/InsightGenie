import os
from datetime import datetime
from fpdf import FPDF

from backend.llm.engine import InsightEngine
from backend.reports.email_sender import send_email

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'InsightGenie Summary Report', 0, 1, 'C')
        self.ln(10)

def generate_and_email_report_task(product_id: int, recipient_email: str, product_name: str):
    print(f"Starting PDF report generation for product: {product_name} (ID: {product_id})...")
    pdf_file = None
    
    try:
        engine = InsightEngine()
        report_sections = {
            "Overall Summary": "Provide a brief, high-level summary of the overall customer sentiment.",
            "Positive Themes (Pros)": "What are the most common positive themes or pros mentioned in the feedback? Use bullet points.",
            "Negative Themes (Cons & Criticisms)": "What are the most common negative themes, criticisms, or cons? Use bullet points.",
            "Feature Requests & Suggestions": "Are there any specific feature requests or suggestions for improvement? List them out, if none, PRINT **NONE**"
        }
        
        report_content = {}
        total_sections = len(report_sections)

        for i, (key, question) in enumerate(report_sections.items()):
            print(f"\n--- Generating Report Section ({i+1}/{total_sections}): {key} ---")
            full_response = "".join(engine.answer_question(question, product_id))
            report_content[key] = full_response
        
        # --- PDF Generation ---
        pdf = PDF()
        pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
        pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 15, product_name, 0, 1, 'C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
        pdf.ln(10)

        for title, content in report_content.items():
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, title, 0, 1, 'L')
            pdf.set_font('Arial', '', 12)
            pdf.multi_cell(0, 8, content)
            pdf.ln(5)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_file = f"InsightGenie_Report_{product_id}_{timestamp}.pdf"
        pdf.output(pdf_file)
        print(f"PDF report generated: {pdf_file}")

        # --- Emailing ---
        subject = f"InsightGenie Summary Report for {product_name}"
        body = f"<html><body><h2>Your Summary Report is Ready</h2><p>Attached is the AI-generated summary report for <b>{product_name}</b>.</p></body></html>"
        send_email(subject, body, recipient_email, pdf_file)

    except Exception as e:
        print(f"An error occurred during PDF report generation: {e}")
    finally:
        # --- Cleanup ---
        if pdf_file and os.path.exists(pdf_file):
            os.remove(pdf_file)
            print(f"Cleaned up temporary file: {pdf_file}")