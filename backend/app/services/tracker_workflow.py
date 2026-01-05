"""
Tracker Workflow Service

Business logic for Production/QC status transitions, validation, and auto-updates.
"""

from typing import Tuple, Dict, Any, Optional
from app.models.reporting_effort_item_tracker import (
    ReportingEffortItemTracker,
    ProductionStatus,
    QCStatus,
)


class TrackerWorkflowService:
    """
    Service for managing tracker workflow logic.
    
    Handles:
    - Status change validation (assignment required, transition rules)
    - Auto-transitions between Production and QC statuses
    - Prod flag validation
    """

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    @staticmethod
    def validate_status_change(
        tracker: ReportingEffortItemTracker,
        status_field: str,
        new_status: str
    ) -> Tuple[bool, str]:
        """
        Validate if a status change is allowed.
        
        Args:
            tracker: The tracker instance
            status_field: 'production_status' or 'qc_status'
            new_status: The new status value to set
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Rule 1: Status change requires programmer assignment
        if status_field == "production_status":
            if not tracker.production_programmer_id:
                return False, "Production programmer must be assigned before changing production status"
        elif status_field == "qc_status":
            if not tracker.qc_programmer_id:
                return False, "QC programmer must be assigned before changing QC status"
        else:
            return False, f"Invalid status field: {status_field}"

        # Rule 2: Production cannot set COMPLETED directly (only auto-set by QC)
        if status_field == "production_status" and new_status == ProductionStatus.COMPLETED.value:
            return False, "Production status can only be set to completed when QC marks it as completed"

        # Rule 3: QC can only set FAILED or COMPLETED if Production is READY_FOR_QC
        if status_field == "qc_status":
            if new_status in [QCStatus.FAILED.value, QCStatus.COMPLETED.value]:
                if tracker.production_status != ProductionStatus.READY_FOR_QC.value:
                    return False, f"QC can only be marked as {new_status} when production is ready for QC"

        return True, ""

    @staticmethod
    def validate_prod_flag(
        tracker: ReportingEffortItemTracker,
        new_value: bool
    ) -> Tuple[bool, str]:
        """
        Validate if the in_production_flag can be set.
        
        The flag can only be True when both production and QC are completed.
        
        Args:
            tracker: The tracker instance
            new_value: The desired flag value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if new_value:
            if tracker.production_status != ProductionStatus.COMPLETED.value:
                return False, "In Production flag can only be set when production is completed"
            if tracker.qc_status != QCStatus.COMPLETED.value:
                return False, "In Production flag can only be set when QC is completed"
        return True, ""

    @staticmethod
    def get_allowed_production_statuses(tracker: ReportingEffortItemTracker) -> list:
        """
        Get the list of production statuses the user can transition to.
        
        COMPLETED is never allowed as it's auto-set by QC completion.
        
        Args:
            tracker: The tracker instance
            
        Returns:
            List of allowed ProductionStatus values
        """
        # All statuses except COMPLETED (which is auto-set by QC)
        return [
            ProductionStatus.NOT_STARTED.value,
            ProductionStatus.IN_PROGRESS.value,
            ProductionStatus.READY_FOR_QC.value,
            ProductionStatus.ON_HOLD.value,
        ]

    @staticmethod
    def get_allowed_qc_statuses(tracker: ReportingEffortItemTracker) -> list:
        """
        Get the list of QC statuses the user can transition to.
        
        FAILED and COMPLETED are only allowed when production is READY_FOR_QC.
        
        Args:
            tracker: The tracker instance
            
        Returns:
            List of allowed QCStatus values
        """
        base_statuses = [
            QCStatus.NOT_STARTED.value,
            QCStatus.IN_PROGRESS.value,
            QCStatus.ON_HOLD.value,
        ]
        
        # Add FAILED and COMPLETED only if production is ready for QC
        if tracker.production_status == ProductionStatus.READY_FOR_QC.value:
            base_statuses.extend([
                QCStatus.FAILED.value,
                QCStatus.COMPLETED.value,
            ])
        
        return base_statuses


# Create a singleton instance for easy import
tracker_workflow_service = TrackerWorkflowService()

