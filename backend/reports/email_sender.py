import os
import smtplib
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class EmailConfig:
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(subject: str, body_html: str, recipient: str, attachment_path: Optional[str] = None):
    if not all([EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT, EmailConfig.EMAIL_SENDER, EmailConfig.EMAIL_PASSWORD]):
        print("Email configuration is missing. Skipping email.")
        return False

    try:
        msg = MIMEMultipart()
        
        assert EmailConfig.SMTP_SERVER is not None, "SMTP_SERVER not configured"
        assert EmailConfig.EMAIL_SENDER is not None, "EMAIL_SENDER not configured"
        assert EmailConfig.EMAIL_PASSWORD is not None, "EMAIL_PASSWORD not configured"
        msg['From'] = EmailConfig.EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)
        
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            server.starttls()
            server.login(EmailConfig.EMAIL_SENDER, EmailConfig.EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent successfully to {recipient}!")
        
        return True
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        return False