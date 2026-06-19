"""
Agent API
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/agent/run")
async def run_agent():
    """Run agent endpoint"""
    pass
