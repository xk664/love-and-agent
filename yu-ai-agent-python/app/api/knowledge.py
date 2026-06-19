"""
Knowledge Base API
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/knowledge/upload")
async def upload_knowledge():
    """Upload knowledge endpoint"""
    pass


@router.get("/knowledge/search")
async def search_knowledge():
    """Search knowledge endpoint"""
    pass
