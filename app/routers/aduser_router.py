import json
from subprocess import PIPE, STDOUT, run

from fastapi import APIRouter, HTTPException, Request, status

from app.audit.audit_log_service import create_audit_log
from app.enums import AuditAction, AuditStatus
from app.models import ADUser, DisableUserRequest
from app.schemas import AuditLogCreate
from app.security import Current_user, Db_session

router = APIRouter(prefix="/aduser", tags=["ADUser"])


@router.get("/", response_model=list[ADUser])
async def get_user(
    session: Current_user,
    request: Request,
    db: Db_session,
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
        f'''Get-AdUser -Filter "{filter_str}" -Properties SamAccountName,Name,Enabled,Description,DistinguishedName | ConvertTo-Json -Compress''',
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

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.SUCCESS,
                message="User research conducted",
                user_id=session.id,
                username=session.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

        return [ADUser.model_validate(user) for user in users_list]
    except json.JSONDecodeError:
        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.FAILED,
                message=f"Invalid JSON returned by AD: {output_string}",
                user_id=session.id,
                username=session.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying Active Directory.",
        )


@router.post("/disable")
async def disable_user(
    payload: DisableUserRequest,
    session: Current_user,
    request: Request,
    db: Db_session
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
        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.SUCCESS,
                message="User deactivated and moved successfully.",
                user_id=session.id,
                username=session.username,
                resource=payload.registration,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

        return json.loads(output)
    except Exception:
        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.FAILED,
                message=f"Failed to deactivate user: {output}",
                user_id=session.id,
                username=session.username,
                resource=payload.registration,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while disabling/moving the user: {output}",
        )
