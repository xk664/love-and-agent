"""
Chat API
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat():
    """Chat endpoint"""
    pass
