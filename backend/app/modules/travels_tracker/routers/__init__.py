from fastapi import APIRouter
from .trip_router import router as trip_router
from .album_router import router as album_router
from .photo_router import router as photo_router
from .activity_router import router as activity_router

# Single router exported by the module — main.py calls app.include_router(router)
router = APIRouter()
router.include_router(trip_router)
router.include_router(album_router)
router.include_router(photo_router)
router.include_router(activity_router)