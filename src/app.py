from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from commons.exceptions_handler import register_exception_handlers
from commons.log_helper import get_logger
from routers import auth_router, users_router
from services import connect_to_mongodb, disconnect_from_mongodb

_LOG = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongodb()

    yield

    disconnect_from_mongodb()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # ty:ignore
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router=auth_router)
app.include_router(router=users_router)


@app.get("/")
def read_root():
    """Returns Hello World."""
    return {"Hello": "World! :,)"}
