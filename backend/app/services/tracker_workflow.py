"""
Tracker Workflow Service

Business logic for Production/QC/Biostat status transitions, validation, and auto-updates.
"""

from typing import Tuple, Dict, Any, Optional
from datetime import datetime, date
from app.models.reporting_effort_item_tracker import (
    ReportingEffortItemTracker,
    ProductionStatus,
    QCStatus,
    BiostatStatus,
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
        new_status: str,
        item_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate if a status change is allowed.

        Args:
            tracker: The tracker instance
            status_field: 'production_status', 'qc_status', or 'biostat_status'
            new_status: The new status value to set
            item_type: Optional item type ('TLF' or 'Dataset') for biostat validation

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
        elif status_field == "biostat_status":
            # Biostat status can only change for TLF items
            if item_type and item_type != "TLF":
                return False, "Biostat review only applies to TLF items"
            if not tracker.biostat_reviewer_id:
                return False, "Biostat reviewer must be assigned before changing biostat status"
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

        # Rule 4: Biostat can only PASS or FAIL if QC is COMPLETED
        if status_field == "biostat_status":
            if new_status in [BiostatStatus.PASSED.value, BiostatStatus.FAILED.value]:
                if tracker.qc_status != QCStatus.COMPLETED.value:
                    return False, f"Biostat can only be marked as {new_status} when QC is completed"

        # Rule 5: Cannot change QC status after biostat has passed (workflow complete)
        if status_field == "qc_status" and tracker.biostat_status == BiostatStatus.PASSED.value:
            return False, "Cannot change QC status after biostat review has passed"

        return True, ""

    @staticmethod
    def validate_prod_flag(
        tracker: ReportingEffortItemTracker,
        new_value: bool,
        item_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate if the in_production_flag can be set.

        The flag can only be True when:
        - Both production and QC are completed
        - For TLF items: biostat status must also be 'passed'

        Args:
            tracker: The tracker instance
            new_value: The desired flag value
            item_type: Optional item type ('TLF' or 'Dataset') for biostat validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        if new_value:
            if tracker.production_status != ProductionStatus.COMPLETED.value:
                return False, "In Production flag can only be set when production is completed"
            if tracker.qc_status != QCStatus.COMPLETED.value:
                return False, "In Production flag can only be set when QC is completed"
            # For TLF items, biostat must also be passed
            if item_type == "TLF" and tracker.biostat_status != BiostatStatus.PASSED.value:
                return False, "In Production flag can only be set when biostat review has passed (TLF items require biostat approval)"
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

    @staticmethod
    def get_allowed_biostat_statuses(tracker: ReportingEffortItemTracker, item_type: Optional[str] = None) -> list:
        """
        Get the list of biostat statuses the user can transition to.

        PASSED and FAILED are only allowed when QC is COMPLETED.
        Not applicable for Dataset items.

        Args:
            tracker: The tracker instance
            item_type: Optional item type ('TLF' or 'Dataset')

        Returns:
            List of allowed BiostatStatus values
        """
        # Dataset items don't have biostat review
        if item_type and item_type != "TLF":
            return [BiostatStatus.NOT_APPLICABLE.value]

        # If biostat_status is not_applicable but item is TLF, return pending as option
        if tracker.biostat_status == BiostatStatus.NOT_APPLICABLE.value:
            return [BiostatStatus.NOT_APPLICABLE.value, BiostatStatus.PENDING.value]

        base_statuses = [BiostatStatus.PENDING.value]

        # Add PASSED and FAILED only if QC is completed
        if tracker.qc_status == QCStatus.COMPLETED.value:
            base_statuses.extend([
                BiostatStatus.PASSED.value,
                BiostatStatus.FAILED.value,
            ])

        return base_statuses

    @staticmethod
    def validate_ready_for_qc(
        tracker: ReportingEffortItemTracker
    ) -> Tuple[bool, str]:
        """
        Validate if production can be moved to ready_for_qc.

        Blocked if there are unresolved biostat comments.

        Args:
            tracker: The tracker instance

        Returns:
            Tuple of (is_valid, error_message)
        """
        if tracker.unresolved_biostat_comment_count > 0:
            return False, f"Cannot mark as ready for QC: {tracker.unresolved_biostat_comment_count} unresolved biostat comment(s) must be addressed first"
        return True, ""

    @staticmethod
    def validate_biostat_pass(
        tracker: ReportingEffortItemTracker
    ) -> Tuple[bool, str]:
        """
        Validate if biostat can pass the item.

        Blocked if there are unresolved QC comments.

        Args:
            tracker: The tracker instance

        Returns:
            Tuple of (is_valid, error_message)
        """
        if tracker.unresolved_comment_count > 0:
            return False, f"Cannot pass biostat review: {tracker.unresolved_comment_count} unresolved comment(s) must be addressed first"
        return True, ""

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
        - Editor: Can only change production/QC status for tasks they are assigned to
        - Biostat: Can only change biostat status for tasks they are assigned to review
        - Viewer: Cannot change any status

        Args:
            user: The user attempting the change
            tracker: The tracker being modified
            status_field: 'production_status', 'qc_status', or 'biostat_status'
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

            # Study Biostat can only change biostat status for tasks assigned to them
            if study_role == StudyRole.BIOSTAT:
                if status_field == "biostat_status":
                    if tracker.biostat_reviewer_id != user.id:
                        return False, "You can only update biostat status for items assigned to you for review"
                    return True, ""
                else:
                    return False, "Biostat role can only update biostat review status"

            # Study Editor can only change status for tasks they're assigned to
            if study_role == StudyRole.EDITOR:
                if status_field == "production_status":
                    if tracker.production_programmer_id != user.id:
                        return False, "You can only update production status for tasks assigned to you"
                elif status_field == "qc_status":
                    if tracker.qc_programmer_id != user.id:
                        return False, "You can only update QC status for tasks assigned to you"
                elif status_field == "biostat_status":
                    return False, "Editors cannot update biostat status"
                else:
                    return False, f"Invalid status field: {status_field}"
                return True, ""

        # Fallback to non-admin behavior
        # Non-admins can only change status for tasks they're assigned to

        if status_field == "production_status":
            if tracker.production_programmer_id != user.id:
                return False, "You can only update production status for tasks assigned to you"
        elif status_field == "qc_status":
            if tracker.qc_programmer_id != user.id:
                return False, "You can only update QC status for tasks assigned to you"
        elif status_field == "biostat_status":
            if tracker.biostat_reviewer_id != user.id:
                return False, "You can only update biostat status for items assigned to you for review"
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
                "biostat_status": True,
                "in_production_flag": True,
            }

        # If study_role is provided, use it for permission determination
        if study_role is not None:
            # Responsible user has full access within the study
            if study_role == RESPONSIBLE_ROLE:
                return {
                    "production_status": True,
                    "qc_status": True,
                    "biostat_status": True,
                    "in_production_flag": True,
                }

            # Study Viewer has no access
            if study_role == StudyRole.VIEWER:
                return {
                    "production_status": False,
                    "qc_status": False,
                    "biostat_status": False,
                    "in_production_flag": False,
                }

            # Study Biostat can only modify biostat status for assigned items
            if study_role == StudyRole.BIOSTAT:
                return {
                    "production_status": False,
                    "qc_status": False,
                    "biostat_status": tracker.biostat_reviewer_id == user.id,
                    "in_production_flag": False,
                }

            # Study Editor can only modify assigned tasks (no biostat access)
            if study_role == StudyRole.EDITOR:
                return {
                    "production_status": tracker.production_programmer_id == user.id,
                    "qc_status": tracker.qc_programmer_id == user.id,
                    "biostat_status": False,
                    "in_production_flag": (
                        tracker.production_programmer_id == user.id or
                        tracker.qc_programmer_id == user.id
                    ),
                }

        # Fallback to non-admin users - can only modify assigned tasks
        return {
            "production_status": tracker.production_programmer_id == user.id,
            "qc_status": tracker.qc_programmer_id == user.id,
            "biostat_status": tracker.biostat_reviewer_id == user.id,
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
        new_status: str,
        item_type: Optional[str] = None,
        default_biostat_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Apply a status change and calculate any cascading auto-updates.

        Auto-transition rules:
        1. QC → FAILED: Production → IN_PROGRESS
        2. QC → COMPLETED: Production → COMPLETED, and for TLF: biostat → PENDING
        3. Production COMPLETED → IN_PROGRESS: QC → IN_PROGRESS, in_production_flag = False
        4. Production → READY_FOR_QC (when QC = FAILED): QC → IN_PROGRESS
        5. Biostat → FAILED: Production → IN_PROGRESS, QC → NOT_STARTED
        6. Biostat → PASSED: biostat_review_date = today

        Args:
            tracker: The tracker instance
            status_field: 'production_status', 'qc_status', or 'biostat_status'
            new_status: The new status value to set
            item_type: Optional item type ('TLF' or 'Dataset') for biostat rules
            default_biostat_id: Optional default biostat reviewer ID for auto-assignment

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
            # For TLF items: also set biostat_status → PENDING and assign default biostat
            elif new_status == QCStatus.COMPLETED.value:
                updates["production_status"] = ProductionStatus.COMPLETED.value
                # Auto-transition to biostat review for TLF items
                if item_type == "TLF":
                    updates["biostat_status"] = BiostatStatus.PENDING.value
                    # Auto-assign default biostat if available and not already assigned
                    if default_biostat_id and not tracker.biostat_reviewer_id:
                        updates["biostat_reviewer_id"] = default_biostat_id

        elif status_field == "production_status":
            # Rule 3: Production COMPLETED → IN_PROGRESS triggers QC → IN_PROGRESS + flag off
            if (tracker.production_status == ProductionStatus.COMPLETED.value and
                new_status == ProductionStatus.IN_PROGRESS.value):
                updates["qc_status"] = QCStatus.IN_PROGRESS.value
                updates["in_production_flag"] = False
                # Also reset biostat status to pending if it was passed
                if tracker.biostat_status == BiostatStatus.PASSED.value:
                    updates["biostat_status"] = BiostatStatus.PENDING.value

            # Rule 4: Production → READY_FOR_QC when QC is FAILED triggers QC → IN_PROGRESS
            elif (new_status == ProductionStatus.READY_FOR_QC.value and
                  tracker.qc_status == QCStatus.FAILED.value):
                updates["qc_status"] = QCStatus.IN_PROGRESS.value

        elif status_field == "biostat_status":
            # Rule 5: Biostat → FAILED triggers Production → IN_PROGRESS, QC → NOT_STARTED
            if new_status == BiostatStatus.FAILED.value:
                updates["production_status"] = ProductionStatus.IN_PROGRESS.value
                updates["qc_status"] = QCStatus.NOT_STARTED.value
                updates["in_production_flag"] = False
                updates["biostat_review_date"] = date.today()

            # Rule 6: Biostat → PASSED sets biostat_review_date
            elif new_status == BiostatStatus.PASSED.value:
                updates["biostat_review_date"] = date.today()

        return updates

    @staticmethod
    def create_history_entries(
        tracker_id: int,
        updates: Dict[str, Any],
        previous_production_status: str,
        previous_qc_status: str,
        previous_biostat_status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> list:
        """
        Create TrackerStatusHistory entries for status changes.

        Args:
            tracker_id: ID of the tracker
            updates: Dict of fields being updated
            previous_production_status: Previous production status value
            previous_qc_status: Previous QC status value
            previous_biostat_status: Previous biostat status value
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

        # Check if biostat status is changing
        if "biostat_status" in updates:
            new_status = updates["biostat_status"]
            if new_status != previous_biostat_status:
                # Create new entry for entering the new status
                history_entries.append(TrackerStatusHistory(
                    tracker_id=tracker_id,
                    status_field="biostat",
                    status_value=new_status,
                    entered_at=now,
                    changed_by_user_id=user_id
                ))

        return history_entries


# Create a singleton instance for easy import
tracker_workflow_service = TrackerWorkflowService()

