from fastapi import HTTPException, status, Depends, APIRouter
from subprocess import run, PIPE, STDOUT
import json
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ADUser
from app.models import ADUser
router = APIRouter(
    prefix="aduser",
    tags=["ADUser"]
)

@router.get("/aduser", response_model=list[ADUser])
async def get_user(username: str | None = None, session: Session = Depends(get_db)):
    if not username:
        filter_str = "*"
    else:
        safe_username = username.replace('"', '\"')
        filter_str = f"Name -like '*{safe_username}*'"
    
    command_args = [
        "powershell.exe",
        "-NonInteractive",
        "-Command",
        f"Get-AdUser -Filter \"{filter_str}\" -Properties SamAccountName,Name,Enabled | ConvertTo-Json -Compress"
    ]
    
    command_output = run(command_args, stdout=PIPE, stderr=STDOUT)
    
    output_string = command_output.stdout.decode('utf-8', errors='ignore').strip()
    
    try:
        json_data = json.loads(output_string)
        
        if isinstance(json_data, dict):
            users_list = [json_data]
        elif isinstance(json_data, list):
            users_list = json_data
        else:
            users_list = []
        
        return [ADUser.model_validate(user) for user in users_list]
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar Active Directory."
        )
        