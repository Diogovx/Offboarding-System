from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.audit import audit_log_router
from app.database import init_db
from app.routers import (
    aduser_router,
    auth_router,
    execute_router,
    intouch_router,
    system_router,
    user_router,
)
from app.security import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    # quando colocar no Docker, temos que alterar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router.router)
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(aduser_router.router)
app.include_router(audit_log_router.router)
app.include_router(intouch_router.router)
app.include_router(execute_router.router)

app.mount("/app", StaticFiles(directory="app"), name="app")
app.mount("/static", StaticFiles(directory="pages"), name="pages")
