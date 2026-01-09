import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo
from app.security import Settings
from app.enums import EmailActions


settings = Settings()


async def send_email(matricula: str, action: EmailActions):
    now = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    sender_email = settings.EMAIL_SENDER
    password = settings.EMAIL_PASSWORD
    receiver_email = settings.EMAIL_RECEIVER

    if not settings.SMTP_SERVER:
        raise RuntimeError("EMAIL_SMTP_HOST não configurado")

    if not sender_email or not password or not receiver_email:
        raise RuntimeError("Variáveis de email não configuradas")

    msg = EmailMessage()
    msg["Subject"] = f"Usuário {action.value.upper()} - Matrícula {matricula}"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content(
        f"O usuário de matrícula {matricula} foi {action.value} com sucesso no sistema.\n"
        f"Data/Hora: {now}"
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(
        settings.SMTP_SERVER, settings.PORT, timeout=10
    ) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.send_message(msg)
