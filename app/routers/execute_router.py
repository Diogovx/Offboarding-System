from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.security.deps import Current_user
from app.services.execute_service import execute_offboarding

router = APIRouter(prefix="/offboarding", tags=["offboarding"])

@router.post("/execute/{matricula}")
async def execute(
    matricula: str, 
    current_user: Current_user,
    background_tasks: BackgroundTasks,
    
):
    resultado = await execute_offboarding(
    matricula, 
    current_user, 
    background_tasks
    )
    
    if not resultado["success"]:
        raise HTTPException(status_code=400, detail=resultado["error"])
        
    return resultado