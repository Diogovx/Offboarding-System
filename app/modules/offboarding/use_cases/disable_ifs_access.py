import httpx
import logging
from app.core.config import settings
from app.integrations.ifs.service import IFSService

logger = logging.getLogger(__name__)

async def check_ifs_status(registration: str) -> bool:
    """
    Checks IFS status.
    """
    try:

        ifs_service = IFSService(base_url=settings.IFS_BASE_URL)

        return await ifs_service.search_user(registration)
    
    except Exception as e:
        
        logger.error(f"Connection failed when checking IFS for {registration}: {e}")
        return False

async def disable_ifs_access(registration: str, **kwargs) -> bool:
    """
    Opens HTTP client and orchestrates deactivation in IFS
    """
    try:
        async with httpx.AsyncClient() as client:

            ifs_service = IFSService(base_url=settings.IFS_BASE_URL)
            return await ifs_service.disable_employee(registration, client)
        
    except Exception as e:
        logger.error(f"Failed to deactivate user {registration} in IFS: {e}")
        return False