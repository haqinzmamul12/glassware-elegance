import os
import ssl
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail 
import os 

from dotenv import load_dotenv
load_dotenv() 

FROM =os.getenv("FROM")
TO =os.getenv("TO")
SEND_GRID_API_KEY =os.getenv("SEND_GRID_API_KEY")


def send_email(name, sender_email, message_body):
    ssl._create_default_https_context = ssl._create_unverified_context

    message = Mail(
        from_email= FROM,
        to_emails= TO,  # Where you want to receive contact messages
        subject=f'New message from {name}',
        html_content=f"""
        <strong>Name:</strong> {name}<br>
        <strong>Email:</strong> {sender_email}<br><br>
        <strong>Message:</strong><br>{message_body}
        """
        )

    # Send using SendGrid
    sg = SendGridAPIClient(SEND_GRID_API_KEY)
    response =sg.send(message)
    print(f"SendGrid response: {response.status_code}")