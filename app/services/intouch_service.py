from http import HTTPStatus

import requests

from app.security import Settings

settings = Settings()

HEADERS = {"Authorization": f"Basic {settings.INTOUCH_TOKEN}"}


def search_user(registration: str):
    services_list_view = []
    print(
        f" Searching for the user with the registration number: {registration}"
    )

    if not settings.INTOUCH_TOKEN:
        return {"erro": "Token not configured"}
    if not settings.INTOUCH_URL:
        return {"erro": "URL not configured"}

    filtro = f'profile.employeeid eq "{registration}"'

    try:
        response = requests.get(
            settings.INTOUCH_URL, params={"filter": filtro}, headers=HEADERS
        )

        if response.status_code != HTTPStatus.OK:
            return {
                "erro": f"Staffbase API Error: {response.status_code}",
                "success": False, "details": response.text
            }

        json_res = response.json()

        if isinstance(json_res, dict) and 'data' in json_res:
            list_users = json_res['data']
        elif isinstance(json_res, list):
            list_users = json_res
        else:
            list_users = []

        if not list_users:
            return {"success": False, "erro": "User not found."}

        raw_user = list_users[0]
        first_name = raw_user.get('firstName', '')
        surname = raw_user.get('lastName', '')
        full_name = f"{first_name} {surname}".strip()

        status_intouch = raw_user.get('status')

        if status_intouch == 'activated':
            services_list_view.append("Intouch")
            services_list_view.append("Acesso")
            services_list_view.append("Rede")

        return {
            "success": True,
            "found": True,
            "id_system": raw_user.get('id'),
            "name": full_name,
            "email": raw_user.get('profile', {}).get('workemail'),
            "role": raw_user.get('position'),
            "current_status": status_intouch,
            "registration": registration,
            "services": services_list_view
        }

    except Exception as e:
        return {"erro": str(e), "success": False}


async def activate_user_intouch(registration: str):

    print(f"Starting the enrollment process: {registration}")
    data = search_user(registration)

    if not data or not data.get('success'):
        return {"success": False, "error": "User not found."}

    user_id = data['id_system']
    name = data['name']
    current_status = data['current_status']

    print(f" Current_status: '{current_status}'")

    if current_status == 'deactivated':
        print(f" User deactivated. Changing status of {name} to activated.")

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
                headers=headers_update
            )

            if resp.status_code in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
                return {
                    "success": True,
                    "message": f"User {name} was successfully renewed.",
                    "acao": "Activation"
                }
            else:
                return {
                    "success": False,
                    "error": (
                        "Error in the Staffbase API when activating: "
                        f"{resp.text}"
                    )
                }
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    elif current_status == 'activated':
        return {
            "success": True,
            "message": f"User {name}: The user is already active.",
            "acao": "none"
        }

    else:
        return {
            "success": False,
            "error": (
                f"Status '{current_status}' does "
                "not allow automatic reactivation."
            )
        }


async def deactivate_user_intouch(registration: str):

    print(f" Starting the enrollment process: {registration}")

    data = search_user(registration)

    if not data or not data.get('success'):
        return {"success": False, "error": "User not found."}

    user_id = data['id_system']
    name = data['name']
    current_status = data['current_status']

    print(f" Current status: '{current_status}'")

    if current_status == 'activated':
        print(" Active user. Changing status to DEACTIVATED.")

        url_update = f"{settings.INTOUCH_URL}/{user_id}"
        payload = {"status": "deactivated"}
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
                headers=headers_update
            )
            if resp.status_code in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
                return {
                    "success": True,
                    "message": f"User {name} was successfully DEACTIVATED.",
                    "acao": "desativacao"
                }
            else:
                return {
                        "success": False,
                        "error": f"Error during deactivation: {resp.text}"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif current_status in {'pending', 'created', 'invited'}:
        print(" Pending/Created user. Executing definitive DELETION.")

        url_delete = f"{settings.INTOUCH_URL}/{user_id}"

        try:
            resp = requests.delete(url_delete, headers=HEADERS)
            if resp.status_code in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
                return {
                    "success": True,
                    "message": (
                        f"User invitation {name} was successfully DELETED."
                    ),
                    "acao": "exclusao"
                }
            else:
                return {
                    "success": False,
                    "error": f"Error during deletion: {resp.text}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif current_status in {'contact', 'deactivated'}:
        print(
            f" Status '{current_status}' is protected"
            " or already processed. No action taken."
        )
        return {
            "success": True,
            "message": (
                f"User {name} is set as '{current_status}' "
                "and does not need to be changed."
            ),
            "acao": "nenhuma"
        }

    else:
        return {
            "success": False,
            "error": (
                f"Unknown status ('{current_status}'). "
                "Operation canceled for safety."
            )
        }
