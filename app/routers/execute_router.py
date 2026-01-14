from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.security.deps import Current_user
from app.services.execute_service import execute_offboarding

router = APIRouter(prefix="/offboarding", tags=["offboarding"])

@router.post("/execute/{registration}")
async def execute(
    registration: str, 
    current_user: Current_user,
    background_tasks: BackgroundTasks,

):
    resultado = await execute_offboarding(
    registration, 
    current_user, 
    background_tasks
    )    
    if not resultado["success"]:
        raise HTTPException(status_code=400, detail=resultado["error"])
   
    return resultado