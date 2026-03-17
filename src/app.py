from commons.exceptions_handler import register_exception_handlers
from commons.log_helper import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_LOG = get_logger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,  # ty:ignore
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/")
def read_root():
    """Returns Hello World."""
    return {"Hello": "World! :,)"}
