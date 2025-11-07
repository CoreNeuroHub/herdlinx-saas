"""
Data adapters for integrating different data sources with SAAS

Currently supports:
- OfficeAdapter: Maps Office SQLite schema to SAAS MongoDB schema
"""

from .office_adapter import OfficeAdapter, get_office_adapter

__all__ = ['OfficeAdapter', 'get_office_adapter']
