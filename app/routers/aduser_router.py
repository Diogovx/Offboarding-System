from fastapi import HTTPException, status, Depends, APIRouter
from subprocess import run, PIPE, STDOUT
import json
from sqlalchemy.orm import Session
from app.models import ADUser, DisableUserRequest
from app.security import get_current_user, require_editor

router = APIRouter(prefix="/aduser", tags=["ADUser"])


@router.get("/", response_model=list[ADUser])
async def get_user(
    registration: str | None = None,
    session: Session = Depends(get_current_user),
):
    if not registration:
        filter_str = "*"
    else:
        safe_registration = registration.replace('"', '"')
        filter_str = f"Description -like '*{safe_registration}*'"

    command_args = [
        "powershell.exe",
        "-NonInteractive",
        "-Command",
        f'Get-AdUser -Filter "{filter_str}" -Properties SamAccountName,Name,Enabled,Description,DistinguishedName | ConvertTo-Json -Compress',
    ]

    command_output = run(command_args, stdout=PIPE, stderr=STDOUT)

    output_string = command_output.stdout.decode(
        "utf-8", errors="ignore"
    ).strip()

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
            detail="Erro ao consultar Active Directory.",
        )


@router.post("/disable")
async def disable_user(
    payload: DisableUserRequest, session: Session = Depends(require_editor)
):
    filter_str = f"Description -like '*{payload.registration}*'"

    ps_lookup = f"""
        $user = Get-ADUser -Filter "{filter_str}" -Properties SamAccountName,Name,Enabled,Description,DistinguishedName
        if (!$user) {{
            Write-Error "Usuário não encontrado pela matrícula."
            exit 1
        }}
        $user | ConvertTo-Json -Compress
    """

    lookup_cmd = ["powershell.exe", "-NonInteractive", "-Command", ps_lookup]

    lookup_result = run(lookup_cmd, stdout=PIPE, stderr=STDOUT)
    lookup_output = lookup_result.stdout.decode(
        "utf-8", errors="ignore"
    ).strip()

    try:
        user_data = json.loads(lookup_output)
    except Exception:
        raise HTTPException(
            status_code=500, detail=f"Erro retornado pelo AD: {lookup_output}"
        )

    distinguished_name = user_data["DistinguishedName"]
    old_description = user_data.get("Description", "")

    new_description = f"{old_description} | Desativado por {payload.performed_by} (Sistema Dismissal Assistant)"

    ps_action = (
        f'Disable-ADAccount -Identity "{distinguished_name}";'
        f'Set-ADUser -Identity "{distinguished_name}" -Description "{new_description}";'
        f'Move-ADObject -Identity "{distinguished_name}" '
        f'-TargetPath "OU=CONTAS DESATIVADAS,OU=Usurios,OU=CLADTEK DO BRASIL - Office RJ,DC=cladtekbr,DC=local";'
        f'Write-Output \'{{"status":"success","user":"{payload.registration}"}}\''
    )

    action_cmd = ["powershell.exe", "-NonInteractive", "-Command", ps_action]

    result = run(action_cmd, stdout=PIPE, stderr=STDOUT)
    output = result.stdout.decode("utf-8", errors="ignore").strip()

    try:
        return json.loads(output)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao desativar/mover o usuário: {output}",
        )
