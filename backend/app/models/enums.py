"""Shared enum definitions for models."""

from enum import Enum


class ItemType(str, Enum):
    """Enum for item types (used by both package_item and reporting_effort_item)."""
    TLF = "TLF"
    Dataset = "Dataset"


class SourceType(str, Enum):
    """Enum for item source types."""
    PACKAGE = "package"
    REPORTING_EFFORT = "reporting_effort"
    CUSTOM = "custom"
    BULK_UPLOAD = "bulk_upload"