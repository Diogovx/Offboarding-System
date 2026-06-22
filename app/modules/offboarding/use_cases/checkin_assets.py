from fastapi import Request
import base64
import logging
import httpx
from datetime import datetime

from app.integrations.snipe_it import SnipeItService
from app.modules.offboarding.schemas import GeneratedTerm
from app.modules.audit.service import AuditLogCreate, create_audit_log
from app.modules.audit.enums import AuditAction, AuditStatus

logger = logging.getLogger(__name__)


async def checkin_assets(
    *,
    registration: str,
    target_name: str,
    snipeit_service: SnipeItService,
    target_username: str,
    req: Request,
    session,
    current_user
) -> tuple[bool, list[GeneratedTerm]]:
    """Generates checkin term documents and checks in all assets for the user.

    Fetches the checkin template once, then iterates over every assigned asset.
    Each asset is processed independently — a failure in one does not stop
    the others. Both the term generation and the checkin are attempted per asset.

    Args:
        registration (str): Employee registration number.
        target_name (str): Full name of the user being offboarded.
        snipeit_service (SnipeItService): Snipe-IT service instance.

    Returns:
        tuple[bool, list[GeneratedTerm]]: Success flag and list of generated
            term documents encoded in Base64.
    """
    generated_terms: list[GeneratedTerm] = []
    any_success = False

    try:
        assets = await snipeit_service.search_assets_by_user(registration)
    except Exception as e:
        logger.error(f"Failed to retrieve assets from {registration}: {e}")
        return False, []

    if not assets:
        logger.info(f"No assets found for {registration}.")
        return False, []

    try:
        template_id = await snipeit_service.get_template_id_by_type("checkin")
    except ValueError as e:
        logger.warning(f"Template checkin not found: {e}")
        template_id = None

    current_date = datetime.now().strftime("%Y%m%d_%H%M")
    format_name = target_name.replace(" ", "_")

    for asset in assets:
        asset_tag = asset.get("asset_tag")
        if not asset_tag:
            logger.warning(f"Asset without asset_tag ignored: {asset}")
            continue

        if template_id is not None:
            try:
                term_bytes = await snipeit_service.generate_term(
                    employee_num=registration,
                    template_id=template_id,
                    asset_tag=asset_tag,
                )
                filename = f"{registration}_{format_name}_{current_date}_{asset_tag}.docx"
                generated_terms.append(
                    GeneratedTerm(
                        filename=filename,
                        content_base64=base64.b64encode(term_bytes).decode("utf-8"),
                    )
                )
                logger.info(f"Term generated for asset {asset_tag}.")
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error generating term for {asset_tag}:"
                    f"{e.response.status_code} — {e.response.text}"
                )
            except Exception as e:
                logger.error(f"Unexpected error generating term for {asset_tag}: {e}")

        try:
            await snipeit_service.checkin_asset(
                registration=registration,
                asset_tag=asset_tag,
                note=f"Automatic offboarding — {current_date}",
            )
            logger.info(f"Checkin completed for asset {asset_tag}.")
            any_success = True

            create_audit_log(
                    session,
                    AuditLogCreate(
                        action=AuditAction.CHECKIN_ASSET,
                        status=AuditStatus.SUCCESS,
                        message=f"Equipment: Check-in on user {registration}'s equipment.",
                        user_id=current_user.id,
                        username=current_user.username,
                        target_username=target_username,
                        target_registration=registration,
                        resource=registration,
                        ip_address=req.client.host if req.client else None,
                        user_agent=req.headers.get("user-agent"),
                    ),
                )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error checking {asset_tag}: "
                f"{e.response.status_code} — {e.response.text}"
            )
            create_audit_log(
                    session,
                    AuditLogCreate(
                        action=AuditAction.CHECKIN_ASSET,
                        status=AuditStatus.FAILED,
                        message=f"Equipment checkin assets error: {e}",
                        user_id=current_user.id,
                        username=current_user.username,
                        target_username=target_username,
                        target_registration=registration,
                        resource=registration,
                        ip_address=req.client.host if req.client else None,
                        user_agent=req.headers.get("user-agent"),
                    ),
                )
        except Exception as e:
            create_audit_log(
                    session,
                    AuditLogCreate(
                        action=AuditAction.CHECKIN_ASSET,
                        status=AuditStatus.FAILED,
                        message=f"Equipment checkin assets failed: {e}",
                        user_id=current_user.id,
                        username=current_user.username,
                        target_username=target_username,
                        target_registration=registration,
                        resource=registration,
                        ip_address=req.client.host if req.client else None,
                        user_agent=req.headers.get("user-agent"),
                    ),
                )
            logger.error(f"Unexpected error checking {asset_tag}: {e}")

    return any_success, generated_terms
