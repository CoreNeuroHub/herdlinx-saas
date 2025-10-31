"""LoRa Payload Processing Utility

Handles buffering, deduplication, and processing of incoming LoRa payloads.
"""
import hashlib
import logging
from datetime import datetime
from office_app.models.batch import Batch
from office_app.models.lora_payload_buffer import LoRaPayloadBuffer, PayloadStatus
from office_app import db

logger = logging.getLogger(__name__)


class PayloadProcessor:
    """Process LoRa payloads with buffering, deduplication, and batch creation"""

    @staticmethod
    def generate_payload_hash(payload):
        """Generate SHA256 hash of payload for deduplication"""
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def receive_payload(raw_payload):
        """
        Receive and buffer an incoming LoRa payload.

        Args:
            raw_payload (str): Raw payload string (e.g., hxb:BATCH001:LF123:UHF456)

        Returns:
            dict: Result with status, message, and payload_id
        """
        try:
            raw_payload = raw_payload.strip()

            if not raw_payload:
                return {
                    'success': False,
                    'message': 'Payload cannot be empty',
                    'status': 'error'
                }

            # Generate hash for deduplication
            payload_hash = PayloadProcessor.generate_payload_hash(raw_payload)

            # Check for duplicates
            existing = LoRaPayloadBuffer.find_by_hash(payload_hash)
            if existing:
                logger.warning(f"Duplicate payload received: {raw_payload}")
                return {
                    'success': False,
                    'message': f'Duplicate payload. Originally received at {existing.received_at}',
                    'status': 'duplicate',
                    'payload_id': existing.id,
                    'original_received_at': existing.received_at.isoformat()
                }

            # Store in buffer
            payload_id = LoRaPayloadBuffer.create_from_payload(raw_payload, payload_hash)

            logger.info(f"Payload buffered: {raw_payload} (ID: {payload_id})")

            return {
                'success': True,
                'message': 'Payload buffered successfully',
                'status': 'buffered',
                'payload_id': payload_id,
                'payload_hash': payload_hash
            }

        except Exception as e:
            logger.error(f"Error receiving payload: {str(e)}")
            return {
                'success': False,
                'message': f'Error buffering payload: {str(e)}',
                'status': 'error'
            }

    @staticmethod
    def process_pending_payloads(batch_size=100):
        """
        Process all pending payloads in the buffer.

        Args:
            batch_size (int): Number of payloads to process at once

        Returns:
            dict: Processing statistics
        """
        stats = {
            'total': 0,
            'processed': 0,
            'duplicates': 0,
            'errors': 0,
            'failed_payloads': []
        }

        try:
            pending_payloads = LoRaPayloadBuffer.get_pending_payloads(limit=batch_size)
            stats['total'] = len(pending_payloads)

            for payload_entry in pending_payloads:
                try:
                    # Mark as processing
                    LoRaPayloadBuffer.mark_as_processing(payload_entry.id)

                    # Parse payload
                    parsed = Batch.parse_payload(payload_entry.raw_payload)

                    if not parsed:
                        error_msg = 'Invalid payload format'
                        LoRaPayloadBuffer.mark_as_error(payload_entry.id, error_msg)
                        stats['errors'] += 1
                        stats['failed_payloads'].append({
                            'id': payload_entry.id,
                            'payload': payload_entry.raw_payload,
                            'reason': error_msg
                        })
                        logger.warning(f"Invalid payload: {payload_entry.raw_payload}")
                        continue

                    # Update parsed data in buffer
                    LoRaPayloadBuffer.update_payload_data(
                        payload_entry.id,
                        parsed['source_type'],
                        parsed['batch_number'],
                        parsed['lf_tag'],
                        parsed['uhf_tag']
                    )

                    # Check if batch exists
                    existing_batch = Batch.query.filter_by(
                        batch_number=parsed['batch_number']
                    ).first()

                    if existing_batch:
                        # Update source_type if not set
                        if not existing_batch.source_type:
                            existing_batch.source_type = parsed['source_type']
                            existing_batch.updated_at = datetime.utcnow()
                            db.session.commit()
                        batch_id = existing_batch.id
                        logger.info(f"Batch exists: {parsed['batch_number']}")
                    else:
                        # Create new batch
                        source_label = 'Barn (HXB)' if parsed['source_type'] == 'hxb' else 'Export (HXE)'
                        batch_id = Batch.create_batch(
                            batch_number=parsed['batch_number'],
                            induction_date=datetime.utcnow().date(),
                            source=source_label,
                            source_type=parsed['source_type'],
                            notes=f'Auto-created from LoRa payload - LF: {parsed["lf_tag"]}, UHF: {parsed["uhf_tag"]}'
                        )
                        logger.info(f"Batch created: {parsed['batch_number']} (ID: {batch_id})")

                    # Mark payload as processed
                    LoRaPayloadBuffer.mark_as_processed(payload_entry.id, batch_id)
                    stats['processed'] += 1

                except Exception as e:
                    error_msg = f'Processing error: {str(e)}'
                    LoRaPayloadBuffer.mark_as_error(payload_entry.id, error_msg)
                    stats['errors'] += 1
                    stats['failed_payloads'].append({
                        'id': payload_entry.id,
                        'payload': payload_entry.raw_payload,
                        'reason': error_msg
                    })
                    logger.error(f"Error processing payload {payload_entry.id}: {error_msg}")

            logger.info(f"Payload processing complete - Processed: {stats['processed']}, Errors: {stats['errors']}")

        except Exception as e:
            logger.error(f"Error processing pending payloads: {str(e)}")
            stats['errors'] += 1

        return stats

    @staticmethod
    def get_buffer_status():
        """Get current buffer statistics"""
        total = LoRaPayloadBuffer.query.count()
        received = LoRaPayloadBuffer.query.filter_by(status=PayloadStatus.RECEIVED).count()
        processing = LoRaPayloadBuffer.query.filter_by(status=PayloadStatus.PROCESSING).count()
        processed = LoRaPayloadBuffer.query.filter_by(status=PayloadStatus.PROCESSED).count()
        duplicates = LoRaPayloadBuffer.query.filter_by(status=PayloadStatus.DUPLICATE).count()
        errors = LoRaPayloadBuffer.query.filter_by(status=PayloadStatus.ERROR).count()

        return {
            'total': total,
            'received': received,
            'processing': processing,
            'processed': processed,
            'duplicates': duplicates,
            'errors': errors
        }
