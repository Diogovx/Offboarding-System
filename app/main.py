from contextlib import asynccontextmanager

from fastapi import FastAPI

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


app.include_router(system_router.router)
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(aduser_router.router)
app.include_router(audit_log_router.router)
app.include_router(intouch_router.router)
app.include_router(execute_router.router)
