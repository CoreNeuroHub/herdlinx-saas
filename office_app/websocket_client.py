"""WebSocket Client for Real-time Updates

Connects to the Raspberry Pi backend WebSocket server for real-time payload/batch updates.
This module runs on the Server/Web UI.
"""
import socketio
import logging
from typing import Callable, Dict, Optional
from datetime import datetime
import os
import threading

logger = logging.getLogger(__name__)


class RealtimeUpdatesClient:
    """WebSocket client for real-time updates from Raspberry Pi backend"""

    def __init__(self, pi_host: str, pi_port: int = 5001, use_ssl: bool = False):
        """
        Initialize WebSocket client

        Args:
            pi_host: Raspberry Pi hostname or IP
            pi_port: Port number
            use_ssl: Use secure WebSocket (WSS)
        """
        self.pi_host = pi_host
        self.pi_port = pi_port
        self.use_ssl = use_ssl
        self.connected = False
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5

        # Build WebSocket URL
        protocol = 'wss' if use_ssl else 'ws'
        self.ws_url = f"{protocol}://{pi_host}:{pi_port}"

        # Create SocketIO client
        self.sio = socketio.Client(
            ssl_verify=not self._is_self_signed(),
            reconnection=True,
            reconnection_delay=1,
            reconnection_delay_max=5,
            reconnection_attempts=self.max_reconnect_attempts
        )

        # Event callbacks
        self.event_callbacks: Dict[str, list] = {
            'connect': [],
            'disconnect': [],
            'payload:received': [],
            'payload:processed': [],
            'batch:created': [],
            'error': []
        }

        # Register event handlers
        self._register_handlers()

    def _is_self_signed(self) -> bool:
        """Check if using self-signed certificate"""
        return os.environ.get('USE_SELF_SIGNED_CERT', 'true').lower() == 'true'

    def _register_handlers(self):
        """Register SocketIO event handlers"""

        @self.sio.on('connect')
        def on_connect():
            logger.info("Connected to remote WebSocket server")
            self.connected = True
            self.connection_attempts = 0
            self._call_callbacks('connect', {})

        @self.sio.on('disconnect')
        def on_disconnect():
            logger.warning("Disconnected from remote WebSocket server")
            self.connected = False
            self._call_callbacks('disconnect', {})

        @self.sio.on('payload:received')
        def on_payload_received(data):
            logger.debug(f"Payload received event: {data}")
            self._call_callbacks('payload:received', data)

        @self.sio.on('payload:processed')
        def on_payload_processed(data):
            logger.debug(f"Payload processed event: {data}")
            self._call_callbacks('payload:processed', data)

        @self.sio.on('batch:created')
        def on_batch_created(data):
            logger.debug(f"Batch created event: {data}")
            self._call_callbacks('batch:created', data)

        @self.sio.on('response')
        def on_response(data):
            logger.debug(f"Server response: {data}")

        @self.sio.on_error_default()
        def on_error(error):
            logger.error(f"WebSocket error: {error}")
            self._call_callbacks('error', {'message': str(error)})

    def _call_callbacks(self, event: str, data: Dict):
        """Call registered callbacks for an event"""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback for {event}: {str(e)}")

    def on(self, event: str, callback: Callable):
        """Register callback for an event

        Args:
            event: Event name (connect, disconnect, payload:received, batch:created, etc)
            callback: Function to call when event occurs
        """
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)
        logger.debug(f"Registered callback for event: {event}")

    def connect(self, timeout: int = 10) -> bool:
        """Connect to remote WebSocket server"""
        try:
            logger.info(f"Connecting to WebSocket server at {self.ws_url}")
            self.sio.connect(self.ws_url, wait_timeout=timeout)
            self.connection_attempts = 0
            return True
        except Exception as e:
            self.connection_attempts += 1
            logger.error(f"Failed to connect (attempt {self.connection_attempts}): {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from remote WebSocket server"""
        if self.connected:
            try:
                self.sio.disconnect()
                logger.info("Disconnected from WebSocket server")
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")

    def subscribe_payloads(self):
        """Subscribe to payload updates"""
        if self.connected:
            self.sio.emit('subscribe:payloads')
            logger.debug("Subscribed to payload updates")

    def unsubscribe_payloads(self):
        """Unsubscribe from payload updates"""
        if self.connected:
            self.sio.emit('unsubscribe:payloads')
            logger.debug("Unsubscribed from payload updates")

    def subscribe_batches(self):
        """Subscribe to batch updates"""
        if self.connected:
            self.sio.emit('subscribe:batches')
            logger.debug("Subscribed to batch updates")

    def unsubscribe_batches(self):
        """Unsubscribe from batch updates"""
        if self.connected:
            self.sio.emit('unsubscribe:batches')
            logger.debug("Unsubscribed from batch updates")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.sio.connected


# Global client instance
_ws_client_instance: Optional[RealtimeUpdatesClient] = None


def init_websocket_client(pi_host: str, pi_port: int = 5001, use_ssl: bool = False, auto_connect: bool = True) -> RealtimeUpdatesClient:
    """Initialize global WebSocket client"""
    global _ws_client_instance
    _ws_client_instance = RealtimeUpdatesClient(pi_host, pi_port, use_ssl)

    if auto_connect:
        # Attempt connection in background thread
        def connect_async():
            if _ws_client_instance.connect():
                _ws_client_instance.subscribe_payloads()
                _ws_client_instance.subscribe_batches()
            else:
                logger.warning("WebSocket connection failed, will retry on next attempt")

        thread = threading.Thread(target=connect_async, daemon=True)
        thread.start()

    return _ws_client_instance


def get_websocket_client() -> Optional[RealtimeUpdatesClient]:
    """Get global WebSocket client instance"""
    return _ws_client_instance


def create_websocket_client_from_config(app) -> RealtimeUpdatesClient:
    """Create WebSocket client from Flask app config"""
    pi_host = app.config.get('REMOTE_PI_HOST', 'localhost')
    pi_port = app.config.get('REMOTE_PI_PORT', 5001)
    use_ssl = app.config.get('USE_SSL_FOR_PI', False)

    return init_websocket_client(pi_host, pi_port, use_ssl)
