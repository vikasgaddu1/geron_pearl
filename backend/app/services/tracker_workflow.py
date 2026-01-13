"""
Tracker Workflow Service

Business logic for Production/QC status transitions, validation, and auto-updates.
"""

from typing import Tuple, Dict, Any, Optional
from datetime import datetime
from app.models.reporting_effort_item_tracker import (
    ReportingEffortItemTracker,
    ProductionStatus,
    QCStatus,
)
from app.models.tracker_status_history import TrackerStatusHistory
from app.models.user import User
from app.models.user_study_role import StudyRole
from app.core.study_permissions import RESPONSIBLE_ROLE


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

    # =========================================================================
    # PERMISSION CHECKING METHODS
    # =========================================================================

    @staticmethod
    def check_status_change_permission(
        user: User,
        tracker: ReportingEffortItemTracker,
        status_field: str,
        study_role: Optional[StudyRole] = None
    ) -> Tuple[bool, str]:
        """
        Check if a user has permission to change a status field.
        
        Rules:
        - Global Admin: Can change any task's status
        - Study Lead: Can change any task's status within that study
        - Editor: Can only change status for tasks they are assigned to
        - Viewer: Cannot change any status
        
        Args:
            user: The user attempting the change
            tracker: The tracker being modified
            status_field: 'production_status' or 'qc_status'
            study_role: Optional study-specific role (takes precedence over global role)
            
        Returns:
            Tuple of (has_permission, error_message)
        """
        # Global Admin can do anything
        if user.is_admin:
            return True, ""
        
        # If study_role is provided, use it for permission checks
        if study_role is not None:
            # Responsible user has full access within the study
            if study_role == RESPONSIBLE_ROLE:
                return True, ""
            
            # Study Viewer cannot modify
            if study_role == StudyRole.VIEWER:
                return False, "Viewers do not have permission to change status"
            
            # Study Editor can only change status for tasks they're assigned to
            if study_role == StudyRole.EDITOR:
                if status_field == "production_status":
                    if tracker.production_programmer_id != user.id:
                        return False, "You can only update production status for tasks assigned to you"
                elif status_field == "qc_status":
                    if tracker.qc_programmer_id != user.id:
                        return False, "You can only update QC status for tasks assigned to you"
                else:
                    return False, f"Invalid status field: {status_field}"
                return True, ""
        
        # Fallback to non-admin behavior
        # Non-admins can only change status for tasks they're assigned to
        
        # Editor can only change status for tasks they're assigned to
        if status_field == "production_status":
            if tracker.production_programmer_id != user.id:
                return False, "You can only update production status for tasks assigned to you"
        elif status_field == "qc_status":
            if tracker.qc_programmer_id != user.id:
                return False, "You can only update QC status for tasks assigned to you"
        else:
            return False, f"Invalid status field: {status_field}"
        
        return True, ""

    @staticmethod
    def can_user_modify_tracker(
        user: User,
        tracker: ReportingEffortItemTracker,
        study_role: Optional[StudyRole] = None
    ) -> Dict[str, bool]:
        """
        Get which parts of a tracker a user can modify.
        
        Returns a dict indicating which fields the user can change.
        Used for frontend to enable/disable UI controls.
        
        Args:
            user: The user
            tracker: The tracker
            study_role: Optional study-specific role (takes precedence over global role)
            
        Returns:
            Dict with boolean flags for each modifiable field
        """
        # Global Admin has full access
        if user.is_admin:
            return {
                "production_status": True,
                "qc_status": True,
                "in_production_flag": True,
            }
        
        # If study_role is provided, use it for permission determination
        if study_role is not None:
            # Responsible user has full access within the study
            if study_role == RESPONSIBLE_ROLE:
                return {
                    "production_status": True,
                    "qc_status": True,
                    "in_production_flag": True,
                }
            
            # Study Viewer has no access
            if study_role == StudyRole.VIEWER:
                return {
                    "production_status": False,
                    "qc_status": False,
                    "in_production_flag": False,
                }
            
            # Study Editor can only modify assigned tasks
            if study_role == StudyRole.EDITOR:
                return {
                    "production_status": tracker.production_programmer_id == user.id,
                    "qc_status": tracker.qc_programmer_id == user.id,
                    "in_production_flag": (
                        tracker.production_programmer_id == user.id or 
                        tracker.qc_programmer_id == user.id
                    ),
                }
        
        # Fallback to non-admin users - can only modify assigned tasks
        return {
            "production_status": tracker.production_programmer_id == user.id,
            "qc_status": tracker.qc_programmer_id == user.id,
            "in_production_flag": (
                tracker.production_programmer_id == user.id or 
                tracker.qc_programmer_id == user.id
            ),
        }

    # =========================================================================
    # AUTO-TRANSITION METHODS
    # =========================================================================

    @staticmethod
    def apply_status_transition(
        tracker: ReportingEffortItemTracker,
        status_field: str,
        new_status: str
    ) -> Dict[str, Any]:
        """
        Apply a status change and calculate any cascading auto-updates.
        
        Auto-transition rules:
        1. QC → FAILED: Production → IN_PROGRESS
        2. QC → COMPLETED: Production → COMPLETED
        3. Production COMPLETED → IN_PROGRESS: QC → IN_PROGRESS, in_production_flag = False
        4. Production → READY_FOR_QC (when QC = FAILED): QC → IN_PROGRESS
        
        Args:
            tracker: The tracker instance
            status_field: 'production_status' or 'qc_status'
            new_status: The new status value to set
            
        Returns:
            Dict of all fields that need to be updated (including auto-transitions)
        """
        updates: Dict[str, Any] = {status_field: new_status}
        
        if status_field == "qc_status":
            # Rule 1: QC → FAILED triggers Production → IN_PROGRESS
            if (new_status == QCStatus.FAILED.value and 
                tracker.production_status == ProductionStatus.READY_FOR_QC.value):
                updates["production_status"] = ProductionStatus.IN_PROGRESS.value
            
            # Rule 2: QC → COMPLETED triggers Production → COMPLETED
            elif new_status == QCStatus.COMPLETED.value:
                updates["production_status"] = ProductionStatus.COMPLETED.value
        
        elif status_field == "production_status":
            # Rule 3: Production COMPLETED → IN_PROGRESS triggers QC → IN_PROGRESS + flag off
            if (tracker.production_status == ProductionStatus.COMPLETED.value and 
                new_status == ProductionStatus.IN_PROGRESS.value):
                updates["qc_status"] = QCStatus.IN_PROGRESS.value
                updates["in_production_flag"] = False
            
            # Rule 4: Production → READY_FOR_QC when QC is FAILED triggers QC → IN_PROGRESS
            elif (new_status == ProductionStatus.READY_FOR_QC.value and 
                  tracker.qc_status == QCStatus.FAILED.value):
                updates["qc_status"] = QCStatus.IN_PROGRESS.value
        
        return updates

    @staticmethod
    def create_history_entries(
        tracker_id: int,
        updates: Dict[str, Any],
        previous_production_status: str,
        previous_qc_status: str,
        user_id: Optional[int] = None
    ) -> list:
        """
        Create TrackerStatusHistory entries for status changes.
        
        Args:
            tracker_id: ID of the tracker
            updates: Dict of fields being updated
            previous_production_status: Previous production status value
            previous_qc_status: Previous QC status value
            user_id: ID of user making the change
            
        Returns:
            List of TrackerStatusHistory objects to be added to the session
        """
        history_entries = []
        now = datetime.utcnow()
        
        # Check if production status is changing
        if "production_status" in updates:
            new_status = updates["production_status"]
            if new_status != previous_production_status:
                # Create new entry for entering the new status
                history_entries.append(TrackerStatusHistory(
                    tracker_id=tracker_id,
                    status_field="production",
                    status_value=new_status,
                    entered_at=now,
                    changed_by_user_id=user_id
                ))
        
        # Check if QC status is changing
        if "qc_status" in updates:
            new_status = updates["qc_status"]
            if new_status != previous_qc_status:
                # Create new entry for entering the new status
                history_entries.append(TrackerStatusHistory(
                    tracker_id=tracker_id,
                    status_field="qc",
                    status_value=new_status,
                    entered_at=now,
                    changed_by_user_id=user_id
                ))
        
        return history_entries


# Create a singleton instance for easy import
tracker_workflow_service = TrackerWorkflowService()

