from fastapi import APIRouter

from app.services.test_service import get_test_message

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("/test")
async def get_test():
    message = await get_test_message()
    return {"message": message}
