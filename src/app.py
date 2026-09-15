import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from commons.constants import CORS_ALLOW_ORIGINS, validate_settings
from commons.exceptions_handler import register_exception_handlers
from commons.log_helper import get_logger
from routers import (
    auth_router,
    gatehouse_router,
    houses_router,
    passes_router,
    profile_router,
    users_router,
)
from services import connect_to_mongodb, disconnect_from_mongodb
from services.passes_service import update_passes_status

_LOG = get_logger(__name__)

TAGS_METADATA = [
    {"name": "Auth", "description": "Registration and login."},
    {"name": "Profile", "description": "Current user profile management."},
    {"name": "Users", "description": "Admin user administration."},
    {"name": "Houses", "description": "Admin house administration."},
    {"name": "Passes", "description": "Pass creation, listing and review."},
    {"name": "Gatehouse", "description": "Gatehouse token and pass validation."},
    {"name": "Health", "description": "Service health checks."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()
    connect_to_mongodb()
    status_task = asyncio.create_task(update_passes_status())
    try:
        yield
    finally:
        status_task.cancel()
        with suppress(asyncio.CancelledError):
            await status_task
        disconnect_from_mongodb()


app = FastAPI(
    title="Passes for Private Residential Development",
    description=(
        "API to manage access passes for a gated residential community, "
        "including pass review, QR generation and gatehouse validation."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,  # ty:ignore
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router=auth_router)
app.include_router(router=users_router)
app.include_router(router=profile_router)
app.include_router(router=houses_router)
app.include_router(router=passes_router)
app.include_router(router=gatehouse_router)


@app.get("/", tags=["Health"])
def read_root():
    """Returns Hello World."""
    return {"Hello": "World! :,)"}


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe used by containers and orchestrators."""
    return {"status": "ok"}
