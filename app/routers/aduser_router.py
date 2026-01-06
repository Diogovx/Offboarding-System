import json
from subprocess import PIPE, STDOUT, run

from fastapi import APIRouter, HTTPException, status

from app.models import ADUser, DisableUserRequest
from app.security import (
    Current_user,
    Editor_user,
)

router = APIRouter(prefix="/aduser", tags=["ADUser"])


@router.get("/", response_model=list[ADUser])
async def get_user(
    session: Current_user,
    registration: str | None = None,
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
        f'''Get-AdUser -Filter "{filter_str}"
        -Properties SamAccountName,Name,Enabled,Description,DistinguishedName
        | ConvertTo-Json -Compress''',
    ]

    command_output = run(command_args, check=False, stdout=PIPE, stderr=STDOUT)

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
    payload: DisableUserRequest, session: Editor_user
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

    lookup_result = run(lookup_cmd, check=False, stdout=PIPE, stderr=STDOUT)
    lookup_output = lookup_result.stdout.decode(
        "utf-8", errors="ignore"
    ).strip()

    try:
        user_data = json.loads(lookup_output)
    except Exception:
        raise HTTPException(
            status_code=500, detail=f"Erro retornado pelo AD: {lookup_output}"
        )

    sam = user_data["SamAccountName"]
    old_description = user_data.get("Description", "")

    new_description = f"""{old_description} | Desativado por {payload.performed_by} (Sistema Dismissal Assistant)"""

    ps_action = f"""
    $ErrorActionPreference = "Stop"

    $identity = "{sam}"

    Disable-ADAccount -Identity $identity
    Set-ADUser -Identity $identity -Description "{new_description}"

    $dn = (Get-ADUser -Identity $identity).DistinguishedName
    Move-ADObject -Identity $dn -TargetPath "OU=CONTAS DESATIVADAS,OU=Usuários,OU=CLADTEK DO BRASIL - Office RJ,DC=cladtekbr,DC=local"


    Write-Output '{{"status":"success","user":"{payload.registration}"}}'
    """

    action_cmd = ["powershell.exe", "-NonInteractive", "-Command", ps_action]

    result = run(action_cmd, check=False, stdout=PIPE, stderr=STDOUT)
    output = result.stdout.decode("utf-8", errors="ignore").strip()

    try:
        return json.loads(output)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao desativar/mover o usuário: {output}",
        )
