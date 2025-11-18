from fastapi import APIRouter


router = APIRouter()


@router.get("/")
async def root():
    return { 
        "status": "online", 
        "version": "v1.0.0",
        "docs": "/docs" 
    }
    