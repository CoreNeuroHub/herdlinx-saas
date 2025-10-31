"""LoRa Payload Buffer Model

Stores incoming LoRa payloads for processing, deduplication, and batch creation.
"""
from datetime import datetime, timedelta
from office_app import db
from enum import Enum


class PayloadStatus(str, Enum):
    """Status of payload processing"""
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    ERROR = "error"


class LoRaPayloadBuffer(db.Model):
    """Buffer for incoming LoRa payloads"""
    __tablename__ = 'lora_payload_buffer'

    id = db.Column(db.Integer, primary_key=True)
    raw_payload = db.Column(db.String(255), nullable=False)  # e.g., hxb:BATCH001:LF123:UHF456
    payload_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)  # SHA256 hash for dedup
    source_type = db.Column(db.String(10))  # hxb or hxe
    batch_number = db.Column(db.String(50), index=True)
    lf_tag = db.Column(db.String(50))
    uhf_tag = db.Column(db.String(50))
    status = db.Column(db.String(20), default=PayloadStatus.RECEIVED, nullable=False)  # received, processing, processed, duplicate, error
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)  # Links to created batch
    error_message = db.Column(db.Text)  # Error details if processing failed
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to Batch
    batch = db.relationship('Batch', backref='payload_buffers', lazy=True)

    @staticmethod
    def create_from_payload(raw_payload, payload_hash):
        """Create a new payload buffer entry"""
        buffer_entry = LoRaPayloadBuffer(
            raw_payload=raw_payload,
            payload_hash=payload_hash,
            status=PayloadStatus.RECEIVED,
            received_at=datetime.utcnow()
        )
        db.session.add(buffer_entry)
        db.session.commit()
        return buffer_entry.id

    @staticmethod
    def find_by_hash(payload_hash):
        """Find payload by hash (for deduplication)"""
        return LoRaPayloadBuffer.query.filter_by(payload_hash=payload_hash).first()

    @staticmethod
    def get_pending_payloads(limit=100):
        """Get unprocessed payloads"""
        return LoRaPayloadBuffer.query.filter(
            LoRaPayloadBuffer.status == PayloadStatus.RECEIVED
        ).order_by(LoRaPayloadBuffer.received_at.asc()).limit(limit).all()

    @staticmethod
    def get_recent_payloads(hours=24, limit=100):
        """Get recently received payloads"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        return LoRaPayloadBuffer.query.filter(
            LoRaPayloadBuffer.received_at >= time_threshold
        ).order_by(LoRaPayloadBuffer.received_at.desc()).limit(limit).all()

    @staticmethod
    def mark_as_processing(payload_id):
        """Mark payload as being processed"""
        payload = LoRaPayloadBuffer.query.get(payload_id)
        if payload:
            payload.status = PayloadStatus.PROCESSING
            payload.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_as_processed(payload_id, batch_id):
        """Mark payload as successfully processed"""
        payload = LoRaPayloadBuffer.query.get(payload_id)
        if payload:
            payload.status = PayloadStatus.PROCESSED
            payload.batch_id = batch_id
            payload.processed_at = datetime.utcnow()
            payload.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_as_duplicate(payload_id, original_payload_id):
        """Mark payload as duplicate"""
        payload = LoRaPayloadBuffer.query.get(payload_id)
        if payload:
            payload.status = PayloadStatus.DUPLICATE
            payload.processed_at = datetime.utcnow()
            payload.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_as_error(payload_id, error_message):
        """Mark payload as error"""
        payload = LoRaPayloadBuffer.query.get(payload_id)
        if payload:
            payload.status = PayloadStatus.ERROR
            payload.error_message = error_message
            payload.processed_at = datetime.utcnow()
            payload.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_payload_data(payload_id, source_type, batch_number, lf_tag, uhf_tag):
        """Update parsed payload data"""
        payload = LoRaPayloadBuffer.query.get(payload_id)
        if payload:
            payload.source_type = source_type
            payload.batch_number = batch_number
            payload.lf_tag = lf_tag
            payload.uhf_tag = uhf_tag
            payload.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'raw_payload': self.raw_payload,
            'payload_hash': self.payload_hash,
            'source_type': self.source_type,
            'batch_number': self.batch_number,
            'lf_tag': self.lf_tag,
            'uhf_tag': self.uhf_tag,
            'status': self.status,
            'batch_id': self.batch_id,
            'error_message': self.error_message,
            'received_at': self.received_at,
            'processed_at': self.processed_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
