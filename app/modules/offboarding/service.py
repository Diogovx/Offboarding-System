import asyncio

from logging import getLogger
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.concurrency import run_in_threadpool
import httpx
import base64
from app.core.database import Db_session
from sqlalchemy import select, func
from app.modules.audit.service import create_audit_log, AuditLogCreate
from app.modules.audit.enums import AuditAction, AuditStatus
from app.modules.shared import (
    EmailActions
)
from .model import (
    OffboardingRecord,
    RevokedAccess,
)
from app.integrations.active_directory import DisableUserRequest, ADService
from app.integrations.gate import deactivate_user_turnstiles
from app.integrations.intouch import service as intouch_service
from app.modules.shared import email_service
from .schemas import (
    OffboardingContext
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
    registration: str,
    snipeit_service,
) -> dict[str, bool]:
    service_map: dict[str, bool] = {}
    ad_service = ADService()

    task_ad = run_in_threadpool(
        ad_service.search_users,
        registration=registration
    )
    task_intouch = run_in_threadpool(
        intouch_service.search_user,
        registration=registration
    )
    task_snipeit = snipeit_service.search_assets_by_user(registration)

    try:
        results = await asyncio.wait_for(
            asyncio.gather(task_ad, task_intouch, task_snipeit),
            timeout=10.0
        )
        ad_response, intouch_data, snipeit_assets = results
    except asyncio.TimeoutError:
        logger.error(f"Timeout: The search for services took more than 10 seconds.")
        raise HTTPException(
            status_code=504,
            detail="External systems (AD or InTouch) are taking too long to respond. Please try again in a few moments."
        )

    if not isinstance(ad_response, Exception) and ad_response and len(ad_response) > 0:
        service_map['Rede'] = bool(ad_response[0].enabled)

    if not isinstance(intouch_data, Exception) and intouch_data and intouch_data.success:
        service_map["InTouch"] = bool(intouch_data.is_active)

    # Verifica se a resposta do Snipe-IT não foi um erro e se tem ativos
    if not isinstance(snipeit_assets, Exception) and snipeit_assets:
        service_map["Equipamentos"] = True
    else:
        service_map["Equipamentos"] = False

    # TODO Turnstile
    # add Turnstile threadpool later

    logger.info(f"Active services for {registration}: {service_map}")
    return service_map


def _audit(
    *,
    session,
    action,
    status,
    message,
    current_user,
    registration,
    target_username,
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
            target_username=target_username,
            target_registration=registration,
            resource=registration,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ),
    )


