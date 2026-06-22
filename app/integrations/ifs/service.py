import logging
import asyncio 
import httpx
from app.core.config import settings

from app.integrations.ifs.schemas import (
    IFSTokenResponse, 
    IFSTokenRequest, 
    IFSUserResponse, 
    IFSUserRequest, 
    IFSPersonUserResponse,
    IFSDesactiveUserRequest 
)

logger = logging.getLogger(__name__)

class IFSService:

    def __init__(self, base_url: str): 
        self.base_url = base_url.rstrip("/")
        self._token = None
        self.headers = {}   

    async def _get_token_ifs(self, client: httpx.AsyncClient) -> str:
        url = f"{self.base_url}/openid-connect-provider/idp/token"

        if self._token:
            return self._token
        
        payload = IFSTokenRequest(
            username=settings.IFS_USERNAME_TST,
            password=settings.IFS_PASSWORD_TST,
            client_id=settings.IFS_CLIENT_ID_TST,
            client_secret=settings.IFS_CLIENT_SECRET_TST
        )

        logger.info("Searching for id_token...")

        token_headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = await client.post(url, data=payload.model_dump(), headers=token_headers)
        response.raise_for_status() 

        token_data = IFSTokenResponse(**response.json())
        self._token = token_data.id_token

        return self._token
    
    async def _get_person_user_ifs(self, registration: str, client: httpx.AsyncClient) -> IFSPersonUserResponse:
        
        url = f"{self.base_url}/main/ifsapplications/projection/v1/PersonHandling.svc/PersonInfoSet?$filter=AlternativeName%20eq%20'{registration}'"

        if not self._token:
            await self._get_token_ifs(client) 

        logger.info(f"Searching PersonId for registration: {registration}")

        person_header = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}"
        }

        response = await client.get(url, headers=person_header)
        response.raise_for_status()

        person_data = IFSPersonUserResponse(**response.json())
        return person_data
    
    async def _get_user_ifs(self, registration: str, client: httpx.AsyncClient) -> IFSUserResponse:
        
        url = f"{self.base_url}/main/ifsapplications/projection/v1/UserRelatedData.svc/Reference_FndUser(Identity='{registration}')"

        if not self._token:
            await self._get_token_ifs(client) 

        logger.info(f"Searching for a collaborator in IFS: {registration}")

        search_headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json"
        }

        response = await client.get(url, headers=search_headers)
        response.raise_for_status()

        user_data = IFSUserResponse(**response.json())
        return user_data

    async def _patch_user_ifs(self, registration: str, etag: str, active: bool, client: httpx.AsyncClient) -> bool:
        
        url = f"{self.base_url}/main/ifsapplications/projection/v1/UserRelatedData.svc/Reference_FndUser(Identity='{registration}')"

        if not self._token:
            await self._get_token_ifs(client) 

        logger.info(f"Updating employee {registration} to status = {active}")

        patch_headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "If-Match": etag              
        }

        status_string = str(active).upper()
        payload = IFSDesactiveUserRequest(Active=status_string)

        response = await client.patch(
            url, 
            headers=patch_headers, 
            json=payload.model_dump() 
        )
        
        response.raise_for_status()

        return response.status_code in (200, 204)
    
    async def disable_employee(self, registration: str, client: httpx.AsyncClient) -> bool:
        """
        Orchestrates the entire IFS deactivation process:
        1. Finds the PersonId.
        2. Retrieves the User Identity and ETag.
        3. Sends the PATCH request to deactivate.
        """
        try:
            person_result = await self._get_person_user_ifs(registration, client)

            if not person_result.value:
                logger.warning(f"IFS Deactivation: No user found for registration {registration}")
                return False
            
            person_id = person_result.value[0].PersonId
           
            user_data = await self._get_user_ifs(person_id, client)

            success = await self._patch_user_ifs(
                registration=person_id,
                etag=user_data.etag,
                active=False,
                client=client
            )
            return success

        except Exception as e:
            logger.error(f"Failed to deactivate user {registration} in IFS: {str(e)}")
            return False
        
    async def search_user(self, registration: str) -> bool:
        """
        Verifies if the user exists and is active in IFS.
        Manages its own HTTP connection to be used independently.
        """
        try:
            async with httpx.AsyncClient() as client:
                person_result = await self._get_person_user_ifs(registration, client)
                if not person_result.value:
                    return False
                    
                person_id = person_result.value[0].PersonId
                user = await self._get_user_ifs(person_id, client)
                
                return user.is_active 
        except Exception as e:
            logger.error(f"Error fetching user status in IFS for {registration}: {e}")
            return False