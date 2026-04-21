import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv


load_dotenv()
email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')

def send_mail(to,subject,body):
    if isinstance(body, list):
        body = "\n".join(body)

    # msg = MIMEText(body)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email
    msg['to'] = to
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Email Error:", e)
        return False
        