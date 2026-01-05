"""
Tests for Tracker Workflow Service - Phase 1: Validation Rules

Tests cover:
1. Status change requires programmer assignment
2. Production cannot set COMPLETED directly
3. QC can only set FAILED/COMPLETED when Production is READY_FOR_QC
"""

import pytest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tracker_workflow import TrackerWorkflowService
from app.models.reporting_effort_item_tracker import (
    ProductionStatus,
    QCStatus,
)


class TestStatusChangeRequiresProductionProgrammer:
    """Test that production status changes require a production programmer to be assigned."""

    def test_status_change_blocked_without_production_programmer(self):
        """Status change should be blocked if no production_programmer_id is set."""
        tracker = MagicMock()
        tracker.production_programmer_id = None
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.NOT_STARTED.value
        tracker.qc_status = QCStatus.NOT_STARTED.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "production_status", ProductionStatus.IN_PROGRESS.value
        )

        assert is_valid is False
        assert "Production programmer must be assigned" in error

    def test_status_change_allowed_with_production_programmer(self):
        """Status change should be allowed when production_programmer_id is set."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = None
        tracker.production_status = ProductionStatus.NOT_STARTED.value
        tracker.qc_status = QCStatus.NOT_STARTED.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "production_status", ProductionStatus.IN_PROGRESS.value
        )

        assert is_valid is True
        assert error == ""


class TestStatusChangeRequiresQCProgrammer:
    """Test that QC status changes require a QC programmer to be assigned."""

    def test_status_change_blocked_without_qc_programmer(self):
        """Status change should be blocked if no qc_programmer_id is set."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = None
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.NOT_STARTED.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "qc_status", QCStatus.IN_PROGRESS.value
        )

        assert is_valid is False
        assert "QC programmer must be assigned" in error

    def test_status_change_allowed_with_qc_programmer(self):
        """Status change should be allowed when qc_programmer_id is set."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.NOT_STARTED.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "qc_status", QCStatus.IN_PROGRESS.value
        )

        assert is_valid is True
        assert error == ""


class TestQCFailRequiresReadyForQC:
    """Test that QC can only set FAILED when Production is READY_FOR_QC."""

    def test_qc_fail_blocked_when_production_not_ready(self):
        """QC→FAILED should be blocked if production != READY_FOR_QC."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.IN_PROGRESS.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "qc_status", QCStatus.FAILED.value
        )

        assert is_valid is False
        assert "ready for QC" in error

    def test_qc_fail_allowed_when_production_ready(self):
        """QC→FAILED should be allowed when production is READY_FOR_QC."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "qc_status", QCStatus.FAILED.value
        )

        assert is_valid is True
        assert error == ""


class TestQCCompleteRequiresReadyForQC:
    """Test that QC can only set COMPLETED when Production is READY_FOR_QC."""

    def test_qc_complete_blocked_when_production_not_ready(self):
        """QC→COMPLETED should be blocked if production != READY_FOR_QC."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.IN_PROGRESS.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "qc_status", QCStatus.COMPLETED.value
        )

        assert is_valid is False
        assert "ready for QC" in error

    def test_qc_complete_allowed_when_production_ready(self):
        """QC→COMPLETED should be allowed when production is READY_FOR_QC."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "qc_status", QCStatus.COMPLETED.value
        )

        assert is_valid is True
        assert error == ""


class TestProductionCannotSetCompletedDirectly:
    """Test that Production status cannot be set to COMPLETED directly."""

    def test_production_completed_always_blocked(self):
        """Production→COMPLETED should always be blocked (must be auto-set)."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "production_status", ProductionStatus.COMPLETED.value
        )

        assert is_valid is False
        assert "completed when QC marks it as completed" in error

    def test_production_ready_for_qc_allowed(self):
        """Production can transition to READY_FOR_QC."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.IN_PROGRESS.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_status_change(
            tracker, "production_status", ProductionStatus.READY_FOR_QC.value
        )

        assert is_valid is True
        assert error == ""


class TestProdFlagValidation:
    """Test validation of in_production_flag."""

    def test_prod_flag_blocked_when_production_not_completed(self):
        """Prod flag should be blocked when production is not completed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.IN_PROGRESS.value
        tracker.qc_status = QCStatus.COMPLETED.value

        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, True)

        assert is_valid is False
        assert "production is completed" in error

    def test_prod_flag_blocked_when_qc_not_completed(self):
        """Prod flag should be blocked when QC is not completed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.COMPLETED.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, True)

        assert is_valid is False
        assert "QC is completed" in error

    def test_prod_flag_allowed_when_both_completed(self):
        """Prod flag should be allowed when both are completed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.COMPLETED.value
        tracker.qc_status = QCStatus.COMPLETED.value

        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, True)

        assert is_valid is True
        assert error == ""

    def test_prod_flag_false_always_allowed(self):
        """Setting prod flag to False should always be allowed."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.IN_PROGRESS.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        is_valid, error = TrackerWorkflowService.validate_prod_flag(tracker, False)

        assert is_valid is True
        assert error == ""


class TestAllowedStatusesMethods:
    """Test the methods that return allowed status transitions."""

    def test_production_completed_never_in_allowed_list(self):
        """COMPLETED should never be in the allowed production statuses list."""
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.COMPLETED.value

        allowed = TrackerWorkflowService.get_allowed_production_statuses(tracker)

        assert ProductionStatus.COMPLETED.value not in allowed
        assert ProductionStatus.READY_FOR_QC.value in allowed
        assert ProductionStatus.IN_PROGRESS.value in allowed

    def test_qc_fail_complete_only_when_production_ready(self):
        """FAILED and COMPLETED should only be in QC allowed list when production is READY_FOR_QC."""
        # When production is NOT ready
        tracker = MagicMock()
        tracker.production_status = ProductionStatus.IN_PROGRESS.value

        allowed = TrackerWorkflowService.get_allowed_qc_statuses(tracker)
        assert QCStatus.FAILED.value not in allowed
        assert QCStatus.COMPLETED.value not in allowed

        # When production IS ready
        tracker.production_status = ProductionStatus.READY_FOR_QC.value

        allowed = TrackerWorkflowService.get_allowed_qc_statuses(tracker)
        assert QCStatus.FAILED.value in allowed
        assert QCStatus.COMPLETED.value in allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