async def execute_offboarding(
    registration: str,
    current_user,
    ad_service,
    snipeit_service,
    background_tasks,
    req: Request,
    session: Db_session
):

    target_user = await run_in_threadpool(intouch_service.search_user, registration)

    if not target_user:
        logger.error(f"Offboarding abortado: Registration {registration} not found")
        return {"success": False, "error": "User not found"}

    services_map = await verify_services_before_disabling(registration, snipeit_service)
    successfully_revoked: list[str] = []

    # LISTA PARA GUARDAR OS TERMOS GERADOS
    generated_terms = []

    name_user_taget = target_user.name

    try:
        current_date = datetime.now().strftime("%Y%m%d")
        format_name = target_user.name.replace(" ", "_")
        filename = f"{registration}_{format_name}_{current_date}.docx"

        assets = await snipeit_service.search_assets_by_user(registration)

        if assets:
            template_id = await snipeit_service.get_template_id_by_type("checkin")

            for asset in assets:
                asset_tag = asset.get("asset_tag")

                # Gera o documento DOCX
                termo_bytes = await snipeit_service.generate_term(
                    employee_num=registration,
                    template_id=template_id,
                    asset_tag=asset_tag
                )
                
                # Converte os bytes do DOCX para Base64 (Texto seguro para trafegar no JSON)
                termo_b64 = base64.b64encode(termo_bytes).decode("utf-8")
                
                # Adiciona na lista de termos gerados
                generated_terms.append({
                    "filename": filename,
                    "content_base64": termo_b64
                })
                
                logger.info(f"Termo de devolução gerado para o ativo {asset_tag}.")
                
                # Faz a devolução no sistema
                await snipeit_service.checkin_asset(registration, asset_tag, note="Offboarding Automático")

            successfully_revoked.append("Equipamentos")
            
    except ValueError as ve:
        logger.warning(f"Snipe-IT aviso: {ve}")
    except httpx.HTTPStatusError as he:
        logger.error(f"Falha na API do Snipe-IT: {he.response.text}")
    except Exception as e:
        logger.error(f"Snipe-IT erro inesperado para {registration}: {e}")

    if services_map.get("Turnstiles") is True:
        try:
            res_turnstiles = await (
                deactivate_user_turnstiles(
                    registration=registration
                )
            )
            if res_turnstiles.get("success"):
                successfully_revoked.append("Acesso")

                _audit(
                    session=session,
                    action=AuditAction.DISABLE_TURNSTILE_USER,
                    status=AuditStatus.SUCCESS,
                    message=f"User {registration} blocked in all turnstiles.",
                    current_user=current_user,
                    target_username=target_user.name,
                    registration=registration,
                    req=req
                )
        except Exception as e:
            _audit(
                session=session,
                action=AuditAction.DISABLE_TURNSTILE_USER,
                status=AuditStatus.FAILED,
                message=f"Turnstile deactivation failed: {e}",
                current_user=current_user,
                target_username=target_user.name,
                registration=registration,
                req=req
            )

    if services_map.get("InTouch") is True:
        try:
            res = await intouch_service.deactivate_user_intouch(registration)
            if res.success:
                successfully_revoked.append("InTouch")
                _audit(
                    session=session,
                    action=AuditAction.DISABLE_INTOUCH_USER,
                    status=AuditStatus.SUCCESS,
                    message=f"InTouch: {res.message}",
                    current_user=current_user,
                    target_username=target_user.name,
                    registration=registration,
                    req=req
                )
            else:
                
                _audit(
                    session=session,
                    action=AuditAction.DISABLE_INTOUCH_USER,
                    status=AuditStatus.FAILED,
                    message=f"InTouch: {res.error}",
                    current_user=current_user,
                    target_username=target_user.name,
                    registration=registration,
                    req=req
                )
        except Exception as e:
            logger.error(f"InTouch error for {registration}: {e}")
            _audit(
                session=session,
                action=AuditAction.DISABLE_INTOUCH_USER,
                status=AuditStatus.FAILED,
                message=f"InTouch deactivation failed: {e}",
                current_user=current_user,
                target_username=target_user.name,
                registration=registration,
                req=req
            )

    if services_map.get("Rede") is True:
        try:
            payload_ad = DisableUserRequest(
                registration=registration,
                performed_by=current_user.username,
            )
            res_ad = await run_in_threadpool(ad_service.disable_user, payload_ad)
            if res_ad.action == "disabled":
                successfully_revoked.append("Rede")
                _audit(
                    session=session,
                    action=AuditAction.DISABLE_AD_USER,
                    status=AuditStatus.SUCCESS,
                    message=f"User {registration} deactivated from AD.",
                    current_user=current_user,
                    target_username=target_user.name,
                    registration=registration,
                    req=req
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
                session=session,
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.FAILED,
                message=f"AD deactivation failed: {e}",
                current_user=current_user,
                target_username=target_user.name,
                registration=registration,
                req=req
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
            record_offboarding(session, context)
        except Exception as e:
            logger.error(f"Failed to record offboarding history for {registration}: {e}")

        action_email = EmailActions.get_by_id(3)
        background_tasks.add_task(
            email_service.send_email,
            registration=registration,
            action=action_email,
            user_target=name_user_taget,
            performed_by=str(current_user.username),
            systems_list=successfully_revoked,
        )

        # RETORNA O SUCESSO E A LISTA DE TERMOS EM BASE64
        return {
            "success": True, 
            "details": successfully_revoked,
            "terms": generated_terms 
        }
