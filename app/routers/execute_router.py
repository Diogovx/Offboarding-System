from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from app.security import Current_user, Db_session 
from app.services.execute_service import execute_offboarding

router = APIRouter(prefix="/offboarding", tags=["offboarding"])

@router.post("/execute/{registration}")
async def execute(
    registration: str,
    current_user: Current_user,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Db_session
):
   
    resultado = await execute_offboarding(
        registration=registration,
        current_user=current_user,
        background_tasks=background_tasks,
        req=request, 
        db=db
    )
    
    return resultado