"""
SecureDx FL Client — Entry Point
Starts the federated learning sync worker.
"""
# services/fl-client/main.py

"""
SecureDx FL Client — Entry Point
"""
import os
import logging
import time
from client.fl_client import run_fl_client

logger = logging.getLogger(__name__)

FL_ENABLED = os.environ.get("FL_ENABLED", "true").lower() == "true"

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    print("=" * 60)
    print("SecureDx FL Client - Sprint 5")
    print("=" * 60)
    print(f"FL Enabled: {FL_ENABLED}")
    print("=" * 60)
    
    if not FL_ENABLED:
        logger.info("FL is DISABLED - exiting")
        logger.info("To enable: Set FL_ENABLED=true in docker-compose.dev.yml")
        import time
        while True:
            time.sleep(3600)  # Sleep forever
    
    # FL is enabled - start client with reconnect loop.
    # This keeps the container alive when coordinator is temporarily unavailable.
    retry_seconds = int(os.environ.get("FL_RETRY_SECONDS", "30"))
    logger.info("FL is ENABLED - starting client")
    while True:
        try:
            run_fl_client()
        except Exception as exc:
            logger.error(
                "FL client crashed; retrying",
                extra={"retry_seconds": retry_seconds, "error": str(exc)},
            )
            time.sleep(retry_seconds)
