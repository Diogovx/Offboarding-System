from fastapi import Request
from logging import getLogger
from app.database import Db_session
from sqlalchemy import select, func
from app.audit.audit_log_service import create_audit_log
from app.enums import AuditAction, AuditStatus, EmailActions
from app.models import (
    DisableUserRequest,
    OffboardingRecord,
    RevokedAccess,
)
from app.schemas import AuditLogCreate, OffboardingContext, InTouchUserSearchModel
from app.services import (
    email_service,
    intouch_service,
    turnstiles_service,
    ADService
)


logger = getLogger("uvcorn.error")


def record_offboarding(
    session: Db_session,
    context: OffboardingContext
) -> OffboardingRecord:
    record = OffboardingRecord(
        user_id=context.user_id,
        username=context.username,
        registration=context.registration,
        performed_by_username=context.performed_by,
    )  # type: ignore[call-arg]
    session.add(record)
    session.flush()

    for system in context.systems:
        session.add(
            RevokedAccess(offboarding_id=record.id, system_name=system)  # type: ignore[call-arg]
        )

    session.commit()
    session.refresh(record)
    return record


def get_offboarding_history(
    db: Db_session,
    *,
    registration: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Retorna o histórico de offboardings, opcionalmente filtrado por matrícula.
    """

    stmt = (
        select(OffboardingRecord)
        .order_by(OffboardingRecord.offboarded_at.desc())
    )

    if registration:
        stmt = stmt.where(OffboardingRecord.registration == registration)

    total = db.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()
    records = db.execute(
        stmt.offset((page - 1) * limit).limit(limit)
    ).scalars().all()

    return {
        "items": [_serialize_record(r) for r in records],
        "total": total,
        "page": page,
        "pages": max(1, -(-total // limit)),
    }


def _serialize_record(record: OffboardingRecord) -> dict:
    return {
        "id": str(record.id),
        "username": record.username,
        "registration": record.registration,
        "offboarded_at": record.offboarded_at.isoformat(),
        "performed_by": record.performed_by_username,
        "revoked_systems": [a.system_name for a in record.revoked_accesses],
    }


async def verify_services_before_disabling(
    registration: str
) -> dict[str, bool]:
    service_map: dict[str, bool] = {}
    ad_service = ADService()

    ad_response = ad_service.search_users(registration=registration)
    if ad_response and len(ad_response) > 0:
        ad_user = ad_response[0]
        enabled = ad_user.enabled
        service_map['Rede'] = bool(enabled)

    intouch_data = intouch_service.search_user(registration=registration)
    if intouch_data and intouch_data.success:
        service_map["InTouch"] = bool(intouch_data.is_active)

    # TODO Turnstile

    logger.info(f"Active services for {registration}: {service_map}")
    return service_map


def _audit(
    session,
    action,
    status,
    message,
    current_user,
    registration,
    req
):
    create_audit_log(
        session,
        AuditLogCreate(
            action=action,
            status=status,
            message=message,
            user_id=current_user.id,
            username=current_user.username,
            resource=registration,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ),
    )


async def execute_offboarding(
    registration: str,
    current_user,
    ad_service,
    background_tasks,
    req: Request,
    session: Db_session
):
    target_user = intouch_service.search_user(registration)

    if not target_user:
        logger.error(
            f"Offboarding abortado: Regitration {registration} not found"
        )
        return {"success": False, "error": "User not found"}

    services_map = await verify_services_before_disabling(registration)

    successfully_revoked: list[str] = []

    if services_map.get("Turnstiles") is True:
        try:
            res_turnstiles = await (
                turnstiles_service.deactivate_user_turnstiles(
                    registration=registration
                )
            )
            if res_turnstiles.get("success"):
                successfully_revoked.append("Acesso")

                _audit(
                    session,
                    AuditAction.DISABLE_TURNSTILE_USER,
                    AuditStatus.SUCCESS,
                    f"User {registration} blocked in all turnstiles.",
                    current_user,
                    registration,
                    req
                )
        except Exception as e:
            _audit(
                session,
                AuditAction.DISABLE_TURNSTILE_USER,
                AuditStatus.FAILED,
                f"Turnstile deactivation failed: {e}",
                current_user,
                registration,
                req
            )

    if services_map.get("InTouch") is True:
        try:
            res = await intouch_service.deactivate_user_intouch(registration)
            if res.success:
                successfully_revoked.append("InTouch")
                _audit(
                    session,
                    AuditAction.DISABLE_INTOUCH_USER,
                    AuditStatus.SUCCESS,
                    f"InTouch: {res.message}",
                    current_user,
                    registration,
                    req
                )
            else:
                _audit(
                    session,
                    AuditAction.DISABLE_INTOUCH_USER,
                    AuditStatus.FAILED,
                    f"InTouch: {res.error}",
                    current_user,
                    registration,
                    req
                )
        except Exception as e:
            logger.error(f"InTouch error for {registration}: {e}")
            _audit(
                session,
                AuditAction.DISABLE_INTOUCH_USER,
                AuditStatus.FAILED,
                f"InTouch deactivation failed: {e}",
                current_user,
                registration,
                req
            )

    if services_map.get("Rede") is True:
        try:
            payload_ad = DisableUserRequest(
                registration=registration,
                performed_by=current_user.username,
            )
            res_ad = ad_service.disable_user(payload_ad)
            if res_ad.action == "disabled":
                successfully_revoked.append("Rede")
                _audit(
                    session,
                    AuditAction.DISABLE_AD_USER,
                    AuditStatus.SUCCESS,
                    f"User {registration} deactivated from AD.",
                    current_user,
                    registration,
                    req
                )
            elif res_ad.action == "already_disabled":
                successfully_revoked.append("Rede")
                logger.warning(
                    f"AD state mismatch for {registration}: "
                    "verify_services reported active but disable_user found already disabled. "
                    "Skipping audit log."
                )
        except Exception as e:
            logger.error(f"AD error for {registration}: {e}")
            _audit(
                session,
                AuditAction.DISABLE_AD_USER,
                AuditStatus.FAILED,
                f"AD deactivation failed: {e}",
                current_user,
                registration,
                req
            )

    if successfully_revoked:
        try:
            context = OffboardingContext(
                user_id=current_user.id,
                username=target_user.name,
                registration=registration,
                performed_by=current_user.username,
                systems=successfully_revoked,
            )
            record_offboarding(
                session,
                context
            )
        except Exception as e:
            logger.error(
                f"Failed to record offboarding history for {registration}: {e}"
            )

        action_email = EmailActions.get_by_id(3)
        background_tasks.add_task(
            email_service.send_email,
            registration=registration,
            action=action_email,
            performed_by=str(current_user.username),
            systems_list=successfully_revoked
        )

        return {"success": True, "details": successfully_revoked}
