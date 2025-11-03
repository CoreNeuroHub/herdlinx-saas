"""Database Sync Service for Server UI

Handles periodic synchronization of database from Pi backend.
Keeps local SQLite replica in sync with Pi's database.
"""
import threading
import logging
import time
from datetime import datetime
from typing import Optional
import requests
import os

logger = logging.getLogger(__name__)


class DatabaseSyncService:
    """Syncs database changes from Pi backend to local Server database"""

    def __init__(self, pi_host: str, pi_port: int = 5001, api_key: Optional[str] = None,
                 sync_interval: int = 10, use_ssl: bool = False):
        """
        Initialize sync service

        Args:
            pi_host: Raspberry Pi hostname or IP
            pi_port: Port number
            api_key: API key for authentication
            sync_interval: Seconds between syncs (default: 10)
            use_ssl: Use HTTPS
        """
        self.pi_host = pi_host
        self.pi_port = pi_port
        self.api_key = api_key or os.environ.get('PI_API_KEY')
        self.sync_interval = sync_interval
        self.use_ssl = use_ssl
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_sync_time: Optional[datetime] = None
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'total_records_synced': 0
        }

        # Build base URL
        protocol = 'https' if use_ssl else 'http'
        self.base_url = f"{protocol}://{pi_host}:{pi_port}"
        self.api_url = f"{self.base_url}/api/sync"

        # SSL verification (disable for self-signed certs)
        self.verify_ssl = use_ssl and not self._is_self_signed()

    def _is_self_signed(self) -> bool:
        """Check if using self-signed certificate"""
        return os.environ.get('USE_SELF_SIGNED_CERT', 'true').lower() == 'true'

    def _get_headers(self) -> dict:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def start(self):
        """Start the background sync service"""
        if self.running:
            logger.warning("Sync service is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        logger.info(f"Database sync service started (interval: {self.sync_interval}s)")

    def stop(self):
        """Stop the background sync service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Database sync service stopped")

    def _sync_loop(self):
        """Main sync loop"""
        initial_sync = True

        while self.running:
            try:
                if initial_sync:
                    # First sync: get everything
                    success = self._sync_full()
                    initial_sync = False
                else:
                    # Subsequent syncs: get only changes
                    success = self._sync_incremental()

                if success:
                    self.last_sync_time = datetime.utcnow()
                    self.sync_stats['successful_syncs'] += 1
                else:
                    self.sync_stats['failed_syncs'] += 1

                self.sync_stats['total_syncs'] += 1

            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                self.sync_stats['failed_syncs'] += 1

            time.sleep(self.sync_interval)

    def _sync_full(self) -> bool:
        """Perform initial full database sync"""
        try:
            logger.info("Starting full database sync from Pi...")

            url = f"{self.api_url}/full-export"
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=30
            )

            if response.status_code != 200:
                logger.warning(f"Full sync failed: {response.status_code}")
                return False

            data = response.json()

            if not data.get('success'):
                logger.warning(f"Full sync failed: {data.get('message')}")
                return False

            # Import here to avoid circular imports
            from office_app import db
            from office_app.models.batch import Batch
            from office_app.models.cattle import Cattle
            from office_app.models.pen import Pen

            # Clear local data
            logger.info("Clearing local database...")
            Batch.query.delete()
            Cattle.query.delete()
            Pen.query.delete()
            db.session.commit()

            # Insert synced data
            batches_data = data.get('data', {}).get('batches', [])
            cattle_data = data.get('data', {}).get('cattle', [])
            pens_data = data.get('data', {}).get('pens', [])

            logger.info(f"Syncing: {len(batches_data)} batches, {len(cattle_data)} cattle, {len(pens_data)} pens")

            for batch_dict in batches_data:
                batch = Batch.query.get(batch_dict['id'])
                if not batch:
                    batch = Batch()
                    batch.id = batch_dict['id']

                batch.batch_number = batch_dict['batch_number']
                batch.induction_date = batch_dict['induction_date']
                batch.source = batch_dict.get('source', '')
                batch.source_type = batch_dict.get('source_type')
                batch.notes = batch_dict.get('notes', '')
                batch.created_at = datetime.fromisoformat(batch_dict['created_at'].replace('Z', '+00:00'))
                batch.updated_at = datetime.fromisoformat(batch_dict['updated_at'].replace('Z', '+00:00'))

                db.session.add(batch)

            for pen_dict in pens_data:
                pen = Pen.query.get(pen_dict['id'])
                if not pen:
                    pen = Pen()
                    pen.id = pen_dict['id']

                pen.pen_number = pen_dict['pen_number']
                pen.capacity = pen_dict['capacity']
                pen.description = pen_dict.get('description', '')
                pen.created_at = datetime.fromisoformat(pen_dict['created_at'].replace('Z', '+00:00'))
                pen.updated_at = datetime.fromisoformat(pen_dict['updated_at'].replace('Z', '+00:00'))

                db.session.add(pen)

            for cattle_dict in cattle_data:
                cattle = Cattle.query.get(cattle_dict['id'])
                if not cattle:
                    cattle = Cattle()
                    cattle.id = cattle_dict['id']

                cattle.batch_id = cattle_dict['batch_id']
                cattle.cattle_id = cattle_dict['cattle_id']
                cattle.sex = cattle_dict.get('sex')
                cattle.weight = cattle_dict.get('weight')
                cattle.health_status = cattle_dict.get('health_status')
                cattle.lf_tag = cattle_dict.get('lf_tag')
                cattle.uhf_tag = cattle_dict.get('uhf_tag')
                cattle.pen_id = cattle_dict.get('pen_id')
                cattle.created_at = datetime.fromisoformat(cattle_dict['created_at'].replace('Z', '+00:00'))
                cattle.updated_at = datetime.fromisoformat(cattle_dict['updated_at'].replace('Z', '+00:00'))

                db.session.add(cattle)

            db.session.commit()

            total = len(batches_data) + len(cattle_data) + len(pens_data)
            self.sync_stats['total_records_synced'] += total

            logger.info(f"Full sync completed: {total} records")
            return True

        except Exception as e:
            logger.error(f"Error in full sync: {str(e)}")
            return False

    def _sync_incremental(self) -> bool:
        """Perform incremental sync of changes only"""
        try:
            if not self.last_sync_time:
                return self._sync_full()

            since = self.last_sync_time.isoformat()

            url = f"{self.api_url}/changes?since={since}"
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=10
            )

            if response.status_code != 200:
                logger.debug(f"Incremental sync failed: {response.status_code}")
                return False

            data = response.json()

            if not data.get('success'):
                logger.debug(f"Incremental sync failed: {data.get('message')}")
                return False

            # Import here to avoid circular imports
            from office_app import db
            from office_app.models.batch import Batch
            from office_app.models.cattle import Cattle
            from office_app.models.pen import Pen

            batches_data = data.get('data', {}).get('batches', [])
            cattle_data = data.get('data', {}).get('cattle', [])
            pens_data = data.get('data', {}).get('pens', [])

            # Update or insert records
            for batch_dict in batches_data:
                batch = Batch.query.get(batch_dict['id'])
                if not batch:
                    batch = Batch()
                    batch.id = batch_dict['id']

                batch.batch_number = batch_dict['batch_number']
                batch.induction_date = batch_dict['induction_date']
                batch.source = batch_dict.get('source', '')
                batch.source_type = batch_dict.get('source_type')
                batch.notes = batch_dict.get('notes', '')
                batch.updated_at = datetime.fromisoformat(batch_dict['updated_at'].replace('Z', '+00:00'))

                db.session.add(batch)

            for pen_dict in pens_data:
                pen = Pen.query.get(pen_dict['id'])
                if not pen:
                    pen = Pen()
                    pen.id = pen_dict['id']

                pen.pen_number = pen_dict['pen_number']
                pen.capacity = pen_dict['capacity']
                pen.description = pen_dict.get('description', '')
                pen.updated_at = datetime.fromisoformat(pen_dict['updated_at'].replace('Z', '+00:00'))

                db.session.add(pen)

            for cattle_dict in cattle_data:
                cattle = Cattle.query.get(cattle_dict['id'])
                if not cattle:
                    cattle = Cattle()
                    cattle.id = cattle_dict['id']

                cattle.batch_id = cattle_dict['batch_id']
                cattle.cattle_id = cattle_dict['cattle_id']
                cattle.sex = cattle_dict.get('sex')
                cattle.weight = cattle_dict.get('weight')
                cattle.health_status = cattle_dict.get('health_status')
                cattle.lf_tag = cattle_dict.get('lf_tag')
                cattle.uhf_tag = cattle_dict.get('uhf_tag')
                cattle.pen_id = cattle_dict.get('pen_id')
                cattle.updated_at = datetime.fromisoformat(cattle_dict['updated_at'].replace('Z', '+00:00'))

                db.session.add(cattle)

            db.session.commit()

            total = len(batches_data) + len(cattle_data) + len(pens_data)
            if total > 0:
                logger.debug(f"Incremental sync: {total} records updated")
                self.sync_stats['total_records_synced'] += total

            return True

        except Exception as e:
            logger.error(f"Error in incremental sync: {str(e)}")
            return False

    def get_stats(self) -> dict:
        """Get sync service statistics"""
        return {
            'running': self.running,
            'sync_interval': self.sync_interval,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            **self.sync_stats
        }


# Global sync service instance
_sync_service_instance: Optional[DatabaseSyncService] = None


def init_sync_service(pi_host: str, pi_port: int = 5001, api_key: Optional[str] = None,
                     sync_interval: int = 10, use_ssl: bool = False) -> DatabaseSyncService:
    """Initialize and start the sync service"""
    global _sync_service_instance
    _sync_service_instance = DatabaseSyncService(pi_host, pi_port, api_key, sync_interval, use_ssl)
    _sync_service_instance.start()
    return _sync_service_instance


def get_sync_service() -> Optional[DatabaseSyncService]:
    """Get the global sync service instance"""
    return _sync_service_instance


def create_sync_service_from_config(app) -> DatabaseSyncService:
    """Create sync service from Flask app config"""
    pi_host = app.config.get('REMOTE_PI_HOST', 'localhost')
    pi_port = app.config.get('REMOTE_PI_PORT', 5001)
    api_key = app.config.get('PI_API_KEY')
    sync_interval = app.config.get('DB_SYNC_INTERVAL', 10)
    use_ssl = app.config.get('USE_SSL_FOR_PI', False)

    return init_sync_service(pi_host, pi_port, api_key, sync_interval, use_ssl)
