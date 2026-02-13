import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from app.enums import EmailActions
from app.security import Settings

settings = Settings()


async def send_email(
    registration: str,
    action: EmailActions,
    performed_by: str = "System",
    systems_list: list | None = None
    ):
    now = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    if systems_list and len(systems_list) > 0:
        items = "\n".join([f"- {s}" for s in systems_list])
        txt_details = f"\nSistemas afetados com sucesso:\n{items}"
    else:

        txt_details = (
            "\nAtenção: Nenhum sistema afetado com sucesso "
            "Atualizando a task")

    msg = EmailMessage()
    msg["Subject"] = f"Offboarding Log - {registration}"
    msg["From"] = settings.EMAIL_SENDER
    msg["To"] = settings.EMAIL_RECEIVER

    msg.set_content(
        f"O usuário com o registro {registration} "
        f"passou pelo processo de: ({action.value}).\n"
        f"Executor: {performed_by}\n"
        f"{txt_details}\n"
        f"Data/Hora: {now}"
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(
        settings.SMTP_SERVER,
        settings.PORT,
        timeout=10
    ) as server:
        server.starttls(context=context)
        server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
        server.send_message(msg)
