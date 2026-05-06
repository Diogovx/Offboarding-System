from fastapi import APIRouter, BackgroundTasks, Request, Query, HTTPException, Depends, Response
from app.core.database import Db_session
from app.core import Current_user
from app.integrations.active_directory import ADServiceDep
from .service import (
    execute_offboarding,
    get_offboarding_history,
    verify_services_before_disabling
)
from app.integrations.snipe_it import GenerateTermRequest, SnipeItService, get_snipeit_service, CheckinAssetRequest

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


@router.get("/search/{registration}")
async def search_services(
    registration: str,
    current_user: Current_user,
    snipeit: SnipeItService = Depends(get_snipeit_service),
) -> dict[str, bool]:

    return await verify_services_before_disabling(registration, snipeit)


@router.post("/execute/{registration}")
async def execute(
    registration: str,
    current_user: Current_user,
    background_tasks: BackgroundTasks,
    ad_service: ADServiceDep,
    request: Request,
    session: Db_session,
    snipeit_service: SnipeItService = Depends(get_snipeit_service)
):

    result = await execute_offboarding(
        registration=registration,
        current_user=current_user,
        background_tasks=background_tasks,
        ad_service=ad_service,
        snipeit_service=snipeit_service,
        req=request,
        session=session
    )

    return result


@router.get("/history")
def list_offboarding_history(
    session: Db_session,
    _: Current_user,
    registration: str | None = Query(default=None, description="Filtrer by registration"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return get_offboarding_history(
        db=session,
        registration=registration,
        page=page,
        limit=limit,
    )


@router.post("/generate-term")
async def download_term(
    request: GenerateTermRequest,
    snipeit: SnipeItService = Depends(get_snipeit_service)
):
    try:
        docx_bytes = await snipeit.generate_term(
            employee_num=request.employee_num,
            asset_tag=request.asset_tag,
            template_id=request.template_id
        )

        filename = f"termo_{request.employee_num}_{request.asset_tag}.docx"
        docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        return Response(
            content=docx_bytes,
            media_type=docx_mime,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar o termo: {str(e)}"
        )
# Lembre-se de importar o seu schema e o get_snipeit_service
# from app.modules.snipe_it.schemas import CheckinAssetRequest
# from app.modules.snipe_it.service import SnipeItService, get_snipeit_service

@router.post("/checkin")
async def checkin_asset(
    payload: CheckinAssetRequest,
    snipeit: SnipeItService = Depends(get_snipeit_service)
):
    try:
        # Chama a função do serviço passando os dados validados pelo Pydantic
        result = await snipeit.checkin_asset(
            registration=payload.registration,
            asset_tag=payload.asset_tag,
            note=payload.note
        )

        # Retorna o sucesso e os dados que a API do Snipe-IT devolveu
        return {
            "success": True,
            "message": f"Ativo {payload.asset_tag} devolvido com sucesso.",
            "data": result
        }

    except ValueError as ve:
        # Captura erros de validação (ex: usuário ou ativo não encontrado)
        raise HTTPException(status_code=404, detail=str(ve))

    except Exception as e:
        # Captura erros de conexão ou falhas internas da API do Snipe-IT
        raise HTTPException(
            status_code=500, detail=f"Erro interno ao fazer checkin: {str(e)}"
        )
