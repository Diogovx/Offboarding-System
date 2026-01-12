from app.models.ad_user_model import DisableUserRequest
from app.routers import aduser_router
from app.services import intouch_service
from app.services.email_service import send_email
from app.enums import EmailActions

async def execute_offboarding(registration, current_user, background_tasks):
    services_list = []

    res_intouch = await intouch_service.deactivate_user_intouch(registration)
    if res_intouch.get("success"):
        services_list.append("Intouch")

    try:
        payload_ad = DisableUserRequest(registration=registration, performed_by=current_user.username)
        res_ad = await aduser_router.disable_user(payload=payload_ad, session=current_user)
        
        if res_ad.get("success"):
            services_list.append("Active Directory")
        else:
            print(f"AD returned success=False: {res_ad.get('message')}")
    except Exception as e:

        print(f"AD skip: {e}")

  
    action = EmailActions.get_by_id(3)
    

    background_tasks.add_task(
        send_email, 
        registration=registration, 
        action=action, 
        performed_by=str(current_user.username), 
        systems_list=services_list             
    )

    return {
        "success": True,
        "details": services_list 
    }