"""
Tests for Tracker API Endpoints - Phase 3: Permissions and API

Tests cover:
1. Permission checks for status changes
2. Validation through API endpoints  
3. Production flag validation
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tracker_workflow import TrackerWorkflowService
from app.models.reporting_effort_item_tracker import ProductionStatus, QCStatus
from app.models.user import UserRole


class TestEditorCanChangeOwnProductionStatus:
    """Test that editors can change production status for tasks assigned to them."""

    def test_editor_can_change_own_production_status(self):
        """Editor assigned as prod_programmer can change production_status."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.EDITOR
        
        tracker = MagicMock()
        tracker.production_programmer_id = 1  # Same as user
        tracker.qc_programmer_id = 2
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "production_status"
        )
        
        assert has_permission is True
        assert error == ""

    def test_editor_can_change_own_qc_status(self):
        """Editor assigned as qc_programmer can change qc_status."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.EDITOR
        
        tracker = MagicMock()
        tracker.production_programmer_id = 2
        tracker.qc_programmer_id = 1  # Same as user
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "qc_status"
        )
        
        assert has_permission is True
        assert error == ""


class TestEditorCannotChangeOthersStatus:
    """Test that editors cannot change status for tasks not assigned to them."""

    def test_editor_cannot_change_others_production_status(self):
        """Editor NOT assigned returns permission denied."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.EDITOR
        
        tracker = MagicMock()
        tracker.production_programmer_id = 2  # Different user
        tracker.qc_programmer_id = 3
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "production_status"
        )
        
        assert has_permission is False
        assert "assigned to you" in error

    def test_editor_cannot_change_others_qc_status(self):
        """Editor NOT assigned to QC cannot change qc_status."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.EDITOR
        
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 2  # Different user
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "qc_status"
        )
        
        assert has_permission is False
        assert "assigned to you" in error


class TestAdminCanChangeAnyStatus:
    """Test that admins can change any task's status."""

    def test_admin_can_change_any_production_status(self):
        """Admin can change any task's production status."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.ADMIN
        
        tracker = MagicMock()
        tracker.production_programmer_id = 2  # Different user
        tracker.qc_programmer_id = 3
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "production_status"
        )
        
        assert has_permission is True
        assert error == ""

    def test_admin_can_change_any_qc_status(self):
        """Admin can change any task's QC status."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.ADMIN
        
        tracker = MagicMock()
        tracker.production_programmer_id = 2
        tracker.qc_programmer_id = 3  # Different user
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "qc_status"
        )
        
        assert has_permission is True
        assert error == ""


class TestViewerCannotChangeStatus:
    """Test that viewers cannot change any status."""

    def test_viewer_cannot_change_production_status(self):
        """Viewer cannot change production status."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.VIEWER
        
        tracker = MagicMock()
        tracker.production_programmer_id = 1  # Even if "assigned"
        tracker.qc_programmer_id = 1
        
        has_permission, error = TrackerWorkflowService.check_status_change_permission(
            user, tracker, "production_status"
        )
        
        assert has_permission is False
        assert "Viewers do not have permission" in error


class TestProdFlagRequiresBothCompleted:
    """Test that prod flag can only be set when both statuses are completed."""

    def test_prod_flag_blocked_when_production_not_completed(self):
        """Prod flag blocked when production is not completed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.COMPLETED.value
        
        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, True)
        
        assert is_valid is False
        assert "production is completed" in error

    def test_prod_flag_blocked_when_qc_not_completed(self):
        """Prod flag blocked when QC is not completed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.COMPLETED.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value
        
        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, True)
        
        assert is_valid is False
        assert "QC is completed" in error

    def test_prod_flag_allowed_when_both_completed(self):
        """Prod flag allowed when both are completed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.COMPLETED.value
        tracker.qc_status = QCStatus.COMPLETED.value
        
        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, True)
        
        assert is_valid is True
        assert error == ""


class TestProdFlagClearsOnReopen:
    """Test that prod flag is cleared when production is reopened."""

    def test_prod_flag_clears_on_reopen(self):
        """When production reopens from COMPLETED, in_production_flag should clear."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.COMPLETED.value
        tracker.qc_status = QCStatus.COMPLETED.value
        tracker.in_production_flag = True

        updates = TrackerWorkflowService.apply_status_transition(
            tracker, "production_status", ProductionStatus.IN_PROGRESS.value
        )

        assert updates.get("in_production_flag") is False


class TestCanUserModifyTracker:
    """Test the can_user_modify_tracker permission matrix."""

    def test_admin_can_modify_all_fields(self):
        """Admin can modify all tracker fields."""
        user = MagicMock()
        user.role = UserRole.ADMIN
        
        tracker = MagicMock()
        tracker.production_programmer_id = 2
        tracker.qc_programmer_id = 3
        
        permissions = TrackerWorkflowService.can_user_modify_tracker(user, tracker)
        
        assert permissions["production_status"] is True
        assert permissions["qc_status"] is True
        assert permissions["in_production_flag"] is True

    def test_viewer_cannot_modify_any_fields(self):
        """Viewer cannot modify any tracker fields."""
        user = MagicMock()
        user.role = UserRole.VIEWER
        
        tracker = MagicMock()
        
        permissions = TrackerWorkflowService.can_user_modify_tracker(user, tracker)
        
        assert permissions["production_status"] is False
        assert permissions["qc_status"] is False
        assert permissions["in_production_flag"] is False

    def test_editor_can_only_modify_assigned_fields(self):
        """Editor can only modify fields for tasks assigned to them."""
        user = MagicMock()
        user.id = 1
        user.role = UserRole.EDITOR
        
        tracker = MagicMock()
        tracker.production_programmer_id = 1  # Assigned
        tracker.qc_programmer_id = 2  # Not assigned
        
        permissions = TrackerWorkflowService.can_user_modify_tracker(user, tracker)
        
        assert permissions["production_status"] is True  # Assigned
        assert permissions["qc_status"] is False  # Not assigned
        assert permissions["in_production_flag"] is True  # Can modify as production programmer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

