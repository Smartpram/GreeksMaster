"""
Factory to provide the preferred Breeze service implementation.
Prefers the breeze_connect_adapter when available, falls back to BreezeAPIService.
"""
from typing import Any
import logging

from app.services.breeze_connect_adapter import BreezeConnectAdapter

logger = logging.getLogger(__name__)


def get_breeze_service() -> Any:
    """Return an object that implements the Breeze API methods used by the app.

    If the breeze_connect adapter is available, return that. Otherwise return
    the local BreezeAPIService implementation.
    """
    try:
        adapter = BreezeConnectAdapter()
        if adapter.is_available():
            logger.info("Using breeze_connect_adapter as Breeze service")
            return adapter
    except Exception:
        logger.exception("Failed to initialize breeze_connect_adapter")

    # Fallback import (late import to avoid circular imports)
    from app.services.breeze_api import BreezeAPIService
    logger.info("Falling back to BreezeAPIService")
    return BreezeAPIService()
