import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo
from app.security import Settings
from app.enums import EmailActions

settings = Settings()

async def send_email(registration: str, action: EmailActions):

    now = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    sender_email = settings.EMAIL_SENDER
    password = settings.EMAIL_PASSWORD
    receiver_email = settings.EMAIL_RECEIVER


    if not settings.SMTP_SERVER:
        raise RuntimeError("EMAIL_SMTP_HOST not configured")

 
    if not sender_email or not password or not receiver_email:
        raise RuntimeError("Email variables not configured")

 
    msg = EmailMessage()
   
    msg["Subject"] = f"User {action.value.upper()} - Registration {registration}"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content(
        f"The user with registration {registration} was successfully {action.value} in the system.\n"
        f"Date/Time: {now}"
    )


    context = ssl.create_default_context()

   
    with smtplib.SMTP(
        settings.SMTP_SERVER, settings.PORT, timeout=10
    ) as server:
        server.starttls(context=context) 
        server.login(sender_email, password)
        server.send_message(msg)