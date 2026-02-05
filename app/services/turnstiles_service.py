import requests
from http import HTTPStatus
from app.security import settings

TURNSTILES = [
    {"name": "Unit A", "url": settings.TURNSTILE_A_URL, "session": settings.TURNSTILE_A_SESSION},
    {"name": "Unit B", "url": settings.TURNSTILE_B_URL, "session": settings.TURNSTILE_B_SESSION}
]

async def deactivate_user_turnstiles(registration: str):
    print(f"DEBUG: Receiving the registration: {registration}")
    
    user_id = int(registration)
    
    payload = {
        "object": "users",
        "values": {

            "end_time": 1700000000
        },
        "where": {
            "users": { "id": user_id }
        }
    }

    for turnstile in TURNSTILES:
        url = f"{turnstile['url']}/modify_objects.fcgi?session={turnstile['session']}"
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            continue 

    return {
        "success": True,
        "action": "turnstile_deactivation"
    }