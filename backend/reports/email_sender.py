import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load environment variables from the .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Email Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER") 
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(subject: str, body_html: str, recipients: list, attachment_path: str):
    """
    Sends an email with an attachment.
    """
    if not all([SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD]):
        print("Email configuration is missing in .env file. Skipping email.")
        return False

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        # Attach the body of the email as HTML
        msg.attach(MIMEText(body_html, 'html'))

        # Attach the file
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            # Set the attachment header
            filename = os.path.basename(attachment_path)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)
        
        # Connect to the SMTP server and send the email
        print(f"Connecting to SMTP server at {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent successfully to {', '.join(recipients)}!")
        
        return True

    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        return False

if __name__ == "__main__":
    
    print("Running email sender test...")
    
    # 1. Create a dummy report file to attach
    dummy_file = "test_report.txt"
    with open(dummy_file, "w") as f:
        f.write("This is a test report.")
    
    # 2. Define email content
    test_subject = "Daily InsightGenie Report"
    test_body = """
    <html>
    <body>
        <h2>InsightGenie Daily Feedback Report</h2>
        <p>Hello,</p>
        <p>Please find the latest feedback report attached.</p>
        <p>Regards,<br>InsightGenie Bot</p>
    </body>
    </html>
    """
    test_recipients = [os.getenv("EMAIL_RECIPIENT", "default_recipient@example.com")]

    # 3. Send the email
    send_email(test_subject, test_body, test_recipients, dummy_file)
    
    # 4. Clean up the dummy file
    os.remove(dummy_file)
