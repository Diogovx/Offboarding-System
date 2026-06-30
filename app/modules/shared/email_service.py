import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from .email_actions import EmailActions
from .email_enums import EMAIL_TEMPLATES
from app.core import settings


async def send_email(
    registration: str,
    action: EmailActions,
    user_target: str,
    performed_by: str = "System",
    systems_list: list | None = None,
    lang: str = 'en'
    ):

    lang_code = lang.split("-", maxsplit=1)[0].lower()
    if lang_code not in EMAIL_TEMPLATES:
        lang_code = "en"

    template = EMAIL_TEMPLATES[lang_code]

    now = datetime.now(ZoneInfo(template["zoneinfo"])).strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    if systems_list and len(systems_list) > 0:
        items = "\n".join([f"- {s}" for s in systems_list])
        txt_details = f"{template['success_title']}\n{items}"
    else:
        txt_details = template['no_systems']

    msg = EmailMessage()
    msg["Subject"] = template["subject"].format(registration=registration)
    msg["From"] = settings.EMAIL_SENDER
    msg["To"] = settings.EMAIL_RECEIVER

    msg.set_content(
        template["body"].format(
            user_target=user_target,
            registration=registration,
            action_value=action.value,
            performed_by=performed_by,
            txt_details=txt_details,
            now=now
        )
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(
        settings.SMTP_SERVER,
        settings.AD_PORT,
        timeout=10
    ) as server:
        server.starttls(context=context)
        server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
        server.send_message(msg)
