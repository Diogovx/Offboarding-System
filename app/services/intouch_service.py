from http import HTTPStatus

import requests
from logging import getLogger
from app.config import settings
from app.schemas import (
    InTouchUserSearchModel,
    InTouchActivateUserModel,
    InTouchDeactivateUserModel
)

logger = getLogger("uvcorn.error")

ACTIVE_STATUSES = {"activated"}

DEACTIVE_STATUSES = {"activated"}

DELETABLE_STATUSES = {"pending", "created", "invited"}

PROTECTED_STATUSES = {"contact", "deactivated"}


def _get_headers(content_type: str | None = None) -> dict:
    headers = {"Authorization": f"Basic {settings.INTOUCH_TOKEN}"}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _validate_config() -> dict | None:
    if not settings.INTOUCH_TOKEN:
        return {"success": False, "error": "InTouch token not configured"}
    if not settings.INTOUCH_URL:
        return {"success": False, "error": "InTouch URL not configured"}
    return None


def search_user(registration: str) -> InTouchUserSearchModel:
    logger.info(f"Searching InTouch user: {registration}")

    if err := _validate_config():
        return InTouchUserSearchModel(error=str(err), registration="")

    filter = f'profile.employeeid eq "{registration}"'

    try:
        response = requests.get(
            settings.INTOUCH_URL,
            params={"filter": filter},
            headers=_get_headers(),
            timeout=10
        )
    except requests.RequestException as e:
        logger.error(f"Intouch connection error: {e}")
        return InTouchUserSearchModel(
            success=False,
            error=f"Connection error: {str(e)}"
        )

    if response.status_code != HTTPStatus.OK:
        return InTouchUserSearchModel(
            success=False,
            details=response.text,
            error=f"Staffbase API Error: {response.status_code}"
        )

    json_res = response.json()

    if isinstance(json_res, dict) and 'data' in json_res:
        list_users = json_res['data']
    elif isinstance(json_res, list):
        list_users = json_res
    else:
        list_users = []

    if not list_users:
        return InTouchUserSearchModel(
            success=False,
            found=False,
            error="User not found."
        )

    raw_user = list_users[0]
    status = raw_user.get('status')
    first_name = raw_user.get('firstName', '')
    last_name = raw_user.get('lastName', '')
    full_name = f"{first_name} {last_name}".strip()

    return InTouchUserSearchModel(
        success=True,
        found=True,
        id_system=raw_user.get('id'),
        name=full_name,
        email=raw_user.get('profile', {}).get('workemail'),
        role=raw_user.get('position'),
        current_status=status,
        is_active=status in ACTIVE_STATUSES,
        registration=registration,
    )


async def activate_user_intouch(registration: str) -> InTouchActivateUserModel:

    logger.info(f"Activating InTouch user: {registration}")

    if err := _validate_config():
        return InTouchActivateUserModel(error=str(err))

    data = search_user(registration)
    if not data or not data.success:
        return InTouchActivateUserModel(success=False, error="User not found.")

    user_id = data.id_system
    name = data.name
    status = data.current_status

    if status in ACTIVE_STATUSES:
        return InTouchActivateUserModel(
            success=True,
            action="none",
            message=f"{name} is already active"
    )

    if status != "deactivated":
        return InTouchActivateUserModel(
            success=False,
            error=f"Status '{status}' does not allow automatic reactivation"
        )

    url_update = f"{settings.INTOUCH_URL}/{user_id}"
    payload = {"status": "activated"}
    headers_update = {
        "Authorization": f"Basic {settings.INTOUCH_TOKEN}",
        "Content-Type": (
            "application/vnd.staffbase.accessors.user-update.v1+json"
        )
    }

    try:
        resp = requests.put(
            url_update,
            json=payload,
            headers=headers_update,
            timeout=10
        )

        if resp.status_code in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
            return InTouchActivateUserModel(
                success=True,
                message=f"User {name} was successfully renewed.",
                action="Activation"
            )
        return InTouchActivateUserModel(
            success=False,
            error=(
            "Error in the Staffbase API when activating: "
            f"{resp.text}"
            )
        )
    except Exception as e:
        return InTouchActivateUserModel(
            success=False,
            error=f"Connection error: {str(e)}"
        )


async def deactivate_user_intouch(registration: str) -> InTouchDeactivateUserModel:

    logger.info(f"Deactivating InTouch user: {registration}")

    if err := _validate_config():
        return InTouchDeactivateUserModel(error=str(err))

    data = search_user(registration)
    if not data or not data.success:
        return InTouchDeactivateUserModel(success=False, error="User not found.")

    user_id = data.id_system
    name = data.name
    status = data.current_status

    logger.info(f" Current status: '{status}'")

    try:
        if status in DEACTIVE_STATUSES:
            logger.info(" Active user. Changing status to DEACTIVATED.")

            url_update = f"{settings.INTOUCH_URL}/{user_id}"
            payload = {"status": "deactivated"}
            headers_update = {
                "Authorization": f"Basic {settings.INTOUCH_TOKEN}",
                "Content-Type": (
                    "application/vnd.staffbase.accessors.user-update.v1+json"
                )
            }

            resp = requests.put(
                url_update,
                json=payload,
                headers=headers_update,
                timeout=10
            )
            if resp.status_code in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
                return InTouchDeactivateUserModel(
                    success=True,
                    action="deactivated",
                    message=f"User {name} was successfully deactivated.",
                )
            return InTouchDeactivateUserModel(
                        success=False,
                        error=f"Error during deactivation: {resp.text}"
            )
        if status in DELETABLE_STATUSES:
            resp = requests.delete(
                f"{settings.INTOUCH_URL}/{user_id}",
                headers=_get_headers(),
                timeout=10,
            )
            if resp.status_code in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
                return InTouchDeactivateUserModel(
                    success=True,
                    action="deleted",
                    message=f"Invitation for {name} deleted"
                )
            return InTouchDeactivateUserModel(
                success=False,
                error=f"Deletion error: {resp.text}"
            )

        if status in PROTECTED_STATUSES:
            return InTouchDeactivateUserModel(
                success=True,
                action="skipped",
                message=f"{name} is '{status}' - no action needed",
            )

        return InTouchDeactivateUserModel(
            success=False,
            error=f"Unknown: '{status}' - operation canceled for safety",
        )

    except requests.RequestException as e:
        return InTouchDeactivateUserModel(
            success=False,
            error=f"Connection error: {str(e)}"
        )

    except Exception as e:
        return InTouchDeactivateUserModel(success=False, error=str(e))
