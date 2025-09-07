# In your report_gen.py file...
from db.store import Session, Feedback, init_db
import pandas as pd
from datetime import datetime
import os
from backend.reports.email_sender import send_email # <-- IMPORT THE FUNCTION

DB_URL = "sqlite:///insightgenie.db"

def generate_and_email_report(limit=100):
    """
    Fetches feedback, saves it as a CSV, and emails the report.
    """
    # ... (your existing code to fetch data and create the DataFrame)
    
    data = [] # Your data fetching logic
    # ...
    
    df = pd.DataFrame(data)

    # Save CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"feedback_report_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"Report generated: {csv_file}")
    
    # --- Email the Report ---
    subject = f"InsightGenie Feedback Report - {datetime.now().strftime('%Y-%m-%d')}"
    body = f"<html><body><h2>Feedback Report</h2><p>Attached is the feedback report generated on {datetime.now()}.</p></body></html>"
    recipients = [os.getenv("EMAIL_RECIPIENT")]
    
    send_email(subject, body, recipients, csv_file)
    
    # Optional: Clean up the local file after sending
    # os.remove(csv_file)
    
    return df

if __name__ == "__main__":
    generate_and_email_report()