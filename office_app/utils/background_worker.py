"""Background Worker for Payload Processing

Handles periodic processing of buffered LoRa payloads in a separate thread.
"""
import threading
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class PayloadProcessingWorker:
    """Background worker for processing buffered payloads"""

    def __init__(self, app, interval=5):
        """
        Initialize the background worker.

        Args:
            app (Flask): Flask application instance
            interval (int): Processing interval in seconds (default: 5)
        """
        self.app = app
        self.interval = interval
        self.thread = None
        self.running = False

    def start(self):
        """Start the background worker thread"""
        if self.running:
            logger.warning("Worker is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Payload processing worker started (interval: {self.interval}s)")

    def stop(self):
        """Stop the background worker thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Payload processing worker stopped")

    def _run(self):
        """Main worker loop"""
        from office_app.utils.payload_processor import PayloadProcessor

        while self.running:
            try:
                with self.app.app_context():
                    # Process pending payloads
                    stats = PayloadProcessor.process_pending_payloads()

                    if stats['total'] > 0:
                        logger.info(
                            f"Payload processing cycle - Total: {stats['total']}, "
                            f"Processed: {stats['processed']}, Errors: {stats['errors']}"
                        )

            except Exception as e:
                logger.error(f"Error in payload processing worker: {str(e)}")

            # Sleep before next cycle
            time.sleep(self.interval)


def init_background_worker(app, interval=5):
    """
    Initialize and start the background worker.

    Args:
        app (Flask): Flask application instance
        interval (int): Processing interval in seconds

    Returns:
        PayloadProcessingWorker: Worker instance
    """
    worker = PayloadProcessingWorker(app, interval=interval)
    worker.start()
    return worker
