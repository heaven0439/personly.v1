import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

async def send_otp_email(email_to: str, otp: str):
    # Set these in your .env file
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SMTP_EMAIL", "your-email@gmail.com")
    sender_password = os.getenv("SMTP_PASSWORD", "your-app-password") # Use Gmail App Passwords

    msg = MIMEMultipart()
    msg['From'] = f"Personly <{sender_email}>"
    msg['To'] = email_to
    msg['Subject'] = "Your Personly Verification Code"

    body = f"Welcome to Personly!\n\nYour 6-digit verification code is: {otp}\n\nThis code expires in 10 minutes."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"OTP successfully emailed to {email_to}")
    except Exception as e:
        print(f"Failed to send email: {e}")