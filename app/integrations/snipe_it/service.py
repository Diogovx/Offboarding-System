import httpx
from app.core.config import settings
from app.integrations.snipe_it.schemas import GenerateTermRequest
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SnipeItService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.SNIPEIT_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get_user_by_registration(
        self,
        client: httpx.AsyncClient,
        registration: str
    ) -> int:
        response = await client.get(
            "users",
            params={"search": registration, "limit": 10}
        )
        response.raise_for_status()

        data = response.json()
        if data.get("total", 0) == 0:
            raise ValueError(
                f"Usuário com matrícula '{registration}' não encontrado no Snipe-IT."
            )

        rows = data.get("rows", [])
        for row in rows:
            if str(row.get("employee_num", "")) == str(registration):
                return row

        logger.warning(
            f"Nenhum usuário com employee_num exato '{registration}'. "
            f"Usando primeiro resultado."
        )
        return rows[0]

    async def _get_asset_by_tag(
        self,
        client: httpx.AsyncClient,
        asset_tag: str
    ) -> int:
        response = await client.get(f"hardware/bytag/{asset_tag}")
        response.raise_for_status()
        return response.json().get("id")

    async def search_assets_by_user(self, registration: str):
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers
        ) as client:
            user = await self._get_user_by_registration(client, registration)
            user_id = user["id"]

            response = await client.get(
                f"users/{user_id}/assets",
                params={"limit": 500}
            )
            response.raise_for_status()

            assets = response.json().get("rows", [])
            logger.info(
                f"{len(assets)} ativo(s) encontrado(s) para matrícula {registration}."
            )
            return assets

    async def checkin_asset(
        self,
        registration: str,
        asset_tag: str,
        note: str = ""
    ):
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers
        ) as client:
            asset_id = await self._get_asset_by_tag(client, asset_tag)

            payload = {
                "note": note,
            }

            response = await client.post(
                f"hardware/{asset_id}/checkin", json=payload
            )
            response.raise_for_status()
            return response.json()

    async def checkout_asset(
        self,
        registration: str,
        asset_tag: str,
        note: str = "Alocado via API (Onboarding)"
    ):
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers
        ) as client:
            user_id = await self._get_user_by_registration(
                client, registration
            )
            asset_id = await self._get_asset_by_tag(client, asset_tag)

            payload = {
                "checkout_to_type": "user",
                "assigned_user": user_id,
                "note": note
            }

            response = await client.post(
                f"hardware/{asset_id}/checkout",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def update_user_notes(
        self,
        registration: str,
        performed_by: str,
    ) -> None:
        """Updates the Snipe-IT user notes field to record the offboarding event.

        Sets a note on the user record indicating who performed the offboarding
        and when it occurred, using the Snipe-IT user update endpoint.

        Args:
            registration (str): Employee registration number.
            performed_by (str): Username of the person who performed the offboarding.
        """
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers
        ) as client:
            user = await self._get_user_by_registration(client, registration)
            user_id = user["id"]

            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            note = (
                f"Desativado via Offboarding System em {timestamp} "
                f"por {performed_by}."
            )

            response = await client.patch(
                f"users/{user_id}",
                json={"notes": note}
            )

            if not response.is_success:
                logger.warning(
                    f"Falha ao atualizar notas do usuário {registration} "
                    f"no Snipe-IT: {response.status_code} — {response.text}"
                )
            else:
                logger.info(
                    f"Notas do usuário {registration} atualizadas no Snipe-IT."
                )

    async def get_templates(self) -> list:
        """
        Busca todos os templates disponíveis na API customizada do Snipe-IT.
        """
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers
        ) as client:
            response = await client.get("terms/templates")
            response.raise_for_status()

            return response.json().get("templates", [])

    async def get_template_id_by_type(self, term_type: str) -> int:
        """
        Busca o ID de um template pelo seu tipo exato (ex: 'checkin' ou 'checkout').
        """
        templates = await self.get_templates()

        for template in templates:
            if template.get("term_type") == term_type:
                return template["id"]

        raise ValueError(
            f"Nenhum template encontrado com o term_type '{term_type}'. "
            "Certifique-se de configurar isso no painel do Snipe-IT."
        )

    async def generate_term(
        self,
        employee_num: str,
        template_id: int,
        asset_tag: str
    ):
        print(f"Tentando conectar em: {self.base_url}/api/v1/terms/generate")
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers
        ) as client:
            payload = {
                "employee_num": employee_num,
                "template_id": template_id,
                "asset_tag": asset_tag
            }

            response = await client.post(
                "terms/generate",
                json=payload
            )
            response.raise_for_status()

            return response.content


def get_snipeit_service() -> SnipeItService:
    """
    Instancia o serviço do Snipe-IT usando as credenciais do sistema (.env)
    """
    return SnipeItService(
        base_url=settings.SNIPEIT_BASE_URL,
    )
