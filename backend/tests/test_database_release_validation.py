"""
Test database release validation (safe non-database test).

Following project testing constraints:
- No database operations (safe pattern)
- Individual test file to avoid session conflicts
- Validation testing only
"""

import pytest
from pydantic import ValidationError

from app.schemas.database_release import DatabaseReleaseCreate, DatabaseReleaseUpdate, DatabaseRelease


class TestDatabaseReleaseValidation:
    """Test database release schema validation."""
    
    def test_database_release_create_valid(self):
        """Test valid database release creation data."""
        valid_data = {
            "study_id": 1,
            "database_release_label": "Release v1.0"
        }
        schema = DatabaseReleaseCreate(**valid_data)
        assert schema.study_id == 1
        assert schema.database_release_label == "Release v1.0"
    
    def test_database_release_create_invalid_study_id(self):
        """Test invalid study_id validation."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseReleaseCreate(study_id=0, database_release_label="Release v1.0")
        assert "greater than 0" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            DatabaseReleaseCreate(study_id=-1, database_release_label="Release v1.0")
        assert "greater than 0" in str(exc_info.value)
    
    def test_database_release_create_empty_label(self):
        """Test empty label validation."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseReleaseCreate(study_id=1, database_release_label="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_database_release_create_long_label(self):
        """Test label length validation."""
        long_label = "x" * 256  # Exceeds 255 character limit
        with pytest.raises(ValidationError) as exc_info:
            DatabaseReleaseCreate(study_id=1, database_release_label=long_label)
        assert "at most 255 characters" in str(exc_info.value)
    
    def test_database_release_update_valid(self):
        """Test valid database release update data."""
        valid_data = {
            "database_release_label": "Updated Release v1.1"
        }
        schema = DatabaseReleaseUpdate(**valid_data)
        assert schema.database_release_label == "Updated Release v1.1"
    
    def test_database_release_update_empty_label(self):
        """Test empty label validation in update."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseReleaseUpdate(database_release_label="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_database_release_response_schema(self):
        """Test database release response schema."""
        valid_data = {
            "id": 1,
            "study_id": 1,
            "database_release_label": "Release v1.0"
        }
        schema = DatabaseRelease(**valid_data)
        assert schema.id == 1
        assert schema.study_id == 1
        assert schema.database_release_label == "Release v1.0"