from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.modules.audit import router
from app.core.database import init_db
from app.integrations.active_directory import aduser_router
from app.integrations.intouch import intouch_router
from app.modules.offboarding import router
from app.core import health
from app.modules.users import user_router
from app.modules.users import (
    auth_router,
)
from app.core.security import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(aduser_router.router)
app.include_router(router.router)
app.include_router(intouch_router.router)
app.include_router(router.router)

app.mount("/app", StaticFiles(directory="app"), name="app")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
