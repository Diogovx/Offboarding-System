from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import init_db
from app.routers import auth_router, system_router, user_router, aduser_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(system_router.router)
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(aduser_router.router)
