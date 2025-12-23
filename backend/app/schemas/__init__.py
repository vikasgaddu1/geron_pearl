"""Schemas package."""

from app.schemas.study import Study, StudyCreate, StudyInDB, StudyUpdate
from app.schemas.database_release import DatabaseRelease, DatabaseReleaseCreate, DatabaseReleaseInDB, DatabaseReleaseUpdate
from app.schemas.reporting_effort import ReportingEffort, ReportingEffortCreate, ReportingEffortInDB, ReportingEffortUpdate
from app.schemas.text_element import TextElement, TextElementCreate, TextElementInDB, TextElementUpdate
from app.schemas.package import Package, PackageCreate, PackageInDB, PackageUpdate, PackageWithItems
from app.schemas.package_item import (
    PackageItem, PackageItemCreate, PackageItemInDB, PackageItemUpdate,
    PackageItemCreateWithDetails, ItemTypeEnum,
    PackageTlfDetailsCreate, PackageTlfDetailsInDB,
    PackageDatasetDetailsCreate, PackageDatasetDetailsInDB,
    PackageItemFootnoteCreate, PackageItemAcronymCreate
)
from app.schemas.user import User, UserCreate, UserInDB, UserUpdate
from app.schemas.reporting_effort_item import (
    ReportingEffortItem, ReportingEffortItemCreate, ReportingEffortItemInDB, 
    ReportingEffortItemUpdate, ReportingEffortItemWithDetails
)
from app.schemas.reporting_effort_item_tracker import (
    ReportingEffortItemTracker, ReportingEffortItemTrackerCreate,
    ReportingEffortItemTrackerInDB, ReportingEffortItemTrackerUpdate,
    ReportingEffortItemTrackerWithDetails
)
from app.schemas.audit_log import (
    AuditLog, AuditLogCreate, AuditLogInDB, AuditLogWithDetails
)
from app.schemas.tracker_comment import (
    TrackerComment, TrackerCommentCreate, TrackerCommentInDB, 
    TrackerCommentUpdate, TrackerCommentSummary, CommentWithUserInfo
)
from app.schemas.tracker_tag import (
    TrackerTag, TrackerTagCreate, TrackerTagUpdate, TrackerTagWithCount,
    TrackerItemTag, TrackerItemTagCreate, TrackerItemTagWithDetails,
    BulkTagAssignment, BulkTagRemoval, BulkOperationResult, TagSummary
)

__all__ = [
    # Study schemas
    "Study", "StudyCreate", "StudyInDB", "StudyUpdate",
    # DatabaseRelease schemas  
    "DatabaseRelease", "DatabaseReleaseCreate", "DatabaseReleaseInDB", "DatabaseReleaseUpdate",
    # ReportingEffort schemas
    "ReportingEffort", "ReportingEffortCreate", "ReportingEffortInDB", "ReportingEffortUpdate",
    # TextElement schemas
    "TextElement", "TextElementCreate", "TextElementInDB", "TextElementUpdate",
    # Package schemas
    "Package", "PackageCreate", "PackageInDB", "PackageUpdate", "PackageWithItems",
    # PackageItem schemas
    "PackageItem", "PackageItemCreate", "PackageItemInDB", "PackageItemUpdate",
    "PackageItemCreateWithDetails", "ItemTypeEnum",
    "PackageTlfDetailsCreate", "PackageTlfDetailsInDB",
    "PackageDatasetDetailsCreate", "PackageDatasetDetailsInDB",
    "PackageItemFootnoteCreate", "PackageItemAcronymCreate",
    # User schemas
    "User", "UserCreate", "UserInDB", "UserUpdate",
    # ReportingEffortItem schemas
    "ReportingEffortItem", "ReportingEffortItemCreate", "ReportingEffortItemInDB",
    "ReportingEffortItemUpdate", "ReportingEffortItemWithDetails",
    # ReportingEffortItemTracker schemas
    "ReportingEffortItemTracker", "ReportingEffortItemTrackerCreate",
    "ReportingEffortItemTrackerInDB", "ReportingEffortItemTrackerUpdate",
    "ReportingEffortItemTrackerWithDetails",
    # AuditLog schemas
    "AuditLog", "AuditLogCreate", "AuditLogInDB", "AuditLogWithDetails",
    # TrackerComment schemas
    "TrackerComment", "TrackerCommentCreate", "TrackerCommentInDB", 
    "TrackerCommentUpdate", "TrackerCommentSummary", "CommentWithUserInfo",
    # TrackerTag schemas
    "TrackerTag", "TrackerTagCreate", "TrackerTagUpdate", "TrackerTagWithCount",
    "TrackerItemTag", "TrackerItemTagCreate", "TrackerItemTagWithDetails",
    "BulkTagAssignment", "BulkTagRemoval", "BulkOperationResult", "TagSummary"
]