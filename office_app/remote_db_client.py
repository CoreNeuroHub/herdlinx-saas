"""Remote Database Client

Connects to the Raspberry Pi backend via REST API and WebSocket for real-time updates.
This module runs on the Server/Web UI.
"""
import requests
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RemoteDBClient:
    """Client for communicating with remote Raspberry Pi backend"""

    def __init__(self, pi_host: str, pi_port: int = 5001, api_key: Optional[str] = None, use_ssl: bool = False):
        """
        Initialize remote database client

        Args:
            pi_host: Raspberry Pi hostname or IP address
            pi_port: Port number (default: 5001)
            api_key: API key for authentication
            use_ssl: Use HTTPS/SSL (default: False for self-signed cert)
        """
        self.pi_host = pi_host
        self.pi_port = pi_port
        self.api_key = api_key or os.environ.get('PI_API_KEY')
        self.use_ssl = use_ssl
        self.token = None
        self.token_expires_at = None

        # Build base URL
        protocol = 'https' if use_ssl else 'http'
        self.base_url = f"{protocol}://{pi_host}:{pi_port}"
        self.api_url = f"{self.base_url}/api/remote"

        # SSL verification (disable for self-signed certs)
        self.verify_ssl = use_ssl and not self._is_self_signed()

    def _is_self_signed(self) -> bool:
        """Check if using self-signed certificate"""
        return os.environ.get('USE_SELF_SIGNED_CERT', 'true').lower() == 'true'

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}

        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        elif self.api_key:
            headers['X-API-Key'] = self.api_key

        return headers

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Dict]:
        """Make HTTP request to remote backend"""
        url = f"{self.api_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=10,
                **kwargs
            )

            if response.status_code == 200 or response.status_code == 201:
                return True, response.json()
            else:
                logger.warning(f"Request failed: {response.status_code} - {response.text}")
                return False, {'error': response.text}

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {self.pi_host}:{self.pi_port}: {str(e)}")
            return False, {'error': 'Connection failed'}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to {self.pi_host}:{self.pi_port}: {str(e)}")
            return False, {'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return False, {'error': str(e)}

    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        try:
            success, response = self._make_request('POST', '/auth/token', json={'user_id': 1})

            if success and 'token' in response:
                self.token = response['token']
                self.token_expires_at = datetime.utcnow() + timedelta(hours=24)
                logger.info("Successfully authenticated with remote backend")
                return True
            else:
                logger.error(f"Authentication failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False

    def is_token_valid(self) -> bool:
        """Check if current token is valid"""
        if not self.token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at

    def health_check(self) -> bool:
        """Check if backend is accessible"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                verify=self.verify_ssl,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    # Batch endpoints

    def get_batches(self, limit: int = 50, offset: int = 0, source_type: Optional[str] = None) -> Optional[List[Dict]]:
        """Get list of batches"""
        if not self.is_token_valid() and not self.authenticate():
            logger.warning("Not authenticated, attempting with API key")

        params = {'limit': limit, 'offset': offset}
        if source_type:
            params['source_type'] = source_type

        success, response = self._make_request('GET', '/batches', params=params)

        if success:
            return response.get('data', [])
        return None

    def get_batch(self, batch_id: int) -> Optional[Dict]:
        """Get specific batch details"""
        if not self.is_token_valid() and not self.authenticate():
            return None

        success, response = self._make_request('GET', f'/batches/{batch_id}')

        if success:
            return response.get('data')
        return None

    # Payload endpoints

    def get_payloads(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> Optional[List[Dict]]:
        """Get list of payloads"""
        if not self.is_token_valid() and not self.authenticate():
            return None

        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status

        success, response = self._make_request('GET', '/payloads', params=params)

        if success:
            return response.get('data', [])
        return None

    def get_payload(self, payload_id: int) -> Optional[Dict]:
        """Get specific payload details"""
        if not self.is_token_valid() and not self.authenticate():
            return None

        success, response = self._make_request('GET', f'/payloads/{payload_id}')

        if success:
            return response.get('data')
        return None

    # System endpoints

    def get_system_status(self) -> Optional[Dict]:
        """Get system status and statistics"""
        if not self.is_token_valid() and not self.authenticate():
            return None

        success, response = self._make_request('GET', '/status')

        if success:
            return response.get('data')
        return None

    def get_buffer_status(self) -> Optional[Dict]:
        """Get buffer statistics"""
        status = self.get_system_status()
        if status:
            return {
                'total_payloads': status.get('total_payloads', 0),
                'processed': status.get('processed_payloads', 0),
                'errors': status.get('error_payloads', 0),
                'processing_rate': status.get('processing_rate', 'N/A')
            }
        return None


# Global client instance
_client_instance: Optional[RemoteDBClient] = None


def init_remote_client(pi_host: str, pi_port: int = 5001, api_key: Optional[str] = None, use_ssl: bool = False) -> RemoteDBClient:
    """Initialize global remote database client"""
    global _client_instance
    _client_instance = RemoteDBClient(pi_host, pi_port, api_key, use_ssl)

    # Attempt initial authentication
    if not _client_instance.health_check():
        logger.error(f"Cannot reach remote backend at {pi_host}:{pi_port}")

    return _client_instance


def get_remote_client() -> Optional[RemoteDBClient]:
    """Get global remote database client instance"""
    return _client_instance


def create_remote_client_from_config(app) -> RemoteDBClient:
    """Create remote client from Flask app config"""
    pi_host = app.config.get('REMOTE_PI_HOST', 'localhost')
    pi_port = app.config.get('REMOTE_PI_PORT', 5001)
    api_key = app.config.get('PI_API_KEY')
    use_ssl = app.config.get('USE_SSL_FOR_PI', False)

    return init_remote_client(pi_host, pi_port, api_key, use_ssl)
