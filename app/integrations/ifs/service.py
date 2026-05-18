import logging
import httpx
from app.core.config import settings
from app.integrations.ifs.schemas import IFSTokenResponse, IFSTokenRequest

logger = logging.getLogger(__name__)

class IFSService:

    def __init__(self, base_url: str): 
        self.base_url = base_url.rstrip("/")
        self._token = None
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
           
        }   

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        url = f"{self.base_url}/openid-connect-provider/idp/token"

        if self._token:
            return self._token
        
        payload = IFSTokenRequest(
            username=settings.IFS_USERNAME,
            password=settings.IFS_PASSWORD,
            client_id=settings.IFS_CLIENT_ID,
            client_secret=settings.IFS_CLIENT_SECRET
        )

        logger.info("Requesting access token for IFS...")

        response = await client.post(url, data=payload.model_dump(), headers=self.headers)
        response.raise_for_status() 

        token_data = IFSTokenResponse(**response.json())
        self._token = token_data.access_token

        return self._token