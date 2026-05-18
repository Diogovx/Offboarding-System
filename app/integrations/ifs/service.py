import logging
import asyncio # to test
import httpx
from app.core.config import settings
from app.integrations.ifs.schemas import IFSTokenResponse, IFSTokenRequest, IFSUserResponse

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
            username=settings.IFS_USERNAME,
            password=settings.IFS_PASSWORD,
            client_id=settings.IFS_CLIENT_ID,
            client_secret=settings.IFS_CLIENT_SECRET
        )

        logger.info("Find id_token...")

        token_headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = await client.post(url, data=payload.model_dump(), headers=token_headers)
        response.raise_for_status() 

        token_data = IFSTokenResponse(**response.json())
        self._token = token_data.id_token

        return self._token
    
    async def _get_user_ifs(self, registration: str, client: httpx.AsyncClient) -> IFSUserResponse:
        
        url = f"{self.base_url}/main/ifsapplications/projection/v1/UserRelatedData.svc/Reference_FndUser(Identity='{registration}')"

        if not self._token:
            await self._get_token_ifs(client) 

        logger.info(f"Buscando colaborador no IFS: {registration}")

        search_headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json"
        }

        response = await client.get(url, headers=search_headers)
        response.raise_for_status()

        user_data = IFSUserResponse(**response.json())
        return user_data
