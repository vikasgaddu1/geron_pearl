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


class TestAutoTransitions:
    """Test automatic status transitions between Production and QC."""

    def test_qc_fail_auto_sets_production_in_progress(self):
        """When QC→FAILED, production should auto-set to IN_PROGRESS."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        updates = TrackerWorkflowService.apply_status_transition(
            tracker, "qc_status", QCStatus.FAILED.value
        )

        assert updates["qc_status"] == QCStatus.FAILED.value
        assert updates["production_status"] == ProductionStatus.IN_PROGRESS.value

    def test_qc_complete_auto_sets_production_complete(self):
        """When QC→COMPLETED, production should auto-set to COMPLETED."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.READY_FOR_QC.value
        tracker.qc_status = QCStatus.IN_PROGRESS.value

        updates = TrackerWorkflowService.apply_status_transition(
            tracker, "qc_status", QCStatus.COMPLETED.value
        )

        assert updates["qc_status"] == QCStatus.COMPLETED.value
        assert updates["production_status"] == ProductionStatus.COMPLETED.value

    def test_production_reopen_auto_sets_qc_in_progress(self):
        """When production COMPLETED→IN_PROGRESS, QC should auto-set to IN_PROGRESS."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.COMPLETED.value
        tracker.qc_status = QCStatus.COMPLETED.value
        tracker.in_production_flag = True

        updates = TrackerWorkflowService.apply_status_transition(
            tracker, "production_status", ProductionStatus.IN_PROGRESS.value
        )

        assert updates["production_status"] == ProductionStatus.IN_PROGRESS.value
        assert updates["qc_status"] == QCStatus.IN_PROGRESS.value

    def test_production_reopen_clears_prod_flag(self):
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

        assert updates["in_production_flag"] is False

    def test_production_ready_resets_qc_from_failed(self):
        """When production→READY_FOR_QC and QC is FAILED, QC should auto-set to IN_PROGRESS."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.IN_PROGRESS.value
        tracker.qc_status = QCStatus.FAILED.value

        updates = TrackerWorkflowService.apply_status_transition(
            tracker, "production_status", ProductionStatus.READY_FOR_QC.value
        )

        assert updates["production_status"] == ProductionStatus.READY_FOR_QC.value
        assert updates["qc_status"] == QCStatus.IN_PROGRESS.value

    def test_no_auto_transition_for_simple_status_change(self):
        """Simple status changes should not trigger auto-transitions."""
        tracker = MagicMock()
        tracker.production_programmer_id = 1
        tracker.qc_programmer_id = 1
        tracker.production_status = ProductionStatus.NOT_STARTED.value
        tracker.qc_status = QCStatus.NOT_STARTED.value

        updates = TrackerWorkflowService.apply_status_transition(
            tracker, "production_status", ProductionStatus.IN_PROGRESS.value
        )

        assert updates == {"production_status": ProductionStatus.IN_PROGRESS.value}
        assert "qc_status" not in updates


class TestStatusHistoryCreation:
    """Test creation of status history entries."""

    def test_status_change_creates_history_entry(self):
        """Every status change should create a history entry."""
        updates = {"production_status": ProductionStatus.IN_PROGRESS.value}

        entries = TrackerWorkflowService.create_history_entries(
            tracker_id=1,
            updates=updates,
            previous_production_status=ProductionStatus.NOT_STARTED.value,
            previous_qc_status=QCStatus.NOT_STARTED.value,
            user_id=1
        )

        assert len(entries) == 1
        assert entries[0].status_field == "production"
        assert entries[0].status_value == ProductionStatus.IN_PROGRESS.value
        assert entries[0].tracker_id == 1
        assert entries[0].changed_by_user_id == 1

    def test_cascading_changes_create_multiple_history_entries(self):
        """Auto-transitions should create history entries for all changed statuses."""
        updates = {
            "qc_status": QCStatus.COMPLETED.value,
            "production_status": ProductionStatus.COMPLETED.value  # Auto-set
        }

        entries = TrackerWorkflowService.create_history_entries(
            tracker_id=1,
            updates=updates,
            previous_production_status=ProductionStatus.READY_FOR_QC.value,
            previous_qc_status=QCStatus.IN_PROGRESS.value,
            user_id=1
        )

        assert len(entries) == 2
        status_fields = [e.status_field for e in entries]
        assert "production" in status_fields
        assert "qc" in status_fields

    def test_no_history_entry_if_status_unchanged(self):
        """No history entry if the status value is the same."""
        updates = {"production_status": ProductionStatus.IN_PROGRESS.value}

        entries = TrackerWorkflowService.create_history_entries(
            tracker_id=1,
            updates=updates,
            previous_production_status=ProductionStatus.IN_PROGRESS.value,  # Same!
            previous_qc_status=QCStatus.NOT_STARTED.value,
            user_id=1
        )

        assert len(entries) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

