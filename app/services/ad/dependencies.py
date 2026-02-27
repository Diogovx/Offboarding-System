from fastapi import Depends
from typing import Annotated
from .services import ADService


def get_ad_service() -> ADService:
    return ADService()


ADServiceDep = Annotated[ADService, Depends(get_ad_service)]
