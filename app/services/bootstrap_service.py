import logging

from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.source_service import SourceService


logger = logging.getLogger(__name__)


def bootstrap_application() -> None:
    initialize_database()
    with get_connection() as connection:
        SourceService(connection).sync_default_sources()
    logger.info("Application bootstrap completed")
