"""
Office System Data Adapter

Maps Office SQLite schema (synced to MongoDB) to SAAS expected schema.
Provides a transparent adapter layer so SAAS models work with office data
without requiring data duplication or transformation in MongoDB.

Architecture:
- Each feedlot has its own Office Raspberry Pi
- Office Pi syncs to a shared MongoDB (per-feedlot collections or shared with namespace)
- SAAS querying needs to filter by feedlot_code to get the right office data

Office sends raw SQLite data to MongoDB:
  - Field names differ (lf_id vs lf_tag, epc vs uhf_tag)
  - Uses integer IDs instead of ObjectId
  - Missing feedlot association
  - Different field naming conventions

This adapter handles the mapping transparently.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from bson import ObjectId
import logging
import os

log = logging.getLogger(__name__)


class OfficeDataMapping:
    """Defines how Office SQLite fields map to SAAS MongoDB fields"""

    # Office collection names
    OFFICE_EVENTS = 'events'
    OFFICE_LIVESTOCK = 'livestock'
    OFFICE_BATCHES = 'batches'
    OFFICE_EVENT_AUDIT = 'event_audit'

    # SAAS collection names
    SAAS_CATTLE = 'cattle'
    SAAS_BATCHES = 'batches'
    SAAS_FEEDLOTS = 'feedlots'
    SAAS_OFFICE_MAPPING = 'office_id_mapping'  # Maps office IDs to SAAS ObjectIds

    # Field mapping: Office → SAAS
    LIVESTOCK_FIELD_MAPPING = {
        'lf_id': 'lf_tag',
        'epc': 'uhf_tag',
        'livestock_id': 'cattle_id',
    }

    BATCH_FIELD_MAPPING = {
        'first_induction_at': 'induction_date',
        'batch_name': 'batch_number',
    }

    # Default values for SAAS fields not provided by office
    LIVESTOCK_DEFAULTS = {
        'weight': 0,
        'health_status': 'unknown',
        'status': 'active',
        'pen_id': None,
        'weight_history': [],
        'tag_pair_history': [],
    }

    BATCH_DEFAULTS = {
        'notes': '',
    }


class OfficeAdapter:
    """
    Adapter for transforming Office data to SAAS format on-the-fly.

    Does NOT modify MongoDB data - instead transforms query results
    when reading from office collections.
    """

    def __init__(self, db):
        """
        Initialize adapter with database connection

        Args:
            db: PyMongo database instance (from app/__init__.py)
        """
        self.db = db
        self.mapping = OfficeDataMapping()
        self._feedlot_code_cache = {}  # Cache feedlot_code → ObjectId mapping

    def set_feedlot_context(self, feedlot_id: str):
        """
        Set the current feedlot context for querying office data

        Each feedlot has its own office Raspberry Pi that syncs data.
        This method sets which feedlot's office data to query.

        Args:
            feedlot_id: SAAS feedlot ObjectId
        """
        self.current_feedlot_id = ObjectId(feedlot_id) if isinstance(feedlot_id, str) else feedlot_id

    def get_feedlot_code_for_feedlot(self, feedlot_id) -> Optional[str]:
        """
        Get office feedlot_code from SAAS feedlot

        The office system identifies feedlots by feedlot_code (e.g., FEEDLOT001).
        Each office Raspberry Pi syncs its data to MongoDB with this code.

        Args:
            feedlot_id: SAAS feedlot ObjectId

        Returns:
            Office feedlot_code string, or None
        """
        try:
            from app.models.feedlot import Feedlot
            feedlot = Feedlot.find_by_id(str(feedlot_id))
            if feedlot:
                return feedlot.get('feedlot_code')
            return None
        except Exception as e:
            log.error(f"Error getting feedlot code: {e}")
            return None

    def get_office_livestock_by_id(self, livestock_id: int) -> Optional[Dict[str, Any]]:
        """
        Get livestock record from office data and transform to SAAS format

        Args:
            livestock_id: Integer livestock ID from office

        Returns:
            Transformed livestock dict in SAAS format, or None
        """
        try:
            collection = self.db[self.mapping.OFFICE_LIVESTOCK]
            office_record = collection.find_one({'livestock_id': livestock_id})

            if not office_record:
                return None

            return self._transform_livestock(office_record)
        except Exception as e:
            log.error(f"Error getting office livestock {livestock_id}: {e}")
            return None

    def get_office_livestock_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """
        Get all livestock for a batch from office data

        Args:
            batch_id: Integer batch ID from office

        Returns:
            List of transformed livestock dicts
        """
        try:
            collection = self.db[self.mapping.OFFICE_LIVESTOCK]
            office_records = list(collection.find({'batch_id': batch_id}))

            return [self._transform_livestock(record) for record in office_records]
        except Exception as e:
            log.error(f"Error getting office livestock for batch {batch_id}: {e}")
            return []

    def get_office_batch_by_id(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """
        Get batch record from office data and transform to SAAS format

        Args:
            batch_id: Integer batch ID from office (SQLite id)

        Returns:
            Transformed batch dict in SAAS format, or None
        """
        try:
            collection = self.db[self.mapping.OFFICE_BATCHES]
            # Office batches are keyed by their integer id or first_event_id
            # Try both approaches
            office_record = collection.find_one({'_id': batch_id})

            if not office_record:
                # Try alternate lookup by event ID
                office_record = collection.find_one({'id': batch_id})

            if not office_record:
                return None

            return self._transform_batch(office_record)
        except Exception as e:
            log.error(f"Error getting office batch {batch_id}: {e}")
            return None

    def get_office_batches_all(self) -> List[Dict[str, Any]]:
        """
        Get all batches from office data

        Returns:
            List of transformed batch dicts
        """
        try:
            collection = self.db[self.mapping.OFFICE_BATCHES]
            office_records = list(collection.find({}))

            return [self._transform_batch(record) for record in office_records]
        except Exception as e:
            log.error(f"Error getting all office batches: {e}")
            return []

    def get_office_events_for_livestock(self, livestock_id: int) -> List[Dict[str, Any]]:
        """
        Get all events for a livestock from audit trail

        Args:
            livestock_id: Integer livestock ID

        Returns:
            List of event records
        """
        try:
            collection = self.db[self.mapping.OFFICE_EVENT_AUDIT]
            events = list(collection.find({'livestock_id': livestock_id}).sort('received_at', 1))

            return events
        except Exception as e:
            log.error(f"Error getting office events for livestock {livestock_id}: {e}")
            return []

    def _transform_livestock(self, office_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform office livestock record to SAAS cattle format

        Maps field names and adds defaults for missing fields.
        Keeps _id as ObjectId from MongoDB for SAAS reference.
        """
        if not office_record:
            return None

        # Create new record with mapped fields
        transformed = {}

        # Keep MongoDB _id as-is (ObjectId)
        if '_id' in office_record:
            transformed['_id'] = office_record['_id']

        # Map field names according to mapping
        for office_field, saas_field in self.mapping.LIVESTOCK_FIELD_MAPPING.items():
            if office_field in office_record:
                transformed[saas_field] = office_record[office_field]

        # Copy unmapped fields that exist in office record
        unmapped_fields = [
            'batch_id', 'induction_event_id', 'first_induction_at',
            'created_at', 'id', 'livestock_id'
        ]
        for field in unmapped_fields:
            if field in office_record:
                transformed[field] = office_record[field]

        # Add defaults for SAAS-specific fields
        for field, default_value in self.mapping.LIVESTOCK_DEFAULTS.items():
            if field not in transformed:
                transformed[field] = default_value

        # Ensure feedlot_id exists (will be populated by SAAS model if needed)
        if 'feedlot_id' not in transformed:
            transformed['feedlot_id'] = None

        # Map first_induction_at to induction_date if not already set
        if 'induction_date' not in transformed and 'first_induction_at' in office_record:
            transformed['induction_date'] = office_record['first_induction_at']

        # Add updated_at timestamp if not present (for SAAS compatibility)
        if 'updated_at' not in transformed:
            transformed['updated_at'] = transformed.get('created_at', datetime.utcnow())

        return transformed

    def _transform_batch(self, office_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform office batch record to SAAS batch format

        Maps field names and adds defaults for missing fields.
        """
        if not office_record:
            return None

        # Create new record with mapped fields
        transformed = {}

        # Keep MongoDB _id as-is (ObjectId)
        if '_id' in office_record:
            transformed['_id'] = office_record['_id']

        # Map field names
        for office_field, saas_field in self.mapping.BATCH_FIELD_MAPPING.items():
            if office_field in office_record:
                transformed[saas_field] = office_record[office_field]

        # Copy unmapped fields that exist
        unmapped_fields = [
            'funder', 'lot', 'pen', 'lot_group', 'pen_location', 'sex',
            'tag_color', 'visual_id', 'notes', 'barn_prefix', 'first_event_id',
            'created_at', 'id', 'batch_name'
        ]
        for field in unmapped_fields:
            if field in office_record:
                transformed[field] = office_record[field]

        # Add defaults
        for field, default_value in self.mapping.BATCH_DEFAULTS.items():
            if field not in transformed:
                transformed[field] = default_value

        # Ensure feedlot_id exists
        if 'feedlot_id' not in transformed:
            transformed['feedlot_id'] = None

        # Ensure batch_number exists (mapped from batch_name)
        if 'batch_number' not in transformed and 'batch_name' in transformed:
            transformed['batch_number'] = transformed['batch_name']
        elif 'batch_number' not in transformed:
            # Generate from first_event_id if available
            if 'first_event_id' in office_record:
                transformed['batch_number'] = office_record['first_event_id']
            else:
                transformed['batch_number'] = 'BATCH_' + str(office_record.get('id', ''))

        # Add updated_at if not present
        if 'updated_at' not in transformed:
            transformed['updated_at'] = transformed.get('created_at', datetime.utcnow())

        # Map induction_date if not already set
        if 'induction_date' not in transformed and 'first_induction_at' in office_record:
            transformed['induction_date'] = office_record['first_induction_at']

        return transformed

    def is_office_collection(self, collection_name: str) -> bool:
        """Check if collection name is from office system"""
        return collection_name in [
            self.mapping.OFFICE_EVENTS,
            self.mapping.OFFICE_LIVESTOCK,
            self.mapping.OFFICE_BATCHES,
            self.mapping.OFFICE_EVENT_AUDIT,
        ]

    def map_office_id_to_saas(self, office_id: int, id_type: str) -> Optional[ObjectId]:
        """
        Get or create SAAS ObjectId for office integer ID

        Maps office integer IDs to SAAS ObjectIds for reference consistency.
        Uses a mapping table in MongoDB to maintain the relationship.

        Args:
            office_id: Integer ID from office system
            id_type: Type of ID (livestock, batch, feedlot)

        Returns:
            ObjectId for use in SAAS, or None if not found
        """
        try:
            mapping_collection = self.db[self.mapping.SAAS_OFFICE_MAPPING]

            # Look up existing mapping
            mapping = mapping_collection.find_one({
                'office_id': office_id,
                'type': id_type
            })

            if mapping:
                return mapping['saas_id']

            # No mapping found - could create one, but for now just return None
            log.debug(f"No SAAS mapping found for office {id_type} {office_id}")
            return None
        except Exception as e:
            log.error(f"Error mapping office ID: {e}")
            return None


def get_office_adapter(db) -> OfficeAdapter:
    """Factory function to get office adapter instance"""
    return OfficeAdapter(db)
