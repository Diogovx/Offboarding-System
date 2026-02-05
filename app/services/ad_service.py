from app.models import ADUser, DisableUserRequest
from app.security import get_ldap_connection
from app.security.security import settings
from fastapi import HTTPException, status
from ldap3 import MODIFY_REPLACE


def search_aduser(registration: str | None = None):
    conn = get_ldap_connection()

    if registration:
        search_filter = (
            f"(&(objectClass=user)"
            f"(description=*{registration}*))"
        )
    else:
        search_filter = (
            "(&(objectClass=user)"
            "(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
        )

    conn.search(
        settings.AD_BASE_DN,
        search_filter,
        attributes=[
            "cn",
            "displayName",
            "sAMAccountName",
            "description",
            "userAccountControl",
            "distinguishedName",
        ],
    )
    return conn.entries


def disable_aduser(payload: DisableUserRequest):
    conn = get_ldap_connection()

    entries = search_aduser(payload.registration)

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found by registration number."
        )

    if len(entries) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="More than one user was found with the same registration number."
        )

    entry = entries[0]

    dn = entry.distinguishedName.value
    old_description = entry.description.value or ""

    new_description = (
        f"{old_description} | "
        f"Disabled by {payload.performed_by} "
        f"(Offboarding System)"
    )

    uac = int(entry.userAccountControl.value)
    new_uac = uac | 2

    conn.modify(
        dn,
        {
            "userAccountControl": [(MODIFY_REPLACE, [new_uac])],
            "description": [(MODIFY_REPLACE, [new_description])],
        },
    )

    if not conn.result["description"] == "success":
        raise HTTPException(
            status_code=500,
            detail=f"Error deactivating user: {conn.result}"
        )

    rdn = dn.split(",", 1)[0]
    target_ou = settings.DISABLED_OU

    conn.modify_dn(
        dn,
        rdn,
        new_superior=target_ou,
    )

    if not conn.result["description"] == "success":
        raise HTTPException(
            status_code=500,
            detail=f"Error moving user: {conn.result}"
        )


def ldap_entry_to_ad_user(entry) -> ADUser:
    uac = int(entry.userAccountControl.value)

    return ADUser(
        name=entry.displayName.value or entry.cn.value,
        sam_account_name=entry.sAMAccountName.value,
        enabled=not bool(uac & 2),
        distinguished_name=entry.distinguishedName.value,
        description=entry.description.value
            if "description" in entry else None
    )
