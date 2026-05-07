# app/modules/offboarding/service.py

import asyncio
import logging

from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import Db_session
from app.integrations.active_directory import ADService
from app.integrations.intouch import service as intouch_service
from app.integrations.snipe_it import SnipeItService
from app.modules.shared import EmailActions, email_service

from .enums import OffboardingSystem
from .repository import create_offboarding_record, get_offboarding_history
from .schemas import (
    OffboardingContext,
    OffboardingHistoryResponse,
    OffboardingResult,
)
from .use_cases.checkin_assets import checkin_assets
from .use_cases.disable_intouch_access import disable_intouch_access
from .use_cases.disable_ad_access import disable_ad_account
from .use_cases.disable_gateway_access import disable_gateway_access

logger = logging.getLogger(__name__)


async def verify_services(
    registration: str,
    snipeit_service: SnipeItService,
) -> dict[str, bool]:
    """Checks which external systems have an active record for the given user.

    Runs AD, InTouch, and Snipe-IT lookups concurrently with a shared timeout.

    Args:
        registration (str): Employee registration number to search across systems.
        snipeit_service (SnipeItService): Snipe-IT service instance.

    Returns:
        dict[str, bool]: Map of system name to active status.

    Raises:
        HTTPException: 504 if external systems exceed the 10-second timeout.
    """
    ad_service = ADService()

    try:
        ad_response, intouch_data, snipeit_assets = await asyncio.wait_for(
            asyncio.gather(
                run_in_threadpool(ad_service.search_users, registration=registration),
                run_in_threadpool(intouch_service.search_user, registration=registration),
                snipeit_service.search_assets_by_user(registration),
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.error("Timeout: service lookup exceeded 10 seconds.")
        raise HTTPException(
            status_code=504,
            detail="External systems are taking too long to respond. Please try again.",
        )

    service_map: dict[str, bool] = {}

    if not isinstance(ad_response, Exception) and ad_response:
        service_map[OffboardingSystem.NETWORK] = bool(ad_response[0].enabled)

    if not isinstance(intouch_data, Exception) and intouch_data and intouch_data.success:
        service_map[OffboardingSystem.INTOUCH] = bool(intouch_data.is_active)

    service_map[OffboardingSystem.EQUIPMENT] = (
        not isinstance(snipeit_assets, Exception) and bool(snipeit_assets)
    )

    logger.info(f"Active services for {registration}: {service_map}")
    return service_map


async def execute_offboarding(
    *,
    registration: str,
    current_user,
    ad_service: ADService,
    snipeit_service: SnipeItService,
    background_tasks,
    req: Request,
    session: Session,
) -> OffboardingResult:
    """Orchestrates the full offboarding process for a given employee.

    Sequentially attempts to revoke access across all active systems.
    Each step is independent — a failure in one does not abort the others.
    Persists a record of successfully revoked systems and sends a notification email.

    Args:
        registration (str): Employee registration number to offboard.
        current_user: Authenticated user performing the operation.
        ad_service (ADService): Active Directory service instance.
        snipeit_service (SnipeItService): Snipe-IT service instance.
        background_tasks: FastAPI BackgroundTasks for async email dispatch.
        req (Request): FastAPI request object for audit metadata extraction.
        session (Session): Active SQLAlchemy database session.

    Returns:
        OffboardingResult: Result containing success status, revoked systems, and generated terms.
    """
    target_user = await run_in_threadpool(intouch_service.search_user, registration)

    if not target_user:
        logger.error(f"Offboarding aborted: registration {registration} not found.")
        return OffboardingResult(success=False, error="User not found.")

    services_map = await verify_services(registration, snipeit_service)
    successfully_revoked: list[str] = []
    generated_terms = []

    shared = dict(
        registration=registration,
        current_user=current_user,
        target_username=target_user.name,
        session=session,
        req=req,
    )

    # Equipment — generate terms and checkin assets
    if services_map.get(OffboardingSystem.EQUIPMENT):
        success, terms = await checkin_assets(
            registration=registration,
            target_name=target_user.name,
            snipeit_service=snipeit_service,
        )
        if success:
            successfully_revoked.append(OffboardingSystem.EQUIPMENT)
            generated_terms.extend(terms)

    # Gate access
    if services_map.get(OffboardingSystem.ACCESS):
        if await disable_gateway_access(**shared):  # type: ignore
            successfully_revoked.append(OffboardingSystem.ACCESS)

    # InTouch
    if services_map.get(OffboardingSystem.INTOUCH):
        if await disable_intouch_access(**shared):  # type: ignore
            successfully_revoked.append(OffboardingSystem.INTOUCH)

    # Active Directory — last, intentionally
    if services_map.get(OffboardingSystem.NETWORK):
        if await disable_ad_account(**shared, ad_service=ad_service):  # type: ignore
            successfully_revoked.append(OffboardingSystem.NETWORK)

    if successfully_revoked:
        try:
            create_offboarding_record(
                session,
                OffboardingContext(
                    user_id=current_user.id,
                    username=target_user.name,
                    registration=registration,
                    performed_by=current_user.username,
                    systems=successfully_revoked,
                ),
            )
        except Exception as e:
            logger.error(f"Failed to persist offboarding record for {registration}: {e}")

        background_tasks.add_task(
            email_service.send_email,
            registration=registration,
            action=EmailActions.get_by_id(3),
            user_target=target_user.name,
            performed_by=str(current_user.username),
            systems_list=successfully_revoked,
        )

    return OffboardingResult(
        success=bool(successfully_revoked),
        details=successfully_revoked,
        terms=[t.model_dump() for t in generated_terms],
    )


def fetch_offboarding_history(
    session: Db_session,
    *,
    registration: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> OffboardingHistoryResponse:
    """Retrieves paginated offboarding history, delegating to the repository layer.

    Args:
        session (Db_session): Active SQLAlchemy database session.
        registration (str | None): Optional registration number filter.
        page (int): Page number, starting at 1.
        limit (int): Maximum records per page.

    Returns:
        OffboardingHistoryResponse: Paginated offboarding history.
    """
    return get_offboarding_history(
        session,
        registration=registration,
        page=page,
        limit=limit,
    )
