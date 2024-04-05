"""
FastAPI vmail application for validating and verifying emails.
"""

import contextlib
import logging
import typing

import fastapi
import fastapi.middleware.cors
import fastapi.security
import sqlalchemy

from .config import get_settings

from . import __version__
from .vmail_router import repo
from .vmail_router import router


L = logging.getLogger("vmail")

settings = get_settings()

ENGINE = None


def get_engine():
    global ENGINE
    if ENGINE is None:
        ENGINE = sqlalchemy.create_engine(
            settings.db_connection_string, pool_pre_ping=True
        )
    return ENGINE


async def create_db_and_tables():
    L.debug("db connect")


def create_application() -> fastapi.FastAPI:
    @contextlib.asynccontextmanager
    async def lifespan(fastapi_app: fastapi.FastAPI):
        L.debug("lifespan connect")
        engine = get_engine()
        await create_db_and_tables()
        yield
        L.debug("lifespan disconnect")
        engine.dispose()

    app = fastapi.FastAPI(
        title="Vmail",
        description=__doc__,
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        fastapi.middleware.cors.CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    api_key_header = fastapi.security.APIKeyHeader(name="X-API-Key")


    def custom_header_dependency(x_api_key: str=fastapi.Header())->str:
        print(f"XAPIKEY = {x_api_key}")
        return x_api_key


    def get_api_key(api_key: str = fastapi.Security(api_key_header)) -> str:
        if api_key in settings.api_keys.values():
            return api_key
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )

    @contextlib.contextmanager
    def get_repository() -> typing.Iterator[repo.VmailRepo]:
        session = sqlalchemy.orm.sessionmaker(bind=get_engine())()
        repository = repo.VmailRepo(session)
        try:
            L.debug("start yield repo")
            yield repository
            L.debug("end yield repo")
        except Exception:
            session.rollback()
        finally:
            session.close()

    @app.middleware("http")
    async def db_session_middleware(request: fastapi.Request, call_next):
        """
        Adds the vmail repository instance to the state property of each request.

        Grabbing the repository is a low-cost operation as it is just instantiating the class.
        """
        with get_repository() as repository:
            request.state.vmailrepo = repository
            response = await call_next(request)
            return response

    app.include_router(
        router.get_vmail_router(
            get_settings,
            dependencies=[
                fastapi.Depends(get_api_key),
                fastapi.Depends(custom_header_dependency)
            ],
        ),
        prefix="",
        tags=["vmail"],
    )

    return app

app = create_application()