"""Schemas package."""

from app.schemas.study import Study, StudyCreate, StudyInDB, StudyUpdate
from app.schemas.database_release import DatabaseRelease, DatabaseReleaseCreate, DatabaseReleaseInDB, DatabaseReleaseUpdate
from app.schemas.reporting_effort import ReportingEffort, ReportingEffortCreate, ReportingEffortInDB, ReportingEffortUpdate
from app.schemas.text_element import TextElement, TextElementCreate, TextElementInDB, TextElementUpdate
from app.schemas.acronym import Acronym, AcronymCreate, AcronymInDB, AcronymUpdate
from app.schemas.acronym_set import AcronymSet, AcronymSetCreate, AcronymSetInDB, AcronymSetUpdate, AcronymSetWithMembers
from app.schemas.acronym_set_member import (
    AcronymSetMember, 
    AcronymSetMemberCreate, 
    AcronymSetMemberInDB, 
    AcronymSetMemberUpdate,
    AcronymSetMemberWithAcronym,
    AcronymSetMemberWithSet,
    AcronymSetMemberWithBoth
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
    # Acronym schemas
    "Acronym", "AcronymCreate", "AcronymInDB", "AcronymUpdate",
    # AcronymSet schemas
    "AcronymSet", "AcronymSetCreate", "AcronymSetInDB", "AcronymSetUpdate", "AcronymSetWithMembers",
    # AcronymSetMember schemas
    "AcronymSetMember", "AcronymSetMemberCreate", "AcronymSetMemberInDB", "AcronymSetMemberUpdate",
    "AcronymSetMemberWithAcronym", "AcronymSetMemberWithSet", "AcronymSetMemberWithBoth"
]