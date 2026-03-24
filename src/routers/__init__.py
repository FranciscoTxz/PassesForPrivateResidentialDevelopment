from .auth_router import router as auth_router
from .gatehouse_router import router as gatehouse_router
from .houses_router import router as houses_router
from .passes_router import router as passes_router
from .profile_router import router as profile_router
from .users_router import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "profile_router",
    "houses_router",
    "passes_router",
    "gatehouse_router",
]
